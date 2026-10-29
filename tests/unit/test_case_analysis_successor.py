import hashlib,json
from datetime import datetime,timedelta,timezone
import pytest
from test_case_analysis_kernel_dispatch import make,REQ,wait,Extractor
from agent_lab.case_analysis_kernel_dispatch import _digest
from agent_lab.orchestrator_kernel import PermissionDenied,ContractError


def prepare(d,*,approved=True,source=None):
    records=d.progress(REQ)['documents']
    old=next(r for r in records if r['processing_status']=='FAILED')
    with d._kernel() as k,k.atomic_execution():
        original=json.loads(k._connection.execute('SELECT payload_json FROM tasks WHERE task_id=?',(old['task_id'],)).fetchone()[0])
        meta=json.loads(next(v[len('document-json:'):] for v in original['inputs'] if v.startswith('document-json:')))
        grant={'original_task_id':old['task_id'],'original_manifest_id':old['manifest_id'],
            'document_id':meta['document_id'],'sha256':meta['sha256'],'case_id':REQ.case_id,'tax_year':REQ.tax_year,
            'owner_hash':hashlib.sha256(REQ.owner_id.encode()).hexdigest(),'authority_reference':'owner://synthetic-one-successor',
            'expires_at':(datetime.now(timezone.utc)+timedelta(minutes=10)).isoformat(),'implementation_ref':'synthetic-reviewed-implementation'}
        if source:grant.update(source)
        task=d._task(REQ,'RUN-SUCCESSOR-TEST',parent=old['task_id'],document={**meta,'supersedes_task_id':old['task_id']})
        task['inputs'] += ['successor-json:'+json.dumps(grant,sort_keys=True),grant['authority_reference']]
        d._register(k,task,gate_triggers=('authority_ambiguity',))
        if approved:k.record_human_gate_decision(task['task_id'],'authority_ambiguity','APPROVED',actor_id='HUMAN_PROJECT_OWNER',authority_reference=_digest(grant))
    return task,old

def failed(tmp_path):
    e=Extractor();e.fail='a.pdf';d,_=make(tmp_path,e);d(REQ);p=wait(d)
    assert p['failed']==1 and p['completed']==1
    return d,e

def preserved(k,old):
    return [dict(k._connection.execute('SELECT * FROM tasks WHERE task_id=?',(old['task_id'],)).fetchone()),
            dict(k._manifest_row(old['manifest_id'])),
            [dict(r) for r in k._connection.execute('SELECT * FROM responses WHERE task_id=?',(old['task_id'],))]]

def test_one_linked_successor_preserves_original_and_other_success(tmp_path):
    d,e=failed(tmp_path);task,old=prepare(d)
    with d._kernel() as k:before=preserved(k,old)
    e.fail=None;receipt=d.owner_successor(REQ,task['task_id']);p=wait(d)
    assert receipt['run_id']=='RUN-SUCCESSOR-TEST' and p['completed']==2 and p['failed']==0
    assert len(p['documents'])==2 and len(p['history'])==1 and p['history'][0]['task_id']==old['task_id']
    assert e.calls==['a.pdf','b.pdf','a.pdf']
    with d._kernel() as k:
        assert preserved(k,old)==before
        successor=k._connection.execute('SELECT payload_json FROM manifests WHERE task_id=?',(task['task_id'],)).fetchone()
        assert json.loads(successor[0])['max_retries']==0
        k.verify_audit_chain()
    reopened,_=make(tmp_path)
    assert reopened.progress(REQ)['completed']==2
    with pytest.raises(PermissionDenied):reopened.owner_successor(REQ,task['task_id'])
    # Even a second approved task cannot spend the same original-failure grant.
    next_task,_=prepare_from_old(d,old)
    with pytest.raises(PermissionDenied):d.owner_successor(REQ,next_task['task_id'])
    assert e.calls==['a.pdf','b.pdf','a.pdf']

def prepare_from_old(d,old):
    # A second proposed successor is intentionally rejected by the durable claim.
    with d._kernel() as k:
        first=json.loads(k._connection.execute("SELECT payload_json FROM tasks WHERE task_id=(SELECT json_extract(payload_json,'$.successor_task_id') FROM audit_events WHERE event_type='UI03_SUCCESSOR_AUTHORIZED' AND entity_id=?)",(old['task_id'],)).fetchone()[0])
    meta=json.loads(next(s[len('document-json:'):] for s in first['inputs'] if s.startswith('document-json:')))
    grant=json.loads(next(s[len('successor-json:'):] for s in first['inputs'] if s.startswith('successor-json:')))
    task=d._task(REQ,'RUN-SECOND-UNAUTHORIZED',parent=old['task_id'],document=meta)
    task['inputs']+=['successor-json:'+json.dumps(grant,sort_keys=True),grant['authority_reference']]
    with d._kernel() as k,k.atomic_execution():
        d._register(k,task,gate_triggers=('authority_ambiguity',))
        k.record_human_gate_decision(task['task_id'],'authority_ambiguity','APPROVED',actor_id='HUMAN_PROJECT_OWNER',authority_reference=_digest(grant))
    return task,old

