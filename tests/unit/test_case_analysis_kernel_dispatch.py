from pathlib import Path
from types import SimpleNamespace
from threading import Event
import json,time
import pytest
from agent_lab.case_analysis_executor import AnalysisRequest,AnalysisExecutionBlocked
from agent_lab.case_analysis_kernel_dispatch import CaseAnalysisKernelDispatcher
from agent_lab.case_analysis_gemini_worker import GeminiCaseDocumentWorker
from agent_lab.document_extraction import DocumentExtractionResult,ExtractedTaxField
from agent_lab.orchestrator_kernel import PermissionDenied

ROOT=Path(__file__).parents[2]
REQ=AnalysisRequest('TEST-UI03-A',2025,'OWNER-A')
RESULT=DocumentExtractionResult('INVOICE','CANDIDATE',None,None,None,(ExtractedTaxField('amount','1.00',1,'1,00 EUR',0.8),),'GEMINI_DOCUMENT_VISION',0.8,True,())
class Extractor:
    def __init__(self):self.calls=[];self.fail=None;self.entered=Event();self.release=Event();self.block=False
    def extract(self,content,*,filename):
        self.calls.append(filename);self.entered.set()
        if self.block:assert self.release.wait(10)
        if filename==self.fail:raise ValueError('PRIVATE_ERROR_MUST_NOT_ESCAPE')
        return RESULT
class Host:
    def list_case_documents(self,c,y):
        assert (c,y)==(REQ.case_id,REQ.tax_year)
        return {'registry_complete':True,'files':[{'id':x,'name':x+'.pdf','mime_type':'application/pdf'} for x in ('a','b')]+[{'id':'csv','mime_type':'text/csv'}]}
    def get_case_document(self,c,y,d):return {'id':d,'name':d+'.pdf'},b'%PDF-synthetic-'+d.encode()
def make(tmp_path,extractor=None):
    extractor=extractor or Extractor()
    return CaseAnalysisKernelDispatcher(tmp_path/'kernel.sqlite',ROOT/'contracts/orchestrator/v1',worker=GeminiCaseDocumentWorker(Host(),extractor=extractor)),extractor
def wait(d):
    deadline=time.monotonic()+15
    while time.monotonic()<deadline:
        p=d.progress(REQ)
        if not p['active']:return p
        time.sleep(.02)
    raise AssertionError('Worker did not finish')
def test_real_kernel_bound_tool_persists_each_candidate_and_restart(tmp_path):
    d,e=make(tmp_path);receipt=d(REQ);p=wait(d)
    assert p['completed']==2 and p['failed']==0 and len(e.calls)==2
    assert all(x['manifest_id'] and x['sha256'] and x['evidence_references'][0]['page']==1 for x in p['documents'])
    reopened,_=make(tmp_path)
    assert reopened.progress(REQ)['documents']==p['documents']
    reopened(REQ);assert wait(reopened)['completed']==2
    assert len(e.calls)==2
    assert reopened.progress(AnalysisRequest('OTHER',2025,'OWNER-A'))['documents']==[]
    assert reopened.progress(AnalysisRequest(REQ.case_id,2024,'OWNER-A'))['documents']==[]
    assert reopened.progress(AnalysisRequest(REQ.case_id,2025,'OTHER'))['documents']==[]
def test_duplicate_and_nonblocking_call(tmp_path):
    e=Extractor();e.block=True;d,_=make(tmp_path,e)
    started=time.monotonic();first=d(REQ)
    assert time.monotonic()-started<2
    assert e.entered.wait(5)
    assert d(REQ)==first
    assert d.progress(REQ)['documents'][0]['processing_status']=='RUNNING'
    e.release.set();assert wait(d)['completed']==2
    assert len(e.calls)==2
def test_failure_isolation_and_private_errors(tmp_path):
    e=Extractor();e.fail='a.pdf';d,_=make(tmp_path,e);d(REQ);p=wait(d)
    assert p['failed']==1 and p['completed']==1
    assert 'PRIVATE_ERROR' not in json.dumps(p)
def test_direct_worker_missing_authority_and_kill_switch_denied(tmp_path):
    d,_=make(tmp_path)
    with pytest.raises(PermissionDenied):d.worker(REQ,'forged')
    with d._kernel() as k:
        k.set_kill_switch('HALTED',actor_id='HUMAN_PROJECT_OWNER',authority_reference='synthetic-halt')
    with pytest.raises(AnalysisExecutionBlocked):d(REQ)
def test_tampered_response_rejected(tmp_path):
    d,_=make(tmp_path);d(REQ);assert wait(d)['completed']==2
    with d._kernel() as k:
        with k._connection:k._connection.execute("UPDATE responses SET payload_json=replace(payload_json,'1.00','9.99')")
    with pytest.raises(Exception):d.progress(REQ)
def test_interrupted_external_intent_is_not_replayed(tmp_path):
    d,e=make(tmp_path)
    with d._kernel() as k:
        t=d._task(REQ,'RUN-INTERRUPTED');k.register_task(t,gate_triggers=())
    with pytest.raises(AnalysisExecutionBlocked,match='RECONCILIATION'):d(REQ)
    assert e.calls==[]

def test_multiple_dispatchers_claim_atomically(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    e=Extractor();e.block=True;d,_=make(tmp_path,e);other,_=make(tmp_path,e);barrier=Barrier(2)
    def submit(value):
        barrier.wait()
        try:return value(REQ)
        except AnalysisExecutionBlocked:return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(submit,x) for x in (d,other)]
        outcomes=[f.result(timeout=10) for f in futures]
    assert sum(x is not None for x in outcomes)==1
    e.release.set();wait(d);wait(other)
    assert len(e.calls)==2  # two DIFFERENT documents, exactly one run

def test_elapsed_task_deadline_is_denied(tmp_path):
    from datetime import datetime,timedelta,timezone
    d,e=make(tmp_path)
    with d._kernel() as k:
        task=d._task(REQ,'RUN-EXPIRED')
        task['created_at']=(datetime.now(timezone.utc)-timedelta(seconds=10)).isoformat();task['timeout_seconds']=1
        d._register(k,task)
        k.set_kill_switch('RUNNING',actor_id='HUMAN_PROJECT_OWNER',authority_reference='synthetic')
        with pytest.raises(PermissionDenied,match='deadline'):d._activate(k,task)
    assert e.calls==[]

@pytest.mark.parametrize('mutation',[
    "UPDATE responses SET task_id=(SELECT task_id FROM tasks WHERE json_extract(payload_json,'$.objective')='UI03_BATCH_V1' LIMIT 1) WHERE task_id IN (SELECT task_id FROM tasks WHERE json_extract(payload_json,'$.objective')='UI03_DOCUMENT_V1')",
    "DELETE FROM responses WHERE task_id IN (SELECT task_id FROM tasks WHERE json_extract(payload_json,'$.objective')='UI03_DOCUMENT_V1')",
    "UPDATE responses SET manifest_id=(SELECT manifest_id FROM manifests LIMIT 1)",
])
def test_response_row_substitution_deletion_or_manifest_rejected(tmp_path,mutation):
    d,e=make(tmp_path);d(REQ);assert wait(d)['completed']==2
    with d._kernel() as k:
        with k._connection:k._connection.execute(mutation)
    with pytest.raises(PermissionDenied):d.progress(REQ)
