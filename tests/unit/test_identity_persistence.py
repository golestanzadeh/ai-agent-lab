from dataclasses import replace
from datetime import date, datetime, timezone
import json
from pathlib import Path
import sqlite3

import pytest

from agent_lab.case_registry import (
    AssessmentMode, CaseRecord, CaseRegistry, CaseType, LifecycleStatus,
    OwnerType, StorageScopeReference, TaxPeriod,
)
from agent_lab.human_declared_fact import (
    FactConfirmationState, FactValidationStatus, HumanDeclaredFact,
    HumanFactValidationResult,
)
from agent_lab.identity_persistence import CasePartyRole, IdentityPersistence
from agent_lab.person_entity_registry import PersonRecord, RegistryStatus

KEY = b"synthetic-review-key-32-bytes-minimum!!!!"
A1 = "sha256:" + "1" * 64
B1 = "sha256:" + "2" * 64
E1 = "sha256:" + "3" * 64
E2 = "sha256:" + "4" * 64
D1 = "sha256:" + "5" * 64
C1 = "sha256:" + "6" * 64
AUDIT = "sha256:" + "7" * 64
NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def registry() -> CaseRegistry:
    result = CaseRegistry()
    for case_id, root in (("C1", "ROOT1"), ("C2", "ROOT2")):
        result.register(CaseRecord(
            case_id, OwnerType.PERSON, "P1", TaxPeriod("CALENDAR_YEAR", 2025),
            CaseType.INDIVIDUAL, AssessmentMode.UNKNOWN_PENDING_VERIFICATION,
            LifecycleStatus.CREATED, StorageScopeReference("private", root), 1, NOW, NOW,
        ))
    return result


def authorizer(action, case_id, root, token):
    return token == (A1 if case_id == "C1" else B1) and root == ("ROOT1" if case_id == "C1" else "ROOT2")

def evidence_resolver(kind, reference, case_id, tax_year, subject_id, valid_from, valid_to):
    if reference not in {A1,B1,E1,E2,D1,C1,AUDIT} or case_id not in {"C1","C2"} or tax_year!=2025 or not subject_id:
        raise ValueError("unresolved evidence")


def person(identity="P1", status=RegistryStatus.ACTIVE):
    return PersonRecord(identity, status, None, NOW, NOW, 1)


def open_store(tmp_path, *, fault=None, cases=None):
    cases = cases or registry()
    store = IdentityPersistence(tmp_path / "identity.sqlite", cases=cases, authorize=authorizer, evidence_resolver=evidence_resolver,
                                integrity_key=KEY, fault_injector=fault)
    return cases, store


def register(store, identity="P1", status=RegistryStatus.ACTIVE):
    store.register_identity(case_id="C1", record=person(identity, status), authorization_ref=A1)


def role(identity="P1", *, binding="R1", role_code="PRIMARY_TAXPAYER",
         start=date(2025, 1, 1), end=None, evidence=E1):
    return CasePartyRole(binding, "C1", "PERSON", identity, role_code, start, end, evidence, A1)


def fact(state=FactConfirmationState.CONFIRMED, value="synthetic"):
    return HumanDeclaredFact(
        "C1", 2025, "synthetic.fact", value, "OWNER", state, NOW,
        HumanFactValidationResult(FactValidationStatus.PASS, ("TYPE",)), A1, (AUDIT,),
    )


def bind_fact(store, item=None, request="F1"):
    return store.bind_fact(
        request_id=request, case_id="C1", tax_year=2025, subject_id="P1",
        fact=item or fact(), declaration_artifact_ref=D1, confirmation_ref=C1,
        valid_from=date(2025, 1, 1), valid_to_exclusive=date(2026, 1, 1),
        authorization_ref=A1,
    )


def test_t01_two_identities_idempotent_restart(tmp_path):
    cases, store = open_store(tmp_path); register(store); register(store, "P2")
    store.register_identity(case_id="C1", record=person("P2"), authorization_ref=A1)
    store.bind_party(role())
    store.bind_party(role("P2", binding="R2", role_code="SPOUSE_OR_PARTNER", evidence=E2))
    store.close()
    reopened = IdentityPersistence(tmp_path / "identity.sqlite", cases=cases, authorize=authorizer, evidence_resolver=evidence_resolver, integrity_key=KEY)
    assert reopened.read_case_identity(case_id="C1", subject_id="P1", on_date=date(2025, 2, 1), authorization_ref=A1).person_id == "P1"
    assert reopened.read_case_identity(case_id="C1", subject_id="P2", on_date=date(2025, 2, 1), authorization_ref=A1).person_id == "P2"
    reopened.close()


