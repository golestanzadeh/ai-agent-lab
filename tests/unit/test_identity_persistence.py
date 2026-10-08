from datetime import date, datetime, timezone
import sqlite3
import pytest

from agent_lab.case_registry import (
    AssessmentMode, CaseRecord, CaseRegistry, CaseType, LifecycleStatus,
    OwnerType, StorageScopeReference, TaxPeriod,
)
from agent_lab.person_entity_registry import PersonRecord, RegistryStatus
from agent_lab.identity_persistence import CasePartyRole, IdentityPersistence


def setup(tmp_path):
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    cases = CaseRegistry()
    for case_id in ("C1", "C2"):
        cases.register(CaseRecord(
            case_id, OwnerType.PERSON, "P1", TaxPeriod("CALENDAR_YEAR", 2025),
            CaseType.INDIVIDUAL, AssessmentMode.UNKNOWN_PENDING_VERIFICATION,
            LifecycleStatus.CREATED, StorageScopeReference("private", case_id),
            1, now, now,
        ))
    path = tmp_path / "identities.sqlite"
    store = IdentityPersistence(path, cases=cases, authorize=lambda action, case_id, root, token: token in ({'C1': {'A1','A2','A3'}, 'C2': {'B1'}}.get(case_id, set())) and root == case_id)
    store.save_identity(PersonRecord("P1", RegistryStatus.ACTIVE, None, now, now, 1))
    return path, cases, store


def test_restart_and_idempotent_identity(tmp_path):
    path, cases, store = setup(tmp_path)
    person = store.load_identity("P1")
    store.save_identity(person)
    store.close()
    store = IdentityPersistence(path, cases=cases, authorize=lambda action, case_id, root, token: token in ({'C1': {'A1','A2','A3'}, 'C2': {'B1'}}.get(case_id, set())) and root == case_id)
    assert store.load_identity("P1") == person
    store.close()


def test_case_isolation_and_effective_dates(tmp_path):
    _, _, store = setup(tmp_path)
    role = CasePartyRole("B1", "C1", "PERSON", "P1", "PRIMARY_TAXPAYER",
                         date(2025, 1, 1), date(2025, 7, 1), "E1", "A1")
    store.bind_party(role)
    store.bind_party(role)
    assert store.list_parties("C1", on_date=date(2025, 6, 30), authorization_ref="A1") == (role,)
    assert store.list_parties("C1", on_date=date(2025, 7, 1), authorization_ref="A1") == ()
    assert store.list_parties("C2", on_date=date(2025, 6, 30), authorization_ref="B1") == ()
    with pytest.raises(ValueError, match="overlapping"):
        store.bind_party(CasePartyRole("B2", "C1", "PERSON", "P1", "PRIMARY_TAXPAYER",
                                      date(2025, 6, 1), None, "E2", "A2"))
    store.close()


def test_wrong_owner_and_corruption_fail_closed(tmp_path):
    _, _, store = setup(tmp_path)
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    store.save_identity(PersonRecord("P2", RegistryStatus.ACTIVE, None, now, now, 1))
    with pytest.raises(PermissionError):
        store.bind_party(CasePartyRole("B2", "C1", "PERSON", "P2", "PRIMARY_TAXPAYER",
                                      date(2025, 1, 1), None, "E2", "A2"))
    store._db.execute("UPDATE identity_record SET digest='invalid' WHERE identity_id='P1'")
    with pytest.raises(ValueError, match="integrity"):
        store.load_identity("P1")
    store.close()


@pytest.mark.parametrize("status", [RegistryStatus.INACTIVE, RegistryStatus.ARCHIVED, RegistryStatus.UNRESOLVED])
def test_non_active_identity_rejected(tmp_path, status):
    _, _, store = setup(tmp_path)
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    store.save_identity(PersonRecord("P3", status, None, now, now, 1))
    with pytest.raises(PermissionError, match="inactive or unresolved"):
        store.bind_party(CasePartyRole(
            "B3", "C1", "PERSON", "P3", "SPOUSE_OR_PARTNER",
            date(2025, 1, 1), None, "E3", "A3"
        ))
    store.close()


