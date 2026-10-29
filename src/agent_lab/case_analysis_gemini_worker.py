"""Registered PDF tool, only callable through a currently authorized Kernel manifest."""
from dataclasses import asdict
import hashlib,os,time
from agent_lab.case_analysis_kernel_dispatch import PROVIDER,now
from agent_lab.orchestrator_kernel import PermissionDenied

class GeminiCaseDocumentWorker:
    def __init__(self,host,*,extractor=None,max_documents=20):
        if type(max_documents) is not int or not 1<=max_documents<=20:raise ValueError('Invalid bounded batch')
        self.host,self._extractor,self.max_documents=host,extractor,max_documents
    def __call__(self,*args,**kwargs):raise PermissionDenied('Kernel manifest execution required')
    def process(self,request,batch,batch_manifest,kernel,dispatcher):
        dispatcher.authorize(kernel,batch,batch_manifest)
        snapshot=self.host.list_case_documents(request.case_id,request.tax_year)
        if not snapshot.get('registry_complete') or len(snapshot['files'])>20:raise ValueError('Incomplete or unbounded registry')
        existing=dispatcher.progress(request)['documents']
        processed=0
        for file in snapshot['files']:
            if file['mime_type']!='application/pdf':continue
            dispatcher.authorize(kernel,batch,batch_manifest)
            entry,content=self.host.get_case_document(request.case_id,request.tax_year,file['id'])
            if entry['id']!=file['id'] or not content.startswith(b'%PDF-') or len(content)>20*1024*1024:raise ValueError('Document identity/type/size mismatch')
            digest=hashlib.sha256(content).hexdigest()
            same=[d for d in existing if d['document_id']==file['id'] and d['sha256']==digest]
            if any(d['processing_status']=='HUMAN_REVIEW_REQUIRED' for d in same):continue
            if processed>=self.max_documents:break
            if any(d['processing_status']=='FAILED' for d in same):continue
            if any(d['processing_status'] in ('RUNNING','RECONCILIATION_REQUIRED') for d in same):raise PermissionDenied('Prior outcome requires explicit reconciliation; replay denied')
            if not kernel.consume_budget(batch_manifest,tokens=100000,tool_calls=1,cost_usd=5.0,child_tasks=1).allowed:
                raise PermissionDenied('Batch budget denied')
            meta={'document_id':file['id'],'filename':entry['name'],'sha256':digest,'model':PROVIDER['model']}
            task=dispatcher._task(request,batch['case_context']['run_id'],parent=batch['task_id'],document=meta)
            dispatcher._register(kernel,task);manifest=dispatcher._activate(kernel,task);started=time.monotonic()
            processed+=1
            try:
                dispatcher.authorize(kernel,task,manifest)
                if not kernel.consume_budget(manifest,tokens=100000,tool_calls=1,cost_usd=5.0).allowed:raise PermissionDenied('Budget denied')
                if self._extractor is None:
                    from google import genai
                    from google.genai import types
                    from agent_lab.gemini_document_extraction import GeminiDocumentExtractor
                    client=genai.Client(api_key=os.environ['GEMINI_API_KEY'],http_options=types.HttpOptions(base_url='https://generativelanguage.googleapis.com',timeout=90000,retry_options=types.HttpRetryOptions(attempts=1)))
                    try:result=GeminiDocumentExtractor(client).extract(content,filename=entry['name'])
                    finally:client.close()
                else:result=self._extractor.extract(content,filename=entry['name'])
                if time.monotonic()-started>task['timeout_seconds']:raise TimeoutError('Deadline exceeded')
                dispatcher.authorize(kernel,task,manifest)
                dispatcher._finish(kernel,task,manifest,{'processing_status':'HUMAN_REVIEW_REQUIRED','finished_at':now(),
                    'extraction_payload':asdict(result),'evidence_references':[{'page':f.page,'quote':f.evidence} for f in result.fields],
                    'acceptance_status':'NOT_ACCEPTED_CANDIDATE_ONLY','needs_human_review':True,'error_details':None})
            except Exception as exc:
                dispatcher._finish(kernel,task,manifest,{'processing_status':'FAILED','finished_at':now(),
                    'error_details':type(exc).__name__,'needs_human_review':True,'retry':'EXPLICIT_RECONCILIATION_REQUIRED'},failed=True)
        return {'processing_status':'HUMAN_REVIEW_REQUIRED','inventory_count':len(snapshot['files']),
            'pdf_count':sum(f['mime_type']=='application/pdf' for f in snapshot['files']),
            'unsupported_count':sum(f['mime_type']!='application/pdf' for f in snapshot['files']),
            'attempted_this_run':processed,'batch_limit':self.max_documents}
