"""Actual SQLite authority transactions; all keys/data are synthetic."""
from copy import deepcopy
from datetime import datetime,timezone
from dataclasses import replace
import base64
import sqlite3
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec,utils
from agent_lab.identity_logical_continuity import (ContinuityKeys,H,ORDER,domain_snapshot,case_manifest,enrollment_preimage)
from agent_lab.identity_persistence import IdentityPersistence
from agent_lab.case_registry import TaxPeriod,StorageScopeReference
from test_identity_persistence import registry,authorizer,evidence_resolver,KEY,person,role,A1,B1
from test_identity_logical_continuity import artifact
from test_f07_operational_read import V
from f07_contract_vectors import sign

OWNER=ec.derive_private_key(1,ec.SECP256R1());KERNEL=ec.derive_private_key(2,ec.SECP256R1())
PINS=ContinuityKeys("TEST-OWNER-KEY",OWNER.public_key(),"TEST-KERNEL-KEY-1",KERNEL.public_key())
NOW=datetime(2026,1,1,0,0,1,tzinfo=timezone.utc)


def cases():
    value=registry();first=value.get("C1")
    value.register(replace(first,case_id="C3",tax_period=TaxPeriod("CALENDAR_YEAR",2024),storage_scope_reference=StorageScopeReference("private","ROOT3")))
    return value


def store_at(path,*,fault=None):
    return IdentityPersistence(path,cases=cases(),authorize=authorizer,evidence_resolver=evidence_resolver,integrity_key=KEY,continuity_keys=PINS,fault_injector=fault)


def owner_artifact(store):
    value=artifact();count,head=store._audit_head()
    value.update(domain_snapshot_digest=H(domain_snapshot(store._db)),case_manifest_digest=H(case_manifest(store._cases.all_records())),enrollment_audit_count=str(count),enrollment_audit_head="sha256:"+head)
    r,s=utils.decode_dss_signature(OWNER.sign(enrollment_preimage(value),ec.ECDSA(hashes.SHA256(),deterministic_signing=True)))
    value["signature"]=base64.urlsafe_b64encode(r.to_bytes(32,"big")+min(s,ORDER-s).to_bytes(32,"big")).rstrip(b"=").decode()
    return value


def enrolled(path):
    store=store_at(path);store.register_identity(case_id="C1",record=person(),authorization_ref=A1);store.bind_party(role())
    value=owner_artifact(store);logical=store.enroll_logical_identity(value,now=NOW)
    return store,value,logical


def request_for(logical,*,case="C1",year="2025",nonce="a"*64,transaction="tx:v1:123e4567-e89b-42d3-a456-426614174001",operation="READ_CASE_IDENTITY"):
    index={"READ_CASE_IDENTITY":1,"LIST_PARTIES":2,"READ_FACTS":3}[operation]
    value=deepcopy(V["vectors"][index]["request"])
    value.update(contract="oi0002.kernel-identity-c09/1.1",case_id=case,tax_year=year,transaction_id=transaction,authorization_references=[A1 if case=="C1" else B1],expected_epoch=str(logical["epoch"]),expected_head=logical["head"])
    value["payload"]={"subject_id":"" if operation=="LIST_PARTIES" else "P1","as_of_date":"" if operation=="READ_FACTS" else year+"-06-01"}
    value["kernel_proof"]["nonce"]=nonce
    return sign(value,KERNEL)


def test_signed_populated_enrollment_restart_and_direct_mutation_denial(tmp_path):
    path=tmp_path/"identity.sqlite";store,value,logical=enrolled(path)
    assert logical["epoch"]==0 and store._db.execute("PRAGMA user_version").fetchone()[0]==4
    snapshot=H(domain_snapshot(store._db))
    with pytest.raises(PermissionError):store.register_identity(case_id="C1",record=person("P-UNAUTHORIZED"),authorization_ref=A1)
    assert H(domain_snapshot(store._db))==snapshot
    store.close();store=store_at(path)
    assert store._logical_row()["head"]==logical["head"]
    assert store.enroll_logical_identity(value,now=NOW)["head"]==logical["head"]
    altered=deepcopy(value);altered["store_id"]="TEST-OTHER"
    with pytest.raises(Exception):store.enroll_logical_identity(altered,now=NOW)
    store.close()


def test_read_consumption_audit_checkpoint_and_stored_snapshot_retry(tmp_path):
    path=tmp_path/"identity.sqlite";store,value,logical=enrolled(path)
    before=store._audit_head()[0];request=request_for(logical)
    result=store.read_operational_identity(request,allowed_case_ids=frozenset({"C1"}),now=NOW)
    assert result["outcome"]=="READ_OK" and result["result"]["items"][0]["person_id"]=="P1"
    assert result["identity_head"]==logical["head"] and result["identity_epoch"]=="0"
    assert int(result["identity_audit_count"])==before+1
    with pytest.raises(PermissionError):store.read_operational_identity(request,allowed_case_ids=frozenset({"C1"}),now=NOW)
    retry=request_for(logical,nonce="b"*64)
    with patch.object(store,"read_case_identity",side_effect=AssertionError("cached result must not reread")):
        repeated=store.read_operational_identity(retry,allowed_case_ids=frozenset({"C1"}),now=NOW)
    assert repeated["result"]==result["result"]
    assert store._db.execute("SELECT COUNT(*) FROM identity_audit_checkpoint").fetchone()[0]==2
    store.close();store=store_at(path)
    assert store._logical_row()["head"]==logical["head"]
    store._verify_logical_integrity();store.close()