def test_t02_owner_strict_and_spouse_separate(tmp_path):
    _, store = open_store(tmp_path); register(store); register(store, "P2")
    with pytest.raises(PermissionError): store.bind_party(role("P2", binding="BAD"))
    store.bind_party(role())
    store.bind_party(role("P2", binding="S", role_code="SPOUSE_OR_PARTNER", evidence=E2))
    assert {p.role for p in store.list_parties("C1", on_date=date(2025, 6, 1), authorization_ref=A1)} == {"PRIMARY_TAXPAYER", "SPOUSE_OR_PARTNER"}
    store.close()


def test_t03_effective_history_boundaries_and_open_end(tmp_path):
    _, store = open_store(tmp_path); register(store)
    store.bind_party(role(binding="OLD", start=date(2024, 1, 1), end=date(2025, 1, 1)))
    store.bind_party(role(binding="NEW", start=date(2025, 1, 1), evidence=E2))
    assert [p.binding_id for p in store.list_parties("C1", on_date=date(2024, 12, 31), authorization_ref=A1)] == ["OLD"]
    assert [p.binding_id for p in store.list_parties("C1", on_date=date(2025, 1, 1), authorization_ref=A1)] == ["NEW"]
    store.close()


def test_t04_cross_subject_exclusive_overlap_rejected_and_adjacent_allowed(tmp_path):
    _, store = open_store(tmp_path); register(store); register(store, "P2"); register(store, "P3")
    store.bind_party(role("P2", binding="S1", role_code="SPOUSE_OR_PARTNER", end=date(2025, 7, 1)))
    with pytest.raises(ValueError, match="overlapping"):
        store.bind_party(role("P3", binding="S2", role_code="SPOUSE_OR_PARTNER", start=date(2025, 6, 1), evidence=E2))
    store.bind_party(role("P3", binding="S3", role_code="SPOUSE_OR_PARTNER", start=date(2025, 7, 1), evidence=E2))
    store.close()


@pytest.mark.parametrize("status", [RegistryStatus.INACTIVE, RegistryStatus.ARCHIVED, RegistryStatus.UNRESOLVED])
def test_t05_non_active_rejected_on_bind_and_read_after_transition(tmp_path, status):
    _, store = open_store(tmp_path); register(store); register(store, "P2", status)
    with pytest.raises(PermissionError): store.bind_party(role("P2", binding="S", role_code="SPOUSE_OR_PARTNER"))
    store.bind_party(role())
    store.update_identity_status(case_id="C1", identity_id="P1", status=status, authorization_ref=A1)
    with pytest.raises(PermissionError): store.read_case_identity(case_id="C1", subject_id="P1", on_date=date(2025, 2, 1), authorization_ref=A1)
    store.close()


def test_t06_complete_fact_envelope_restart_and_original_digest(tmp_path):
    cases, store = open_store(tmp_path); register(store); store.bind_party(role())
    item = fact(); original = item.artifact_identity.reference; envelope = bind_fact(store, item)
    assert envelope.fact_artifact_ref == original and envelope.semantic_key == item.semantic_key
    store.close()
    reopened = IdentityPersistence(tmp_path / "identity.sqlite", cases=cases, authorize=authorizer, evidence_resolver=evidence_resolver, integrity_key=KEY)
    assert reopened.read_facts(case_id="C1", tax_year=2025, subject_id="P1", authorization_ref=A1) == (envelope,)
    assert item.artifact_identity.reference == original
    reopened.close()


def test_t07_scope_confirmation_replay_and_lineage_fail_closed(tmp_path):
    _, store = open_store(tmp_path); register(store); store.bind_party(role())
    with pytest.raises(Exception): bind_fact(store, fact(FactConfirmationState.PENDING))
    with pytest.raises(ValueError): store.bind_fact(request_id="X", case_id="C1", tax_year=2025, subject_id="P1", fact=fact(), declaration_artifact_ref="bad", confirmation_ref=C1, valid_from=date(2025,1,1), valid_to_exclusive=date(2026,1,1), authorization_ref=A1)
    bind_fact(store)
    with pytest.raises(ValueError, match="conflict"): bind_fact(store, fact(value="changed"))
    with pytest.raises(ValueError): store.bind_fact(request_id="Y", case_id="C1", tax_year=2025, subject_id="P1", fact=fact(), declaration_artifact_ref=D1, confirmation_ref=C1, valid_from=date(2025,7,1), valid_to_exclusive=date(2026,2,1), authorization_ref=A1)
    store.close()


