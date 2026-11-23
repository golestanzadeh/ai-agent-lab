"""Owner Broker operations in the EXISTING Kernel ledger/transaction/audit.

No HTTP issuer, database, identity writer or continuity substitute. Enrollment is
local credential enrollment only, never live Identity genesis or Witness acceptance.
"""
import base64
from datetime import datetime,timedelta,timezone
import hashlib
import secrets

from agent_lab.ipc_wire_primitives import canonical_json_bytes
from agent_lab.owner_identity_assertion import (
    CONTRACT,SCOPE,EnrolledOwnerCredential,OwnerAssertionError,intent_challenge,
    verify_owner_assertion,verify_challenge_assertion,
)

APPROVAL='APPROVE_OPTION_B_OWNER_ENROLLMENT_V1'
REGISTRATION_DOMAIN=b'AI-TAX-AGENT\0OWNER-BROKER-REGISTRATION\0V1\0'

def _time(value):return value.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
def _hash(value):return 'sha256:'+hashlib.sha256(canonical_json_bytes(value)).hexdigest()
def _encode(value):return base64.b64encode(value).decode('ascii')
def _decode(value):return base64.b64decode(value,validate=True)
def _key(deployment):return 'owner-broker:v1:'+deployment
def _load(kernel,deployment):
    kernel._verify_identity_protocol_state()
    state=kernel._identity_payload('identity_kernel_state','deployment_id',_key(deployment))
    if state is None:raise OwnerAssertionError('Owner enrollment unavailable')
    return state
def _save(kernel,deployment,state):
    kernel._store_identity_payload('identity_kernel_state','deployment_id',_key(deployment),state)
def _clock(now):
    if not isinstance(now,datetime) or now.utcoffset() is None:raise OwnerAssertionError('aware Owner clock required')

def begin_enrollment(kernel,*,owner_id,deployment_id,store_id,approval,now):
    """Trusted native bootstrap only. Explicit approved scope, no agent endpoint."""
    _clock(now)
    if approval!=APPROVAL or any(type(v) is not str or not 1<=len(v)<=256 for v in (owner_id,deployment_id,store_id)):
        raise OwnerAssertionError('exact approved enrollment scope required')
    with kernel.atomic_execution():
        kernel._verify_identity_protocol_state()
        old=kernel._identity_payload('identity_kernel_state','deployment_id',_key(deployment_id))
        if old is not None:
            if (old['owner_id'],old['store_id'])!=(owner_id,store_id):raise OwnerAssertionError('enrollment scope conflict')
            if old['status']=='ENROLLED_LOCAL':raise OwnerAssertionError('Owner already enrolled; no replacement permitted')
            if old['expires_at']>_time(now):return old
        state=dict(contract='ai-tax-agent.owner-broker-registration/1',owner_id=owner_id,
            deployment_id=deployment_id,store_id=store_id,approval=APPROVAL,nonce=secrets.token_hex(32),
            issued_at=_time(now),expires_at=_time(now+timedelta(minutes=5)),status='PENDING')
        _save(kernel,deployment_id,state)
        return state

def enrollment_challenge(state):
    fields=('contract','owner_id','deployment_id','store_id','approval','nonce','issued_at','expires_at')
    return hashlib.sha256(REGISTRATION_DOMAIN+canonical_json_bytes({key:state[key] for key in fields})).digest()

def _finish_enrollment(kernel,*,deployment_id,credential,assertion,now):
    """Broker native registration + fresh required-UV possession, no arbitrary pin."""
    _clock(now)
    with kernel.atomic_execution():
        state=_load(kernel,deployment_id)
        if state['status']!='PENDING' or not state['issued_at']<=_time(now)<state['expires_at']:
            raise OwnerAssertionError('pending enrollment expired or already settled')
        proof=verify_challenge_assertion(challenge=enrollment_challenge(state),nonce=state['nonce'],
            owner_id=state['owner_id'],enrollment=credential,**assertion)
        state.update(status='ENROLLED_LOCAL',credential_id=_encode(credential.credential_id),
            public_key_der=_encode(credential.public_key_der),counter=proof.counter,
            proof_digest=proof.proof_digest,revoked=False, intents={})
        _save(kernel,deployment_id,state)
        binding={name:state[name] for name in ('contract','owner_id','deployment_id','store_id','credential_id','public_key_der','proof_digest')}
        return dict(status=state['status'],enrollment_ref=_hash(binding),proof_digest=proof.proof_digest)

