from fastapi.testclient import TestClient
from test_case_document_registry import setup,host_module,CASE,OTHER,OWNER
from test_case_analysis_kernel_dispatch import Extractor,ROOT,wait
from agent_lab.case_analysis_executor import AnalysisRequest
from agent_lab.case_analysis_kernel_dispatch import CaseAnalysisKernelDispatcher
from agent_lab.case_analysis_gemini_worker import GeminiCaseDocumentWorker

def test_actual_routes_owner_scope_origin_restart_and_languages(setup,host_module,monkeypatch,tmp_path):
    h,drive,p=setup;drive.document(content=b'%PDF-synthetic')
    class Download:
        def __init__(self,buffer,request):self.buffer,self.request=buffer,request
        def next_chunk(self):self.buffer.write(self.request.content);return None,True
    monkeypatch.setattr('googleapiclient.http.MediaIoBaseDownload',Download)
    e=Extractor();d=CaseAnalysisKernelDispatcher(tmp_path/'kernel.sqlite',ROOT/'contracts/orchestrator/v1',worker=GeminiCaseDocumentWorker(h,extractor=e))
    monkeypatch.setattr(host_module,'LocalCaseHost',lambda:h)
    monkeypatch.setenv('GEMINI_API_KEY','synthetic-not-a-credential')
    client=TestClient(host_module.create_local_case_app(kernel_dispatch=d),base_url='http://127.0.0.1:8766')
    data={'case_id':CASE,'tax_year':2025};headers={'Origin':'http://127.0.0.1:8766'}
    assert client.post('/cases/analysis/execute',data=data,headers={'Origin':'https://evil.invalid'}).status_code==403
    assert client.post('/cases/analysis/execute',data={'case_id':CASE,'tax_year':2024},headers=headers).status_code==409
    assert client.get('/cases/analysis/progress',params=data,headers={'Host':'evil.invalid'}).status_code==403
    assert client.get('/cases/analysis/progress',params={'case_id':'UNKNOWN','tax_year':2025}).status_code==409
    response=client.post('/cases/analysis/execute',data=data,headers=headers)
    assert response.status_code==200 and response.json()['status']=='REGISTERED'
    d._pool.shutdown(wait=True)
    result=client.get('/cases/analysis/progress',params=data)
    assert result.status_code==200 and result.json()['completed']==1
    assert result.json()['documents'][0]['extraction_payload']['fields'][0]['evidence']
    assert client.get('/cases/analysis/progress',params={'case_id':OTHER,'tax_year':2025}).json()['documents']==[]
    # A network-held document lock does not block metadata-only navigation.
    from concurrent.futures import ThreadPoolExecutor
    with h._lock,ThreadPoolExecutor() as pool:
        assert len(pool.submit(h.read_cases).result(timeout=3))==2
    for language,direction in [('fa-IR','rtl'),('de-DE','ltr')]:
        page=client.get('/',params={'tab':'analysis','case_id':CASE,'lang':language})
        assert page.status_code==200 and 'dir="'+direction+'"' in page.text
        assert 'analysis_request.js' in page.text
    restarted=CaseAnalysisKernelDispatcher(tmp_path/'kernel.sqlite',ROOT/'contracts/orchestrator/v1')
    assert restarted.progress(AnalysisRequest(CASE,2025,OWNER))['completed']==1
