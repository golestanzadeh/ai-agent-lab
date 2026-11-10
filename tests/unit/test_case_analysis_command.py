from dataclasses import replace
import hashlib,json
import pytest
from test_case_analysis_kernel_dispatch import make,REQ,wait,Host
from test_structured_financial import _csv,_row
from agent_lab.case_analysis_executor import CaseAnalysisExecutor,AnalysisExecutionBlocked
from agent_lab.orchestrator_kernel import PermissionDenied

def start(d,*,scope='CASE',document_id=None,intent='NORMAL',sha=None,key='REQUEST-00000000000001'):
    request=replace(REQ,scope=scope,document_id=document_id,execution_intent=intent,request_id=key,expected_sha256=sha)
    return CaseAnalysisExecutor(verify_case=lambda c,y,o:(c,y,o)==(REQ.case_id,REQ.tax_year,REQ.owner_id),kernel_dispatch=d).execute(request)

def setup(tmp_path):
    d,e=make(tmp_path)
    d.worker.host.list_case_documents=lambda c,y: {'registry_complete':True,'files':[{'id':x,'name':x+'.pdf','mime_type':'application/pdf'} for x in ('a','b')]}
    with d._kernel() as k:k.set_kill_switch('RUNNING',actor_id='HUMAN_PROJECT_OWNER',authority_reference='owner://synthetic-only')
    return d,e

def test_one_command_initial_skip_and_durable_request_idempotency(tmp_path):
    d,e=setup(tmp_path);first=start(d);assert wait(d)['completed']==2 and len(e.calls)==2
    assert start(d)==first and len(e.calls)==2
    start(d,key='REQUEST-00000000000002');p=wait(d);assert p['completed']==2 and len(e.calls)==2
    with d._kernel() as k:k.verify_audit_chain()

def test_successful_document_rerun_failure_retains_valid_result(tmp_path):
    d,e=setup(tmp_path);start(d);before=wait(d);old=next(x for x in before['documents'] if x['document_id']=='a')
    e.fail='a.pdf'
    start(d,scope='DOCUMENT',document_id='a',intent='EXPLICIT_RERUN',sha=old['sha256'],key='REQUEST-00000000000002')
    p=wait(d);a=next(x for x in p['documents'] if x['document_id']=='a')
    assert a['processing_status']=='FAILED' and a['previous_valid_result']['task_id']==old['task_id']
    assert e.calls==['a.pdf','b.pdf','a.pdf']
    from agent_lab.case_analysis_kernel_dispatch import CaseAnalysisKernelDispatcher
    reopened=CaseAnalysisKernelDispatcher(d.database_path,d.contract_root,worker=d.worker)
    assert reopened.progress(REQ)['documents']==p['documents']

def test_failed_unknown_outcome_not_replayed_by_normal_case_but_explicit_document_allowed(tmp_path):
    d,e=setup(tmp_path);e.fail='a.pdf';start(d);p=wait(d);old=next(x for x in p['documents'] if x['document_id']=='a')
    start(d,key='REQUEST-00000000000002');wait(d);assert len(e.calls)==2
    e.fail=None
    start(d,scope='DOCUMENT',document_id='a',intent='EXPLICIT_RERUN',sha=old['sha256'],key='REQUEST-00000000000003')
    assert wait(d)['completed']==2 and len(e.calls)==3

def test_changed_digest_unknown_document_and_unsupported_fail_without_provider(tmp_path):
    d,e=setup(tmp_path)
    start(d,scope='DOCUMENT',document_id='a',intent='EXPLICIT_RERUN',sha='0'*64);wait(d);assert not e.calls
    start(d,scope='DOCUMENT',document_id='foreign',key='REQUEST-00000000000002');wait(d);assert not e.calls
    d.worker.host.list_case_documents=lambda c,y:{'registry_complete':True,'files':[{'id':'other','name':'other.bin','mime_type':'application/octet-stream'}]}
    start(d,key='REQUEST-00000000000003');wait(d);assert not e.calls

def test_active_duplicate_and_kill_switch(tmp_path):
    d,e=setup(tmp_path);e.block=True;receipt=start(d);assert e.entered.wait(5)
    assert start(d)==receipt
    with pytest.raises(PermissionDenied):start(d,key='REQUEST-00000000000002')
    e.release.set();wait(d)
    with d._kernel() as k:k.set_kill_switch('HALTED',actor_id='HUMAN_PROJECT_OWNER',authority_reference='owner://synthetic-stop')
    with pytest.raises(PermissionDenied):start(d,key='REQUEST-00000000000003')

def test_same_request_id_cannot_change_scope(tmp_path):
    d,e=setup(tmp_path);start(d);wait(d)
    with pytest.raises(PermissionDenied):start(d,scope='DOCUMENT',document_id='a')
    with pytest.raises(AnalysisExecutionBlocked):start(d,scope='ALL')
    with pytest.raises(AnalysisExecutionBlocked):start(d,intent='EXPLICIT_RERUN')
    with pytest.raises(AnalysisExecutionBlocked):
        CaseAnalysisExecutor(verify_case=lambda *a:True,kernel_dispatch=d).execute(replace(REQ,scope='DOCUMENT',document_id='a'))