def test_authorization_fail_closed_and_cross_case(tmp_path):
    path, cases, store = setup(tmp_path)
    role = CasePartyRole("B1", "C1", "PERSON", "P1", "PRIMARY_TAXPAYER",
                         date(2025, 1, 1), None, "E1", "A1")
    store.bind_party(role)
    with pytest.raises(PermissionError):
        store.list_parties("C1", on_date=date(2025, 2, 1), authorization_ref="B1")
    with pytest.raises(PermissionError):
        store.list_parties("C2", on_date=date(2025, 2, 1), authorization_ref="A1")
    store.close()
    no_authorizer = IdentityPersistence(path, cases=cases)
    with pytest.raises(PermissionError):
        no_authorizer.list_parties("C1", on_date=date(2025, 2, 1), authorization_ref="A1")
    no_authorizer.close()


def test_effective_years_restart_and_integrity(tmp_path):
    path, cases, store = setup(tmp_path)
    early = CasePartyRole("OLD", "C1", "PERSON", "P1", "PRIMARY_TAXPAYER",
                          date(2024, 1, 1), date(2025, 1, 1), "E-OLD", "A1")
    later = CasePartyRole("NEW", "C1", "PERSON", "P1", "PRIMARY_TAXPAYER",
                          date(2025, 1, 1), None, "E-NEW", "A1")
    store.bind_party(early)
    store.bind_party(later)
    store.close()
    store = IdentityPersistence(path, cases=cases, authorize=lambda a,c,r,t: c == r == "C1" and t == "A1")
    assert store.list_parties("C1", on_date=date(2024, 12, 31), authorization_ref="A1") == (early,)
    assert store.list_parties("C1", on_date=date(2025, 1, 1), authorization_ref="A1") == (later,)
    store._db.execute("UPDATE case_party_role SET digest='bad' WHERE binding_id='NEW'")
    with pytest.raises(ValueError, match="integrity"):
        store.list_parties("C1", on_date=date(2025, 1, 1), authorization_ref="A1")
    store.close()


def test_unsupported_schema_rejected(tmp_path):
    _, _, store = setup(tmp_path)
    store._db.execute('PRAGMA ignore_check_constraints=ON')
    store._db.execute("UPDATE identity_record SET schema_version=99 WHERE identity_id='P1'")
    with pytest.raises(ValueError, match="unsupported"):
        store.load_identity("P1")
    store.close()


def test_audit_is_transactional_and_no_duplicate_events(tmp_path):
    _, _, store = setup(tmp_path)
    role = CasePartyRole("B1", "C1", "PERSON", "P1", "PRIMARY_TAXPAYER",
                         date(2025, 1, 1), None, "E1", "A1")
    store.bind_party(role)
    store.bind_party(role)
    rows = store._db.execute(
        "SELECT action, case_id, subject_id FROM identity_audit ORDER BY event_id"
    ).fetchall()
    assert [tuple(row) for row in rows] == [
        ("IDENTITY_REGISTER", None, "P1"),
        ("CASE_PARTY_BIND", "C1", "P1"),
    ]
    store.close()


