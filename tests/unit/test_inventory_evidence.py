from datetime import datetime, timezone

import pytest

from agent_lab.audit import AuditStore
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
from agent_lab.document_identity import DocumentIdentityRegistry
from agent_lab.document_inventory import DocumentInventory, DocumentInventoryItem
from agent_lab.inventory_evidence import (
    InventoryEvidenceError,
    InventoryEvidenceNotFoundError,
    InventoryEvidenceStore,
)


def _case(case_id: str, root: str) -> CaseRecord:
    return CaseRecord(
        case_id=case_id,
        owner_type=OwnerType.PERSON,
        owner_id=f"owner-{case_id}",
        tax_period=TaxPeriod("CALENDAR_YEAR", 2024),
        case_type=CaseType.INDIVIDUAL,
        assessment_mode=AssessmentMode.UNKNOWN_PENDING_VERIFICATION,
        lifecycle_status=LifecycleStatus.CREATED,
        storage_scope_reference=StorageScopeReference("test", root),
        schema_version=1,
        created_at=datetime(2026, 9, 6, tzinfo=timezone.utc),
        updated_at=datetime(2026, 9, 6, tzinfo=timezone.utc),
    )


def _inventory(case_id: str, object_ids: tuple[str, ...]) -> DocumentInventory:
    items = tuple(
        DocumentInventoryItem(
            object_id=object_id,
            name=f"doc-{object_id}.pdf",
            mime_type="application/pdf",
            parent_ids=("root",),
            is_folder=False,
        )
        for object_id in object_ids
    )
    return DocumentInventory(
        case_id=case_id,
        generated_at=datetime(2026, 9, 6, tzinfo=timezone.utc),
        items=items,
    )


def _store() -> tuple[CaseRegistry, CaseStateStore, AuditStore, InventoryEvidenceStore]:
    registry = CaseRegistry()
    registry.register(_case("CASE-A", "root-a"))
    registry.register(_case("CASE-B", "root-b"))
    state = CaseStateStore(registry)
    state.create_run("CASE-A")
    state.create_run("CASE-B")
    audit = AuditStore(registry, state)
    return registry, state, audit, InventoryEvidenceStore(registry, state, audit)


def test_record_is_case_scoped_and_updates_case_state() -> None:
    _, state, audit, store = _store()
    run = state.list_runs("CASE-A")[0]

    evidence = store.record(
        "CASE-A",
        run.run_id,
        _inventory("CASE-A", ("1", "2")),
        source_provider="test",
        source_scope_ref="root-a",
    )

    assert evidence.case_id == "CASE-A"
    assert evidence.document_count == 2
    assert evidence.folder_count == 0
    assert state.get_state("CASE-A").evidence_ref == evidence.evidence_id
    assert audit.list_events("CASE-A", run.run_id)[0].evidence_refs == (evidence.evidence_id,)


def test_same_logical_snapshot_is_idempotent() -> None:
    _, state, _, store = _store()
    run = state.list_runs("CASE-A")[0]
    inventory = _inventory("CASE-A", ("1", "2"))

    first = store.record("CASE-A", run.run_id, inventory, source_provider="test", source_scope_ref="root-a")
    second = store.record("CASE-A", run.run_id, inventory, source_provider="test", source_scope_ref="root-a")

    assert second == first
    assert len(store.list_for_case("CASE-A")) == 1


def test_inventory_from_another_case_is_rejected() -> None:
    _, state, _, store = _store()
    run = state.list_runs("CASE-A")[0]

    with pytest.raises(InventoryEvidenceError):
        store.record(
            "CASE-A",
            run.run_id,
            _inventory("CASE-B", ("1",)),
            source_provider="test",
            source_scope_ref="root-a",
        )


def test_run_from_another_case_is_rejected() -> None:
    _, state, _, store = _store()
    foreign_run = state.list_runs("CASE-B")[0]

    with pytest.raises(PermissionError):
        store.record(
            "CASE-A",
            foreign_run.run_id,
            _inventory("CASE-A", ("1",)),
            source_provider="test",
            source_scope_ref="root-a",
        )


def test_evidence_cannot_be_read_from_another_case() -> None:
    _, state, _, store = _store()
    run = state.list_runs("CASE-A")[0]
    evidence = store.record(
        "CASE-A",
        run.run_id,
        _inventory("CASE-A", ("1",)),
        source_provider="test",
        source_scope_ref="root-a",
    )

    with pytest.raises(InventoryEvidenceNotFoundError):
        store.get("CASE-B", evidence.evidence_id)


def test_inventory_evidence_links_logical_document_identity() -> None:
    registry, state, audit, store = _store()
    run = state.list_runs("CASE-A")[0]
    identity = DocumentIdentityRegistry(registry, state)

    evidence = store.record(
        "CASE-A",
        run.run_id,
        _inventory("CASE-A", ("1", "2")),
        source_provider="test",
        source_scope_ref="root-a",
        document_identity=identity,
    )

    records = identity.list_for_case("CASE-A")
    assert evidence.document_identity_refs == tuple(record.document_id for record in records)
    assert len(evidence.document_identity_refs) == 2
    assert all(ref.startswith("DOC-CASE-A-") for ref in evidence.document_identity_refs)
    assert audit.list_events("CASE-A", run.run_id)[0].metadata["document_identity_refs"] == evidence.document_identity_refs


def test_inventory_evidence_identity_links_are_case_scoped() -> None:
    registry, state, _, store = _store()
    run_a = state.list_runs("CASE-A")[0]
    identity = DocumentIdentityRegistry(registry, state)

    evidence = store.record(
        "CASE-A",
        run_a.run_id,
        _inventory("CASE-A", ("1",)),
        source_provider="test",
        source_scope_ref="root-a",
        document_identity=identity,
    )

    foreign_run = state.list_runs("CASE-B")[0]
    with pytest.raises(PermissionError):
        store.record(
            "CASE-A",
            foreign_run.run_id,
            _inventory("CASE-A", ("1",)),
            source_provider="test",
            source_scope_ref="root-a",
            document_identity=identity,
        )

    assert evidence.case_id == "CASE-A"
    assert all(ref.startswith("DOC-CASE-A-") for ref in evidence.document_identity_refs)
