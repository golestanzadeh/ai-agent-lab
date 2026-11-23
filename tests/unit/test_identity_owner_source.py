"""Canonical Identity SQLite Owner declarations; no live source or real values."""
from dataclasses import replace
from datetime import timedelta
import json
import pytest
from agent_lab.identity_owner_source import CanonicalOwnerDeclarationSource,verify_storage,TABLE,_write
from agent_lab.identity_mutation_source import resolve
from agent_lab.owner_identity_assertion import CONTRACT,intent_challenge,OwnerAssertionError
from agent_lab.ipc_wire_primitives import canonical_sha256 as H
from test_owner_identity_broker import credential,assertion
from test_identity_logical_runtime import enrolled,store_at,NOW,OWNER
from test_f07_atomic_mutation import prepare_request,resign,commit_request

VALUES=dict(first_name='Synthetic',last_name='Person',birth_date='1990-01-02',tax_id='12345678901')

def staged(tmp_path):
    owner,artifact,logical=enrolled(tmp_path/'identity.sqlite')
    request=prepare_request(logical)
    from cryptography.hazmat.primitives import serialization
    key,pin=credential();key=OWNER
    pin=replace(pin,owner_id='P1',public_key_der=key.public_key().public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo))
    source=CanonicalOwnerDeclarationSource(owner,enrollment=pin,deployment_id=artifact['deployment_id'],store_id=artifact['store_id'])
    scope=dict(operation='REGISTER_IDENTITY',owner_id='P1',case_id='C1',tax_year='2025',subject_id='P2',input_digest=H(VALUES),
        deployment_id=artifact['deployment_id'],store_id=artifact['store_id'],task_id=request['task_id'],manifest_id=request['manifest_id'],run_id=request['run_id'])
    stamp=lambda t:t.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    intent=dict(contract=CONTRACT,**scope,nonce='9'*64,issued_at=stamp(NOW),expires_at=stamp(NOW+timedelta(minutes=5)))
    record=dict(identity_id='P2',record_type='PERSON',status='ACTIVE',name='Synthetic Person',created_at=NOW.isoformat(),updated_at=NOW.isoformat(),
        lookup_attributes=[[k,v] for k,v in VALUES.items()],record_schema_version=2)
    raw=json.dumps(record,sort_keys=True,separators=(',',':')).encode()
    proof=assertion(key,pin,intent_challenge(intent))
    reference,records=source.stage(intent=intent,assertion=proof,confirmed_values=VALUES,artifacts=(('IDENTITY_RECORD',raw),),now=NOW)
    owner._mutation_source=source
    request['authorization_references']=[reference]
    request['payload'].update(identity_record_ref=records[0],evidence_refs=list(records),owner_input_digest=H(VALUES))
    request=resign(request)
    return owner,source,request,intent,proof,raw,pin

def test_source_content_scope_restart_and_atomic_commit(tmp_path):
    owner,source,request,intent,proof,raw,pin=staged(tmp_path)
    assert source.stage(intent=intent,assertion=proof,confirmed_values=VALUES,artifacts=(('IDENTITY_RECORD',raw),),now=NOW)[0]==request['authorization_references'][0]
    bundle,refs=resolve(source,request,owner._cases.get('C1'),NOW)
    assert refs[request['payload']['identity_record_ref']].observed.content==raw
    before=owner._logical_row()['head']
    result=owner.mutate_operational_identity(request,allowed_case_ids=frozenset({'C1'}),now=NOW)
    assert result['outcome']=='PREPARED'
    commit=commit_request(owner,request)
    result=owner.mutate_operational_identity(commit,allowed_case_ids=frozenset({'C1'}),now=NOW)
    assert result['outcome']=='IDENTITY_COMMITTED' and owner._load_identity('P2').preferred_display_name=='Synthetic Person'
    assert owner._logical_row()['head']!=before
    owner.close()
    owner=store_at(tmp_path/'identity.sqlite')
    try:
        verify_storage(owner)
        assert owner._load_identity('P2').person_id=='P2'
    finally:owner.close()

def test_revoked_after_prepare_cannot_commit(tmp_path):
    owner,source,request,*_=staged(tmp_path)
    try:
        owner.mutate_operational_identity(request,allowed_case_ids=frozenset({'C1'}),now=NOW)
        commit=commit_request(owner,request)
        reference=request['authorization_references'][0]
        row=source._row(reference);row['revoked']=True
        owner._commit('SYNTHETIC_AUTHORIZED_REVOCATION',lambda:_write(owner,reference,row))
        with pytest.raises(Exception):owner.mutate_operational_identity(commit,allowed_case_ids=frozenset({'C1'}),now=NOW)
        assert owner._load_identity('P2') is None
    finally:owner.close()

def test_unaccepted_source_key_cannot_select_new_authority(tmp_path):
    owner,artifact,_=enrolled(tmp_path/'identity.sqlite')
    try:
        _,pin=credential();pin=replace(pin,owner_id='P1')
        with pytest.raises(OwnerAssertionError):CanonicalOwnerDeclarationSource(owner,enrollment=pin,
            deployment_id=artifact['deployment_id'],store_id=artifact['store_id'])
    finally:owner.close()

@pytest.mark.parametrize('attack',['case','year','subject','run','operation','expiry','values','bytes','revoke','delete'])
def test_source_substitution_revocation_and_integrity(tmp_path,attack):
    owner,source,request,intent,proof,raw,pin=staged(tmp_path)
    try:
        if attack in {'values','bytes'}:
            with pytest.raises(Exception):source.stage(intent=intent,assertion=proof,
                confirmed_values={**VALUES,'first_name':'OTHER'} if attack=='values' else VALUES,
                artifacts=(('IDENTITY_RECORD',raw.replace(b'Synthetic',b'Altered')),),now=NOW)
            return
        if attack in {'revoke','delete'}:
            reference=request['authorization_references'][0]
            if attack=='revoke':
                row=source._row(reference);row['revoked']=True
                owner._commit('SYNTHETIC_AUTHORIZED_REVOCATION',lambda:_write(owner,reference,row))
            else:
                with owner._db:owner._db.execute('DELETE FROM '+TABLE)
            with pytest.raises(Exception):source.resolve(request,owner._cases.get('C1'),NOW)
            if attack=='delete':return  # Deliberate corruption must also fail close.
        else:
            if attack=='subject':request['payload']['subject_id']='OTHER'
            if attack in {'case','year','run','operation'}:
                key={'case':'case_id','year':'tax_year','run':'run_id','operation':'domain_operation'}[attack]
                request[key]={'case':'C3','year':'2024','run':'OTHER','operation':'BIND_PARTY'}[attack]
            with pytest.raises(Exception):resolve(source,request,owner._cases.get('C1'),NOW+timedelta(minutes=6) if attack=='expiry' else NOW)
    finally:
        if attack=='delete':owner._db.close()
        else:owner.close()

