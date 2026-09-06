from datetime import datetime, timezone

import pytest

from agent_lab.case001_migration import Case001MigrationCompatibility, MigrationCompatibilityError
from agent_lab.case_registry import (
    CaseRecord,
    CaseRegistry,
    CaseType,
    LifecycleStatus,
    OwnerType,
    StorageScopeReference,
    TaxPeriod,
)


def test_migration_source_scope_must_match_registered_case_scope() -> None:
    registry = CaseRegistry()
    now = datetime.now(timezone.utc)
    registry.register(CaseRecord(
        case_id="CASE-001",
        owner_type=OwnerType.PERSON,
        owner_id="PERSON-001",
        tax_period=TaxPeriod("CALENDAR_YEAR", 2024),
        case_type=CaseType.INDIVIDUAL,
        assessment_mode="UNKNOWN_PENDING_VERIFICATION",
        lifecycle_status=LifecycleStatus.CREATED,
        storage_scope_reference=StorageScopeReference("google_drive", "registered-root"),
        schema_version=1,
        created_at=now,
        updated_at=now,
    ))

    compatibility = Case001MigrationCompatibility(registry)
    with pytest.raises(MigrationCompatibilityError):
        compatibility.prepare(
            source_scope_ref="google_drive:unrelated-root",
            target_scope_ref="google_drive:target-root",
        )


def test_migration_source_scope_accepts_exact_registered_scope() -> None:
    registry = CaseRegistry()
    now = datetime.now(timezone.utc)
    registry.register(CaseRecord(
        case_id="CASE-001",
        owner_type=OwnerType.PERSON,
        owner_id="PERSON-001",
        tax_period=TaxPeriod("CALENDAR_YEAR", 2024),
        case_type=CaseType.INDIVIDUAL,
        assessment_mode="UNKNOWN_PENDING_VERIFICATION",
        lifecycle_status=LifecycleStatus.CREATED,
        storage_scope_reference=StorageScopeReference("google_drive", "registered-root"),
        schema_version=1,
        created_at=now,
        updated_at=now,
    ))

    plan = Case001MigrationCompatibility(registry).prepare(
        source_scope_ref="google_drive:registered-root",
        target_scope_ref="google_drive:target-root",
    )
    assert plan.source_scope_ref == "google_drive:registered-root"
