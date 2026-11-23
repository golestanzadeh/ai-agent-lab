"""Isolated canonical Kernel ledger and native-registration verification vectors."""
from datetime import datetime,timezone,timedelta
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
import pytest
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import ec
from agent_lab import owner_identity_broker as broker
from agent_lab.owner_identity_assertion import EnrolledOwnerCredential,OwnerAssertionError,RP_ID
from agent_lab.owner_identity_native import _client,registration_public_key,WindowsHello
from agent_lab.orchestrator_kernel import OrchestratorKernel

ROOT=Path(__file__).resolve().parents[2]/'contracts'/'orchestrator'/'v1'
NOW=datetime.now(timezone.utc)

def credential():
    private=ec.generate_private_key(ec.SECP256R1())
    return private,EnrolledOwnerCredential('TEST-OWNER',b'TEST-CREDENTIAL',private.public_key().public_bytes(
        serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo),0)

def assertion(private,enrollment,challenge,counter=1):
    raw,_,_=_client('webauthn.get',challenge)
    auth=hashlib.sha256(RP_ID.encode()).digest()+b'\x05'+counter.to_bytes(4,'big')
    return dict(credential_id=enrollment.credential_id,client_data_json=raw,authenticator_data=auth,
        signature=private.sign(auth+hashlib.sha256(raw).digest(),ec.ECDSA(hashes.SHA256())))

def enroll(kernel,*,deployment='TEST-DEPLOYMENT',owner='TEST-OWNER',store='TEST-STORE'):
    state=broker.begin_enrollment(kernel,owner_id=owner,deployment_id=deployment,store_id=store,approval=broker.APPROVAL,now=NOW)
    key,pin=credential()
    result=broker._finish_enrollment(kernel,deployment_id=deployment,credential=pin,
        assertion=assertion(key,pin,broker.enrollment_challenge(state)),now=NOW)
    return key,pin,result

def scope():
    return dict(operation='REGISTER_IDENTITY',owner_id='TEST-OWNER',case_id='TEST-CASE',tax_year='2025',
        subject_id='TEST-PERSON',input_digest='sha256:'+'1'*64,deployment_id='TEST-DEPLOYMENT',store_id='TEST-STORE',
        task_id='TEST-TASK',manifest_id='TEST-MANIFEST',run_id='TEST-RUN')

def test_enrollment_cancel_expiry_and_restart(tmp_path):
    path=tmp_path/'kernel.sqlite'
    with OrchestratorKernel(path,ROOT) as kernel:
        state=broker.begin_enrollment(kernel,owner_id='TEST-OWNER',deployment_id='TEST-DEPLOYMENT',store_id='TEST-STORE',approval=broker.APPROVAL,now=NOW)
        assert broker._load(kernel,'TEST-DEPLOYMENT')['status']=='PENDING'
        key,pin=credential()
        with pytest.raises(OwnerAssertionError):broker._finish_enrollment(kernel,deployment_id='TEST-DEPLOYMENT',credential=pin,
            assertion=assertion(key,pin,broker.enrollment_challenge(state)),now=NOW+timedelta(minutes=5))
        assert broker._load(kernel,'TEST-DEPLOYMENT')['status']=='PENDING'
    with OrchestratorKernel(path,ROOT) as kernel:
        key,pin,result=enroll(kernel)
        assert result['status']=='ENROLLED_LOCAL'
    with OrchestratorKernel(path,ROOT) as kernel:
        assert broker._credential(broker._load(kernel,'TEST-DEPLOYMENT')).public_key_der==pin.public_key_der
        with pytest.raises(OwnerAssertionError):enroll(kernel)

