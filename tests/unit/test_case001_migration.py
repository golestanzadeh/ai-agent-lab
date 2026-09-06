from datetime import datetime, timezone

import pytest

from agent_lab.audit import AuditStore
from agent_lab.case001_migration import (
    Case001MigrationCompatibility,
    DocumentMigrationMapping,
    MigrationCompatibilityError,
    MigrationStatus,
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
            storage_scope_reference=StorageScopeReference("google_drive", "legacy-root"),
            schema_version=1,
            created_at=now,
            updated_at=now,
        )
    )
    return registry


def make_identity(registry: CaseRegistry, object_ids: tuple[str, ...]) -> tuple[CaseStateStore, DocumentIdentityRegistry, tuple[str, ...]]:
    state = CaseStateStore(registry)
    run_id = state.create_run("CASE-001", request_id="migration-test").run_id
    identity = DocumentIdentityRegistry(registry, state)
    document_ids = []
    for object_id in object_ids:
        record, _ = identity.resolve_inventory_item(
            "CASE-001",
            run_id,
            DocumentInventoryItem(object_id, f"{object_id}.pdf", "application/pdf", ("legacy",), False),
            source_provider="google_drive",
            source_scope_ref="legacy",
        )
        document_ids.append(record.document_id)
    return state, identity, tuple(document_ids)


def make_inventory_evidence(
    registry: CaseRegistry,
    state: CaseStateStore,
    identity: DocumentIdentityRegistry,
    object_ids: tuple[str, ...],
) -> tuple[InventoryEvidenceStore, object]:
    audit = AuditStore(registry, state)
    store = InventoryEvidenceStore(registry, state, audit)
    run_id = state.list_runs("CASE-001")[0].run_id
    inventory = DocumentInventory(
        case_id="CASE-001",
        generated_at=datetime(2026, 9, 6, tzinfo=timezone.utc),
        items=tuple(
            DocumentInventoryItem(object_id, f"{object_id}.pdf", "application/pdf", ("legacy",), False)
            for object_id in object_ids
        ),
    )
    evidence = store.record(
        "CASE-001",
        run_id,
        inventory,
        source_provider="google_drive",
        source_scope_ref="legacy",
        document_identity=identity,
    )
    return store, evidence


def test_prepare_preserves_case_and_tax_period():
    service = Case001MigrationCompatibility(make_registry())
    plan = service.prepare(source_scope_ref="legacy-documents", target_scope_ref="2024-documents")
    assert plan.case_id == "CASE-001"
    assert plan.tax_period.year == 2024
    assert plan.status is MigrationStatus.PREPARED


def test_validate_marks_plan_validated():
    service = Case001MigrationCompatibility(make_registry())
    plan = service.prepare(source_scope_ref="legacy-documents", target_scope_ref="2024-documents")
    validated = service.validate(plan)
    assert validated.status is MigrationStatus.VALIDATED


def test_document_mapping_preserves_logical_identity():
    service = Case001MigrationCompatibility(make_registry())
    mapping = DocumentMigrationMapping(
        "google_drive", "object-1", "DOC-CASE-001-00000001", "legacy", "target"
    )
    plan = service.prepare(source_scope_ref="legacy", target_scope_ref="target", mappings=(mapping,))
    validated = service.validate(plan)
    assert validated.mappings[0].logical_document_id == "DOC-CASE-001-00000001"


def test_duplicate_source_object_fails_closed():
    service = Case001MigrationCompatibility(make_registry())
    mappings = (
        DocumentMigrationMapping("google_drive", "object-1", "DOC-1", "legacy", "target"),
        DocumentMigrationMapping("google_drive", "object-1", "DOC-2", "legacy", "target"),
    )
    plan = service.prepare(source_scope_ref="legacy", target_scope_ref="target", mappings=mappings)
    with pytest.raises(MigrationCompatibilityError, match="duplicate source object"):
        service.validate(plan)


def test_duplicate_logical_document_fails_closed():
    service = Case001MigrationCompatibility(make_registry())
    mappings = (
        DocumentMigrationMapping("google_drive", "object-1", "DOC-1", "legacy", "target"),
        DocumentMigrationMapping("google_drive", "object-2", "DOC-1", "legacy", "target"),
    )
    plan = service.prepare(source_scope_ref="legacy", target_scope_ref="target", mappings=mappings)
    with pytest.raises(MigrationCompatibilityError, match="duplicate logical document"):
        service.validate(plan)