def test_confirmed_fact_reference_and_scope(tmp_path):
    from agent_lab.human_declared_fact import (
        HumanDeclaredFact, FactConfirmationState, FactValidationStatus,
        HumanFactValidationResult,
    )
    _, _, store = setup(tmp_path)
    role = CasePartyRole("B1", "C1", "PERSON", "P1", "PRIMARY_TAXPAYER",
                         date(2025, 1, 1), None, "E1", "A1")
    store.bind_party(role)
    now = datetime(2025, 4, 1, tzinfo=timezone.utc)
    def make_fact(state):
        return HumanDeclaredFact(
            case_id="C1", tax_year=2025, semantic_key="synthetic.test",
            value="sample", declaring_actor_reference="OWNER",
            confirmation_state=state, declared_at=now,
            validation=HumanFactValidationResult(FactValidationStatus.PASS, ("type",)),
            authorization_reference="A1", audit_references=("AUDIT-1",),
        )
    fact = make_fact(FactConfirmationState.CONFIRMED)
    ref = store.bind_fact_reference(request_id="REQ1", case_id="C1", tax_year=2025,
                                    subject_id="P1", fact=fact, authorization_ref="A1")
    assert ref == fact.artifact_identity.reference
    assert store.read_fact_references(case_id="C1", tax_year=2025,
                                      subject_id="P1", authorization_ref="A1") == (ref,)
    with pytest.raises(ValueError):
        store.bind_fact_reference(request_id="REQ1", case_id="C1", tax_year=2025,
                                  subject_id="P1", fact=__import__('dataclasses').replace(fact, value='changed'),
                                  authorization_ref="A1")
    store.close()


def test_fact_rejects_wrong_year_unconfirmed_and_wrong_case(tmp_path):
    from agent_lab.human_declared_fact import (
        HumanDeclaredFact, FactConfirmationState, FactValidationStatus,
        HumanFactValidationResult,
    )
    _, _, store = setup(tmp_path)
    store.bind_party(CasePartyRole("B1", "C1", "PERSON", "P1", "PRIMARY_TAXPAYER",
                                  date(2025, 1, 1), None, "E1", "A1"))
    fact = HumanDeclaredFact(
        case_id="C1", tax_year=2025, semantic_key="synthetic", value="ok",
        declaring_actor_reference="OWNER", confirmation_state=FactConfirmationState.PENDING,
        declared_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        validation=HumanFactValidationResult(FactValidationStatus.PASS, ("type",)),
        authorization_reference="A1", audit_references=("AUDIT-1",),
    )
    with pytest.raises(ValueError):
        store.bind_fact_reference(request_id="REQ1", case_id="C1", tax_year=2025,
                                  subject_id="P1", fact=fact, authorization_ref="A1")
    confirmed = __import__('dataclasses').replace(fact, confirmation_state=FactConfirmationState.CONFIRMED)
    with pytest.raises(ValueError):
        store.bind_fact_reference(request_id="REQ2", case_id="C1", tax_year=2024,
                                  subject_id="P1", fact=confirmed, authorization_ref="A1")
    with pytest.raises(ValueError):
        store.bind_fact_reference(request_id="REQ3", case_id="C2", tax_year=2025,
                                  subject_id="P1", fact=confirmed, authorization_ref="A1")
    store.close()


def test_denied_access_writes_redacted_audit(tmp_path):
    _, _, store = setup(tmp_path)
    with pytest.raises(PermissionError):
        store.list_parties("C1", on_date=date(2025, 1, 1), authorization_ref="INVALID")
    rows = store._db.execute(
        "SELECT action, subject_id, payload_digest FROM identity_audit WHERE action='SECURITY_DENIED'"
    ).fetchall()
    assert len(rows) == 1
    assert rows[0]["subject_id"] == "REDACTED"
    assert len(rows[0]["payload_digest"]) == 64
    store.close()


def test_db_user_version_fail_closed(tmp_path):
    path, cases, store = setup(tmp_path)
    store.close()
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA user_version=99")
    with pytest.raises(ValueError, match="unsupported database schema"):
        IdentityPersistence(path, cases=cases)


def test_kernel_permission_adapter_scope_and_default_deny(tmp_path):
    from agent_lab.identity_permission_adapter import kernel_case_authorizer
    from agent_lab.orchestrator_kernel import KernelDecision
    _, cases, store = setup(tmp_path)
    class FakeKernel:
        def permission_decision(self, manifest_id, capability, **scope):
            assert manifest_id == "MANIFEST-TEST"
            assert scope["tax_year"] == 2025
            assert scope["run_id"] == "RUN-TEST"
            return KernelDecision(True, "ALLOW", "synthetic")
    callback = kernel_case_authorizer(kernel=FakeKernel(), cases=cases,
                                      manifest_id="MANIFEST-TEST", run_id="RUN-TEST")
    assert callback("read_party", "C1", "C1", "AUTH")
    assert not callback("read_party", "C1", "C2", "AUTH")
    assert not callback("unknown_action", "C1", "C1", "AUTH")
    assert not callback("read_party", "C1", "C1", "")
    store.close()


