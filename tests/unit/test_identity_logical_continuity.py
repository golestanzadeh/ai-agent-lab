from copy import deepcopy
from datetime import datetime,timezone
import base64
import sqlite3

import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec,utils
from cryptography.exceptions import InvalidSignature
from agent_lab.identity_logical_continuity import (H,C,ORDER,SCHEMA,cell,case_manifest,domain_snapshot,
    enrollment_preimage,verify_enrollment,genesis_preimage,successor_preimage,witness_commitment,witness_slot,
    checkpoint_identifiers,domain_result)
from agent_lab.identity_persistence import IdentityPersistence
from test_identity_persistence import registry,open_store,register,role,bind_fact,A1,E1,E2


def artifact():
    return {"contract":"ai-tax-agent.identity-enrollment/1.0","deployment_id":"TEST-DEPLOYMENT","store_id":"TEST-STORE","enrollment_id":"TEST-ENROLLMENT","schema_version":"4","domain_snapshot_digest":"sha256:"+"a"*64,"enrollment_audit_count":"0","enrollment_audit_head":"sha256:"+"0"*64,"case_manifest_digest":H(case_manifest([])),"backup_generation":"0","nonce":"1"*64,"issued_at":"2026-01-01T00:00:00.000000Z","not_before":"2026-01-01T00:00:00.000000Z","expires_at":"2026-01-01T00:05:00.000000Z","key_id":"TEST-OWNER-KEY","algorithm":"ECDSA-P256-SHA256","signature":"","bootstrap_task_id":"TEST-BOOTSTRAP-TASK","bootstrap_manifest_id":"TEST-BOOTSTRAP-MANIFEST","bootstrap_run_id":"TEST-BOOTSTRAP-RUN","bootstrap_actor_instance_id":"TEST-BOOTSTRAP-ACTOR","bootstrap_role_id":"OPERATIONS_INTEGRATION_AGENT"}


def signed_artifact():
    value=artifact();key=ec.derive_private_key(1,ec.SECP256R1())
    r,s=utils.decode_dss_signature(key.sign(enrollment_preimage(value),ec.ECDSA(hashes.SHA256(),deterministic_signing=True)))
    value["signature"]=base64.urlsafe_b64encode(r.to_bytes(32,"big")+min(s,ORDER-s).to_bytes(32,"big")).rstrip(b"=").decode()
    return value,key.public_key()


def vectors():
    value,_=signed_artifact();genesis=genesis_preimage(value)
    successor=successor_preimage(deployment_id=value["deployment_id"],prior_epoch="0",prior_head=H(genesis),case_id="TEST-CASE",tax_year="2025",transaction_id="TEST-TX",domain_operation="REGISTER_IDENTITY",mutation_content_digest="sha256:"+"b"*64,domain_result_digest="sha256:"+"c"*64)
    composite=witness_commitment(deployment_id=value["deployment_id"],logical_epoch="1",logical_head=H(successor),audit_cut_count="2",audit_cut_head="sha256:"+"d"*64)
    return {"profile":"F07-OPTION-A-V1","owner_artifact":value,"owner_signature_preimage_hex":enrollment_preimage(value).hex(),"owner_artifact_digest":H(value),"genesis":genesis,"genesis_bytes_hex":C(genesis).hex(),"genesis_head":H(genesis),"successor":successor,"successor_head":H(successor),"witness_composite":composite,"witness_identity_head":H(composite),"empty_case_manifest":case_manifest([]),"empty_case_manifest_digest":H(case_manifest([])),"checkpoint_ids":list(checkpoint_identifiers("TEST-DEPLOYMENT","tx:v1:123e4567-e89b-42d3-a456-426614174001","sha256:"+"a"*64,"sha256:"+"b"*64))}


def test_frozen_vectors():
    import json
    from pathlib import Path
    value=json.loads((Path(__file__).parents[1]/"fixtures/f07-option-a-v1.json").read_text())
    assert value==vectors()


def test_registry_manifest_deterministic_complete_and_empty():
    records=registry().all_records()
    assert case_manifest(records)==case_manifest(reversed(records))
    assert len(case_manifest(records)["records"])==2
    assert case_manifest([])=={"profile":"identity-case-manifest/1","records":[]}
    with pytest.raises(ValueError):case_manifest([records[0],records[0]])
    with pytest.raises(ValueError):case_manifest([{}])


