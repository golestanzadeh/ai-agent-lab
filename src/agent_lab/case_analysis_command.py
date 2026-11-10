"""Unified command helpers; execution and durable state remain owned by Kernel."""
from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal
import csv, hashlib, io, json, re
from uuid import uuid4

from agent_lab.orchestrator_kernel import PermissionDenied

AUTHORITY='owner://unified-dashboard-analysis-20261110'

def read_document(host,request,document_id):
    reader=getattr(host,'get_analysis_document',host.get_case_document)
    return reader(request.case_id,request.tax_year,document_id)


def command(request):
    return {k:v for k,v in asdict(request).items() if k not in ('owner_id','successor_task_id')}


def admit(d, request):
    """Existing atomic Kernel intent is the durable idempotency reservation."""
    if d.worker is None:raise PermissionDenied('Worker unavailable')
    value=command(request);key=(request.owner_id,request.case_id,request.tax_year)
    with d._lock,d._kernel() as k,k.atomic_execution():
        k.verify_audit_chain()
        for task in d._tasks(k,request):
            values=[s[len('analysis-command:'):] for s in task['inputs'] if s.startswith('analysis-command:')]
            if values and json.loads(values[0])['request_id']==request.request_id:
                if json.loads(values[0])!=value:raise PermissionDenied('Request identity reused with different command')
                return {**task['case_context'],'status':'REGISTERED'}
        if k.kill_switch_state()!='RUNNING':raise PermissionDenied('Kill switch blocks analysis')
        if key in d._active or any(t['status'] in ('REGISTERED','ACTIVE') for t in d._tasks(k,request)):
            raise PermissionDenied('Execution active or requires reconciliation')
        if len(d._active)>=4:raise PermissionDenied('Bounded worker capacity reached')
        run='RUN-UI03-'+uuid4().hex.upper();task=d._task(request,run)
        task['inputs'] += [AUTHORITY,'analysis-command:'+json.dumps(value,sort_keys=True)]
        d._register(k,task)
        receipt={**task['case_context'],'status':'REGISTERED'}
        d._active[key]=receipt
        # Admission stays locked until submission; a crash leaves a durable
        # unstarted intent requiring reconciliation, never automatic replay.
        d._pool.submit(d._run,request,task)
        return receipt


def process(worker, request, batch, manifest, kernel, dispatcher):
    dispatcher.authorize(kernel,batch,manifest)
    snapshot=getattr(worker.host,'list_analysis_documents',worker.host.list_case_documents)(request.case_id,request.tax_year)
    files=snapshot.get('files',[])
    if not snapshot.get('registry_complete') or len(files)>20 or len({f['id'] for f in files})!=len(files):
        raise PermissionDenied('Incomplete or ambiguous document registry')
    if request.scope=='DOCUMENT':
        files=[f for f in files if f['id']==request.document_id]
        if len(files)!=1:raise PermissionDenied('Document is not owned by this case')
    existing=dispatcher.progress(request)
    all_previous=existing['documents']+existing['history']
    attempted=0;unsupported=[];reused=0;reconciliation=[]
    for f in files:
        dispatcher.authorize(kernel,batch,manifest)
        if f['mime_type'] not in ('application/pdf','text/csv'):
            unsupported.append({'document_id':f['id'],'filename':f['name'],'status':'UNSUPPORTED_FORMAT'});continue
        entry,content=read_document(worker.host,request,f['id'])
        if entry['id']!=f['id'] or not content or len(content)>20*1024*1024:raise PermissionDenied('Document source mismatch')
        sha=hashlib.sha256(content).hexdigest()
        if f['mime_type']=='text/csv' and request.execution_intent=='NORMAL':
            from agent_lab.case_analysis_projection import read
            prior=read(dispatcher,request,kernel=kernel)
            if prior and prior['payload']['csv']['source_sha256']==sha:
                reused+=1;continue
        if request.execution_intent=='EXPLICIT_RERUN' and sha!=request.expected_sha256:raise PermissionDenied('Source version changed; refresh required')
        same=[p for p in all_previous if p['document_id']==f['id'] and p['sha256']==sha]
        if any(p['processing_status'] in ('QUEUED','RUNNING','RECONCILIATION_REQUIRED') for p in same):
            reconciliation.append(f['id']);continue
        if request.execution_intent=='NORMAL' and any(p['processing_status']=='HUMAN_REVIEW_REQUIRED' for p in same):
            reused+=1;continue
        if request.execution_intent=='NORMAL' and any(p.get('diagnostic',{}).get('provider_outcome_uncertain') or
                p.get('diagnostic',{}).get('stage')=='UNKNOWN_LEGACY' for p in same):
            reconciliation.append(f['id']);continue
        if attempted>=worker.max_documents:break
        if not kernel.consume_budget(manifest,tokens=100000,tool_calls=1,cost_usd=5.0,child_tasks=1).allowed:raise PermissionDenied('Batch budget denied')
        meta={'document_id':f['id'],'filename':entry['name'],'sha256':sha,
              'model':'deterministic-sparkasse-v1' if f['mime_type']=='text/csv' else 'gemini-3.8-flash',
              'worker':'CSV' if f['mime_type']=='text/csv' else 'PDF',
              'initiated_via':'DASHBOARD','execution_intent':request.execution_intent,'request_id':request.request_id}
        task=dispatcher._task(request,batch['case_context']['run_id'],parent=batch['task_id'],document=meta)
        task['inputs'] += [AUTHORITY]
        dispatcher._register(kernel,task);mid=dispatcher._activate(kernel,task);attempted+=1
        if meta['worker']=='PDF':worker.process_one(request,task,mid,kernel,dispatcher)
        else:process_csv(worker,request,task,mid,kernel,dispatcher,meta)
    return {'processing_status':'HUMAN_REVIEW_REQUIRED','attempted_this_run':attempted,
            'reused_unchanged':reused,'unsupported':unsupported,'reconciliation_required':reconciliation}


