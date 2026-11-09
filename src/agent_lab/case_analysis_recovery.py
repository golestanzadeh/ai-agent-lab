"""Owner-requested, single-document plans using existing Kernel Human Gates."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from uuid import uuid4

from agent_lab.orchestrator_kernel import PermissionDenied, _digest


def _original(d, k, request, task_id):
    tasks = {t['task_id']: t for t in d._tasks(k, request)}
    t = tasks.get(task_id)
    if t is None or t['objective'] != 'UI03_DOCUMENT_V1' or t['status'] != 'FAILED':
        raise PermissionDenied('A scoped failed document is required')
    d._verified_responses(k, t)
    meta = json.loads(next(v[len('document-json:'):] for v in t['inputs'] if v.startswith('document-json:')))
    m = k._connection.execute('SELECT manifest_id,state FROM manifests WHERE task_id=?', (task_id,)).fetchall()
    if len(m) != 1 or m[0]['state'] != 'FAILED':
        raise PermissionDenied('Failed manifest required')
    return t, meta, m[0]['manifest_id']


def prepare(d, request, failed_task_id):
    if d.worker is None:
        raise PermissionDenied('Authorized worker unavailable')
    with d._lock, d._kernel() as k, k.atomic_execution():
        k.verify_audit_chain()
        t, meta, manifest = _original(d, k, request, failed_task_id)
        if k.kill_switch_state() != 'RUNNING':
            raise PermissionDenied('Kill switch blocks recovery')
        if k._connection.execute("SELECT 1 FROM audit_events WHERE event_type='UI03_SUCCESSOR_AUTHORIZED' AND entity_id=?", (failed_task_id,)).fetchone():
            raise PermissionDenied('This failure already has an attempted successor')
        for pending in d._tasks(k, request):
            if pending['status'] not in ('REGISTERED', 'ACTIVE', 'HUMAN_REQUIRED'):
                continue
            if pending['status']=='HUMAN_REQUIRED':
                gate=k._connection.execute("SELECT status FROM task_human_gates WHERE task_id=? AND trigger='authority_ambiguity'",(pending['task_id'],)).fetchone()
                if gate is None or gate[0]!='PENDING':continue
            if pending['parent_task_id'] == failed_task_id and pending['status'] in ('REGISTERED','HUMAN_REQUIRED'):
                pending_grant=json.loads(next(v[len('successor-json:'):] for v in pending['inputs'] if v.startswith('successor-json:')))
                if datetime.now(timezone.utc) < min(datetime.fromisoformat(pending['expires_at']),datetime.fromisoformat(pending_grant['expires_at'])):
                    return plan(k, pending)
                if pending['status']=='HUMAN_REQUIRED':
                    k.record_human_gate_decision(pending['task_id'],'authority_ambiguity','REJECTED',
                        actor_id='HUMAN_PROJECT_OWNER',authority_reference='owner://ui03-expired-recovery-plan')
                else:
                    k.close_unstarted_task(pending['task_id'], actor_id='HUMAN_PROJECT_OWNER',
                                          authority_reference='owner://ui03-expired-recovery-plan',
                                          reason='Owner requested replacement of expired unstarted plan',
                                          outcome='EXPIRED' if datetime.now(timezone.utc)>=datetime.fromisoformat(pending['expires_at']) else 'CANCELLED')
                continue
            raise PermissionDenied('Other case execution requires reconciliation')
        # Read only the exact old source; do not spend provider budget or call Gemini.
        entry, content = d.worker.host.get_case_document(request.case_id, request.tax_year, meta['document_id'])
        if entry['id'] != meta['document_id'] or hashlib.sha256(content).hexdigest() != meta['sha256']:
            raise PermissionDenied('Original source changed')
        run = 'RUN-UI03-' + uuid4().hex.upper()
        task = d._task(request, run, parent=failed_task_id,
                       document={**meta, 'supersedes_task_id': failed_task_id})
        grant = {'original_task_id': failed_task_id, 'original_manifest_id': manifest,
                 'document_id': meta['document_id'], 'sha256': meta['sha256'],
                 'case_id': request.case_id, 'tax_year': request.tax_year,
                 'owner_hash': hashlib.sha256(request.owner_id.encode()).hexdigest(),
                 'authority_reference': 'owner://ui03-document-retry/' + task['task_id'],
                 'expires_at': (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
                 'implementation_ref': 'ui03-owner-recovery-v1'}
        task['inputs'] += ['successor-json:' + json.dumps(grant, sort_keys=True), grant['authority_reference']]
        d._register(k, task, gate_triggers=('authority_ambiguity',))
        # Deliberately no approval here. Only the explicit confirmation endpoint may approve.
        return plan(k, task)


def plan(k, task):
    meta = json.loads(next(v[len('document-json:'):] for v in task['inputs'] if v.startswith('document-json:')))
    return {'case_id': task['case_context']['case_id'], 'tax_year': task['case_context']['tax_year'],
            'run_id': task['case_context']['run_id'], 'successor_task_id': task['task_id'],
            'document_id': meta['document_id'], 'sha256': meta['sha256'],
            'max_retries': 0, 'model': meta['model'], 'store': False,
            'status': 'OWNER_APPROVAL_REQUIRED', 'requires_uncertain_outcome_acknowledgement': True}


def approve(d, request, task_id, acknowledgement):
    if acknowledgement != 'APPROVE_ONE_ATTEMPT_INCLUDING_UNCERTAIN_OUTCOME':
        raise PermissionDenied('Explicit Owner acknowledgement required')
    with d._lock, d._kernel() as k, k.atomic_execution():
        tasks = {t['task_id']: t for t in d._tasks(k, request)}
        task = tasks.get(task_id)
        if task is None or task['status'] not in ('HUMAN_REQUIRED', 'REGISTERED'):
            raise PermissionDenied('Unconsumed recovery plan required')
        grant = json.loads(next(v[len('successor-json:'):] for v in task['inputs'] if v.startswith('successor-json:')))
        if datetime.now(timezone.utc) >= datetime.fromisoformat(grant['expires_at']):
            raise PermissionDenied('Recovery approval expired')
        gate = k._connection.execute("SELECT status FROM task_human_gates WHERE task_id=? AND trigger='authority_ambiguity'", (task_id,)).fetchone()
        if gate is None:
            raise PermissionDenied('Approval unavailable')
        if task['status'] == 'HUMAN_REQUIRED' and gate[0] == 'PENDING':
            k.record_human_gate_decision(task_id, 'authority_ambiguity', 'APPROVED',
                                        actor_id='HUMAN_PROJECT_OWNER', authority_reference=_digest(grant))
        elif task['status'] != 'REGISTERED' or gate[0] != 'APPROVED':
            raise PermissionDenied('Approval already used or unavailable')
        # An interrupted approved-but-unclaimed admission may resume. Verify the
        # original durable approval and all source/scope bindings; never mint a
        # second approval or permit a consumed claim to dispatch again.
        d._successor_binding(k, {**task, 'status': 'REGISTERED'}, execution=True, claimed=False)
    return d.owner_successor(request, task_id)


def decorate(k, documents):
    """Unstarted/closed plans never hide a real failure or result."""
    from agent_lab.case_analysis_diagnostics import legacy
    for document in documents:
        events=k._connection.execute("SELECT payload_json FROM audit_events WHERE event_type='UI03_DIAGNOSTIC_RECORDED' AND entity_id=? ORDER BY event_id",(document['task_id'],)).fetchall()
        if events:
            value=json.loads(events[-1][0])['diagnostic']
            if (value['task_id']!=document['task_id'] or value['run_id']!=document['run_id'] or value['document_id']!=document['document_id']):
                raise PermissionDenied('Diagnostic scope mismatch')
            document['diagnostic']=value
        if document['processing_status'] == 'FAILED':
            document.setdefault('diagnostic', legacy(document))
            document['retry_eligibility'] = 'EXPLICIT_OWNER_APPROVAL_REQUIRED'
        if 'supersedes_task_id' in document:
            claim = k._connection.execute("SELECT 1 FROM audit_events WHERE event_type='UI03_SUCCESSOR_AUTHORIZED' AND json_extract(payload_json,'$.successor_task_id')=?", (document['task_id'],)).fetchone()
            document['_unstarted_plan'] = claim is None
    return documents
