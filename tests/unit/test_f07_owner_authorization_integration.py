"""F05/F06: real Kernel, Identity SQLite and native transport, isolated fixtures.

No authorization mock or native Owner ceremony. Synthetic enrollment/key/Witness
fixtures remain test-only; none is installed as operational authority.
"""
from contextlib import contextmanager,closing
from dataclasses import replace
from datetime import datetime,timedelta,timezone
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch

import pytest

from agent_lab import owner_identity_broker as broker
from agent_lab.identity_owner_source import CanonicalOwnerDeclarationSource
from agent_lab.owner_identity_assertion import OwnerAssertionError,intent_challenge
from agent_lab.owner_identity_delivery import sign as real_sign,verify as verify_delivery
from agent_lab.orchestrator_kernel import OrchestratorKernel,PermissionDenied
from agent_lab.ipc_wire_primitives import canonical_sha256 as H
from test_f07_inactive_runtime import runtime_at,stage
from test_identity_logical_runtime import store_at,KERNEL
from test_identity_logical_continuity import artifact
from test_owner_identity_broker import credential,assertion,ROOT

VALUES=dict(first_name='Synthetic',last_name='Person',birth_date='1990-01-02',tax_id='12345678901')
pytestmark=pytest.mark.skipif(sys.platform!='win32',reason='existing real Windows Named Pipe fixture')

@contextmanager
def owner_runtime_at(path,*,approval_age=timedelta(0)):
    binding=artifact()
    scope=dict(operation='REGISTER_IDENTITY',owner_id='P1',case_id='C1',tax_year='2025',subject_id='P2',
        input_digest=H(VALUES),deployment_id=binding['deployment_id'],store_id=binding['store_id'],
        task_id='TASK-RUNTIME-1',manifest_id='MAN-RUNTIME-1',run_id='RUN-RUNTIME-1')
    now=datetime.now(timezone.utc)-approval_age
    record=dict(identity_id='P2',record_type='PERSON',status='ACTIVE',name='Synthetic Person',
        created_at=now.isoformat(),updated_at=now.isoformat(),lookup_attributes=list(map(list,VALUES.items())),record_schema_version=2)
    raw=json.dumps(record,sort_keys=True,separators=(',',':')).encode()
    record_ref='sha256:'+hashlib.sha256(raw).hexdigest()
    auth=broker.authorization_reference(scope)
    def authority_factory(database,**kwargs):
        authority=store_at(database,**kwargs)
        authority._mutation_source=CanonicalOwnerDeclarationSource(authority,
            deployment_id=binding['deployment_id'],store_id=binding['store_id'])
        return authority
    with patch('test_f07_inactive_runtime.store_at',side_effect=authority_factory):
        with runtime_at(path,source=False,inputs=[auth,record_ref]) as state:
            kernel=state['kernel']
            private,pin=credential();pin=replace(pin,owner_id='P1')
            pending=broker.begin_enrollment(kernel,owner_id='P1',deployment_id=scope['deployment_id'],store_id=scope['store_id'],approval=broker.APPROVAL,now=now)
            broker._finish_enrollment(kernel,deployment_id=scope['deployment_id'],credential=pin,
                assertion=assertion(private,pin,broker.enrollment_challenge(pending)),now=now)
            intent=broker.issue_intent(kernel,scope=scope,now=now)
            broker.approve_intent(kernel,deployment_id=scope['deployment_id'],nonce=intent['nonce'],
                assertion=assertion(private,pin,intent_challenge(intent),2),now=now)
            export_args=dict(deployment_id=scope['deployment_id'],nonce=intent['nonce'],expected_scope=scope,
                now=now,signing_key=KERNEL,key_id='TEST-KERNEL-KEY-1')
            delivery=broker.approved_source_evidence(kernel,**export_args)
            with closing(store_at(path/'identity.sqlite')) as authority:
                source=CanonicalOwnerDeclarationSource(authority,deployment_id=scope['deployment_id'],store_id=scope['store_id'])
                staged,_=source.stage(delivery=delivery,confirmed_values=VALUES,artifacts=(('IDENTITY_RECORD',raw),),now=now)
                assert staged==auth
            state['arguments']['authorization_references']=[auth]
            state['payload'].update(identity_record_ref=record_ref,evidence_refs=[record_ref],owner_input_digest=H(VALUES))
            state.update(owner_scope=scope,owner_intent=intent,export_args=export_args)
            yield state

def revoke_owner(kernel,deployment):
    with kernel.atomic_execution():
        current=broker._load(kernel,deployment);current['revoked']=True
        broker._save(kernel,deployment,current)

@pytest.mark.parametrize('kind',['credential','manifest'])
def test_f05_export_serializes_concurrent_revocation(tmp_path,kind):
    with owner_runtime_at(tmp_path) as state:
        ready=Event();begin=Event();attempt=Event();entered=Event()
        def revoke():
            with OrchestratorKernel(tmp_path/'kernel.sqlite',ROOT) as other:
                other._connection.set_trace_callback(lambda sql:attempt.set() if sql=='BEGIN IMMEDIATE' else None)
                ready.set();assert begin.wait(5)
                with other.atomic_execution():
                    entered.set()
                    if kind=='credential':
                        row=broker._load(other,state['owner_scope']['deployment_id']);row['revoked']=True
                        broker._save(other,state['owner_scope']['deployment_id'],row)
                    else:other.transition_manifest('MAN-RUNTIME-1','REVOKED',actor_id='HUMAN_PROJECT_OWNER',reason='synthetic race')
        def signing(payload,key):
            assert state['kernel']._connection.in_transaction
            begin.set();assert attempt.wait(5)
            # Trace confirms the second connection reached BEGIN IMMEDIATE.
            # It must not enter until the entire delivery has been signed.
            assert not entered.wait(.1)
            return real_sign(payload,key)
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(revoke);assert ready.wait(5)
            try:
                with patch('agent_lab.owner_identity_delivery.sign',side_effect=signing):
                    delivery=broker.approved_source_evidence(state['kernel'],**state['export_args'])
            finally:begin.set()
            future.result(timeout=5)
        assert entered.is_set()
        verify_delivery(delivery,kernel_public_key=KERNEL.public_key(),key_id='TEST-KERNEL-KEY-1',
            deployment_id=state['owner_scope']['deployment_id'],store_id=state['owner_scope']['store_id'])
        with patch('agent_lab.owner_identity_delivery.sign',side_effect=AssertionError('must not sign after revocation')) as denied_sign:
            with pytest.raises((OwnerAssertionError,PermissionDenied)):broker.approved_source_evidence(state['kernel'],**state['export_args'])
            denied_sign.assert_not_called()