def test_mapping_scope_mismatch_fails_closed():
    service = Case001MigrationCompatibility(make_registry())
    mapping = DocumentMigrationMapping("google_drive", "object-1", "DOC-1", "other", "target")
    plan = service.prepare(source_scope_ref="legacy", target_scope_ref="target", mappings=(mapping,))
    with pytest.raises(MigrationCompatibilityError, match="source scope mismatch"):
        service.validate(plan)


def test_unregistered_case_cannot_be_migrated():
    registry = CaseRegistry()
    service = Case001MigrationCompatibility(registry)
    with pytest.raises(MigrationCompatibilityError, match="not registered"):
        service.prepare(source_scope_ref="legacy", target_scope_ref="target")


def test_non_2024_case_cannot_be_migrated():
    registry = make_registry()
    now = datetime.now(timezone.utc)
    registry = CaseRegistry()
    registry.register(
        CaseRecord(
            case_id="CASE-001",
            owner_type=OwnerType.PERSON,
            owner_id="PERSON-001",
            tax_period=TaxPeriod("CALENDAR_YEAR", 2025),
            case_type=CaseType.INDIVIDUAL,
            assessment_mode=AssessmentMode.UNKNOWN_PENDING_VERIFICATION,
            lifecycle_status=LifecycleStatus.CREATED,
            storage_scope_reference=StorageScopeReference("google_drive", "legacy-root"),
            schema_version=1,
            created_at=now,
            updated_at=now,
        )
    )
    service = Case001MigrationCompatibility(registry)
    with pytest.raises(MigrationCompatibilityError, match="2024 case"):
        service.prepare(source_scope_ref="legacy", target_scope_ref="target")


def test_identity_registry_is_authoritative_for_mapping_identity():
    registry = make_registry()
    state, identity, document_ids = make_identity(registry, ("object-1",))
    service = Case001MigrationCompatibility(registry, identity)
    mapping = DocumentMigrationMapping("google_drive", "object-1", document_ids[0], "legacy", "target")
    plan = service.prepare(source_scope_ref="legacy", target_scope_ref="target", mappings=(mapping,))
    assert service.validate(plan).status is MigrationStatus.VALIDATED
    assert state.list_runs("CASE-001")[0].case_id == "CASE-001"


def test_unregistered_logical_document_fails_closed_when_identity_is_connected():
    registry = make_registry()
    _, identity, _ = make_identity(registry, ("object-1",))
    service = Case001MigrationCompatibility(registry, identity)
    mapping = DocumentMigrationMapping("google_drive", "object-1", "DOC-CASE-001-99999999", "legacy", "target")
    plan = service.prepare(source_scope_ref="legacy", target_scope_ref="target", mappings=(mapping,))
    with pytest.raises(MigrationCompatibilityError, match="logical document is not registered"):
        service.validate(plan)


def test_identity_object_mismatch_fails_closed():
    registry = make_registry()
    _, identity, document_ids = make_identity(registry, ("object-1",))
    service = Case001MigrationCompatibility(registry, identity)
    mapping = DocumentMigrationMapping("google_drive", "object-2", document_ids[0], "legacy", "target")
    plan = service.prepare(source_scope_ref="legacy", target_scope_ref="target", mappings=(mapping,))
    with pytest.raises(MigrationCompatibilityError, match="document identity object mismatch"):
        service.validate(plan)


def test_migration_mapping_must_match_inventory_evidence_and_identity_links():
    registry = make_registry()
    state, identity, document_ids = make_identity(registry, ("object-1", "object-2"))
    _, evidence = make_inventory_evidence(registry, state, identity, ("object-1", "object-2"))
    service = Case001MigrationCompatibility(registry, identity)
    mappings = tuple(
        DocumentMigrationMapping("google_drive", object_id, document_id, "legacy", "target")
        for object_id, document_id in zip(("object-1", "object-2"), document_ids)
    )
    plan = service.prepare(source_scope_ref="legacy", target_scope_ref="target", mappings=mappings)
    validated = service.validate(plan, inventory_evidence=evidence)
    assert validated.status is MigrationStatus.VALIDATED
    assert evidence.document_identity_refs == document_ids


def test_migration_rejects_inventory_evidence_from_another_scope():
    registry = make_registry()
    state, identity, document_ids = make_identity(registry, ("object-1",))
    _, evidence = make_inventory_evidence(registry, state, identity, ("object-1",))
    service = Case001MigrationCompatibility(registry, identity)
    mapping = DocumentMigrationMapping("google_drive", "object-1", document_ids[0], "legacy", "target")
    plan = service.prepare(source_scope_ref="other-scope", target_scope_ref="target", mappings=(mapping,))
    with pytest.raises(MigrationCompatibilityError, match="inventory evidence source scope mismatch"):
        service.validate(plan, inventory_evidence=evidence)