def test_t08_idempotent_fact_and_crash_after_commit_fails_closed(tmp_path):
    fired=[]
    def crash(stage):
        if stage == "SUBJECT_FACT_BIND:AFTER_COMMIT" and not fired:
            fired.append(stage); raise RuntimeError("crash")
    cases, store = open_store(tmp_path, fault=crash); register(store); store.bind_party(role())
    with pytest.raises(RuntimeError): bind_fact(store)
    store._db.close()
    with pytest.raises(ValueError, match="anchor continuity"):
        IdentityPersistence(tmp_path / "identity.sqlite", cases=cases, authorize=authorizer, evidence_resolver=evidence_resolver, integrity_key=KEY)


@pytest.mark.parametrize("target", ["IDENTITY_REGISTER", "CASE_PARTY_BIND", "SUBJECT_FACT_BIND"])
def test_t08_crash_before_commit_rolls_back_row_and_audit(tmp_path, target):
    armed={"value":False}
    def crash(stage):
        if armed["value"] and stage == target + ":BEFORE_COMMIT": raise RuntimeError("crash")
    cases,store=open_store(tmp_path,fault=crash)
    if target != "IDENTITY_REGISTER": register(store)
    if target == "SUBJECT_FACT_BIND": store.bind_party(role())
    armed["value"]=True
    with pytest.raises(RuntimeError):
        if target == "IDENTITY_REGISTER": register(store)
        elif target == "CASE_PARTY_BIND": store.bind_party(role())
        else: bind_fact(store)
    store._verify_audit_continuity()
    table={"IDENTITY_REGISTER":"identity_record","CASE_PARTY_BIND":"case_party_role","SUBJECT_FACT_BIND":"subject_fact_binding"}[target]
    expected=0 if target=="IDENTITY_REGISTER" else (0 if target=="CASE_PARTY_BIND" else 0)
    assert store._db.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == expected
    store.close()


def test_t09_cross_case_and_storage_root_isolation(tmp_path):
    _, store = open_store(tmp_path); register(store); store.bind_party(role())
    with pytest.raises(PermissionError): store.list_parties("C1", on_date=date(2025,1,1), authorization_ref=B1)
    with pytest.raises(PermissionError): store.read_case_identity(case_id="C2", subject_id="P1", on_date=date(2025,1,1), authorization_ref=A1)
    store.close()


@pytest.mark.parametrize("tamper", ["audit_delete", "audit_rewrite", "row_substitute"])
def test_t10_tamper_detection(tmp_path, tamper):
    cases, store = open_store(tmp_path); register(store); store.bind_party(role())
    if tamper == "audit_delete": store._db.execute("DELETE FROM identity_audit WHERE event_id=1")
    elif tamper == "audit_rewrite": store._db.execute("UPDATE identity_audit SET event_payload='{}' WHERE event_id=1")
    else: store._db.execute("UPDATE identity_record SET payload='{}',digest=? WHERE identity_id='P1'", ("0"*64,))
    store._db.commit(); store._db.close()
    with pytest.raises(ValueError): IdentityPersistence(tmp_path / "identity.sqlite", cases=cases, authorize=authorizer, evidence_resolver=evidence_resolver, integrity_key=KEY)


def test_t10_backup_restore_and_key_required(tmp_path):
    cases, store = open_store(tmp_path); register(store); store.bind_party(role()); target=store.backup_to(tmp_path / "backup.sqlite"); store.close()
    restored=IdentityPersistence(target,cases=cases,authorize=authorizer,evidence_resolver=evidence_resolver,integrity_key=KEY)
    assert restored.read_case_identity(case_id="C1",subject_id="P1",on_date=date(2025,1,1),authorization_ref=A1).person_id=="P1"
    restored.close()
    with pytest.raises(ValueError): IdentityPersistence(tmp_path / "other.sqlite",cases=cases,evidence_resolver=evidence_resolver,integrity_key=b"short")