def test_real_kernel_adapter_denies_unknown_manifest(tmp_path):
    from pathlib import Path
    from agent_lab.identity_permission_adapter import kernel_case_authorizer
    from agent_lab.orchestrator_kernel import OrchestratorKernel
    _, cases, store = setup(tmp_path)
    contracts = Path(__file__).resolve().parents[2] / "contracts" / "orchestrator" / "v1"
    with OrchestratorKernel(tmp_path / "kernel.sqlite3", contracts) as kernel:
        callback = kernel_case_authorizer(
            kernel=kernel, cases=cases, manifest_id="UNKNOWN-MANIFEST", run_id="RUN1"
        )
        assert not callback("read_party", "C1", "C1", "AUTH")
        assert not callback("bind_party", "C1", "C1", "AUTH")
    store.close()


def test_integrity_failure_is_audited(tmp_path):
    _, _, store = setup(tmp_path)
    store._db.execute("UPDATE identity_record SET digest='bad' WHERE identity_id='P1'")
    with pytest.raises(ValueError, match="integrity"):
        store.load_identity("P1")
    row = store._db.execute(
        "SELECT action, subject_id FROM identity_audit WHERE action='INTEGRITY_FAILURE'"
    ).fetchone()
    assert tuple(row) == ("INTEGRITY_FAILURE", "P1")
    store.close()


def test_case_binding_transaction_rollback(tmp_path):
    _, _, store = setup(tmp_path)
    role = CasePartyRole("B1", "C1", "PERSON", "P1", "PRIMARY_TAXPAYER",
                         date(2025, 1, 1), None, "E1", "A1")
    store.bind_party(role)
    with pytest.raises(ValueError):
        store.bind_party(CasePartyRole(
            "B2", "C1", "PERSON", "P1", "PRIMARY_TAXPAYER",
            date(2025, 2, 1), None, "E2", "A2",
        ))
    assert store._db.execute("SELECT count(*) FROM case_party_role").fetchone()[0] == 1
    assert store._db.execute(
        "SELECT count(*) FROM identity_audit WHERE action='CASE_PARTY_BIND'"
    ).fetchone()[0] == 1
    store.close()


def test_unversioned_existing_database_requires_migration(tmp_path):
    path = tmp_path / "unversioned.sqlite"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE unrelated (id INTEGER)")
    cases = CaseRegistry()
    with pytest.raises(ValueError, match="reviewed migration"):
        IdentityPersistence(path, cases=cases)


def test_case_scoped_identity_read(tmp_path):
    _, _, store = setup(tmp_path)
    store.bind_party(CasePartyRole(
        "B1", "C1", "PERSON", "P1", "PRIMARY_TAXPAYER",
        date(2025, 1, 1), None, "E1", "A1",
    ))
    assert store.read_case_identity(case_id="C1", subject_id="P1",
                                    on_date=date(2025, 2, 1),
                                    authorization_ref="A1").person_id == "P1"
    with pytest.raises(PermissionError):
        store.read_case_identity(case_id="C2", subject_id="P1",
                                 on_date=date(2025, 2, 1),
                                 authorization_ref="B1")
    store.close()


def test_two_distinct_people_survive_restart(tmp_path):
    path, cases, store = setup(tmp_path)
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    store.save_identity(PersonRecord("P2", RegistryStatus.ACTIVE, "Synthetic Two", now, now, 1))
    store.close()
    reopened = IdentityPersistence(path, cases=cases)
    assert reopened.load_identity("P1").person_id == "P1"
    assert reopened.load_identity("P2").person_id == "P2"
    assert reopened.load_identity("P1") != reopened.load_identity("P2")
    reopened.close()
