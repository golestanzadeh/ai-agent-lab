"""Inactive mutation entry point using real Identity SQLite and synthetic sources."""
from copy import deepcopy
from dataclasses import replace
from datetime import date, timedelta
from hashlib import sha256
import json

import pytest
from agent_lab.identity_mutation_source import ProtectedMutationSource, MaterializedMutation, EvidenceArtifact
from agent_lab.identity_protected_revision import ProtectedReference, ProtectedRevision, MaterializedRevision
from agent_lab.identity_evidence_authority import EvidenceScope
from agent_lab.identity_logical_continuity import H, sign_kernel_proof, successor_preimage
from agent_lab.ipc_operational_read import read_projection
from agent_lab.f07_commit_witness import slot_projection
from test_identity_logical_runtime import enrolled, store_at, request_for, KERNEL, NOW
from test_identity_persistence import A1, person


class Sources(ProtectedMutationSource):
    def __init__(self):
        self.subject="P2"
        self.semantic="identity.registration"
        self.materials=None
        self.changed = False
        self.revoked = False

    def resolve(self, request, case, now):
        raw = b"synthetic owner authorization"
        scope = EvidenceScope(request["case_id"],int(request["tax_year"]),self.subject,self.semantic,
                              request["actor_instance_id"],request["run_id"],request["task_id"],request["manifest_id"],
                              date(2025,1,1),date(2026,1,1))
        record = dict(identity_id="P2",record_type="PERSON",status="ACTIVE",name=None,
                      created_at=NOW.isoformat(),updated_at=NOW.isoformat(),lookup_attributes=[],record_schema_version=2)
        content = json.dumps(record,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
        artifacts = []
        materials=self.materials or ((A1,"IDENTITY_AUTHORIZATION",raw,"AUTH"),
                ("sha256:"+"8"*64,"IDENTITY_RECORD",content,"RECORD"))
        for reference,kind,body,object_id in materials:
            revision = ProtectedRevision("private",case.storage_scope_reference.root_id,object_id,"1")
            accepted = ProtectedReference(revision,scope,"sha256:"+sha256(body).hexdigest(),now+timedelta(minutes=1),now if self.revoked else None)
            artifacts.append(EvidenceArtifact(reference,kind,accepted,MaterializedRevision(revision,body+b"altered" if self.changed else body)))
        return MaterializedMutation(self.subject,"TEST-AUTHORIZATION-1",tuple(artifacts))


def prepare_request(logical):
    request = request_for(logical)
    request.update(message_type="PREPARE_MUTATION",domain_operation="REGISTER_IDENTITY",capability="identity_register",
                   payload=dict(request_id="TEST-REGISTER-P2",subject_id="P2",identity_record_ref="sha256:"+"8"*64,evidence_refs=["sha256:"+"8"*64]))
    from agent_lab.ipc_envelope import OPERATION_CAPABILITIES
    request["capability"] = OPERATION_CAPABILITIES[request["domain_operation"]]
    return resign(request)


def resign(request):
    request = deepcopy(request)
    old = request["kernel_proof"]["kernel_projection"]
    request["kernel_proof"]["kernel_projection"] = {key:old[key] for key in ("witnessed_audit_count","witnessed_audit_head","recovery_request_digest")}
    request["kernel_proof"]["kernel_projection"] = read_projection(request)
    request["kernel_proof"]["pending_row_digest"] = H(request["kernel_proof"]["kernel_projection"])
    return sign_kernel_proof(request,KERNEL)


def commit_request(store, prepare):
    from agent_lab.identity_atomic_mutation import load,stable
    tx = load(store,"TX:"+prepare["transaction_id"])
    request = deepcopy(prepare)
    request.update(message_type="COMMIT_MUTATION",prepared_request_digest=prepare["request_digest"])
    request["kernel_proof"]["nonce"] = "b"*64
    request = resign(request)
    projection = request["kernel_proof"]["kernel_projection"]
    successor = successor_preimage(deployment_id=request["deployment_id"],prior_epoch=request["expected_epoch"],prior_head=request["expected_head"],
        case_id=request["case_id"],tax_year=request["tax_year"],transaction_id=request["transaction_id"],domain_operation=request["domain_operation"],
        mutation_content_digest=stable(request),domain_result_digest=tx["domain_result_digest"])
    projection.update(projected_epoch=successor["next_epoch"],projected_head=H(successor),kernel_pending_head="sha256:"+"9"*64,
        mutation_witness_slot=slot_projection(request,previous_epoch="1",previous_sequence="1",previous_record="sha256:"+"a"*64,backup_generation=tx["backup_generation"]))
    request["kernel_proof"]["pending_row_digest"] = H(projection)
    return sign_kernel_proof(request,KERNEL)


def execute(store,request):
    return store.mutate_operational_identity(request,allowed_case_ids=frozenset({"C1"}),now=NOW)


def setup(path):
    store,_,logical = enrolled(path)
    store._mutation_source = Sources()
    return store,prepare_request(logical)


def test_atomic_register_restart_and_get(tmp_path):
    from agent_lab.identity_atomic_mutation import load
    path = tmp_path/"identity.sqlite"
    store,prepare = setup(path)
    assert execute(store,prepare)["outcome"] == "PREPARED"
    assert store._load_identity("P2") is None
    commit = commit_request(store,prepare)
    response = execute(store,commit)
    assert response["outcome"] == "IDENTITY_COMMITTED"
    assert store._load_identity("P2") is not None
    assert load(store,"AUTH:TEST-AUTHORIZATION-1")["state"] == "CONSUMED"
    store.close()
    store = store_at(path)
    request = deepcopy(prepare)
    request.update(message_type="GET_TRANSACTION",payload={"original_request_digest":prepare["request_digest"]})
    request["kernel_proof"]["nonce"] = "c"*64
    result = execute(store,resign(request))
    assert result["result"] == response["result"]
    assert result["identity_head"] == response["identity_head"]
    with pytest.raises(PermissionError):execute(store,commit)
    store.close()


@pytest.mark.parametrize("boundary",["IDENTITY_MUTATION:BEFORE_COMMIT","IDENTITY_MUTATION:AFTER_COMMIT","IDENTITY_MUTATION:AFTER_ANCHOR"])
def test_atomic_crash_recovery(tmp_path,boundary):
    path = tmp_path/"identity.sqlite"
    store,prepare = setup(path)
    execute(store,prepare)
    commit = commit_request(store,prepare)
    def fail(stage):
        if stage == boundary:raise RuntimeError("synthetic crash")
    store._fault = fail
    with pytest.raises(RuntimeError):execute(store,commit)
    store._db.close()
    store = store_at(path)
    assert (store._load_identity("P2") is not None) == (boundary != "IDENTITY_MUTATION:BEFORE_COMMIT")
    store._verify_logical_integrity()
    store.close()


@pytest.mark.parametrize("attack",["changed","revoked","missing","case","year"])
def test_fail_closed_evidence_and_scope(tmp_path,attack):
    store,request = setup(tmp_path/"identity.sqlite")
    if attack in {"changed","revoked"}:setattr(store._mutation_source,attack,True)
    if attack == "missing":store._mutation_source=None
    if attack == "case":request["case_id"]="C2"
    if attack == "year":request["tax_year"]="2024"
    request = resign(request)
    with pytest.raises(Exception):execute(store,request)
    assert store._load_identity("P2") is None
    store.close()


@pytest.mark.parametrize("lost",[None,"PREPARE_RESPONSE","COMMIT_RESPONSE","FINALIZE_RESPONSE","WITNESS_UPLOAD","BUDGET"])
def test_real_kernel_identity_custodian_transaction(tmp_path,lost):
    from unittest.mock import patch
    from test_c09_custodian_operational import fixture,rpc
    from test_identity_logical_runtime import KERNEL
    from test_orchestrator_kernel import task,manifest
    from agent_lab.orchestrator_kernel import StateTransitionError
    from datetime import datetime,timezone
    kernel,identity,owner,pending,host,client,provider,session = fixture(tmp_path)
    identity._mutation_source = Sources()
    try:
        with patch("agent_lab.c09_pipe_transport.exchange_custodian_control",side_effect=rpc(host)):
            kernel.witness_identity_checkpoint(pending["receipt"]["checkpoint_id"],custodian=client,provider=provider,signing_key=KERNEL,kernel_key_id="TEST-KERNEL-KEY-1")
            work = task(task_id="TASK-MUTATION-1",role_id="IDENTITY_ADMINISTRATION_AGENT",permissions=["identity_create"],case_context=dict(case_id="C1",tax_year=2025,run_id="RUN-MUTATION-1"))
            work["inputs"]=[A1,"sha256:"+"8"*64]
            kernel.register_task(work,gate_triggers=[])
            grant=manifest(work,manifest_id="MAN-MUTATION-1",tiers=["A4"])
            kernel.register_manifest(grant)
            kernel.validate_manifest(grant["manifest_id"])
            kernel.activate_manifest(grant["manifest_id"])
            kwargs=dict(deployment_id=owner["deployment_id"],manifest_id=grant["manifest_id"],task_id=work["task_id"],run_id="RUN-MUTATION-1",case_id="C1",tax_year=2025,
                operation="REGISTER_IDENTITY",authorization_references=[A1],signing_key=KERNEL,key_id="TEST-KERNEL-KEY-1",transaction_id="tx:v1:123e4567-e89b-42d3-a456-426614174999")
            payload=dict(request_id="TEST-REGISTER-P2",subject_id="P2",identity_record_ref="sha256:"+"8"*64,evidence_refs=["sha256:"+"8"*64])
            if lost=="BUDGET":
                from agent_lab.orchestrator_kernel import PermissionDenied,OrchestratorKernel
                from test_kernel_identity_operational import ROOT
                kernel.consume_budget(grant["manifest_id"],tool_calls=grant["budget"]["tool_call_limit"])
                with pytest.raises(PermissionDenied):
                    kernel.issue_identity_mutation(**kwargs,message_type="PREPARE_MUTATION",payload=payload)
                assert kernel._manifest_row(grant["manifest_id"])["state"]=="BLOCKED"
                kernel.close()
                kernel=OrchestratorKernel(tmp_path/"kernel.sqlite",ROOT)
                assert kernel._manifest_row(grant["manifest_id"])["state"]=="BLOCKED"
                kernel._verify_identity_protocol_state()
                return
            prepare=kernel.issue_identity_mutation(**kwargs,message_type="PREPARE_MUTATION",payload=payload)
            prepared=identity.mutate_operational_identity(prepare,allowed_case_ids=frozenset({"C1"}))
            if lost=="PREPARE_RESPONSE":
                prepare_retry=kernel.issue_identity_mutation(**kwargs,message_type="PREPARE_MUTATION",payload=payload)
                prepared=identity.mutate_operational_identity(prepare_retry,allowed_case_ids=frozenset({"C1"}))
                kernel.record_identity_mutation_response(prepare_retry,prepared)
            else:
                kernel.record_identity_mutation_response(prepare,prepared)
            commit=kernel.issue_identity_mutation(**kwargs,message_type="COMMIT_MUTATION",payload=payload)
            committed=identity.mutate_operational_identity(commit,allowed_case_ids=frozenset({"C1"}))
            if lost=="COMMIT_RESPONSE":
                get=kernel.issue_identity_mutation(**kwargs,message_type="GET_TRANSACTION",payload={"original_request_digest":prepare["request_digest"]})
                recovered=identity.mutate_operational_identity(get,allowed_case_ids=frozenset({"C1"}))
                assert recovered["result"]==committed["result"]
                kernel.record_identity_mutation_response(get,recovered)
            else:
                kernel.record_identity_mutation_response(commit,committed)
            if lost=="WITNESS_UPLOAD":
                from agent_lab.c09_witness_protocol import WitnessError
                session.fail_after_upload=True
                with pytest.raises(WitnessError):
                    kernel.witness_identity_checkpoint("MUTATION:"+kwargs["transaction_id"],custodian=client,provider=provider,signing_key=KERNEL,kernel_key_id="TEST-KERNEL-KEY-1")
            witnessed=kernel.witness_identity_checkpoint("MUTATION:"+kwargs["transaction_id"],custodian=client,provider=provider,signing_key=KERNEL,kernel_key_id="TEST-KERNEL-KEY-1")
            receipt=witnessed["receipt"]
            evidence=witnessed["custodian_verification"]["response"]
            final=dict(staged_receipt_digest=H(receipt),witness_object_key=witnessed["object_key"],witness_generation=witnessed["generation"],
                       witness_preimage_digest=receipt["witness_preimage_digest"],signed_record_digest=evidence["signed_record_digest"],
                       custodian_verification_digest=H(evidence),custodian_nonce=evidence["nonce"])
            finalize=kernel.issue_identity_mutation(**kwargs,message_type="FINALIZE_MUTATION",payload=final)
            result=identity.mutate_operational_identity(finalize,allowed_case_ids=frozenset({"C1"}))
            assert result["outcome"]=="COMMITTED_FINAL"
            if lost=="FINALIZE_RESPONSE":
                get=kernel.issue_identity_mutation(**kwargs,message_type="GET_TRANSACTION",payload={"original_request_digest":prepare["request_digest"]})
                recovered=identity.mutate_operational_identity(get,allowed_case_ids=frozenset({"C1"}))
                assert recovered["outcome"]=="COMMITTED_FINAL"
                kernel.record_identity_mutation_response(get,recovered)
            else:
                kernel.record_identity_mutation_response(finalize,result)
            state=kernel._identity_payload("identity_kernel_state","deployment_id",owner["deployment_id"])
            assert state["active_mutation"] is None and state["logical_head"]==result["identity_head"]
            assert len(session.objects)==2
            kernel._verify_identity_protocol_state()
            identity._verify_logical_integrity()
    finally:
        host.close()
        identity.close()
        kernel.close()


def test_concurrent_same_authorization_has_one_reservation(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from agent_lab.identity_atomic_mutation import load
    path=tmp_path/"identity.sqlite"
    store,request=setup(path)
    store.close()
    second=deepcopy(request)
    second["transaction_id"]="tx:v1:123e4567-e89b-42d3-a456-426614174002"
    second["kernel_proof"]["nonce"]="d"*64
    second=resign(second)
    def run(value):
        local=store_at(path)
        local._mutation_source=Sources()
        try:
            return execute(local,value)["outcome"]
        except PermissionError:
            return "DENIED"
        finally:
            local.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(run,(request,second)))
    assert sorted(results)==["DENIED","PREPARED"]
    store=store_at(path)
    assert load(store,"AUTH:TEST-AUTHORIZATION-1")["state"]=="RESERVED"
    assert store._load_identity("P2") is None
    store.close()


def test_abort_tombstone_and_prepared_recovery(tmp_path):
    from agent_lab.identity_atomic_mutation import load
    store,prepare=setup(tmp_path/"identity.sqlite")
    original=execute(store,prepare)
    request=deepcopy(prepare)
    request["kernel_proof"]["nonce"]="d"*64
    repeated=execute(store,resign(request))
    assert {k:v for k,v in original.items() if k not in {"request_digest","response_digest"}}=={k:v for k,v in repeated.items() if k not in {"request_digest","response_digest"}}
    request.update(message_type="ABORT_PREPARED",payload={"original_request_digest":prepare["request_digest"]})
    request["kernel_proof"]["nonce"]="e"*64
    aborted=execute(store,resign(request))
    assert aborted["outcome"]=="ABORTED"
    assert load(store,"AUTH:TEST-AUTHORIZATION-1")["state"]=="RELEASED"
    request=deepcopy(prepare)
    request["transaction_id"]="tx:v1:123e4567-e89b-42d3-a456-426614174003"
    request["kernel_proof"]["nonce"]="f"*64
    with pytest.raises(PermissionError):execute(store,resign(request))
    store.close()


def test_changed_evidence_at_commit_rolls_back_every_effect(tmp_path):
    from agent_lab.identity_atomic_mutation import load
    store,prepare=setup(tmp_path/"identity.sqlite")
    execute(store,prepare)
    commit=commit_request(store,prepare)
    old_head=store._logical_row()["head"]
    store._mutation_source.changed=True
    with pytest.raises(Exception):execute(store,commit)
    assert store._load_identity("P2") is None
    assert store._logical_row()["head"]==old_head
    assert load(store,"AUTH:TEST-AUTHORIZATION-1")["state"]=="RESERVED"
    store.close()


@pytest.mark.parametrize("raw",[b'{"x":1,"x":2}',b'{ "x":1}',b'{"x": 1}'])
def test_noncanonical_protected_dto_rejected(raw):
    from agent_lab.identity_atomic_mutation import protected_json
    with pytest.raises(ValueError):protected_json(raw)


def test_role_evidence_must_be_unique_and_typed():
    from types import SimpleNamespace
    from agent_lab.identity_atomic_mutation import role_reference
    refs={A1:SimpleNamespace(kind="ROLE_EVIDENCE"),"second":SimpleNamespace(kind="ROLE_EVIDENCE"),"other":SimpleNamespace(kind="IDENTITY_AUTHORIZATION")}
    assert role_reference(refs,["other",A1])==A1
    with pytest.raises(PermissionError):role_reference(refs,[A1,"second"])
    with pytest.raises(PermissionError):role_reference(refs,["other"])


@pytest.mark.parametrize("operation",["UPDATE_IDENTITY_STATUS","BIND_PARTY","CORRECT_PARTY_ROLE","BIND_FACT"])
def test_existing_domain_operations_use_atomic_path(tmp_path,operation):
    from agent_lab.ipc_envelope import OPERATION_CAPABILITIES
    from agent_lab.identity_persistence import _canonical
    from test_identity_persistence import E1,D1,C1,AUDIT,fact
    store,prepare=setup(tmp_path/"identity.sqlite")
    source=store._mutation_source
    source.subject="P1"
    materials=[(A1,"IDENTITY_AUTHORIZATION",b"test authorization","AUTH")]
    payload=dict(request_id="TEST-EXISTING-OP",subject_id="P1",evidence_refs=[E1])
    if operation=="UPDATE_IDENTITY_STATUS":
        payload.update(from_status="ACTIVE",to_status="INACTIVE",effective_date="2025-06-01")
        materials.append((E1,"OWNER_DECLARATION",b"test status declaration","STATUS"))
    elif operation=="BIND_PARTY":
        payload.update(party_role="DOCUMENT_ISSUER",valid_from="2025-01-01",valid_to_exclusive="2026-01-01")
        materials.append((E1,"ROLE_EVIDENCE",b"test role declaration","ROLE"))
    elif operation=="CORRECT_PARTY_ROLE":
        row=store._db.execute("SELECT * FROM case_party_role WHERE binding_id='R1'").fetchone()
        names={"binding_id","case_id","subject_type","subject_id","role","valid_from","valid_to_exclusive","evidence_ref","authorization_ref"}
        prior={key:row[key] for key in names}
        replacement={**prior,"valid_to_exclusive":"2025-06-01"}
        payload=dict(request_id="TEST-EXISTING-OP",prior_binding_ref=E1,replacement_binding_ref=D1,effective_date="2025-06-01",evidence_refs=sorted([E1,D1]))
        materials.extend([(E1,"ROLE_EVIDENCE",_canonical(prior).encode(),"PRIOR"),(D1,"ROLE_EVIDENCE",_canonical(replacement).encode(),"CORRECTION")])
    else:
        source.semantic="synthetic.fact"
        body=dict(fact_payload=store._fact_payload(fact()),declaration_artifact_ref=D1,confirmation_ref=C1)
        payload.update(fact_envelope_ref="sha256:"+"8"*64,evidence_refs=["sha256:"+"8"*64],valid_from="2025-01-01",valid_to_exclusive="2026-01-01")
        materials.extend([(E1,"ROLE_EVIDENCE",b"original role evidence","ROLE"),("sha256:"+"8"*64,"FACT_ENVELOPE",_canonical(body).encode(),"FACT"),(D1,"OWNER_DECLARATION",b"test declaration","DECLARATION"),
            (C1,"OWNER_CONFIRMATION",b"test confirmation","CONFIRMATION"),(AUDIT,"IDENTITY_AUDIT",b"test source audit","AUDIT")])
    source.materials=materials
    prepare.update(domain_operation=operation,capability=OPERATION_CAPABILITIES[operation],payload=payload)
    prepare=resign(prepare)
    assert execute(store,prepare)["outcome"]=="PREPARED"
    assert execute(store,commit_request(store,prepare))["outcome"]=="IDENTITY_COMMITTED"
    if operation=="CORRECT_PARTY_ROLE":
        assert store._db.execute("SELECT COUNT(*) FROM case_party_role").fetchone()[0]==1
        assert store._db.execute("SELECT COUNT(*) FROM case_party_role_history").fetchone()[0]==2
    store._verify_logical_integrity()
    store.close()


@pytest.mark.parametrize("boundary",["BEFORE_COMMIT","AFTER_COMMIT"])
def test_additive_schema_v4_v5_crash_preserves_existing_state(tmp_path,boundary):
    import sqlite3
    from agent_lab.identity_logical_continuity import domain_snapshot
    path=tmp_path/"identity.sqlite"
    store,_,logical=enrolled(path)
    snapshot=H(domain_snapshot(store._db))
    audit=store._audit_head()
    store.close()
    with sqlite3.connect(path) as db:
        db.execute("DROP TABLE identity_mutation_record")
        db.execute("DELETE FROM schema_migration_receipt WHERE migration_id='IDENTITY_SCHEMA_V4_TO_V5'")
        db.execute("PRAGMA user_version=4")
    def fail(stage):
        if stage=="MIGRATION_V4_V5:"+boundary:raise RuntimeError("migration crash")
    with pytest.raises(RuntimeError):store_at(path,fault=fail)
    with sqlite3.connect(path) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0]==(4 if boundary=="BEFORE_COMMIT" else 5)
    store=store_at(path)
    assert H(domain_snapshot(store._db))==snapshot
    assert store._audit_head()==audit
    assert store._logical_row()["head"]==logical["head"]
    store.close()


@pytest.mark.parametrize("target",["TX","AUTH","AUTHREF","NONCE"])
def test_mutation_metadata_deletion_fails_closed(tmp_path,target):
    import sqlite3
    path=tmp_path/"identity.sqlite"
    store,prepare=setup(path)
    execute(store,prepare)
    store.close()
    with sqlite3.connect(path) as db:
        db.execute("DELETE FROM identity_mutation_record WHERE key LIKE ?",(target+":%",))
    with pytest.raises(ValueError):store_at(path)
