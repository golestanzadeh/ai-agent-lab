from fastapi.testclient import TestClient
from test_case_document_registry import setup,host_module,CASE,OTHER,OWNER
from test_case_analysis_kernel_dispatch import Extractor,ROOT
from agent_lab.case_analysis_kernel_dispatch import CaseAnalysisKernelDispatcher
from agent_lab.case_analysis_gemini_worker import GeminiCaseDocumentWorker
from agent_lab.case_analysis_executor import AnalysisRequest
from agent_lab.case_analysis_recovery import approve


def test_unified_http_command_scopes_and_never_approves_human_gate(setup,host_module,monkeypatch,tmp_path):
    h,drive,p=setup;drive.document(content=b'%PDF-synthetic')
    class Download:
        def __init__(self,buffer,request):self.buffer,self.request=buffer,request
        def next_chunk(self):self.buffer.write(self.request.content);return None,True
    monkeypatch.setattr('googleapiclient.http.MediaIoBaseDownload',Download)
    e=Extractor();d=CaseAnalysisKernelDispatcher(tmp_path/'unified.sqlite',ROOT/'contracts/orchestrator/v1',worker=GeminiCaseDocumentWorker(h,extractor=e))
    with d._kernel() as k:k.set_kill_switch('RUNNING',actor_id='HUMAN_PROJECT_OWNER',authority_reference='owner://test-only')
    monkeypatch.setattr(host_module,'LocalCaseHost',lambda:h)
    client=TestClient(host_module.create_local_case_app(kernel_dispatch=d),base_url='http://127.0.0.1:8766')
    data={'case_id':CASE,'tax_year':2025,'scope':'CASE','execution_intent':'NORMAL','request_id':'REQUEST-ROUTE-0000000001'}
    headers={'Origin':'http://127.0.0.1:8766'}
    assert client.post('/cases/analysis/execute',data=data,headers={'Origin':'https://evil.invalid'}).status_code==403
    assert client.post('/cases/analysis/execute',data={**data,'case_id':'CASE-UNKNOWN'},headers=headers).status_code==409
    response=client.post('/cases/analysis/execute',data=data,headers=headers);assert response.status_code==200
    d._pool.submit(lambda:None).result(timeout=10)
    assert client.post('/cases/analysis/execute',data=data,headers=headers).json()==response.json()
    progress=client.get('/cases/analysis/progress',params={'case_id':CASE,'tax_year':2025}).json()
    assert progress['completed']==1 and e.calls==['f1.pdf']
    doc=progress['documents'][0]
    form={**data,'scope':'DOCUMENT','document_id':doc['document_id'],'execution_intent':'EXPLICIT_RERUN','expected_sha256':doc['sha256'],'request_id':'REQUEST-ROUTE-0000000002'}
    assert client.post('/cases/analysis/execute',data=form,headers=headers).status_code==200
    d._pool.submit(lambda:None).result(timeout=10)
    assert e.calls==['f1.pdf','f1.pdf']
    with d._kernel() as k:
        k.verify_audit_chain()
        assert not k._connection.execute("SELECT 1 FROM audit_events WHERE event_type='HUMAN_GATE_DECIDED'").fetchone()


def test_actual_self_service_routes_gate_single_document_and_restart(setup,host_module,monkeypatch,tmp_path):
    h,drive,p=setup;drive.document(content=b'%PDF-synthetic')
    class Download:
        def __init__(self,buffer,request):self.buffer,self.request=buffer,request
        def next_chunk(self):self.buffer.write(self.request.content);return None,True
    monkeypatch.setattr('googleapiclient.http.MediaIoBaseDownload',Download)
    e=Extractor();e.fail='f1.pdf'
    d=CaseAnalysisKernelDispatcher(tmp_path/'k.sqlite',ROOT/'contracts/orchestrator/v1',worker=GeminiCaseDocumentWorker(h,extractor=e))
    monkeypatch.setattr(host_module,'LocalCaseHost',lambda:h)
    client=TestClient(host_module.create_local_case_app(kernel_dispatch=d),base_url='http://127.0.0.1:8766')
    data={'case_id':CASE,'tax_year':2025};headers={'Origin':'http://127.0.0.1:8766'}
    assert client.post('/cases/analysis/execute',data=data,headers=headers).status_code==200
    d._pool.submit(lambda:None).result(timeout=10)
    old=client.get('/cases/analysis/progress',params=data).json()['documents'][0]
    assert old['processing_status']=='FAILED' and old['diagnostic']['error_code']=='PROVIDER_OUTCOME_UNCERTAIN'
    url='/cases/analysis/retry/prepare';form={**data,'failed_task_id':old['task_id']}
    assert client.post(url,data=form,headers={'Origin':'https://evil.invalid'}).status_code==403
    assert client.post(url,data={**form,'case_id':OTHER},headers=headers).status_code==409
    plan=client.post(url,data=form,headers=headers).json();assert e.calls==['f1.pdf']
    assert client.post(url,data=form,headers=headers).json()==plan
    form={**data,'successor_task_id':plan['successor_task_id'],'acknowledgement':'NO'}
    assert client.post('/cases/analysis/retry/approve',data=form,headers=headers).status_code==409
    e.fail=None;form['acknowledgement']='APPROVE_ONE_ATTEMPT_INCLUDING_UNCERTAIN_OUTCOME'
    response=client.post('/cases/analysis/retry/approve',data=form,headers=headers)
    assert response.status_code==409 and response.json()['detail']=='OWNER_AUTHENTICATION_REQUIRED'
    assert e.calls==['f1.pdf']
    with d._kernel() as k:
        assert k._connection.execute("SELECT status FROM task_human_gates WHERE task_id=?",(plan['successor_task_id'],)).fetchone()[0]=='PENDING'
    # Synthetic trusted-local broker exercises the separate approved boundary.
    d.approve_retry(AnalysisRequest(CASE,2025,OWNER),plan['successor_task_id'],form['acknowledgement'])
    d._pool.submit(lambda:None).result(timeout=10)
    result=client.get('/cases/analysis/progress',params=data).json()
    assert result['completed']==1 and len(result['history'])==1 and e.calls==['f1.pdf','f1.pdf']
    assert client.post('/cases/analysis/retry/approve',data=form,headers=headers).status_code==409
    reopened=CaseAnalysisKernelDispatcher(tmp_path/'k.sqlite',ROOT/'contracts/orchestrator/v1',worker=d.worker)
    assert reopened.progress(AnalysisRequest(CASE,2025,OWNER))['documents']==result['documents']
    assert client.get('/cases/analysis/verified-results',params=data).json()['result'] is None
    assert client.get('/cases/analysis/verified-results',params=data,headers={'Origin':'https://evil.invalid'}).status_code==403
