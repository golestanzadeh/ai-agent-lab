from datetime import datetime, timezone
from threading import Event, Thread

import pytest

from agent_lab.approval import (
    ApprovalAlreadyConsumedError,
    ApprovalError,
    ApprovalExecutionContext,
    ApprovalStatus,
    ApprovalStore,
    ApprovalValidationError,
    IntendedOperation,
)
from agent_lab.audit import AuditEventType, AuditStore
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

NOW = datetime(2026, 9, 7, tzinfo=timezone.utc)


def make_store():
    registry = CaseRegistry()
    for case_id, year in (("CASE-2024-0001", 2024), ("CASE-2025-0001", 2025)):
        registry.register(
            CaseRecord(
                case_id=case_id,
                owner_type=OwnerType.PERSON,
                owner_id="PERSON-0001",
                tax_period=TaxPeriod("CALENDAR_YEAR", year),
                case_type=CaseType.INDIVIDUAL,
                assessment_mode=AssessmentMode.UNKNOWN_PENDING_VERIFICATION,
                lifecycle_status=LifecycleStatus.CREATED,
                storage_scope_reference=StorageScopeReference("memory", f"root-{year}"),
                schema_version=1,
                created_at=NOW,
                updated_at=NOW,
            )
        )
    state = CaseStateStore(registry)
    state.create_run("CASE-2024-0001")
    state.create_run("CASE-2025-0001")
    audit = AuditStore(registry, state)
    return registry, state, audit, ApprovalStore(
        case_registry=registry, case_state=state, audit_store=audit
    )


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
        timestamp=NOW,
    )
    values.update(overrides)
    return store.create_pending(**values)


def approve(store, **overrides):
    approval = create_pending(store, **overrides)
    return store.grant(
        approval.approval_id,
        approver="human-001",
        authorization_reference="AUTH-001",
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


def test_pending_and_grant_are_audited_and_immutable():
    _, _, audit, store = make_store()
    approval = approve(store)
    assert approval.approval_status is ApprovalStatus.APPROVED
    assert approval.audit_reference == "AUDIT-00000002"
    assert [event.event_type for event in audit.list_events(approval.case_id, approval.run_id)] == [
        AuditEventType.APPROVAL_REQUESTED,
        AuditEventType.APPROVAL_GRANTED,
    ]
    with pytest.raises(Exception):
        approval.approval_status = ApprovalStatus.CONSUMED


@pytest.mark.parametrize(
    "field",
    [
        "case_id", "run_id", "manifest_identity", "manifest_version",
        "manifest_reference", "preflight_identity", "preflight_reference", "actor",
    ],
)
def test_missing_execution_binding_fails_closed(field):
    _, _, _, store = make_store()
    approval = approve(store)
    with pytest.raises(ApprovalError):
        store.validate(approval.approval_id, context(**{field: ""}))


@pytest.mark.parametrize(
    "field",
    [
        "case_id", "run_id", "manifest_identity", "manifest_version",
        "manifest_reference", "preflight_identity", "preflight_reference", "actor",
    ],
)
def test_mismatched_binding_fails_closed(field):
    _, _, _, store = make_store()
    approval = approve(store)
    with pytest.raises(ApprovalValidationError):
        store.validate(approval.approval_id, context(**{field: f"MISMATCH-{field}"}))


def test_preflight_must_be_successful():
    _, _, _, store = make_store()
    with pytest.raises(ApprovalError):
        create_pending(store, preflight_result="FAILED")


def test_unknown_operation_fails_closed():
    _, _, _, store = make_store()
    with pytest.raises(ApprovalError):
        create_pending(store, intended_operation="PHYSICAL_MIGRATION")


def test_case_and_run_must_match():
    _, _, _, store = make_store()
    with pytest.raises(ApprovalError):
        create_pending(store, case_id="CASE-DOES-NOT-EXIST")
    with pytest.raises(ApprovalError):
        create_pending(store, run_id="RUN-00000002")


def test_successful_consumption_is_one_time_and_audited():
    _, _, audit, store = make_store()
    approval = approve(store)
    consumed = store.consume(approval.approval_id, context())
    assert consumed.approval_status is ApprovalStatus.CONSUMED
    assert consumed.audit_reference == "AUDIT-00000003"
    with pytest.raises(ApprovalAlreadyConsumedError, match="APPROVAL_ALREADY_CONSUMED"):
        store.consume(approval.approval_id, context())
    assert len([e for e in audit.list_events(approval.case_id, approval.run_id) if e.event_type is AuditEventType.APPROVAL_CONSUMED]) == 1


def test_reject_revoke_and_expire_are_terminal_for_execution():
    _, _, _, store = make_store()
    rejected = create_pending(store)
    store.reject(rejected.approval_id, actor="human-001")
    with pytest.raises(ApprovalValidationError):
        store.consume(rejected.approval_id, context())

    revoked = approve(store)
    store.revoke(revoked.approval_id, actor="human-001")
    with pytest.raises(ApprovalValidationError):
        store.consume(revoked.approval_id, context())

    expired = approve(store)
    store.expire(expired.approval_id, actor="human-001")
    with pytest.raises(ApprovalValidationError):
        store.consume(expired.approval_id, context())


def test_audit_publication_failure_rolls_back_consumption_and_sequence():
    _, _, audit, store = make_store()
    approval = approve(store)
    original_events = audit._events

    class FailingEvents(dict):
        def __setitem__(self, key, value):
            if value.event_type is AuditEventType.APPROVAL_CONSUMED:
                raise RuntimeError("injected audit publication failure")
            return super().__setitem__(key, value)

    audit._events = FailingEvents(original_events)
    with pytest.raises(RuntimeError, match="injected audit publication failure"):
        store.consume(approval.approval_id, context())
    audit._events = original_events
    assert store.get(approval.approval_id).approval_status is ApprovalStatus.APPROVED
    assert audit._sequence == 2
    assert not [e for e in audit.list_events(approval.case_id, approval.run_id) if e.event_type is AuditEventType.APPROVAL_CONSUMED]
    next_event = audit.append(
        case_id=approval.case_id,
        run_id=approval.run_id,
        event_type=AuditEventType.STATE_CHANGED,
        actor_type="system",
        actor_id="test",
        operation="sequence_check",
    )
    assert next_event.event_id == "AUDIT-00000003"


def test_concurrent_consumption_allows_exactly_one_success():
    _, _, audit, store = make_store()
    approval = approve(store)
    start = Event()
    results = []

    def worker():
        start.wait()
        try:
            store.consume(approval.approval_id, context())
            results.append("success")
        except ApprovalAlreadyConsumedError:
            results.append("already-consumed")

    threads = [Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    start.set()
    for thread in threads:
        thread.join()

    assert sorted(results) == ["already-consumed", "success"]
    assert len([e for e in audit.list_events(approval.case_id, approval.run_id) if e.event_type is AuditEventType.APPROVAL_CONSUMED]) == 1


def test_case_state_is_only_a_reference_boundary():
    _, state, _, store = make_store()
    approval = approve(store)
    state.update_state("CASE-2024-0001", approvals_ref=approval.approval_id)
    assert state.get_state("CASE-2024-0001").approvals_ref == approval.approval_id