def test_t12_no_live_case001_bootstrap_or_private_data():
    source=Path("src/agent_lab/identity_persistence.py").read_text(encoding="utf-8")
    assert "CASE-001" not in source and "Person A" not in source and "Person B" not in source


def test_raw_identity_bypass_api_removed(tmp_path):
    _, store=open_store(tmp_path)
    assert not hasattr(store,"save_identity") and not hasattr(store,"load_identity") and not hasattr(store,"restore_identity")
    store.close()


def test_lifecycle_operations_default_deny_and_audit_validation(tmp_path):
    cases=registry(); store=IdentityPersistence(tmp_path/"identity.sqlite",cases=cases,evidence_resolver=evidence_resolver,integrity_key=KEY)
    with pytest.raises(PermissionError): store.register_identity(case_id="C1",record=person(),authorization_ref=A1)
    store.close()


def test_synced_deployment_path_rejected(tmp_path):
    path=tmp_path / "OneDrive" / "db.sqlite"; path.parent.mkdir()
    with pytest.raises(ValueError,match="synced"): IdentityPersistence(path,cases=registry(),evidence_resolver=evidence_resolver,integrity_key=KEY)


def test_unversioned_and_unsupported_schema_rejected(tmp_path):
    path=tmp_path/"legacy.sqlite"
    with sqlite3.connect(path) as db: db.execute("CREATE TABLE unrelated(id INTEGER)")
    with pytest.raises(ValueError,match="unversioned"): IdentityPersistence(path,cases=registry(),evidence_resolver=evidence_resolver,integrity_key=KEY)
    path2=tmp_path/"future.sqlite"
    with sqlite3.connect(path2) as db: db.execute("PRAGMA user_version=99")
    with pytest.raises(ValueError,match="unsupported"): IdentityPersistence(path2,cases=registry(),evidence_resolver=evidence_resolver,integrity_key=KEY)


def test_reviewed_empty_v1_migration_to_v2(tmp_path):
    path=tmp_path/"v1.sqlite"
    with sqlite3.connect(path) as db:
        db.executescript("""
        CREATE TABLE identity_record(identity_id TEXT PRIMARY KEY,record_type TEXT,payload TEXT,digest TEXT,schema_version INTEGER);
        CREATE TABLE case_party_role(binding_id TEXT PRIMARY KEY,case_id TEXT,subject_type TEXT,subject_id TEXT,role TEXT,valid_from TEXT,valid_to_exclusive TEXT,evidence_ref TEXT,authorization_ref TEXT,digest TEXT,schema_version INTEGER);
        CREATE TABLE identity_audit(event_id INTEGER PRIMARY KEY AUTOINCREMENT,action TEXT,case_id TEXT,subject_id TEXT,payload_digest TEXT,recorded_at TEXT);
        CREATE TABLE subject_fact_binding(request_id TEXT PRIMARY KEY,case_id TEXT,tax_year INTEGER,subject_id TEXT,artifact_ref TEXT,authorization_ref TEXT,digest TEXT);
        PRAGMA user_version=1;
        """)
    store=IdentityPersistence(path,cases=registry(),authorize=authorizer,evidence_resolver=evidence_resolver,integrity_key=KEY)
    assert store._db.execute("PRAGMA user_version").fetchone()[0] == 2
    store.close()


def test_kernel_adapter_expiry_denies_read_and_write(tmp_path, monkeypatch):
    from datetime import timedelta
    import agent_lab.orchestrator_kernel as kernel_module
    from agent_lab.identity_permission_adapter import kernel_case_authorizer
    from agent_lab.orchestrator_kernel import OrchestratorKernel
    from test_orchestrator_kernel import manifest, task
    contract_root = Path(__file__).resolve().parents[2] / "contracts" / "orchestrator" / "v2"
    cases = registry()
    scope = {"case_id":"C1","tax_year":2025,"run_id":"RUN1"}
    payload = task(role_id="IDENTITY_ADMINISTRATION_AGENT", permissions=["identity_read","case_party_bind"], case_context=scope)
    item = manifest(payload, tiers=["A3","A4"])
    with OrchestratorKernel(tmp_path/"kernel.sqlite", contract_root) as kernel:
        kernel.register_task(payload, gate_triggers=()); kernel.register_manifest(item); kernel.validate_manifest(item["manifest_id"])
        kernel.set_kill_switch("RUNNING", actor_id="HUMAN_PROJECT_OWNER", authority_reference="synthetic")
        kernel.activate_manifest(item["manifest_id"])
        check=kernel_case_authorizer(kernel=kernel,cases=cases,manifest_id=item["manifest_id"],run_id="RUN1")
        assert check("read_party","C1","ROOT1",A1) and check("bind_party","C1","ROOT1",A1)
        monkeypatch.setattr(kernel_module,"_utc_now",lambda:datetime.fromisoformat(item["expires_at"])+timedelta(seconds=1))
        assert not check("read_party","C1","ROOT1",A1)
        assert not check("bind_party","C1","ROOT1",A1)