def test_domain_snapshot_actual_schema_and_audit_independence(tmp_path):
    _,store=open_store(tmp_path)
    try:
        before=H(domain_snapshot(store._db));register(store)
        after=H(domain_snapshot(store._db));assert before!=after
        store.record_ipc_boundary_denial(case_id="C1",tax_year=2025,request_digest="sha256:"+"e"*64,operation="READ_FACTS")
        assert after==H(domain_snapshot(store._db))
        assert len(domain_snapshot(store._db)["tables"])==9
        store._db.execute("ALTER TABLE identity_record ADD COLUMN unexpected TEXT")
        with pytest.raises(ValueError):domain_snapshot(store._db)
    finally:store._db.close()


@pytest.mark.parametrize("operation",["REGISTER_IDENTITY","UPDATE_IDENTITY_STATUS","BIND_PARTY","CORRECT_PARTY_ROLE","BIND_FACT"])
def test_exact_actual_mutation_result_rows(tmp_path,operation):
    _,store=open_store(tmp_path)
    try:
        register(store);store.bind_party(role())
        key="P1";expected=2
        if operation=="UPDATE_IDENTITY_STATUS":
            from agent_lab.person_entity_registry import RegistryStatus
            store.update_identity_status(case_id="C1",identity_id="P1",status=RegistryStatus.INACTIVE,authorization_ref=A1)
        if operation=="BIND_PARTY":key="R1";expected=1
        if operation=="CORRECT_PARTY_ROLE":
            from datetime import date
            store.correct_party_role(case_id="C1",binding_id="R1",valid_to_exclusive=date(2025,12,31),correction_evidence_ref=E2,authorization_ref=A1);key="R1";expected=3
        if operation=="BIND_FACT":bind_fact(store);key="F1";expected=1
        projection=domain_result(store._db,operation,"C1","2025",key)
        assert len(projection["rows"])==expected
        assert H(projection)==H(deepcopy(projection))
        if operation not in {"REGISTER_IDENTITY","UPDATE_IDENTITY_STATUS"}:
            with pytest.raises(ValueError):domain_result(store._db,operation,"C2","2025",key)
    finally:store.close()


def test_owner_signature_scope_expiry_and_malleability():
    value,key=signed_artifact();now=datetime(2026,1,1,0,1,tzinfo=timezone.utc)
    assert verify_enrollment(value,key,"TEST-OWNER-KEY",now)==H(value)
    for field in ("deployment_id","store_id","bootstrap_task_id","bootstrap_actor_instance_id"):
        changed=deepcopy(value);changed[field]+="-ALTERED"
        with pytest.raises((ValueError,InvalidSignature)):verify_enrollment(changed,key,"TEST-OWNER-KEY",now)
    with pytest.raises(ValueError):verify_enrollment(value,key,"OTHER",now)
    with pytest.raises(ValueError):verify_enrollment(value,key,"TEST-OWNER-KEY",datetime(2027,1,1,tzinfo=timezone.utc))
    changed=deepcopy(value);raw=base64.urlsafe_b64decode(changed["signature"]+"==")
    changed["signature"]=base64.urlsafe_b64encode(raw[:32]+(ORDER-int.from_bytes(raw[32:],"big")).to_bytes(32,"big")).rstrip(b"=").decode()
    with pytest.raises(ValueError):verify_enrollment(changed,key,"TEST-OWNER-KEY",now)


def test_witness_allocation_and_identifier_golden():
    zero="sha256:"+"0"*64;head="sha256:"+"a"*64
    assert witness_slot(0,0,zero)==(1,1)
    assert witness_slot(1,1,head)==(1,2)
    assert witness_slot(1,20,head,restore=True)==(2,1)
    with pytest.raises(ValueError):witness_slot(1,10**20-1,head)
    cp,op=checkpoint_identifiers("TEST-DEPLOYMENT","tx:v1:123e4567-e89b-42d3-a456-426614174001",head,"sha256:"+"b"*64)
    assert cp=="CP:041a88e4dc41c2d54f621726a55d58324086af9b026e8fcf04389a50ff0b0cdd"
    assert op=="AUDIT:041A88E4DC41C2D54F621726A55D58324086AF9B026E8FCF04389A50FF0B0CDD"


def test_cell_types_do_not_alias():
    assert cell(None)!=cell("") and cell(1)!=cell("1")
    with pytest.raises(ValueError):cell(1.0)