def process_csv(worker,request,task,manifest,kernel,dispatcher,meta):
    """Reuse canonical deterministic ingestion; bank categories are source labels,
    never legal tax classifications. No provider receives CSV bytes.
    """
    stage='CSV_SOURCE_VERIFICATION'
    try:
        dispatcher.authorize(kernel,task,manifest)
        entry,content=read_document(worker.host,request,meta['document_id'])
        if entry['id']!=meta['document_id'] or hashlib.sha256(content).hexdigest()!=meta['sha256']:raise PermissionDenied('CSV source mismatch')
        if not kernel.consume_budget(manifest,tokens=0,tool_calls=1,cost_usd=0).allowed:raise PermissionDenied('CSV budget denied')
        stage='CSV_PARSE'
        from agent_lab.structured_financial import ingest_sparkasse_csv
        # Same exact-cents/currency preflight as the accepted field test. Bound
        # rows before the existing pair detector, whose cost is quadratic.
        if len(content)>4*1024*1024:raise ValueError('CSV analysis size limit')
        reader=csv.DictReader(io.StringIO(content.decode('cp1252'),newline=''),delimiter=';')
        count=0
        for raw in reader:
            count+=1
            if (count>5000 or None in raw or any(v is None for v in raw.values())
                    or not re.fullmatch(r'-?(?:\d+|\d{1,3}(?:\.\d{3})+),\d{2}',raw.get('Betrag','').strip())
                    or raw.get('Waehrung','').strip()!='EUR'):
                raise ValueError('Unsupported CSV shape/precision/currency or row limit')
        parsed=ingest_sparkasse_csv(content,case_id=request.case_id,tax_year=request.tax_year,source_id=meta['document_id'])
        if not parsed.transactions or len(parsed.transactions)>100000 or parsed.invalid_rows:raise ValueError('Incomplete CSV requires review')
        credits=Decimal(0);debits=Decimal(0);categories={}
        for tx in parsed.transactions:
            if tx.booking_date.year!=request.tax_year or tx.currency!='EUR' or not tx.amount.is_finite() or tx.amount!=tx.amount.quantize(Decimal('.01')):
                raise ValueError('CSV year/currency/precision mismatch')
            credits+=max(tx.amount,Decimal(0));debits+=max(-tx.amount,Decimal(0))
            label=tx.bank_category or 'UNCLASSIFIED_SOURCE'
            categories[label]=categories.get(label,Decimal(0))+tx.amount
        result={'summary':parsed.summary(),'credits':str(credits),'debits':str(debits),'net':str(credits-debits),
                'source_category_totals':{k:str(v) for k,v in categories.items()},
                'classification_status':'SOURCE_BANK_LABELS_ONLY_NOT_TAX_CLASSIFICATION',
                'tax_deductibility':'NOT_ASSESSED','needs_human_review':True,
                'ledger':parsed.to_dict()}
        dispatcher.authorize(kernel,task,manifest)
        dispatcher._finish(kernel,task,manifest,{'processing_status':'HUMAN_REVIEW_REQUIRED','finished_at':datetime.now(timezone.utc).isoformat(),
            'csv_payload':result,'evidence_references':[{'source_sha256':meta['sha256']}],
            'needs_human_review':True,'acceptance_status':'NOT_ACCEPTED_CANDIDATE_ONLY'})
    except Exception as exc:
        from agent_lab.case_analysis_diagnostics import diagnostic,record
        detail=diagnostic(exc,stage,task,meta);record(kernel,task,manifest,detail)
        dispatcher._finish(kernel,task,manifest,{'processing_status':'FAILED','diagnostic':detail,'error_details':type(exc).__name__},failed=True)


def project(documents, history):
    """A failed replacement cannot erase a previously persisted valid result."""
    excluded=[d for d in history if d.get('_unstarted_plan') or d['processing_status'] in ('EXPIRED','CANCELLED','QUEUED')]
    combined=[d for d in documents+history if d not in excluded];groups={}
    for d in combined:
        if d.get('_unstarted_plan'):continue
        groups.setdefault(d['document_id'],[]).append(d)
    current=[];past=list(excluded)
    for values in groups.values():
        values.sort(key=lambda x:(x['created_at'],x['task_id']))
        latest=values[-1];valid=[v for v in values if v['processing_status']=='HUMAN_REVIEW_REQUIRED']
        if valid and latest is not valid[-1]:latest={**latest,'previous_valid_result':valid[-1]}
        current.append(latest);past.extend(v for v in values if v['task_id']!=latest['task_id'])
    return current,past