def test_actual_concurrent_multi_case_multi_year_reads(tmp_path):
    path=tmp_path/"identity.sqlite";store,_,logical=enrolled(path);store.close()
    requests=[request_for(logical,case=case,year=year,nonce=str(index)*64,transaction=f"tx:v1:123e4567-e89b-42d3-a456-42661417400{index}",operation="LIST_PARTIES") for index,(case,year) in enumerate((("C1","2025"),("C2","2025"),("C3","2024")),start=2)]
    def run(request):
        local=store_at(path)
        try:return local.read_operational_identity(request,allowed_case_ids=frozenset({request["case_id"]}),now=NOW)
        finally:local.close()
    with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,requests))
    assert len({result["identity_audit_count"] for result in results})==3
    assert {(r["result"]["case_id"],r["result"]["tax_year"]) for r in results}=={("C1","2025"),("C2","2025"),("C3","2024")}
    assert all(r["identity_head"]==logical["head"] for r in results)


@pytest.mark.parametrize("attack",["year","allowlist","deployment","nonce","version","head"])
def test_isolation_replay_and_downgrade(tmp_path,attack):
    store,_,logical=enrolled(tmp_path/"identity.sqlite");request=request_for(logical)
    allowed=frozenset({"C1"})
    if attack=="year":request["tax_year"]="2024"
    if attack=="allowlist":allowed=frozenset({"C2"})
    if attack=="deployment":request["deployment_id"]="TEST-OTHER"
    if attack=="version":request["contract"]="oi0002.kernel-identity-c09/1.0"
    if attack=="head":request["expected_head"]="sha256:"+"0"*64
    request=sign(request,KERNEL)
    try:
        if attack=="nonce":store.read_operational_identity(request,allowed_case_ids=allowed,now=NOW)
        with pytest.raises((ValueError,PermissionError)):store.read_operational_identity(request,allowed_case_ids=allowed,now=NOW)
    finally:store.close()


def test_attempt_deletion_is_detected_after_restart(tmp_path):
    path=tmp_path/"identity.sqlite";store,_,logical=enrolled(path)
    store.read_operational_identity(request_for(logical),allowed_case_ids=frozenset({"C1"}),now=NOW);store.close()
    with sqlite3.connect(path) as db:db.execute("DELETE FROM identity_protocol_attempt")
    with pytest.raises(ValueError):store_at(path)


def test_crash_before_read_commit_rolls_back_all_effects(tmp_path):
    store,_,logical=enrolled(tmp_path/"identity.sqlite");before=store._audit_head()
    def fail(stage):
        if stage=="IDENTITY_READ:BEFORE_COMMIT":raise RuntimeError("injected crash")
    store._fault=fail
    with pytest.raises(RuntimeError):store.read_operational_identity(request_for(logical),allowed_case_ids=frozenset({"C1"}),now=NOW)
    assert store._audit_head()==before
    for table in ("identity_protocol_attempt","identity_protocol_result","identity_audit_checkpoint"):assert store._db.execute("SELECT COUNT(*) FROM "+table).fetchone()[0]==0
    store.close()


@pytest.mark.parametrize("boundary",["BEFORE_COMMIT","AFTER_COMMIT"])
def test_populated_v3_v4_migration_crash_recovery(tmp_path,boundary):
    path=tmp_path/"identity.sqlite";store=store_at(path)
    store.register_identity(case_id="C1",record=person(),authorization_ref=A1);store.bind_party(role())
    snapshot=H(domain_snapshot(store._db));audit=store._audit_head();store.close()
    with sqlite3.connect(path) as db:
        for table in ("identity_logical_state","identity_protocol_result","identity_protocol_attempt","identity_audit_checkpoint"):db.execute("DROP TABLE "+table)
        db.execute("DELETE FROM schema_migration_receipt WHERE migration_id='IDENTITY_SCHEMA_V3_TO_V4'")
        db.execute("PRAGMA user_version=3")
    def fail(stage):
        if stage=="MIGRATION_V3_V4:"+boundary:raise RuntimeError("migration crash")
    with pytest.raises(RuntimeError):store_at(path,fault=fail)
    with sqlite3.connect(path) as db:assert db.execute("PRAGMA user_version").fetchone()[0]==(3 if boundary=="BEFORE_COMMIT" else 4)
    store=store_at(path)
    assert H(domain_snapshot(store._db))==snapshot and store._audit_head()==audit
    assert store._logical_row() is None
    store.close()


def test_read_postcommit_anchor_interruption_fails_closed(tmp_path):
    path=tmp_path/"identity.sqlite";store,_,logical=enrolled(path)
    def fail(stage):
        if stage=="IDENTITY_READ:AFTER_COMMIT":raise RuntimeError("anchor gap")
    store._fault=fail
    with pytest.raises(RuntimeError):store.read_operational_identity(request_for(logical),allowed_case_ids=frozenset({"C1"}),now=NOW)
    assert store._db.execute("SELECT COUNT(*) FROM identity_protocol_attempt").fetchone()[0]==1
    store._db.close()
    with pytest.raises(ValueError,match="anchor continuity"):store_at(path)
