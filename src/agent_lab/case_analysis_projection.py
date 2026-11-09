"""Durable, case-scoped projection of reviewed artifacts through existing Kernel records.

Import is a trusted local Owner operation, never an HTTP upload or a tax-acceptance
endpoint. The dashboard only reads the immutable response and its audit binding.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
from uuid import uuid4

from agent_lab.orchestrator_kernel import PermissionDenied, _digest

OBJECTIVE='CASE_ANALYSIS_PROJECTION_V1'
FIELDS={'case_id','tax_year','csv','subtotals','conditional','links','questions','spouse_payroll','acceptance'}


def validate(request, payload):
    if set(payload)!=FIELDS or payload['case_id']!=request.case_id or payload['tax_year']!=request.tax_year:
        raise PermissionDenied('Projection scope/schema mismatch')
    if payload['acceptance']!='VERIFIED_SUBTOTALS_NOT_FINAL_TAX_ACCEPTANCE':
        raise PermissionDenied('Final tax acceptance cannot be imported here')
    if len(json.dumps(payload,ensure_ascii=False).encode())>512*1024:
        raise ValueError('Projection too large')
    c=payload['csv']
    if set(c)!={'source_sha256','row_count','credits','debits','net','status'} or type(c['row_count']) is not int or not 0<c['row_count']<=100000:
        raise ValueError('Invalid CSV evidence')
    if not isinstance(c['source_sha256'],str) or len(c['source_sha256'])!=64 or any(x not in '0123456789abcdef' for x in c['source_sha256']):
        raise ValueError('Source digest required')
    for key in ['credits','debits','net']:
        if not isinstance(c[key],str) or len(c[key])>32 or not Decimal(c[key]).is_finite():raise ValueError('Invalid exact amount')
    if Decimal(c['credits'])-Decimal(c['debits'])!=Decimal(c['net']):raise ValueError('CSV reconciliation mismatch')
    if not isinstance(payload['subtotals'],dict) or not isinstance(payload['conditional'],dict):raise ValueError('Invalid subtotals')
    if not isinstance(payload['links'],list) or len(payload['links'])>10000:raise ValueError('Invalid evidence links')
    if not isinstance(payload['questions'],list) or any(not isinstance(x,str) or len(x)>2000 for x in payload['questions']):raise ValueError('Invalid questions')


def import_reviewed(d, request, payload, *, source_bindings, authority_reference, verify_case):
    """Caller verifies actual immutable source hashes/review evidence and case authority.

    No registered provider is called; this is a local derived-evidence import,
    with its own least-privilege manifest and normal Kernel budget/audit checks.
    """
    validate(request,payload)
    if not callable(verify_case) or verify_case(request.case_id,request.tax_year,request.owner_id) is not True:
        raise PermissionDenied('Canonical case authority unavailable')
    if not authority_reference.startswith('owner://') or not source_bindings or any(not isinstance(x,str) or not x.startswith('sha256:') or len(x)!=71 for x in source_bindings):
        raise PermissionDenied('Explicit Owner authority and immutable bindings required')
    owner='owner-sha256:'+hashlib.sha256(request.owner_id.encode()).hexdigest()
    with d._lock,d._kernel() as k,k.atomic_execution():
        k.verify_audit_chain()
        if k.kill_switch_state()!='RUNNING':raise PermissionDenied('Kernel halted')
        old=read(d,request,kernel=k)
        if old and old['payload']==payload and old['source_bindings']==source_bindings:return old
        uid=uuid4().hex.upper();run='RUN-CASE-PROJECTION-'+uid
        task=d._task(request,run)
        task.update(objective=OBJECTIVE,inputs=[authority_reference,owner,*source_bindings],
                    allowed_tools=['local_reviewed_artifact_read'],
                    budget={'token_limit':1,'tool_call_limit':1,'cost_limit_usd':0.01},
                    expected_outputs=['kernel://case-projection/'+run])
        d._register(k,task)
        manifest={'schema_version':1,'manifest_id':'MAN-CASE-PROJECTION-'+uid,
                  'task_id':task['task_id'],'parent_task_id':None,'role_id':task['role_id'],'actor_instance_id':task['actor_instance_id'],
                  'scope':{'repository':task['repository'],'ref':task['ref'],'allowed_paths':[],'case_context':task['case_context']},
                  'inputs':task['inputs'],'expected_outputs':task['expected_outputs'],'allowed_tools':task['allowed_tools'],
                  'requested_access_tiers':['A3','A4'],'requested_capabilities':task['permissions'],
                  'forbidden_actions':task['forbidden_actions'],'budget':task['budget'],'timeout_seconds':120,
                  'max_retries':0,'stop_conditions':task['stop_conditions'],'escalation_route':task['escalation_route'],
                  'issued_at':datetime.now(timezone.utc).isoformat(),'expires_at':task['expires_at'],'status':'PROPOSED'}
        mid=manifest['manifest_id'];k.register_manifest(manifest);k.validate_manifest(mid);k.activate_manifest(mid)
        for capability in task['permissions']:
            if not k.permission_decision(mid,capability,**task['case_context']).allowed:raise PermissionDenied('Projection permission denied')
        if not k.consume_budget(mid,tokens=0,tool_calls=1,cost_usd=0).allowed:raise PermissionDenied('Projection budget denied')
        result={'run_id':run,'payload':payload,'source_bindings':source_bindings}
        k.transition_manifest(mid,'BLOCKED',actor_id=task['actor_instance_id'],reason='Projection is not final tax acceptance')
        k.record_response(mid,{'schema_version':1,'response_id':'RESP-CASE-PROJECTION-'+uid,'task_id':task['task_id'],
            'parent_task_id':None,'role_id':task['role_id'],'actor_instance_id':task['actor_instance_id'],
            'status':'HUMAN_REQUIRED','result_summary':json.dumps(result,ensure_ascii=False,sort_keys=True),
            'artifact_references':task['expected_outputs'],'changed_paths_or_state':[],'tests':[],
            'evidence':source_bindings,'authority_used':[authority_reference],
            'costs':{'tokens_used':0,'tool_calls_used':1,'cost_usd':0.0},
            'unresolved_risks':['Not a final tax result; conditional amounts remain conditional'],
            'recommended_next_action':'Review outstanding evidence; Approval and Submission disabled',
            'human_required':True,'created_at':datetime.now(timezone.utc).isoformat()})
        return result


def read(d, request, *, kernel=None):
    if kernel is None:
        with d._lock,d._kernel() as k:return read(d,request,kernel=k)
    k=kernel;k.verify_audit_chain()
    owner='owner-sha256:'+hashlib.sha256(request.owner_id.encode()).hexdigest()
    for r in k._connection.execute("SELECT payload_json,status FROM tasks WHERE json_extract(payload_json,'$.objective')=? ORDER BY created_at DESC,task_id DESC",(OBJECTIVE,)):
        t=json.loads(r['payload_json'])
        if t['case_context']['case_id']!=request.case_id or t['case_context']['tax_year']!=request.tax_year or owner not in t['inputs']:continue
        bindings=k._connection.execute("SELECT payload_json FROM audit_events WHERE event_type='UI03_INTENT_BOUND' AND entity_id=?",(t['task_id'],)).fetchall()
        if len(bindings)!=1 or json.loads(bindings[0][0]).get('task_digest')!=_digest(t):raise PermissionDenied('Projection intent mismatch')
        d._verified_responses(k,{**t,'status':r['status']})
        row=k._connection.execute('SELECT payload_json FROM responses WHERE task_id=?',(t['task_id'],)).fetchone()
        if row is None:raise PermissionDenied('Incomplete case projection')
        result=json.loads(json.loads(row[0])['result_summary']);validate(request,result['payload'])
        if result['run_id']!=t['case_context']['run_id'] or result['source_bindings']!=[x for x in t['inputs'] if x.startswith('sha256:')]:
            raise PermissionDenied('Projection binding mismatch')
        return result
    return None