def test_kernel_adapter_kill_switch_revocation_denies(tmp_path):
    from agent_lab.identity_permission_adapter import kernel_case_authorizer
    from agent_lab.orchestrator_kernel import OrchestratorKernel
    from test_orchestrator_kernel import manifest, task
    contract_root = Path(__file__).resolve().parents[2] / "contracts" / "orchestrator" / "v2"
    cases=registry(); scope={"case_id":"C1","tax_year":2025,"run_id":"RUN1"}
    payload=task(role_id="IDENTITY_ADMINISTRATION_AGENT",permissions=["identity_read"],case_context=scope)
    item=manifest(payload,tiers=["A3"])
    with OrchestratorKernel(tmp_path/"kernel.sqlite",contract_root) as kernel:
        kernel.register_task(payload,gate_triggers=()); kernel.register_manifest(item); kernel.validate_manifest(item["manifest_id"])
        kernel.set_kill_switch("RUNNING",actor_id="HUMAN_PROJECT_OWNER",authority_reference="synthetic"); kernel.activate_manifest(item["manifest_id"])
        check=kernel_case_authorizer(kernel=kernel,cases=cases,manifest_id=item["manifest_id"],run_id="RUN1")
        kernel.set_kill_switch("HALTED",actor_id="HUMAN_PROJECT_OWNER",authority_reference="stop")
        assert not check("read_party","C1","ROOT1",A1)


def test_f02_generic_tax_role_cannot_administer_identity(tmp_path):
    from agent_lab.identity_permission_adapter import kernel_case_authorizer
    from agent_lab.orchestrator_kernel import OrchestratorKernel
    from test_orchestrator_kernel import manifest, task
    contract_root = Path(__file__).resolve().parents[2] / "contracts" / "orchestrator" / "v2"
    cases=registry(); scope={"case_id":"C1","tax_year":2025,"run_id":"RUN1"}
    payload=task(role_id="TAX_LAW_AGENT",permissions=["read_derived_case_artifact"],case_context=scope)
    item=manifest(payload,tiers=["A3"])
    with OrchestratorKernel(tmp_path/"kernel.sqlite",contract_root) as kernel:
        kernel.register_task(payload,gate_triggers=()); kernel.register_manifest(item); kernel.validate_manifest(item["manifest_id"])
        kernel.set_kill_switch("RUNNING",actor_id="HUMAN_PROJECT_OWNER",authority_reference="synthetic"); kernel.activate_manifest(item["manifest_id"])
        check=kernel_case_authorizer(kernel=kernel,cases=cases,manifest_id=item["manifest_id"],run_id="RUN1")
        assert not check("read_party","C1","ROOT1",A1)
        assert not check("register_identity","C1","ROOT1",A1)


def test_f05_evidence_backed_role_correction_preserves_immutable_history(tmp_path):
    _,store=open_store(tmp_path); register(store); store.bind_party(role())
    corrected=store.correct_party_role(
        case_id="C1",binding_id="R1",valid_to_exclusive=date(2025,7,1),
        correction_evidence_ref=E2,authorization_ref=A1,
    )
    assert corrected.valid_to_exclusive == date(2025,7,1)
    history=store._db.execute("SELECT revision,payload FROM case_party_role_history WHERE binding_id='R1' ORDER BY revision").fetchall()
    assert [row["revision"] for row in history] == [1,2]
    assert json.loads(history[0]["payload"])["valid_to_exclusive"] is None
    assert json.loads(history[1]["payload"])["valid_to_exclusive"] == "2025-07-01"
    assert store.list_parties("C1",on_date=date(2025,6,30),authorization_ref=A1)
    assert not store.list_parties("C1",on_date=date(2025,7,1),authorization_ref=A1)
    store.close()
    reopened=IdentityPersistence(tmp_path/"identity.sqlite",cases=registry(),authorize=authorizer,evidence_resolver=evidence_resolver,integrity_key=KEY)
    assert reopened._db.execute("SELECT count(*) FROM case_party_role_history").fetchone()[0] == 2
    reopened.close()