def enroll_native(kernel,*,owner_id,deployment_id,store_id,approval,clock,key_root=None):
    """The production bootstrap entry point has no injectable authenticator/key."""
    from agent_lab.owner_identity_native import WindowsHello
    state=begin_enrollment(kernel,owner_id=owner_id,deployment_id=deployment_id,store_id=store_id,
                           approval=approval,now=clock())
    native=WindowsHello()
    credential_id,public=native.register(owner_id,enrollment_challenge(state))
    credential=EnrolledOwnerCredential(owner_id,credential_id,public,0)
    assertion=native.assert_challenge(enrollment_challenge(state),credential_id)
    # Verify before provisioning app keys. finish repeats under the writer lock.
    verify_challenge_assertion(challenge=enrollment_challenge(state),nonce=state['nonce'],
        owner_id=owner_id,enrollment=credential,**assertion)
    if key_root is not None:
        from agent_lab.owner_identity_keys import provision_keys
        provision_keys(key_root,owner_id=owner_id,approval=approval)
    return _finish_enrollment(kernel,deployment_id=deployment_id,credential=credential,assertion=assertion,now=clock())

def _credential(state,*,counter=None):
    if state['status']!='ENROLLED_LOCAL' or state.get('revoked') is not False:
        raise OwnerAssertionError('accepted nonrevoked Owner enrollment required')
    return EnrolledOwnerCredential(state['owner_id'],_decode(state['credential_id']),_decode(state['public_key_der']),
                                  state['counter'] if counter is None else counter)

def _authorize(kernel,scope):
    from agent_lab.ipc_operational_read import OPERATION_CAPABILITIES
    kernel._identity_continuity_context(manifest_id=scope['manifest_id'],task_id=scope['task_id'],
        run_id=scope['run_id'],case_id=scope['case_id'],tax_year=int(scope['tax_year']),operation=scope['operation'])
    capability=OPERATION_CAPABILITIES.get(scope['operation'])
    if capability is None or not kernel.permission_decision(scope['manifest_id'],capability,
        case_id=scope['case_id'],tax_year=int(scope['tax_year']),run_id=scope['run_id']).allowed:
        raise OwnerAssertionError('active exact Kernel permission required')
    state=kernel._identity_payload('identity_kernel_state','deployment_id',scope['deployment_id'])
    if state is None or state.get('status')!='ACTIVE' or kernel._identity_verified_heads.get(scope['deployment_id'])!=state.get('previous_record'):
        raise OwnerAssertionError('externally verified Identity deployment required')

def issue_intent(kernel,*,scope,now):
    _clock(now)
    if type(scope) is not dict or set(scope)!=SCOPE:raise OwnerAssertionError('closed Owner execution scope required')
    with kernel.atomic_execution():
        state=_load(kernel,scope['deployment_id']);_credential(state)
        if (state['owner_id'],state['store_id'])!=(scope['owner_id'],scope['store_id']):raise OwnerAssertionError('Owner/store mismatch')
        _authorize(kernel,scope)
        intent=dict(contract=CONTRACT,**scope,nonce=secrets.token_hex(32),issued_at=_time(now),expires_at=_time(now+timedelta(minutes=5)))
        intent_challenge(intent)
        state['intents'][intent['nonce']]=dict(intent=intent,status='PENDING',counter=state['counter'])
        _save(kernel,scope['deployment_id'],state)
        return intent

