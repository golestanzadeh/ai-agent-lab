"""Bounded existing-Kernel adapter; tasks/manifests/responses are the only execution state."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta,timezone
import hashlib,json
from pathlib import Path
from threading import RLock
from uuid import uuid4
from agent_lab.case_analysis_executor import AnalysisExecutionBlocked
from agent_lab.orchestrator_kernel import OrchestratorKernel,PermissionDenied,_digest

AUTHORITY='owner://UI03-FINAL-20261029/registered-gemini-development'
PROVIDER={'project':'ai-tax-agent-507813','model':'gemini-3.8-flash','store':False,'logging':'disabled','billing':'active','authority':AUTHORITY,'scope':'development-document-extraction-only'}
PROVIDER_REF='sha256:'+hashlib.sha256(json.dumps(PROVIDER,sort_keys=True).encode()).hexdigest()
TOOLS=['case_drive_pdf_read','registered_gemini_pdf_extract']
CAPS=['read_case_packet','write_derived_case_artifact']
def now():return datetime.now(timezone.utc).isoformat()

class CaseAnalysisKernelDispatcher:
    def __init__(self,database_path,contract_root,*,worker=None):
        self.database_path,self.contract_root=Path(database_path),Path(contract_root)
        self.worker=worker;self._lock=RLock();self._active={}
        self._pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='kernel-ui03')
    def _kernel(self):return OrchestratorKernel(self.database_path,self.contract_root)
    def _register(self,k,task):
        k.register_task(task,gate_triggers=())
        with k._write_scope():
            k._append_event('UI03_INTENT_BOUND','TASK',task['task_id'],task['actor_instance_id'],{'task_digest':_digest(task)})
    def _task(self,request,run_id,*,parent=None,document=None):
        uid=uuid4().hex.upper()
        task={'schema_version':1,'task_id':'TASK-UI03-'+uid,'parent_task_id':parent,
            'objective':'UI03_DOCUMENT_V1' if document else 'UI03_BATCH_V1',
            'role_id':'EVIDENCE_AGENT','actor_instance_id':'AGI-UI03-'+uid,
            'repository':'golestanzadeh/ai-agent-lab','ref':'c09-witness-hardening',
            'case_context':{'case_id':request.case_id,'tax_year':request.tax_year,'run_id':run_id},
            'inputs':[AUTHORITY,PROVIDER_REF,'owner-sha256:'+hashlib.sha256(request.owner_id.encode()).hexdigest()],
            'expected_outputs':['kernel://ui03/'+run_id+'/'+uid],'allowed_tools':TOOLS,'permissions':CAPS,
            'forbidden_actions':['external_transfer','mutate_source_evidence','cross_case_access','tax_acceptance','elster_submission'],
            'budget':{'token_limit':100000,'tool_call_limit':2,'cost_limit_usd':5.0},
            'timeout_seconds':120,'max_retries':0,
            'acceptance_criteria':['Candidate extraction only; independent review required'],
            'stop_conditions':['scope mismatch','kill switch','deadline','uncertain provider outcome'],
            'escalation_route':['HUMAN_PROJECT_OWNER'],'created_at':now(),
            'expires_at':(datetime.now(timezone.utc)+timedelta(minutes=30)).isoformat(),'status':'REGISTERED'}
        if document:task['inputs'].append('document-json:'+json.dumps(document,sort_keys=True))
        else:
            task['budget']={'token_limit':1000000,'tool_call_limit':20,'cost_limit_usd':100.0}
            task['timeout_seconds']=1200
        return task
    def _activate(self,kernel,task):
        m={'schema_version':1,'manifest_id':'MAN-UI03-'+uuid4().hex.upper(),
            'task_id':task['task_id'],'parent_task_id':task['parent_task_id'],'role_id':task['role_id'],'actor_instance_id':task['actor_instance_id'],
            'scope':{'repository':task['repository'],'ref':task['ref'],'allowed_paths':[],'case_context':task['case_context']},
            'inputs':task['inputs'],'expected_outputs':task['expected_outputs'],'allowed_tools':task['allowed_tools'],
            'requested_access_tiers':['A3','A4'],'requested_capabilities':CAPS,'forbidden_actions':task['forbidden_actions'],
            'budget':task['budget'],'timeout_seconds':task['timeout_seconds'],'max_retries':0,
            'stop_conditions':task['stop_conditions'],'escalation_route':task['escalation_route'],
            'issued_at':now(),'expires_at':task['expires_at'],'status':'PROPOSED'}
        kernel.register_manifest(m);kernel.validate_manifest(m['manifest_id']);kernel.activate_manifest(m['manifest_id'])
        self.authorize(kernel,task,m['manifest_id']);return m['manifest_id']
    @staticmethod
    def authorize(kernel,task,manifest_id):
        kernel.verify_audit_chain()
        if datetime.now(timezone.utc)>=datetime.fromisoformat(task['created_at'])+timedelta(seconds=task['timeout_seconds']):
            raise PermissionDenied('Task deadline exceeded')
        durable=kernel._connection.execute('SELECT payload_json FROM tasks WHERE task_id=?',(task['task_id'],)).fetchone()
        if durable is None or json.loads(durable[0])!=task:raise PermissionDenied('Task lineage mismatch')
        receipts=kernel._connection.execute("SELECT payload_json FROM audit_events WHERE event_type='UI03_INTENT_BOUND' AND entity_id=?",(task['task_id'],)).fetchall()
        if len(receipts)!=1 or json.loads(receipts[0][0]).get('task_digest')!=_digest(task):raise PermissionDenied('Intent integrity mismatch')
        row=kernel._manifest_row(manifest_id);m=json.loads(row['payload_json'])
        if row['task_id']!=task['task_id'] or row['actor_instance_id']!=task['actor_instance_id'] or row['role_id']!='EVIDENCE_AGENT' or m['scope']['case_context']!=task['case_context'] or m['allowed_tools']!=TOOLS or PROVIDER_REF not in task['inputs'] or AUTHORITY not in task['inputs']:
            raise PermissionDenied('Provider binding mismatch')
        for cap in CAPS:
            if not kernel.permission_decision(manifest_id,cap,**task['case_context']).allowed:raise PermissionDenied('Kernel execution denied')
    def __call__(self,request):
        if self.worker is None:raise AnalysisExecutionBlocked('Authorized worker unavailable')
        key=(request.owner_id,request.case_id,request.tax_year)
        with self._lock:
            if key in self._active:return self._active[key]
            if len(self._active)>=4:raise AnalysisExecutionBlocked('Bounded worker queue full')
            with self._kernel() as k, k.atomic_execution():
                k.verify_audit_chain()
                if k.kill_switch_state()=='HALTED' and not k._connection.execute("SELECT 1 FROM audit_events WHERE event_type='KILL_SWITCH_CHANGED'").fetchone():
                    k.set_kill_switch('RUNNING',actor_id='HUMAN_PROJECT_OWNER',authority_reference=AUTHORITY)
                if k.kill_switch_state()!='RUNNING':raise AnalysisExecutionBlocked('Kill switch blocks dispatch')
                if any(t['status'] in ('REGISTERED','ACTIVE') for t in self._tasks(k,request)):
                    raise AnalysisExecutionBlocked('RECONCILIATION_REQUIRED: no automatic provider replay')
                run='RUN-UI03-'+uuid4().hex.upper();task=self._task(request,run);self._register(k,task)
            receipt={'case_id':request.case_id,'tax_year':request.tax_year,'run_id':run,'status':'REGISTERED'}
            self._active[key]=receipt;self._pool.submit(self._run,request,task);return receipt
    def _finish(self,k,task,manifest,payload,*,failed=False):
        self.authorize(k,task,manifest)
        if not failed:k.transition_manifest(manifest,'BLOCKED',actor_id=task['actor_instance_id'],reason='Candidate awaits independent review')
        usage=dict(k._connection.execute('SELECT tokens_used,tool_calls_used,cost_usd FROM budget_usage WHERE manifest_id=?',(manifest,)).fetchone())
        k.record_response(manifest,{'schema_version':1,'response_id':'RESP-UI03-'+uuid4().hex.upper(),
            'task_id':task['task_id'],'parent_task_id':task['parent_task_id'],'role_id':task['role_id'],'actor_instance_id':task['actor_instance_id'],
            'status':'FAILED' if failed else 'HUMAN_REQUIRED','result_summary':json.dumps(payload,ensure_ascii=False,sort_keys=True),
            'artifact_references':task['expected_outputs'],'changed_paths_or_state':[],'tests':[],'evidence':[PROVIDER_REF],
            'authority_used':[AUTHORITY],'costs':usage,'unresolved_risks':['Candidate not accepted; budget charge is conservative reservation, not metered billing'],
            'recommended_next_action':'Independent review; no automatic external retry','human_required':not failed,'created_at':now()})
    def _run(self,request,task):
        try:
            with self._kernel() as k:
                manifest=self._activate(k,task)
                summary=self.worker.process(request,task,manifest,k,self)
                self._finish(k,task,manifest,summary)
        except Exception as exc:
            # Failures are durable without private exception text. If authority
            # itself is lost, preserve the uncertain intent rather than bypass it.
            try:
                with self._kernel() as k:
                    row=k._connection.execute('SELECT manifest_id FROM manifests WHERE task_id=?',(task['task_id'],)).fetchone()
                    if row:self._finish(k,task,row[0],{'processing_status':'FAILED','error_details':type(exc).__name__},failed=True)
            except Exception:
                pass
        finally:
            with self._lock:self._active.pop((request.owner_id,request.case_id,request.tax_year),None)
    def _tasks(self,k,request):
        owner='owner-sha256:'+hashlib.sha256(request.owner_id.encode()).hexdigest();result=[]
        for row in k._connection.execute('SELECT payload_json,status FROM tasks ORDER BY created_at,task_id'):
            p=json.loads(row['payload_json']);s=p['case_context']
            if p['objective'] in ('UI03_BATCH_V1','UI03_DOCUMENT_V1') and s and s['case_id']==request.case_id and s['tax_year']==request.tax_year and owner in p['inputs']:
                result.append({**p,'status':row['status']})
        return result
    def progress(self,request):
        with self._lock,self._kernel() as k:
            k.verify_audit_chain();tasks=self._tasks(k,request);documents=[]
            # The frozen UI25 projection is intentionally TEST-only. Reuse its
            # response-digest invariant here, behind this real case/Owner resolver.
            for t in tasks:
                if t['objective']=='UI03_DOCUMENT_V1':
                    bindings=k._connection.execute("SELECT payload_json FROM audit_events WHERE event_type='UI03_INTENT_BOUND' AND entity_id=?",(t['task_id'],)).fetchall()
                    original={**t,'status':'REGISTERED'}
                    if len(bindings)!=1 or json.loads(bindings[0][0]).get('task_digest')!=_digest(original):raise PermissionDenied('Document intent mismatch')
                responses=k._connection.execute('SELECT * FROM responses WHERE task_id=?',(t['task_id'],)).fetchall()
                if len(responses)>1 or (not responses and t['status'] in ('HUMAN_REQUIRED','FAILED')):
                    raise PermissionDenied('Missing or ambiguous terminal response')
                for r in responses:
                    payload=json.loads(r['payload_json'])
                    if (set(payload)!=OrchestratorKernel.RESPONSE_FIELDS
                            or payload['task_id']!=t['task_id'] or r['task_id']!=t['task_id']
                            or payload['response_id']!=r['response_id'] or payload['status']!=r['status']
                            or payload['role_id']!=t['role_id'] or payload['actor_instance_id']!=t['actor_instance_id']
                            or payload['parent_task_id']!=t['parent_task_id']):
                        raise PermissionDenied('Response task lineage mismatch')
                    manifest=k._manifest_row(r['manifest_id'])
                    if (manifest['task_id']!=t['task_id'] or manifest['actor_instance_id']!=t['actor_instance_id']
                            or manifest['role_id']!=t['role_id']):raise PermissionDenied('Response manifest lineage mismatch')
                    audit=k._connection.execute("SELECT payload_json FROM audit_events WHERE event_type='RESPONSE_RECORDED' AND entity_id=?",(r['response_id'],)).fetchall()
                    expected={'task_id':t['task_id'],'manifest_id':r['manifest_id'],'status':r['status'],'response_digest':_digest(payload)}
                    if len(audit)!=1 or json.loads(audit[0][0])!=expected:raise PermissionDenied('Response integrity mismatch')
            for t in tasks:
                if t['objective']!='UI03_DOCUMENT_V1':continue
                row=k._connection.execute('SELECT payload_json FROM responses WHERE task_id=?',(t['task_id'],)).fetchone()
                if row is None and t['status'] in ('HUMAN_REQUIRED','FAILED'):
                    raise PermissionDenied('Terminal document response missing')
                meta=json.loads(next(s[len('document-json:'):] for s in t['inputs'] if s.startswith('document-json:')))
                m=k._connection.execute('SELECT manifest_id,state FROM manifests WHERE task_id=?',(t['task_id'],)).fetchone()
                d={**meta,**t['case_context'],'task_id':t['task_id'],'manifest_id':m['manifest_id'] if m else None,
                    'processing_status':'QUEUED','created_at':t['created_at'],'acceptance_status':'NOT_ACCEPTED_CANDIDATE_ONLY'}
                if row:d.update(json.loads(json.loads(row[0])['result_summary']))
                elif t['status']=='ACTIVE':d['processing_status']='RUNNING' if (request.owner_id,request.case_id,request.tax_year) in self._active else 'RECONCILIATION_REQUIRED'
                documents.append(d)
            return {'case_id':request.case_id,'tax_year':request.tax_year,'documents':documents,
                'completed':sum(d['processing_status']=='HUMAN_REVIEW_REQUIRED' for d in documents),
                'failed':sum(d['processing_status']=='FAILED' for d in documents),
                'active':(request.owner_id,request.case_id,request.tax_year) in self._active,
                'runs':[{'run_id':t['case_context']['run_id'],'status':t['status']} for t in tasks if t['objective']=='UI03_BATCH_V1']}