@pytest.mark.parametrize('change',[{'sha256':'0'*64},{'case_id':'OTHER'},{'tax_year':2024},{'owner_hash':'0'*64},{'original_manifest_id':'MAN-NOT-BOUND'}, {'expires_at':'2000-01-01T00:00:00+00:00'}])
def test_mismatched_or_expired_successor_authority_denied(tmp_path,change):
    d,e=failed(tmp_path);task,_=prepare(d,source=change);before=list(e.calls)
    with pytest.raises((PermissionDenied,ContractError)):d.owner_successor(REQ,task['task_id'])
    assert e.calls==before

def test_missing_owner_gate_and_source_changes_do_not_send(tmp_path):
    d,e=failed(tmp_path);task,_=prepare(d,approved=False)
    with pytest.raises((PermissionDenied,ContractError)):d.owner_successor(REQ,task['task_id'])
    assert len(e.calls)==2

def test_successor_failure_is_not_retried(tmp_path):
    d,e=failed(tmp_path);task,_=prepare(d);d.owner_successor(REQ,task['task_id']);p=wait(d)
    assert p['failed']==1 and p['completed']==1 and len(e.calls)==3
    with pytest.raises((PermissionDenied,ContractError)):d.owner_successor(REQ,task['task_id'])
    assert len(e.calls)==3


def test_changed_original_bytes_never_reach_provider(tmp_path):
    d,e=failed(tmp_path);task,_=prepare(d);before=list(e.calls)
    d.worker.host.get_case_document=lambda c,y,doc:({'id':doc,'name':'a.pdf'},b'%PDF-altered')
    d.owner_successor(REQ,task['task_id']);p=wait(d)
    assert p['failed']==1 and p['completed']==1 and e.calls==before
    with pytest.raises(PermissionDenied):d.owner_successor(REQ,task['task_id'])

@pytest.mark.parametrize('mutation',[
    "UPDATE responses SET payload_json=replace(payload_json,'ValueError','CORRUPTED_FAILURE') WHERE task_id=?",
    "DELETE FROM responses WHERE task_id=?",
    "UPDATE responses SET manifest_id=(SELECT manifest_id FROM manifests WHERE task_id!=? LIMIT 1) WHERE task_id=?",
])
def test_corrupt_original_failure_denied_before_provider_or_claim(tmp_path,mutation):
    d,e=failed(tmp_path);task,old=prepare(d);before=list(e.calls)
    with d._kernel() as k:
        args=(old['task_id'],)*mutation.count('?')
        with k._connection:k._connection.execute(mutation,args)
    with pytest.raises((PermissionDenied,ContractError)):d.owner_successor(REQ,task['task_id'])
    assert e.calls==before
    with d._kernel() as k:
        assert k._connection.execute("SELECT count(*) FROM audit_events WHERE event_type='UI03_SUCCESSOR_AUTHORIZED'").fetchone()[0]==0

def test_forged_approval_rows_without_owner_audit_do_not_grant_authority(tmp_path):
    d,e=failed(tmp_path);task,_=prepare(d,approved=False)
    grant=json.loads(next(s[len('successor-json:'):] for s in task['inputs'] if s.startswith('successor-json:')))
    with d._kernel() as k:
        with k._connection:
            k._connection.execute("UPDATE task_human_gates SET status='APPROVED',authority_reference=? WHERE task_id=?",(_digest(grant),task['task_id']))
            k._connection.execute("UPDATE tasks SET status='REGISTERED' WHERE task_id=?",(task['task_id'],))
    with pytest.raises(PermissionDenied,match='approval audit'):d.owner_successor(REQ,task['task_id'])
    assert len(e.calls)==2

def test_original_failure_corrupted_after_claim_still_cannot_transmit(tmp_path):
    d,e=failed(tmp_path);task,old=prepare(d);before=list(e.calls)
    original_get=d.worker.host.get_case_document
    def changed(c,y,doc):
        with d._kernel() as k:
            with k._connection:k._connection.execute("UPDATE responses SET payload_json=replace(payload_json,'ValueError','CORRUPTED_FAILURE') WHERE task_id=?",(old['task_id'],))
        return original_get(c,y,doc)
    d.worker.host.get_case_document=changed
    d.owner_successor(REQ,task['task_id']);d._pool.submit(lambda:None).result(timeout=10)
    assert e.calls==before

def test_installed_interactions_transport_has_zero_retries(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from google.genai._gaos.google_genai import _translate_retry_config
    from google.genai._gaos.utils.retries import retry_with_attempt_count_backoff
    d,e=failed(tmp_path);task,_=prepare(d);calls=[];observed=[]
    monkeypatch.setenv('GEMINI_API_KEY','synthetic-not-a-key')
    def factory(*,api_key,http_options):
        assert api_key=='synthetic-not-a-key'
        assert http_options.base_url=='https://generativelanguage.googleapis.com'
        config=_translate_retry_config(http_options);observed.append(config.max_retries)
        def create(**kwargs):
            assert kwargs['store'] is False and kwargs['model']=='gemini-3.8-flash'
            assert kwargs['automatic_continuation'] is False
            def denied(attempt):calls.append(attempt);raise RuntimeError('synthetic provider failure')
            return retry_with_attempt_count_backoff(denied,max_retries=config.max_retries)
        return SimpleNamespace(interactions=SimpleNamespace(create=create),close=lambda:None)
    monkeypatch.setattr('google.genai.Client',factory)
    d.worker._extractor=None
    d.owner_successor(REQ,task['task_id']);result=wait(d)
    assert result['failed']==1 and observed==[0] and calls==[0]
