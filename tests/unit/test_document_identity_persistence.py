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
from agent_lab.document_identity import DocumentIdentityError, DocumentIdentityRegistry
from agent_lab.document_inventory import DocumentInventoryItem


def build_registry() -> CaseRegistry:
    registry = CaseRegistry()
    now = datetime.now(timezone.utc)
    for case_id, year, root in (("CASE-001", 2024, "root-1"), ("CASE-002", 2025, "root-2")):
        registry.register(CaseRecord(
            case_id=case_id,
            owner_type=OwnerType.PERSON,
            owner_id="PERSON-001",
            tax_period=TaxPeriod("CALENDAR_YEAR", year),
            case_type=CaseType.INDIVIDUAL,
            assessment_mode="UNKNOWN_PENDING_VERIFICATION",
            lifecycle_status=LifecycleStatus.CREATED,
            storage_scope_reference=StorageScopeReference("google_drive", root),
            schema_version=1,
            created_at=now,
            updated_at=now,
        ))
    return registry


def test_snapshot_round_trip_preserves_logical_identity(tmp_path) -> None:
    registry = build_registry()
    state = CaseStateStore(registry)
    run = state.create_run("CASE-001", request_id="persistence-test").run_id
    identity = DocumentIdentityRegistry(registry, state)
    item = DocumentInventoryItem("drive-1", "a.pdf", "application/pdf", ("root-1",), False)

    record, observation = identity.resolve_inventory_item(
        "CASE-001", run, item, source_provider="google_drive", source_scope_ref="root-1"
    )
    path = tmp_path / "identity.json"
    identity.save_snapshot("CASE-001", path)

    restored = DocumentIdentityRegistry(registry, state)
    restored.load_snapshot("CASE-001", path)
    restored_record = restored.get("CASE-001", record.document_id)

    assert restored_record == record
    assert restored.observations_for_document("CASE-001", record.document_id)[0] == observation

    next_run = state.create_run("CASE-001", request_id="persistence-test-2").run_id
    next_record, _ = restored.resolve_inventory_item(
        "CASE-001", next_run, item, source_provider="google_drive", source_scope_ref="root-1"
    )
    assert next_record.document_id == record.document_id


def test_snapshot_rejects_cross_case_payload(tmp_path) -> None:
    registry = build_registry()
    state = CaseStateStore(registry)
    run = state.create_run("CASE-001", request_id="cross-case").run_id
    identity = DocumentIdentityRegistry(registry, state)
    item = DocumentInventoryItem("drive-1", "a.pdf", "application/pdf", ("root-1",), False)
    identity.resolve_inventory_item("CASE-001", run, item, source_provider="google_drive", source_scope_ref="root-1")
    payload = identity.export_snapshot("CASE-001")

    with pytest.raises(DocumentIdentityError):
        identity.import_snapshot("CASE-002", payload)


def test_snapshot_rejects_observation_for_unknown_document() -> None:
    registry = build_registry()
    state = CaseStateStore(registry)
    identity = DocumentIdentityRegistry(registry, state)
    payload = {
        "schema_version": 1,
        "case_id": "CASE-001",
        "sequence": 1,
        "observation_sequence": 1,
        "records": [],
        "observations": [{
            "observation_id": "OBS-CASE-001-00000001",
            "document_id": "DOC-CASE-001-00000001",
            "case_id": "CASE-001",
            "run_id": "RUN-00000001",
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "source_provider": "google_drive",
            "source_object_id": "drive-1",
            "source_scope_ref": "root-1",
            "name": "a.pdf",
            "mime_type": "application/pdf",
            "parent_ids": ["root-1"],
            "is_folder": False,
            "source_status": "ACTIVE",
        }],
    }
    with pytest.raises(DocumentIdentityError):
        identity.import_snapshot("CASE-001", payload)
