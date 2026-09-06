"""Acceptance tests for the mandatory cross-case isolation boundary."""

from datetime import datetime, timezone

import pytest

from agent_lab.audit import ActorType, AuditEventType, AuditStore, InvalidAuditEventError
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
from agent_lab.case_scoped_drive import CaseScopedDriveResolver, OutOfScopeError
from agent_lab.case_state import CaseStateStore


CASE_A = "CASE-2024-0001"
CASE_B = "CASE-2025-0001"


def make_case(case_id: str, year: int, root: str) -> CaseRecord:
    now = datetime.now(timezone.utc)
    return CaseRecord(
        case_id=case_id,
        owner_type=OwnerType.PERSON,
        owner_id="PERSON-0001",
        tax_period=TaxPeriod("CALENDAR_YEAR", year),
        case_type=CaseType.INDIVIDUAL,
        assessment_mode=AssessmentMode.INDIVIDUAL_ASSESSMENT,
        lifecycle_status=LifecycleStatus.CREATED,
        storage_scope_reference=StorageScopeReference("memory", root),
        schema_version=1,
        created_at=now,
        updated_at=now,
    )


def make_system() -> tuple[CaseRegistry, CaseStateStore, CaseScopedDriveResolver, AuditStore]:
    registry = CaseRegistry()
    registry.register(make_case(CASE_A, 2024, "root-a"))
    registry.register(make_case(CASE_B, 2025, "root-b"))
    state = CaseStateStore(registry)
    resolver = CaseScopedDriveResolver(registry)
    audit = AuditStore(registry, state)
    return registry, state, resolver, audit


def test_two_cases_have_distinct_storage_scopes():
    _, _, resolver, _ = make_system()
    assert resolver.resolve(CASE_A).storage_scope != resolver.resolve(CASE_B).storage_scope


def test_case_a_cannot_access_case_b_storage():
    _, _, resolver, _ = make_system()
    with pytest.raises(OutOfScopeError):
        resolver.assert_case_object(CASE_A, resolver.resolve(CASE_B).storage_scope)


def test_case_b_cannot_access_case_a_storage():
    _, _, resolver, _ = make_system()
    with pytest.raises(OutOfScopeError):
        resolver.assert_case_object(CASE_B, resolver.resolve(CASE_A).storage_scope)


def test_run_created_for_a_cannot_be_used_by_b():
    _, state, _, audit = make_system()
    run_a = state.create_run(CASE_A)
    with pytest.raises(InvalidAuditEventError):
        audit.append(
            case_id=CASE_B,
            run_id=run_a.run_id,
            event_type=AuditEventType.TOOL_CALLED,
            actor_type=ActorType.TOOL,
            actor_id="storage",
            operation="read",
        )


def test_case_a_audit_listing_never_returns_case_b_events():
    _, state, _, audit = make_system()
    run_a = state.create_run(CASE_A)
    run_b = state.create_run(CASE_B)
    audit.append(
        case_id=CASE_A, run_id=run_a.run_id,
        event_type=AuditEventType.RUN_STARTED, actor_type=ActorType.SYSTEM,
        actor_id="runtime", operation="start",
    )
    audit.append(
        case_id=CASE_B, run_id=run_b.run_id,
        event_type=AuditEventType.RUN_STARTED, actor_type=ActorType.SYSTEM,
        actor_id="runtime", operation="start",
    )
    events = audit.list_events(CASE_A)
    assert len(events) == 1
    assert all(event.case_id == CASE_A for event in events)
    assert all(event.run_id != run_b.run_id for event in events)


def test_case_a_cannot_read_case_b_audit_event():
    _, state, _, audit = make_system()
    run_b = state.create_run(CASE_B)
    event_b = audit.append(
        case_id=CASE_B, run_id=run_b.run_id,
        event_type=AuditEventType.ERROR_RECORDED, actor_type=ActorType.SYSTEM,
        actor_id="runtime", operation="error",
    )
    with pytest.raises(Exception):
        audit.get(CASE_A, event_b.event_id)


def test_case_state_lookup_is_case_bound():
    _, state, _, _ = make_system()
    run_a = state.create_run(CASE_A)
    assert state.get_run(CASE_A, run_a.run_id).case_id == CASE_A
    with pytest.raises(Exception):
        state.get_run(CASE_B, run_a.run_id)


def test_cross_case_storage_roots_are_rejected_if_same_root_is_introduced():
    registry = CaseRegistry()
    registry.register(make_case(CASE_A, 2024, "same-root"))
    registry.register(make_case(CASE_B, 2025, "same-root"))
    with pytest.raises(ValueError, match="storage root mapped to multiple cases"):
        registry.validate()


def test_unknown_case_cannot_enter_any_case_scoped_boundary():
    registry, state, resolver, audit = make_system()
    unknown = "CASE-2099-9999"
    with pytest.raises(Exception):
        resolver.resolve(unknown)
    with pytest.raises(Exception):
        state.create_run(unknown)
    with pytest.raises(Exception):
        audit.append(
            case_id=unknown, run_id=None,
            event_type=AuditEventType.ERROR_RECORDED,
            actor_type=ActorType.SYSTEM, actor_id="runtime", operation="error",
        )


def test_case_ids_remain_distinct_even_for_same_persistent_owner():
    registry, _, _, _ = make_system()
    records = registry.list_by_owner("PERSON-0001")
    assert tuple(record.case_id for record in records) == (CASE_A, CASE_B)
    assert records[0].tax_period != records[1].tax_period