def test_f05_export_wait_counts_against_original_lease(tmp_path):
    with owner_runtime_at(tmp_path) as state:
        locked=Event();attempt=Event()
        def holder():
            with OrchestratorKernel(tmp_path/'kernel.sqlite',ROOT) as other:
                with other.atomic_execution():
                    locked.set();assert attempt.wait(5)
                    Event().wait(.1)
        expires=datetime.strptime(state['owner_intent']['expires_at'],'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
        kernel=state['kernel']
        kernel._connection.set_trace_callback(lambda sql:attempt.set() if sql=='BEGIN IMMEDIATE' else None)
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                future=pool.submit(holder);assert locked.wait(5)
                with patch('agent_lab.owner_identity_delivery.sign',side_effect=AssertionError('expired queued export must not sign')):
                    with pytest.raises(OwnerAssertionError,match='expired'):
                        broker.approved_source_evidence(kernel,**{**state['export_args'],'now':expires-timedelta(seconds=.05)})
                future.result(timeout=5)
        finally:kernel._connection.set_trace_callback(None)

@pytest.mark.parametrize('boundary',['PREPARE_MUTATION','COMMIT_MUTATION'])
@pytest.mark.parametrize('failure',['revoked','expired','substituted'])
def test_f06_actual_kernel_hook_denies_before_dispatch(tmp_path,boundary,failure):
    with owner_runtime_at(tmp_path) as state:
        if boundary=='COMMIT_MUTATION':assert stage(state,'PREPARE_MUTATION')['outcome']=='PREPARED'
        payload=dict(state['payload'])
        if failure=='revoked':revoke_owner(state['kernel'],state['owner_scope']['deployment_id'])
        if failure=='substituted':payload['subject_id']='P3'
        moment=datetime.now(timezone.utc)+timedelta(minutes=6) if failure=='expired' else datetime.now(timezone.utc)
        # Clock control only: real permission/continuity/Owner hook remain intact.
        with patch('agent_lab.orchestrator_kernel._utc_now',return_value=moment),patch(
            'agent_lab.c09_pipe_transport._exchange_canonical',side_effect=AssertionError('denied before transport')):
            with pytest.raises(OwnerAssertionError):stage(state,boundary,payload)
        with closing(store_at(tmp_path/'identity.sqlite')) as authority:
            assert authority._load_identity('P2') is None
        state['kernel']._verify_identity_protocol_state()

def test_f06_valid_owner_mutation_and_post_commit_recovery(tmp_path):
    with owner_runtime_at(tmp_path,approval_age=timedelta(minutes=4,seconds=55)) as state:
        assert stage(state,'PREPARE_MUTATION')['outcome']=='PREPARED'
        assert stage(state,'COMMIT_MUTATION')['outcome']=='IDENTITY_COMMITTED'
        tx=state['kernel']._identity_payload('identity_kernel_state','deployment_id',state['owner_scope']['deployment_id'])['mutations'][state['arguments']['transaction_id']]
        linkage=dict(original_request_digest=tx['prepare_request']['request_digest'])
        revoke_owner(state['kernel'],state['owner_scope']['deployment_id'])
        expires=datetime.strptime(state['owner_intent']['expires_at'],'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
        Event().wait(max(0,(expires-datetime.now(timezone.utc)).total_seconds())+.01)
        assert datetime.now(timezone.utc)>=expires
        # Settling an already committed domain change must remain possible even
        # after its one-use Owner approval expires/is revoked; no new write.
        assert stage(state,'GET_TRANSACTION',linkage)['outcome']=='IDENTITY_COMMITTED'
        pending=state['client'].reconcile('MUTATION:'+state['arguments']['transaction_id'])
        receipt=pending['receipt'];verified=pending['custodian_verification']['response']
        final=dict(staged_receipt_digest=H(receipt),witness_object_key=pending['object_key'],witness_generation=pending['generation'],
            witness_preimage_digest=receipt['witness_preimage_digest'],signed_record_digest=verified['signed_record_digest'],
            custodian_verification_digest=H(verified),custodian_nonce=verified['nonce'])
        assert stage(state,'FINALIZE_MUTATION',final)['outcome']=='COMMITTED_FINAL'
        state['restart']()
        assert stage(state,'GET_TRANSACTION',linkage)['outcome']=='COMMITTED_FINAL'
        with closing(store_at(tmp_path/'identity.sqlite')) as authority:
            assert authority._load_identity('P2').preferred_display_name=='Synthetic Person'
            authority._verify_data_integrity();authority._verify_logical_integrity()

def test_f06_existing_non_owner_authorization_unchanged(tmp_path):
    with runtime_at(tmp_path) as state:
        assert stage(state,'PREPARE_MUTATION')['outcome']=='PREPARED'
        assert stage(state,'COMMIT_MUTATION')['outcome']=='IDENTITY_COMMITTED'