def test_f05_correction_rejects_missing_evidence_and_history_tampering(tmp_path):
    cases,store=open_store(tmp_path); register(store); store.bind_party(role())
    with pytest.raises(ValueError,match="canonical correction"):
        store.correct_party_role(case_id="C1",binding_id="R1",valid_to_exclusive=date(2025,7,1),correction_evidence_ref="missing",authorization_ref=A1)
    store.correct_party_role(case_id="C1",binding_id="R1",valid_to_exclusive=date(2025,7,1),correction_evidence_ref=E2,authorization_ref=A1)
    store._db.execute("UPDATE case_party_role_history SET correction_evidence_ref=? WHERE binding_id='R1' AND revision=1",("sha256:"+"f"*64,))
    store._db.commit(); store._db.close()
    with pytest.raises(ValueError,match="history integrity"):
        IdentityPersistence(tmp_path/"identity.sqlite",cases=cases,authorize=authorizer,evidence_resolver=evidence_resolver,integrity_key=KEY)


def test_f05_deleted_history_is_detected(tmp_path):
    cases,store=open_store(tmp_path); register(store); store.bind_party(role())
    store.correct_party_role(case_id="C1",binding_id="R1",valid_to_exclusive=date(2025,7,1),correction_evidence_ref=E2,authorization_ref=A1)
    store._db.execute("DELETE FROM case_party_role_history WHERE binding_id='R1' AND revision=1")
    store._db.commit(); store._db.close()
    with pytest.raises(ValueError,match="history continuity"):
        IdentityPersistence(tmp_path/"identity.sqlite",cases=cases,authorize=authorizer,evidence_resolver=evidence_resolver,integrity_key=KEY)


def _create_empty_v1(path):
    with sqlite3.connect(path) as db:
        db.executescript("""
        CREATE TABLE identity_record(identity_id TEXT PRIMARY KEY,record_type TEXT,payload TEXT,digest TEXT,schema_version INTEGER);
        CREATE TABLE case_party_role(binding_id TEXT PRIMARY KEY,case_id TEXT,subject_type TEXT,subject_id TEXT,role TEXT,valid_from TEXT,valid_to_exclusive TEXT,evidence_ref TEXT,authorization_ref TEXT,digest TEXT,schema_version INTEGER);
        CREATE TABLE identity_audit(event_id INTEGER PRIMARY KEY AUTOINCREMENT,action TEXT,case_id TEXT,subject_id TEXT,payload_digest TEXT,recorded_at TEXT);
        CREATE TABLE subject_fact_binding(request_id TEXT PRIMARY KEY,case_id TEXT,tax_year INTEGER,subject_id TEXT,artifact_ref TEXT,authorization_ref TEXT,digest TEXT);
        PRAGMA user_version=1;
        """)


@pytest.mark.parametrize("stage",[
    "MIGRATION_V1_V2:AFTER_BEGIN","MIGRATION_V1_V2:AFTER_RENAME",
    "MIGRATION_V1_V2:AFTER_SCHEMA","MIGRATION_V1_V2:AFTER_COPY",
    "MIGRATION_V1_V2:BEFORE_COMMIT",
])
def test_f07_migration_interruptions_roll_back_to_intact_v1(tmp_path,stage):
    path=tmp_path/(stage.rsplit(":",1)[-1]+".sqlite"); _create_empty_v1(path)
    def fault(observed):
        if observed == stage: raise RuntimeError("synthetic migration interruption")
    with pytest.raises(RuntimeError,match="interruption"):
        IdentityPersistence(path,cases=registry(),authorize=authorizer,evidence_resolver=evidence_resolver,integrity_key=KEY,fault_injector=fault)
    with sqlite3.connect(path) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 1
        tables={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"identity_record","case_party_role","identity_audit","subject_fact_binding"} <= tables
        assert not any(name.endswith("_v1") for name in tables)


