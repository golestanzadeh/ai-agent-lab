from datetime import datetime, timezone

import pytest

from agent_lab.case001_migration_manifest import (
    Case001MigrationManifestGenerator,
    MigrationManifestError,
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
from agent_lab.document_identity import DocumentIdentityRegistry
from agent_lab.document_inventory import DocumentInventory, DocumentInventoryItem
from agent_lab.inventory_evidence import InventoryEvidenceStore
from agent_lab.audit import AuditStore


def make_registry() -> CaseRegistry:
    registry = CaseRegistry()
    now = datetime.now(timezone.utc)
    registry.register(
        CaseRecord(
            case_id="CASE-001",
            owner_type=OwnerType.PERSON,
            owner_id="PERSON-001",
            tax_period=TaxPeriod("CALENDAR_YEAR", 2024),
            case_type=CaseType.INDIVIDUAL,
            assessment_mode=AssessmentMode.UNKNOWN_PENDING_VERIFICATION,
            lifecycle_status=LifecycleStatus.CREATED,
            storage_scope_reference=StorageScopeReference("google_drive", "legacy"),
            schema_version=1,
            created_at=now,
            updated_at=now,
        )
    )
    return registry


def make_context(object_ids: tuple[str, ...]):
    registry = make_registry()
    state = CaseStateStore(registry)
    run_id = state.create_run("CASE-001", request_id="manifest-test").run_id
    identity = DocumentIdentityRegistry(registry, state)
    items = []
    for object_id in object_ids:
        item = DocumentInventoryItem(object_id, f"{object_id}.pdf", "application/pdf", ("legacy",), False)
        identity.resolve_inventory_item(
            "CASE-001", run_id, item, source_provider="google_drive", source_scope_ref="legacy"
        )
        items.append(item)
    inventory = DocumentInventory("CASE-001", datetime.now(timezone.utc), tuple(items))
    return registry, state, identity, inventory, run_id


def test_generator_creates_manifest_from_inventory_and_identity():
    registry, state, identity, inventory, _ = make_context(("object-1", "object-2"))
    generator = Case001MigrationManifestGenerator(registry, identity)
    manifest = generator.generate(
        inventory,
        source_provider="google_drive",
        source_scope_ref="legacy",
        target_scope_ref="target-2024",
    )
    assert manifest.case_id == "CASE-001"
    assert manifest.tax_period_year == 2024
    assert manifest.document_count == 2
    assert tuple(m.source_object_id for m in manifest.mappings) == ("object-1", "object-2")
    assert tuple(m.logical_document_id for m in manifest.mappings) == (
        "DOC-CASE-001-00000001",
        "DOC-CASE-001-00000002",
    )
    assert state.list_runs("CASE-001")


def test_generator_records_evidence_reference_without_mutating_storage():
    registry, state, identity, inventory, run_id = make_context(("object-1",))
    evidence_store = InventoryEvidenceStore(registry, state, AuditStore(registry, state))
    evidence = evidence_store.record(
        "CASE-001", run_id, inventory,
        source_provider="google_drive", source_scope_ref="legacy",
        document_identity=identity,
    )
    generator = Case001MigrationManifestGenerator(registry, identity)
    manifest = generator.generate(
        inventory,
        source_provider="google_drive",
        source_scope_ref="legacy",
        target_scope_ref="target-2024",
        inventory_evidence=evidence,
    )
    assert manifest.inventory_evidence_id == evidence.evidence_id
    assert manifest.document_count == evidence.document_count


def test_generator_rejects_inventory_document_without_identity():
    registry, _, identity, _, _ = make_context(("object-1",))
    inventory = DocumentInventory(
        "CASE-001",
        datetime.now(timezone.utc),
        (DocumentInventoryItem("object-2", "object-2.pdf", "application/pdf", ("legacy",), False),),
    )
    generator = Case001MigrationManifestGenerator(registry, identity)
    with pytest.raises(MigrationManifestError, match="no logical identity"):
        generator.generate(
            inventory,
            source_provider="google_drive",
            source_scope_ref="legacy",
            target_scope_ref="target-2024",
        )


def test_generator_excludes_folders_from_document_mappings():
    registry, _, identity, _, _ = make_context(("object-1",))
    inventory = DocumentInventory(
        "CASE-001",
        datetime.now(timezone.utc),
        (
            DocumentInventoryItem("folder-1", "Folder", "application/vnd.google-apps.folder", ("legacy",), True),
            DocumentInventoryItem("object-1", "object-1.pdf", "application/pdf", ("legacy",), False),
        ),
    )
    generator = Case001MigrationManifestGenerator(registry, identity)
    manifest = generator.generate(
        inventory,
        source_provider="google_drive",
        source_scope_ref="legacy",
        target_scope_ref="target-2024",
    )
    assert manifest.document_count == 1


def test_generator_rejects_wrong_case_inventory():
    registry, _, identity, _, _ = make_context(("object-1",))
    inventory = DocumentInventory(
        "CASE-002",
        datetime.now(timezone.utc),
        (DocumentInventoryItem("object-1", "object-1.pdf", "application/pdf", ("legacy",), False),),
    )
    generator = Case001MigrationManifestGenerator(registry, identity)
    with pytest.raises(MigrationManifestError, match="another case"):
        generator.generate(
            inventory,
            source_provider="google_drive",
            source_scope_ref="legacy",
            target_scope_ref="target-2024",
        )


def test_generator_rejects_source_scope_mismatch():
    registry, _, identity, inventory, _ = make_context(("object-1",))
    generator = Case001MigrationManifestGenerator(registry, identity)
    with pytest.raises(MigrationManifestError, match="source scope mismatch"):
        generator.generate(
            inventory,
            source_provider="google_drive",
            source_scope_ref="wrong-source",
            target_scope_ref="target-2024",
        )