def test_csv_uses_canonical_parser_without_gemini_and_binds_exact_source(tmp_path):
    d,e=setup(tmp_path);payload=_csv(_row(booking='02.04.25',value='02.04.25'))
    d.worker.host.list_case_documents=lambda c,y:{'registry_complete':True,'files':[{'id':'csv','name':'bank.csv','mime_type':'text/csv'}]}
    d.worker.host.get_case_document=lambda c,y,i:({'id':i,'name':'bank.csv'},payload)
    start(d);p=wait(d);assert not e.calls and p['completed']==1
    document=p['documents'][0];csv=document['csv_payload']
    assert document['worker']=='CSV' and document['sha256']==hashlib.sha256(payload).hexdigest()
    assert csv['summary']['parsed_row_count']==1 and csv['debits']=='240.00' and csv['net']=='-240.00'
    assert csv['tax_deductibility']=='NOT_ASSESSED'
    with d._kernel() as k:
        task=json.loads(k._connection.execute('SELECT payload_json FROM tasks WHERE task_id=?',(document['task_id'],)).fetchone()[0])
        assert 'registered_gemini_pdf_extract' not in task['allowed_tools']
        response=json.loads(k._connection.execute('SELECT payload_json FROM responses WHERE task_id=?',(document['task_id'],)).fetchone()[0])
        assert json.loads(response['result_summary'])['csv_payload']['ledger']['transactions'][0]['source_row_number']==2

def test_cross_scope_resolver_and_invalid_csv_rejected(tmp_path):
    d,e=setup(tmp_path)
    with pytest.raises(AnalysisExecutionBlocked):
        CaseAnalysisExecutor(verify_case=lambda *a:False,kernel_dispatch=d).execute(replace(REQ,request_id='REQUEST-00000000000001'))
    d.worker.host.list_case_documents=lambda c,y:{'registry_complete':True,'files':[{'id':'csv','name':'bank.csv','mime_type':'text/csv'}]}
    d.worker.host.get_case_document=lambda c,y,i:({'id':i,'name':'bank.csv'},b'bad csv')
    start(d);p=wait(d);assert p['failed']==1 and not e.calls

def test_normal_case_retries_known_pre_provider_failure_only(tmp_path,monkeypatch):
    d,e=setup(tmp_path);d.worker._extractor=None
    monkeypatch.delenv('GEMINI_API_KEY',raising=False)
    start(d);p=wait(d);assert p['failed']==2
    d.worker._extractor=e
    start(d,key='REQUEST-00000000000002');assert wait(d)['completed']==2 and len(e.calls)==2

def test_changed_version_normal_processing_preserves_previous_source_history(tmp_path):
    d,e=setup(tmp_path);start(d);p=wait(d);old=p['documents'][0]
    d.worker.host.get_case_document=lambda c,y,i:({'id':i,'name':i+'.pdf'},b'%PDF-new-version-'+i.encode())
    start(d,key='REQUEST-00000000000002');p=wait(d)
    assert p['completed']==2 and len(e.calls)==4
    assert any(x['task_id']==old['task_id'] and x['sha256']==old['sha256'] for x in p['history'])

def test_csv_row_limit_rejected_before_quadratic_parser(tmp_path,monkeypatch):
    d,e=setup(tmp_path);payload=_csv(*[_row(booking='02.04.25',value='02.04.25')]*5001)
    d.worker.host.list_case_documents=lambda c,y:{'registry_complete':True,'files':[{'id':'csv','name':'bank.csv','mime_type':'text/csv'}]}
    d.worker.host.get_case_document=lambda c,y,i:({'id':i,'name':'bank.csv'},payload)
    def forbidden(*a,**k):raise AssertionError('Unbounded parser must not run')
    monkeypatch.setattr('agent_lab.structured_financial.ingest_sparkasse_csv',forbidden)
    start(d);p=wait(d);assert p['failed']==1 and not e.calls
    assert p['documents'][0]['diagnostic']['exception_type']=='ValueError'

@pytest.mark.parametrize('failure',['persistence','deadline'])
def test_post_provider_failure_never_normal_replays(tmp_path,monkeypatch,failure):
    d,e=setup(tmp_path)
    if failure=='persistence':
        finish=d._finish
        def interrupted(k,t,m,p,**kw):
            if t['objective']=='UI03_DOCUMENT_V1' and not kw.get('failed'):
                raise RuntimeError('Injected result persistence interruption')
            return finish(k,t,m,p,**kw)
        monkeypatch.setattr(d,'_finish',interrupted)
    else:
        from types import SimpleNamespace
        ticks=iter([0,121,0,121])
        monkeypatch.setattr('agent_lab.case_analysis_gemini_worker.time',SimpleNamespace(monotonic=lambda:next(ticks)))
    start(d);p=wait(d)
    assert len(e.calls)==2 and p['failed']==2
    assert all(x['diagnostic']['provider_outcome_uncertain'] for x in p['documents'])
    start(d,key='REQUEST-00000000000002');wait(d);assert len(e.calls)==2
