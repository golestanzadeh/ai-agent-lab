from datetime import datetime, timezone
import json
import sqlite3
from threading import Event, Thread

import pytest

from agent_lab.approval import (
    ApprovalAlreadyConsumedError,
    ApprovalExecutionContext,
    ApprovalNotFoundError,
    ApprovalStatus,
    ApprovalValidationError,
    IntendedOperation,
)
from agent_lab.audit import ActorType, AuditEventType
from agent_lab.case_registry import (
    AssessmentMode,
    CaseRecord,
    CaseRegistry,
    CaseType,
    LifecycleStatus,
    OwnerType,
    StorageScopeReference,
    TaxPeriod,
)
from agent_lab.case_state import CaseStateStore
from agent_lab.durable_approval import (
    DurableApprovalIntegrityError,
    DurableApprovalSchemaError,
    DurableApprovalStore,
)

NOW = datetime(2026, 9, 10, tzinfo=timezone.utc)


def make_scope():
    registry = CaseRegistry()
    registry.register(
        CaseRecord(
            case_id="CASE-2024-0001",
            owner_type=OwnerType.PERSON,
            owner_id="PERSON-0001",
            tax_period=TaxPeriod("CALENDAR_YEAR", 2024),
            case_type=CaseType.INDIVIDUAL,
            assessment_mode=AssessmentMode.UNKNOWN_PENDING_VERIFICATION,
            lifecycle_status=LifecycleStatus.CREATED,
            storage_scope_reference=StorageScopeReference("memory", "root-2024"),
            schema_version=1,
            created_at=NOW,
            updated_at=NOW,
        )
    )
    state = CaseStateStore(registry)
    state.create_run("CASE-2024-0001")
    return registry, state


def make_store(path):
    registry, state = make_scope()
    return registry, state, DurableApprovalStore(path, case_registry=registry, case_state=state)


def create_pending(store, **overrides):
    values = dict(
        case_id="CASE-2024-0001",
        run_id="RUN-00000001",
        manifest_identity="MANIFEST-001",
        manifest_version="1",
        manifest_reference="manifest://CASE-001/001",
        preflight_identity="PREFLIGHT-001",
        preflight_reference="preflight://CASE-001/001",
        preflight_result="PASSED",
        intended_operation=IntendedOperation.PHYSICAL_MIGRATION,
        actor="executor-001",
        requester_actor_type=ActorType.AGENT,
        timestamp=NOW,
    )
    values.update(overrides)
    return store.create_pending(**values)


def approve(store):
    pending = create_pending(store)
    return store.grant(
        pending.approval_id,
        approver="human-001",
        authorization_reference="AUTH-DURABLE-001",
        timestamp=NOW,
    )


def context(**overrides):
    values = dict(
        case_id="CASE-2024-0001",
        run_id="RUN-00000001",
        manifest_identity="MANIFEST-001",
        manifest_version="1",
        manifest_reference="manifest://CASE-001/001",
        preflight_identity="PREFLIGHT-001",
        preflight_reference="preflight://CASE-001/001",
        preflight_result="PASSED",
        intended_operation=IntendedOperation.PHYSICAL_MIGRATION,
        actor="executor-001",
    )
    values.update(overrides)
    return ApprovalExecutionContext(**values)


def reopen(path):
    registry, state = make_scope()
    return DurableApprovalStore(path, case_registry=registry, case_state=state)


def test_create_and_grant_survive_restart(tmp_path):
    db = tmp_path / "approval.sqlite3"
    _, _, store = make_store(db)
    approved = approve(store)
    store.close()

    with reopen(db) as reloaded:
        restored = reloaded.get(approved.approval_id)
        assert restored == approved
        assert restored.approval_status is ApprovalStatus.APPROVED
        assert [e.event_type for e in reloaded.list_audit_events(restored.case_id, restored.run_id)] == [
            AuditEventType.APPROVAL_REQUESTED,
            AuditEventType.APPROVAL_GRANTED,
        ]


def test_exact_binding_survives_reload_and_mismatch_fails_closed(tmp_path):
    db = tmp_path / "approval.sqlite3"
    _, _, store = make_store(db)
    approved = approve(store)
    store.close()

    with reopen(db) as reloaded:
        assert reloaded.validate(approved.approval_id, context()).approval_status is ApprovalStatus.APPROVED
        with pytest.raises(ApprovalValidationError, match="manifest binding mismatch"):
            reloaded.validate(approved.approval_id, context(manifest_reference="wrong"))


def test_consumption_is_terminal_across_restart(tmp_path):
    db = tmp_path / "approval.sqlite3"
    _, _, store = make_store(db)
    approved = approve(store)
    consumed = store.consume(approved.approval_id, context())
    assert consumed.approval_status is ApprovalStatus.CONSUMED
    store.close()

    with reopen(db) as reloaded:
        assert reloaded.get(approved.approval_id).approval_status is ApprovalStatus.CONSUMED
        with pytest.raises(ApprovalAlreadyConsumedError, match="APPROVAL_ALREADY_CONSUMED"):
            reloaded.consume(approved.approval_id, context())
        events = reloaded.list_audit_events(approved.case_id, approved.run_id)
        assert len([e for e in events if e.event_type is AuditEventType.APPROVAL_CONSUMED]) == 1


