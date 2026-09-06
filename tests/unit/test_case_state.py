from datetime import datetime, timezone

import pytest

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
from agent_lab.case_state import CaseStateStore, RunStatus


def make_registry() -> CaseRegistry:
    registry = CaseRegistry()
    now = datetime.now(timezone.utc)
    registry.register(
        CaseRecord(
            case_id="CASE-2024-0001",
            owner_type=OwnerType.PERSON,
            owner_id="PERSON-0001",
            tax_period=TaxPeriod("CALENDAR_YEAR", 2024),
            case_type=CaseType.INDIVIDUAL,
            assessment_mode=AssessmentMode.UNKNOWN_PENDING_VERIFICATION,
            lifecycle_status=LifecycleStatus.CREATED,
            storage_scope_reference=StorageScopeReference("memory", "root-1"),
            schema_version=1,
            created_at=now,
            updated_at=now,
        )
    )
    registry.register(
        CaseRecord(
            case_id="CASE-2025-0001",
            owner_type=OwnerType.PERSON,
            owner_id="PERSON-0001",
            tax_period=TaxPeriod("CALENDAR_YEAR", 2025),
            case_type=CaseType.INDIVIDUAL,
            assessment_mode=AssessmentMode.UNKNOWN_PENDING_VERIFICATION,
            lifecycle_status=LifecycleStatus.CREATED,
            storage_scope_reference=StorageScopeReference("memory", "root-2"),
            schema_version=1,
            created_at=now,
            updated_at=now,
        )
    )
    return registry


def test_initialize_requires_known_case_and_is_idempotent():
    store = CaseStateStore(make_registry())
    first = store.initialize_case("CASE-2024-0001")
    second = store.initialize_case("CASE-2024-0001")
    assert first == second
    assert first.lifecycle_status == "READY"


def test_unknown_case_fails_closed():
    store = CaseStateStore(make_registry())
    with pytest.raises(KeyError):
        store.initialize_case("CASE-9999-0001")


def test_create_run_binds_exactly_one_case():
    store = CaseStateStore(make_registry())
    run = store.create_run("CASE-2024-0001", request_id="req-1")
    assert run.run_id == "RUN-00000001"
    assert run.case_id == "CASE-2024-0001"
    assert run.status is RunStatus.CREATED


def test_run_request_is_idempotent_for_same_case():
    store = CaseStateStore(make_registry())
    first = store.create_run("CASE-2024-0001", request_id="req-1")
    second = store.create_run("CASE-2024-0001", request_id="req-1")
    assert first == second
    assert len(store.list_runs("CASE-2024-0001")) == 1


def test_request_id_cannot_cross_case_boundary():
    store = CaseStateStore(make_registry())
    store.create_run("CASE-2024-0001", request_id="req-1")
    with pytest.raises(ValueError):
        store.create_run("CASE-2025-0001", request_id="req-1")


def test_cross_case_run_read_is_rejected():
    store = CaseStateStore(make_registry())
    run = store.create_run("CASE-2024-0001")
    with pytest.raises(PermissionError):
        store.get_run("CASE-2025-0001", run.run_id)


def test_legal_run_transitions_are_enforced():
    store = CaseStateStore(make_registry())
    run = store.create_run("CASE-2024-0001")
    run = store.transition_run("CASE-2024-0001", run.run_id, RunStatus.RUNNING)
    assert run.status is RunStatus.RUNNING
    run = store.transition_run("CASE-2024-0001", run.run_id, RunStatus.SUCCEEDED)
    assert run.status is RunStatus.SUCCEEDED
    with pytest.raises(ValueError):
        store.transition_run("CASE-2024-0001", run.run_id, RunStatus.RUNNING)


def test_state_updates_are_case_scoped_and_can_reference_run():
    store = CaseStateStore(make_registry())
    run = store.create_run("CASE-2024-0001")
    state = store.update_state(
        "CASE-2024-0001",
        last_run_id=run.run_id,
        documents_ref="inventory-v1",
        evidence_ref="evidence-v1",
    )
    assert state.last_run_id == run.run_id
    assert state.documents_ref == "inventory-v1"
    assert state.evidence_ref == "evidence-v1"
    with pytest.raises(PermissionError):
        store.update_state("CASE-2025-0001", last_run_id=run.run_id)


def test_unknown_state_field_is_rejected():
    store = CaseStateStore(make_registry())
    store.initialize_case("CASE-2024-0001")
    with pytest.raises(ValueError):
        store.update_state("CASE-2024-0001", arbitrary_ref="bad")


def test_terminal_run_cannot_be_mutated():
    store = CaseStateStore(make_registry())
    run = store.create_run("CASE-2024-0001")
    store.transition_run("CASE-2024-0001", run.run_id, RunStatus.RUNNING)
    store.transition_run("CASE-2024-0001", run.run_id, RunStatus.FAILED)
    with pytest.raises(ValueError):
        store.transition_run("CASE-2024-0001", run.run_id, RunStatus.CANCELLED)


def test_runs_remain_separate_across_cases():
    store = CaseStateStore(make_registry())
    first = store.create_run("CASE-2024-0001")
    second = store.create_run("CASE-2025-0001")
    assert first.run_id != second.run_id
    assert store.list_runs("CASE-2024-0001") == (first,)
    assert store.list_runs("CASE-2025-0001") == (second,)


def test_store_validation_preserves_case_and_run_invariants():
    store = CaseStateStore(make_registry())
    run = store.create_run("CASE-2024-0001")
    store.update_state("CASE-2024-0001", last_run_id=run.run_id)
    store.validate()
