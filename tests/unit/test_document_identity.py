from datetime import datetime, timezone

import pytest

from agent_lab.case_registry import (
    CaseRecord,
    CaseRegistry,
    CaseType,
    LifecycleStatus,
    OwnerType,
    StorageScopeReference,
    TaxPeriod,
)
from agent_lab.case_state import CaseStateStore
from agent_lab.document_identity import (
    DocumentIdentityNotFoundError,
    DocumentIdentityRegistry,
    SourceStatus,
)
from agent_lab.document_inventory import DocumentInventoryItem


def build_case_registry() -> CaseRegistry:
    registry = CaseRegistry()
    now = datetime.now(timezone.utc)
    registry.register(
        CaseRecord(
            case_id="CASE-001",
            owner_type=OwnerType.PERSON,
            owner_id="PERSON-001",
            tax_period=TaxPeriod("CALENDAR_YEAR", 2024),
            case_type=CaseType.INDIVIDUAL,
            assessment_mode="UNKNOWN_PENDING_VERIFICATION",
            lifecycle_status=LifecycleStatus.CREATED,
            storage_scope_reference=StorageScopeReference("google_drive", "root-1"),
            schema_version=1,
            created_at=now,
            updated_at=now,
        )
    )
    registry.register(
        CaseRecord(
            case_id="CASE-002",
            owner_type=OwnerType.PERSON,
            owner_id="PERSON-001",
            tax_period=TaxPeriod("CALENDAR_YEAR", 2025),
            case_type=CaseType.INDIVIDUAL,
            assessment_mode="UNKNOWN_PENDING_VERIFICATION",
            lifecycle_status=LifecycleStatus.CREATED,
            storage_scope_reference=StorageScopeReference("google_drive", "root-2"),
            schema_version=1,
            created_at=now,
            updated_at=now,
        )
    )
    return registry


def make_run(case_state: CaseStateStore, case_id: str) -> str:
    return case_state.create_run(case_id, request_id=f"request-{case_id}").run_id


def item(object_id: str, name: str) -> DocumentInventoryItem:
    return DocumentInventoryItem(object_id, name, "application/pdf", ("root-1",), False)


def test_same_source_object_is_idempotent_logical_identity() -> None:
    registry = build_case_registry()
    state = CaseStateStore(registry)
    run1 = make_run(state, "CASE-001")
    run2 = make_run(state, "CASE-001")
    identity = DocumentIdentityRegistry(registry, state)

    first, observation1 = identity.resolve_inventory_item(
        "CASE-001", run1, item("drive-1", "a.pdf"), source_provider="google_drive", source_scope_ref="root-1"
    )
    second, observation2 = identity.resolve_inventory_item(
        "CASE-001", run2, item("drive-1", "a.pdf"), source_provider="google_drive", source_scope_ref="root-1"
    )

    assert first.document_id == second.document_id
    assert observation1.document_id == observation2.document_id
    assert len(identity.list_for_case("CASE-001")) == 1
    assert len(identity.observations_for_document("CASE-001", first.document_id)) == 2


def test_same_name_different_object_creates_separate_identity() -> None:
    registry = build_case_registry()
    state = CaseStateStore(registry)
    run_id = make_run(state, "CASE-001")
    identity = DocumentIdentityRegistry(registry, state)

    first, _ = identity.resolve_inventory_item("CASE-001", run_id, item("drive-1", "same.pdf"), source_provider="google_drive", source_scope_ref="root-1")
    second, _ = identity.resolve_inventory_item("CASE-001", run_id, item("drive-2", "same.pdf"), source_provider="google_drive", source_scope_ref="root-1")

    assert first.document_id != second.document_id
    assert len(identity.list_for_case("CASE-001")) == 2


def test_rename_same_object_preserves_identity_and_updates_metadata() -> None:
    registry = build_case_registry()
    state = CaseStateStore(registry)
    run_id = make_run(state, "CASE-001")
    identity = DocumentIdentityRegistry(registry, state)

    first, _ = identity.resolve_inventory_item("CASE-001", run_id, item("drive-1", "old.pdf"), source_provider="google_drive", source_scope_ref="root-1")
    second, _ = identity.resolve_inventory_item("CASE-001", run_id, item("drive-1", "new.pdf"), source_provider="google_drive", source_scope_ref="root-1")

    assert first.document_id == second.document_id
    assert second.current_name == "new.pdf"
    assert second.source_status is SourceStatus.ACTIVE


def test_cross_case_lookup_fails_closed() -> None:
    registry = build_case_registry()
    state = CaseStateStore(registry)
    run_id = make_run(state, "CASE-001")
    identity = DocumentIdentityRegistry(registry, state)

    record, _ = identity.resolve_inventory_item("CASE-001", run_id, item("drive-1", "a.pdf"), source_provider="google_drive", source_scope_ref="root-1")

    with pytest.raises(DocumentIdentityNotFoundError):
        identity.get("CASE-002", record.document_id)


def test_cross_case_resolution_cannot_reuse_foreign_run() -> None:
    registry = build_case_registry()
    state = CaseStateStore(registry)
    run_id = make_run(state, "CASE-001")
    identity = DocumentIdentityRegistry(registry, state)

    with pytest.raises(PermissionError):
        identity.resolve_inventory_item("CASE-002", run_id, item("drive-2", "b.pdf"), source_provider="google_drive", source_scope_ref="root-2")


def test_unknown_case_fails_closed() -> None:
    registry = build_case_registry()
    state = CaseStateStore(registry)
    identity = DocumentIdentityRegistry(registry, state)

    with pytest.raises(Exception):
        identity.list_for_case("CASE-999")