def test_concurrent_store_instances_allow_exactly_one_consumer(tmp_path):
    db = tmp_path / "approval.sqlite3"
    _, _, creator = make_store(db)
    approved = approve(creator)
    creator.close()

    store_a = reopen(db)
    store_b = reopen(db)
    start = Event()
    results = []

    def worker(store):
        start.wait()
        try:
            store.consume(approved.approval_id, context())
            results.append("success")
        except ApprovalAlreadyConsumedError:
            results.append("already-consumed")

    threads = [Thread(target=worker, args=(store_a,)), Thread(target=worker, args=(store_b,))]
    for thread in threads:
        thread.start()
    start.set()
    for thread in threads:
        thread.join(timeout=5)

    store_a.close()
    store_b.close()
    assert sorted(results) == ["already-consumed", "success"]

    with reopen(db) as final:
        assert final.get(approved.approval_id).approval_status is ApprovalStatus.CONSUMED
        assert len([
            e for e in final.list_audit_events(approved.case_id, approved.run_id)
            if e.event_type is AuditEventType.APPROVAL_CONSUMED
        ]) == 1


def test_audit_insert_failure_rolls_back_consumption_and_counter(tmp_path):
    db = tmp_path / "approval.sqlite3"
    _, _, store = make_store(db)
    approved = approve(store)
    store.close()

    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            CREATE TRIGGER fail_consumed_audit
            BEFORE INSERT ON durable_approval_audit
            WHEN NEW.event_type = 'APPROVAL_CONSUMED'
            BEGIN
                SELECT RAISE(ABORT, 'injected durable audit failure');
            END;
            """
        )

    failing = reopen(db)
    with pytest.raises(sqlite3.IntegrityError, match="injected durable audit failure"):
        failing.consume(approved.approval_id, context())
    assert failing.get(approved.approval_id).approval_status is ApprovalStatus.APPROVED
    failing.close()

    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT value FROM durable_counters WHERE kind='audit'").fetchone()[0] == 2
        conn.execute("DROP TRIGGER fail_consumed_audit")

    with reopen(db) as recovered:
        consumed = recovered.consume(approved.approval_id, context())
        assert consumed.audit_reference == "AUDIT-00000003"


def test_corrupt_approval_integrity_fails_closed(tmp_path):
    db = tmp_path / "approval.sqlite3"
    _, _, store = make_store(db)
    approved = approve(store)
    store.close()

    with sqlite3.connect(db) as conn:
        conn.execute(
            "UPDATE durable_approvals SET manifest_reference='tampered' WHERE approval_id=?",
            (approved.approval_id,),
        )

    with reopen(db) as reloaded:
        with pytest.raises(DurableApprovalIntegrityError, match="integrity mismatch"):
            reloaded.get(approved.approval_id)


def test_corrupt_audit_integrity_fails_closed(tmp_path):
    db = tmp_path / "approval.sqlite3"
    _, _, store = make_store(db)
    approved = approve(store)
    store.close()

    with sqlite3.connect(db) as conn:
        conn.execute(
            "UPDATE durable_approval_audit SET actor_id='tampered' WHERE event_id='AUDIT-00000001'"
        )

    with reopen(db) as reloaded:
        with pytest.raises(DurableApprovalIntegrityError, match="audit integrity mismatch"):
            reloaded.list_audit_events(approved.case_id, approved.run_id)


def test_unknown_schema_version_fails_on_reopen(tmp_path):
    db = tmp_path / "approval.sqlite3"
    _, _, store = make_store(db)
    create_pending(store)
    store.close()

    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE durable_schema SET version=999 WHERE component='approval'")

    registry, state = make_scope()
    with pytest.raises(DurableApprovalSchemaError, match="unsupported"):
        DurableApprovalStore(db, case_registry=registry, case_state=state)


def test_unknown_record_schema_version_fails_closed(tmp_path):
    db = tmp_path / "approval.sqlite3"
    _, _, store = make_store(db)
    approval = create_pending(store)
    store.close()

    with sqlite3.connect(db) as conn:
        conn.execute(
            "UPDATE durable_approvals SET schema_version=999 WHERE approval_id=?",
            (approval.approval_id,),
        )

    with reopen(db) as reloaded:
        with pytest.raises(DurableApprovalSchemaError, match="unsupported approval record"):
            reloaded.get(approval.approval_id)


def test_legacy_review_export_is_not_executable_authority(tmp_path):
    review = tmp_path / "review.json"
    review.write_text(
        json.dumps({"approval_id": "APP-00000001", "approval_status": "APPROVED"}),
        encoding="utf-8",
    )
    db = tmp_path / "approval.sqlite3"
    _, _, store = make_store(db)
    with pytest.raises(ApprovalNotFoundError):
        store.get("APP-00000001")
    assert review.exists()
    store.close()


def test_all_lifecycle_transitions_have_durable_audit_event(tmp_path):
    db = tmp_path / "approval.sqlite3"
    _, _, store = make_store(db)

    rejected = create_pending(store)
    store.reject(rejected.approval_id, actor="human-001")

    revoked = approve(store)
    store.revoke(revoked.approval_id, actor="human-001")

    expired = approve(store)
    store.expire(expired.approval_id, actor="human-001")

    consumed = approve(store)
    store.consume(consumed.approval_id, context())

    event_types = [e.event_type for e in store.list_audit_events("CASE-2024-0001", "RUN-00000001")]
    for required in (
        AuditEventType.APPROVAL_REQUESTED,
        AuditEventType.APPROVAL_GRANTED,
        AuditEventType.APPROVAL_REJECTED,
        AuditEventType.APPROVAL_REVOKED,
        AuditEventType.APPROVAL_EXPIRED,
        AuditEventType.APPROVAL_CONSUMED,
    ):
        assert required in event_types
    store.close()