def test_nonce_atomic_replay_rollback_and_lost_response(tmp_path):
    path=tmp_path/'kernel.sqlite'
    with OrchestratorKernel(path,ROOT) as kernel:
        private,pin,_=enroll(kernel)
        # Unit isolation of the nonce transaction. Real permission/Witness denial
        # and integration below exercise the production authorization function.
        with patch.object(broker,'_authorize'):
            intent=broker.issue_intent(kernel,scope=scope(),now=NOW)
            from agent_lab.owner_identity_assertion import intent_challenge
            proof=assertion(private,pin,intent_challenge(intent),counter=2)
            save=broker._save
            def fail(*args):save(*args);raise RuntimeError('injected before commit')
            with patch.object(broker,'_save',side_effect=fail),pytest.raises(RuntimeError):
                broker.approve_intent(kernel,deployment_id='TEST-DEPLOYMENT',nonce=intent['nonce'],assertion=proof,now=NOW)
            assert broker._load(kernel,'TEST-DEPLOYMENT')['intents'][intent['nonce']]['status']=='PENDING'
            first=broker.approve_intent(kernel,deployment_id='TEST-DEPLOYMENT',nonce=intent['nonce'],assertion=proof,now=NOW)
            assert broker.approve_intent(kernel,deployment_id='TEST-DEPLOYMENT',nonce=intent['nonce'],assertion=proof,now=NOW)==first
    with OrchestratorKernel(path,ROOT) as kernel,patch.object(broker,'_authorize'):
        assert broker.approve_intent(kernel,deployment_id='TEST-DEPLOYMENT',nonce=intent['nonce'],assertion=proof,now=NOW)==first
        with pytest.raises(OwnerAssertionError):broker.approve_intent(kernel,deployment_id='TEST-DEPLOYMENT',nonce=intent['nonce'],
            assertion=assertion(private,pin,intent_challenge(intent),counter=3),now=NOW)
        state=broker._load(kernel,'TEST-DEPLOYMENT');state['revoked']=True
        with kernel.atomic_execution():broker._save(kernel,'TEST-DEPLOYMENT',state)
        with pytest.raises(OwnerAssertionError):broker.approve_intent(kernel,deployment_id='TEST-DEPLOYMENT',nonce=intent['nonce'],assertion=proof,now=NOW)

def test_missing_kernel_authority_denied(tmp_path):
    with OrchestratorKernel(tmp_path/'kernel.sqlite',ROOT) as kernel:
        enroll(kernel)
        with pytest.raises(Exception):broker.issue_intent(kernel,scope=scope(),now=NOW)
        assert broker._load(kernel,'TEST-DEPLOYMENT')['intents']=={}

def registration_vector():
    private,pin=credential();point=private.public_key().public_numbers()
    cose=b'\xa5\x01\x02\x03\x26\x20\x01\x21\x58\x20'+point.x.to_bytes(32,'big')+b'\x22\x58\x20'+point.y.to_bytes(32,'big')
    raw=hashlib.sha256(RP_ID.encode()).digest()+b'\x45'+b'\0'*4+b'\0'*16+len(pin.credential_id).to_bytes(2,'big')+pin.credential_id+cose
    return pin,raw

def test_registration_p256_extraction():
    pin,raw=registration_vector()
    assert registration_public_key(raw,pin.credential_id)==pin.public_key_der

@pytest.mark.parametrize('attack',['rp','uv','backup','truncated','credential','cose','trailing'])
def test_registration_substitution_denied(attack):
    pin,raw=registration_vector();ident=pin.credential_id
    if attack=='rp':raw=b'x'*32+raw[32:]
    if attack=='uv':raw=raw[:32]+b'\x41'+raw[33:]
    if attack=='backup':raw=raw[:32]+b'\x4d'+raw[33:]
    if attack=='truncated':raw=raw[:54]
    if attack=='credential':ident=b'OTHER'
    if attack=='cose':raw=raw[:-1]
    if attack=='trailing':raw+=b'\0'
    with pytest.raises(OwnerAssertionError):registration_public_key(raw,ident)

@pytest.mark.parametrize('code',[0x80090016,0x80090036,0x800704c7])
def test_native_error_and_cancellation(code):
    with pytest.raises(OwnerAssertionError):WindowsHello._check(code)