def approve_intent(kernel,*,deployment_id,nonce,assertion,now):
    """Consume challenge and issue scoped approval in ONE Kernel SQLite commit.

    Identical lost-response recovery returns the original approval, never a second
    grant. Actual Identity one-time authorization is still consumed by its existing
    atomic mutation, not by this Broker ledger.
    """
    _clock(now)
    with kernel.atomic_execution():
        state=_load(kernel,deployment_id);_credential(state)
        item=state['intents'].get(nonce)
        if item is None:raise OwnerAssertionError('unknown Owner nonce')
        intent=item['intent'];scope={k:intent[k] for k in SCOPE};_authorize(kernel,scope)
        proof=verify_owner_assertion(intent=intent,expected_scope=scope,
            enrollment=_credential(state,counter=item['counter']),now=now,**assertion)
        if item['status']=='APPROVED':
            if item['proof_digest']!=proof.proof_digest:raise OwnerAssertionError('Owner nonce already consumed')
            return item['approval']
        if state['counter'] and proof.counter<=state['counter']:raise OwnerAssertionError('stale Owner counter')
        approval=dict(contract='ai-tax-agent.owner-approval/1',intent_digest=proof.intent_digest,
                      proof_digest=proof.proof_digest,scope=scope,nonce=nonce)
        approval['authority_reference']=_hash(approval)
        item.update(status='APPROVED',approval=approval,proof_digest=proof.proof_digest)
        state['counter']=proof.counter
        _save(kernel,deployment_id,state)
        return approval

def main():
    import argparse
    import os
    from pathlib import Path
    from uuid import uuid4
    from agent_lab.orchestrator_kernel import OrchestratorKernel
    parser=argparse.ArgumentParser(description='Native Option B Owner credential enrollment; no person records or protected runtime activation')
    parser.add_argument('--enroll',action='store_true')
    args=parser.parse_args()
    if not args.enroll:
        parser.print_help();return 0
    # Resolve the actual local Owner SID, not a browser actor string. SID chooses
    # which credential to enroll; Windows Hello possession supplies authentication.
    import win32api,win32security
    token=win32security.OpenProcessToken(win32api.GetCurrentProcess(),win32security.TOKEN_QUERY)
    try:owner='WINDOWS-OWNER:'+win32security.ConvertSidToStringSid(win32security.GetTokenInformation(token,win32security.TokenUser)[0])
    finally:token.Close()
    root=Path(os.environ['LOCALAPPDATA'])/'AI-Tax-Agent'/'Cases'
    database=root/'orchestrator-kernel.sqlite'
    if not database.is_file():raise OwnerAssertionError('existing canonical Kernel database required')
    contract=Path(__file__).resolve().parents[2]/'contracts'/'orchestrator'/'v1'
    print('AI-Tax-Agent: enroll one Windows Hello Owner credential and separate local application keys.')
    print('No taxpayer records, external submission, cloud permissions or Family activation. Windows Hello will request verification twice.')
    with OrchestratorKernel(database,contract) as kernel:
        kernel._verify_identity_protocol_state()
        states=[__import__('json').loads(row[0]) for row in kernel._connection.execute(
            "SELECT payload_json FROM identity_kernel_state WHERE deployment_id LIKE 'owner-broker:v1:%'")]
        if len(states)>1:raise OwnerAssertionError('ambiguous local Owner deployment; reconciliation required')
        state=states[0] if states else dict(deployment_id='dep:v1:'+str(uuid4()),store_id='store:v1:'+str(uuid4()))
        result=enroll_native(kernel,owner_id=owner,deployment_id=state['deployment_id'],store_id=state['store_id'],
            approval=APPROVAL,clock=lambda:datetime.now(timezone.utc),key_root=root)
        print(result['status'])
        print('Credential enrollment only. Family remains gated by accepted source, Witness and runtime composition.')
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except OwnerAssertionError as error:
        print(str(error));raise SystemExit(2)
