from datetime import datetime, timezone

import pytest

from agent_lab.audit import (
    ActorType,
    AuditEventNotFoundError,
    AuditEventType,
    AuditStatus,
    AuditStore,
    InvalidAuditEventError,
)
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


def make_registry() -> CaseRegistry:
    registry = CaseRegistry()
    now = datetime.now(timezone.utc)
    for year, root in ((2024, "root-1"), (2025, "root-2")):
        registry.register(
            CaseRecord(
                case_id=f"CASE-{year}-0001",
                owner_type=OwnerType.PERSON,
                owner_id="PERSON-0001",
                tax_period=TaxPeriod("CALENDAR_YEAR", year),
                case_type=CaseType.INDIVIDUAL,
                assessment_mode=AssessmentMode.UNKNOWN_PENDING_VERIFICATION,
                lifecycle_status=LifecycleStatus.CREATED,
                storage_scope_reference=StorageScopeReference("memory", root),
                schema_version=1,
                created_at=now,
                updated_at=now,
            )
        )
    return registry


def make_store() -> tuple[CaseRegistry, CaseStateStore, AuditStore]:
    registry = make_registry()
    state = CaseStateStore(registry)
    audit = AuditStore(registry, state)
    return registry, state, audit


def test_append_records_reconstructable_event():
    _, state, audit = make_store()
    run = state.create_run("CASE-2024-0001")
    event = audit.append(
        case_id="CASE-2024-0001",
        run_id=run.run_id,
        event_type=AuditEventType.TOOL_COMPLETED,
        actor_type=ActorType.TOOL,
        actor_id="drive.metadata",
        operation="list_documents",
        status=AuditStatus.SUCCESS,
        input_refs=("case-scope:documents",),
        output_refs=("inventory-v1",),
    )
    assert event.event_id == "AUDIT-00000001"
    assert audit.get("CASE-2024-0001", event.event_id) == event


def test_events_are_case_scoped_and_run_scoped():
    _, state, audit = make_store()
    run_a = state.create_run("CASE-2024-0001")
    run_b = state.create_run("CASE-2025-0001")
    audit.append(
        case_id="CASE-2024-0001", run_id=run_a.run_id,
        event_type=AuditEventType.RUN_STARTED, actor_type=ActorType.SYSTEM,
        actor_id="runtime", operation="start", status=AuditStatus.INFO,
    )
    audit.append(
        case_id="CASE-2025-0001", run_id=run_b.run_id,
        event_type=AuditEventType.RUN_STARTED, actor_type=ActorType.SYSTEM,
        actor_id="runtime", operation="start", status=AuditStatus.INFO,
    )
    assert len(audit.list_events("CASE-2024-0001", run_a.run_id)) == 1
    assert len(audit.list_events("CASE-2025-0001", run_b.run_id)) == 1
    assert audit.list_events("CASE-2024-0001", run_a.run_id)[0].case_id == "CASE-2024-0001"


def test_cross_case_run_is_rejected():
    _, state, audit = make_store()
    run = state.create_run("CASE-2024-0001")
    with pytest.raises(InvalidAuditEventError):
        audit.append(
            case_id="CASE-2025-0001", run_id=run.run_id,
            event_type=AuditEventType.TOOL_CALLED, actor_type=ActorType.TOOL,
            actor_id="tool", operation="read", status=AuditStatus.INFO,
        )


def test_unknown_case_fails_closed():
    _, _, audit = make_store()
    with pytest.raises(InvalidAuditEventError):
        audit.append(
            case_id="CASE-9999-0001", run_id=None,
            event_type=AuditEventType.ERROR_RECORDED, actor_type=ActorType.SYSTEM,
            actor_id="runtime", operation="error",
        )


def test_blank_actor_or_operation_is_rejected():
    _, _, audit = make_store()
    with pytest.raises(InvalidAuditEventError):
        audit.append(
            case_id="CASE-2024-0001", run_id=None,
            event_type=AuditEventType.ERROR_RECORDED, actor_type=ActorType.SYSTEM,
            actor_id="", operation="error",
        )


def test_get_cannot_cross_case_boundary():
    _, state, audit = make_store()
    run = state.create_run("CASE-2024-0001")
    event = audit.append(
        case_id="CASE-2024-0001", run_id=run.run_id,
        event_type=AuditEventType.RUN_CREATED, actor_type=ActorType.SYSTEM,
        actor_id="runtime", operation="create",
    )
    with pytest.raises(AuditEventNotFoundError):
        audit.get("CASE-2025-0001", event.event_id)


def test_append_only_events_have_unique_monotonic_ids():
    _, _, audit = make_store()
    first = audit.append(
        case_id="CASE-2024-0001", run_id=None,
        event_type=AuditEventType.APPROVAL_REQUESTED, actor_type=ActorType.SYSTEM,
        actor_id="runtime", operation="request", approval_ref="APP-1",
    )
    second = audit.append(
        case_id="CASE-2024-0001", run_id=None,
        event_type=AuditEventType.APPROVAL_GRANTED, actor_type=ActorType.HUMAN,
        actor_id="user", operation="approve", approval_ref="APP-1",
    )
    assert first.event_id != second.event_id
    assert second.event_id > first.event_id


def test_reference_fields_do_not_require_raw_payloads():
    _, state, audit = make_store()
    run = state.create_run("CASE-2024-0001")
    event = audit.append(
        case_id="CASE-2024-0001", run_id=run.run_id,
        event_type=AuditEventType.DECISION_RECORDED, actor_type=ActorType.AGENT,
        actor_id="tax-analysis", operation="classify",
        decision_ref="DEC-001", evidence_refs=("EVID-001",),
        input_refs=("DOC-001",), output_refs=("CAT-001",),
    )
    assert event.decision_ref == "DEC-001"
    assert event.evidence_refs == ("EVID-001",)
    assert event.input_refs == ("DOC-001",)
    assert event.output_refs == ("CAT-001",)


def test_validation_preserves_audit_invariants():
    _, state, audit = make_store()
    run = state.create_run("CASE-2024-0001")
    audit.append(
        case_id="CASE-2024-0001", run_id=run.run_id,
        event_type=AuditEventType.RUN_STARTED, actor_type=ActorType.SYSTEM,
        actor_id="runtime", operation="start",
    )
    audit.validate()
