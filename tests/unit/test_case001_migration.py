from datetime import datetime, timezone

import pytest

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
    case = registry.get("CASE-001")
    assert case is not None
    registry = CaseRegistry()
    now = datetime.now(timezone.utc)
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