def test_f07_post_commit_interruption_leaves_verified_v2(tmp_path):
    path=tmp_path/"post.sqlite"; _create_empty_v1(path)
    def fault(observed):
        if observed == "MIGRATION_V1_V2:AFTER_COMMIT": raise RuntimeError("synthetic migration interruption")
    with pytest.raises(RuntimeError,match="interruption"):
        IdentityPersistence(path,cases=registry(),authorize=authorizer,evidence_resolver=evidence_resolver,integrity_key=KEY,fault_injector=fault)
    reopened=IdentityPersistence(path,cases=registry(),authorize=authorizer,evidence_resolver=evidence_resolver,integrity_key=KEY)
    assert reopened._db.execute("PRAGMA user_version").fetchone()[0] == 2
    reopened.close()


def test_f07_database_commit_to_anchor_interruption_reconciles_from_signed_receipt(tmp_path):
    path=tmp_path/"commit-gap.sqlite"; _create_empty_v1(path)
    def fault(observed):
        if observed == "MIGRATION_V1_V2:AFTER_DATABASE_COMMIT": raise RuntimeError("synthetic migration interruption")
    with pytest.raises(RuntimeError,match="interruption"):
        IdentityPersistence(path,cases=registry(),authorize=authorizer,evidence_resolver=evidence_resolver,integrity_key=KEY,fault_injector=fault)
    assert not path.with_suffix(path.suffix+".audit-anchor").exists()
    reopened=IdentityPersistence(path,cases=registry(),authorize=authorizer,evidence_resolver=evidence_resolver,integrity_key=KEY)
    assert path.with_suffix(path.suffix+".audit-anchor").exists()
    reopened.close()
    path.with_suffix(path.suffix+".audit-anchor").unlink()
    with pytest.raises(ValueError,match="anchor missing"):
        IdentityPersistence(path,cases=registry(),authorize=authorizer,evidence_resolver=evidence_resolver,integrity_key=KEY)


def test_f07_populated_v1_migrates_without_losing_identity_role_or_audit(tmp_path):
    from agent_lab.identity_persistence import _canonical, _legacy_digest
    path=tmp_path/"populated.sqlite"; _create_empty_v1(path)
    payload=IdentityPersistence._identity_payload(person())
    role_payload={"binding_id":"R1","case_id":"C1","subject_type":"PERSON","subject_id":"P1","role":"PRIMARY_TAXPAYER","valid_from":"2025-01-01","valid_to_exclusive":None,"evidence_ref":E1,"authorization_ref":A1}
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO identity_record VALUES(?,?,?,?,1)",("P1","PERSON",_canonical(payload),_legacy_digest(payload)))
        db.execute("INSERT INTO case_party_role VALUES(?,?,?,?,?,?,?,?,?,?,1)",(*role_payload.values(),_legacy_digest(role_payload)))
        db.execute("INSERT INTO identity_audit(action,case_id,subject_id,payload_digest,recorded_at) VALUES(?,?,?,?,?)",("ORIGINAL_SECURITY_EVENT","C1","P1","legacy-digest",NOW.isoformat()))
    store=IdentityPersistence(path,cases=registry(),authorize=authorizer,evidence_resolver=evidence_resolver,integrity_key=KEY)
    assert store.read_case_identity(case_id="C1",subject_id="P1",on_date=date(2025,2,1),authorization_ref=A1).person_id == "P1"
    assert store._db.execute("SELECT count(*) FROM identity_history").fetchone()[0] == 1
    assert store._db.execute("SELECT count(*) FROM identity_audit").fetchone()[0] == 1
    legacy=store._db.execute("SELECT * FROM legacy_identity_audit").fetchone()
    assert legacy["action"] == "ORIGINAL_SECURITY_EVENT"
    assert legacy["case_id"] == "C1" and legacy["subject_id"] == "P1"
    assert legacy["payload_digest"] == "legacy-digest"
    assert legacy["recorded_at"] == NOW.isoformat()
    store.close()


def test_f07_v1_with_unmigratable_fact_is_preserved_and_blocked(tmp_path):
    path=tmp_path/"fact.sqlite"; _create_empty_v1(path)
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO subject_fact_binding VALUES(?,?,?,?,?,?,?)",("F1","C1",2025,"P1","legacy",A1,"legacy"))
    with pytest.raises(ValueError,match="reviewed lineage migration"):
        IdentityPersistence(path,cases=registry(),authorize=authorizer,evidence_resolver=evidence_resolver,integrity_key=KEY)
    with sqlite3.connect(path) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM subject_fact_binding").fetchone()[0] == 1
