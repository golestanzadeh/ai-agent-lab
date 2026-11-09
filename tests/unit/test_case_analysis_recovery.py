import json
import pytest

from test_case_analysis_kernel_dispatch import make, REQ, wait
from test_case_analysis_successor import failed
from agent_lab.orchestrator_kernel import PermissionDenied

ACK='APPROVE_ONE_ATTEMPT_INCLUDING_UNCERTAIN_OUTCOME'


def test_missing_explicit_key_is_configuration_failure_before_sdk(tmp_path,monkeypatch):
    """Reproduces the former os.environ[...] KeyError without any provider I/O."""
    d,_=make(tmp_path);d.worker._extractor=None
    monkeypatch.delenv('GEMINI_API_KEY',raising=False)
    def forbidden(**kwargs):raise AssertionError('Provider client must not be constructed')
    monkeypatch.setattr('google.genai.Client',forbidden)
    d(REQ);p=wait(d)
    assert p['failed']==2
    assert all(x['diagnostic']['error_code']=='PROVIDER_CONFIGURATION_MISSING' for x in p['documents'])
    reopened,_=make(tmp_path)
    assert reopened.progress(REQ)['documents']==p['documents']


def test_plan_requires_real_owner_confirmation_and_only_one_attempt(tmp_path):
    d,e=failed(tmp_path);old=next(x for x in d.progress(REQ)['documents'] if x['processing_status']=='FAILED')
    calls=list(e.calls);plan=d.prepare_retry(REQ,old['task_id'])
    assert d.prepare_retry(REQ,old['task_id'])==plan and e.calls==calls
    p=d.progress(REQ)
    assert p['failed']==1 and p['completed']==1
    assert any(x['task_id']==plan['successor_task_id'] for x in p['history'])
    with pytest.raises(PermissionDenied):d.approve_retry(REQ,plan['successor_task_id'],'')
    e.fail=None;d.approve_retry(REQ,plan['successor_task_id'],ACK)
    assert wait(d)['completed']==2 and e.calls==calls+['a.pdf']
    with pytest.raises(PermissionDenied):d.approve_retry(REQ,plan['successor_task_id'],ACK)
    assert e.calls==calls+['a.pdf']


def test_changed_source_and_foreign_failure_do_not_create_plans(tmp_path):
    d,e=failed(tmp_path);old=next(x for x in d.progress(REQ)['documents'] if x['processing_status']=='FAILED')
    with pytest.raises(PermissionDenied):d.prepare_retry(REQ,'TASK-UNKNOWN')
    d.worker.host.get_case_document=lambda *args:({'id':'a','name':'a.pdf'},b'%PDF-changed')
    with pytest.raises(PermissionDenied):d.prepare_retry(REQ,old['task_id'])
    assert len(e.calls)==2


def test_sanitized_diagnostic_has_no_exception_message_or_payload(tmp_path):
    d,_=make(tmp_path)
    class PrivateFailure:
        def extract(self,*args,**kwargs):raise KeyError('SECRET_TOKEN_AND_PATIENT_CONTENT')
    d.worker._extractor=PrivateFailure();d(REQ);p=wait(d)
    assert p['failed']==2
    with d._kernel() as k:
        k.verify_audit_chain()
        payloads=[r[0] for r in k._connection.execute("SELECT payload_json FROM audit_events WHERE event_type='UI03_DIAGNOSTIC_RECORDED'")]
        assert len(payloads)==2 and 'SECRET_TOKEN' not in json.dumps(payloads)
    assert all(x['diagnostic']['stage']=='PROVIDER_ATTEMPT' and x['diagnostic']['provider_outcome_uncertain'] for x in p['documents'])