def test_actual_kernel_scope_and_witness_binding(tmp_path):
    from test_f07_inactive_runtime import runtime_at
    from agent_lab.owner_identity_assertion import intent_challenge
    with runtime_at(tmp_path) as runtime:
        kernel=runtime['kernel'];deployment=runtime['owner']['deployment_id'];store=runtime['owner']['store_id']
        key,pin,_=enroll(kernel,deployment=deployment,store=store)
        exact={**scope(), 'deployment_id':deployment,'store_id':store,'case_id':'C1','task_id':'TASK-RUNTIME-1',
               'manifest_id':'MAN-RUNTIME-1','run_id':'RUN-RUNTIME-1'}
        intent=broker.issue_intent(kernel,scope=exact,now=NOW)
        grant=broker.approve_intent(kernel,deployment_id=deployment,nonce=intent['nonce'],
            assertion=assertion(key,pin,intent_challenge(intent),2),now=NOW)
        assert grant['scope']==exact
        with pytest.raises(Exception):broker.issue_intent(kernel,scope={**exact,'case_id':'C2'},now=NOW)
        kernel.set_kill_switch('HALTED',actor_id='HUMAN_PROJECT_OWNER',authority_reference='TEST-STOP')
        with pytest.raises(Exception):broker.issue_intent(kernel,scope=exact,now=NOW)

def test_concurrent_nonce_approval_has_one_record(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from agent_lab.owner_identity_assertion import intent_challenge
    path=tmp_path/'kernel.sqlite'
    with OrchestratorKernel(path,ROOT) as kernel,patch.object(broker,'_authorize'):
        key,pin,_=enroll(kernel)
        intent=broker.issue_intent(kernel,scope=scope(),now=NOW)
    signed=assertion(key,pin,intent_challenge(intent),2)
    def approve(_):
        with OrchestratorKernel(path,ROOT) as kernel:
            return broker.approve_intent(kernel,deployment_id='TEST-DEPLOYMENT',nonce=intent['nonce'],assertion=signed,now=NOW)
    with patch.object(broker,'_authorize'),ThreadPoolExecutor(max_workers=2) as workers:
        values=list(workers.map(approve,range(2)))
    assert values[0]==values[1]
    with OrchestratorKernel(path,ROOT) as kernel:
        state=broker._load(kernel,'TEST-DEPLOYMENT')
        assert len(state['intents'])==1 and state['counter']==2

def test_enrollment_pin_deletion_detected(tmp_path):
    with OrchestratorKernel(tmp_path/'kernel.sqlite',ROOT) as kernel:
        enroll(kernel)
        with kernel._connection:kernel._connection.execute('DELETE FROM identity_kernel_state')
        with pytest.raises(Exception):broker._load(kernel,'TEST-DEPLOYMENT')

def test_actual_dpapi_keys_isolated_and_not_interchangeable(tmp_path):
    import sys
    if sys.platform!='win32':pytest.skip('Windows DPAPI')
    from agent_lab.owner_identity_keys import provision_keys,load_key
    provision_keys(tmp_path,owner_id='TEST-OWNER',approval=broker.APPROVAL)
    first=load_key(tmp_path,role='kernel',owner_id='TEST-OWNER')
    second=load_key(tmp_path,role='identity',owner_id='TEST-OWNER')
    assert first.private_numbers()!=second.private_numbers()
    assert load_key(tmp_path,role='kernel',owner_id='TEST-OWNER').private_numbers()==first.private_numbers()
    with pytest.raises(Exception):load_key(tmp_path,role='kernel',owner_id='OTHER')
    (tmp_path/'owner-kernel-signing.dpapi').write_bytes((tmp_path/'owner-identity-signing.dpapi').read_bytes())
    with pytest.raises(Exception):load_key(tmp_path,role='kernel',owner_id='TEST-OWNER')
    (tmp_path/'owner-kernel-signing.dpapi').unlink()
    with pytest.raises(Exception):load_key(tmp_path,role='kernel',owner_id='TEST-OWNER')
    assert not (tmp_path/'owner-kernel-signing.dpapi').exists()
