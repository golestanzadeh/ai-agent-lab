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
from agent_lab.case_scoped_drive import (
    CaseNotFoundError,
    CaseScopedDriveResolver,
    OutOfScopeError,
)


def make_case(case_id: str, owner_id: str, root_id: str) -> CaseRecord:
    now = datetime.now(timezone.utc)
    return CaseRecord(
        case_id=case_id,
        owner_type=OwnerType.PERSON,
        owner_id=owner_id,
        tax_period=TaxPeriod("CALENDAR_YEAR", 2025),
        case_type=CaseType.INDIVIDUAL,
        assessment_mode=AssessmentMode.INDIVIDUAL_ASSESSMENT,
        lifecycle_status=LifecycleStatus.CREATED,
        storage_scope_reference=StorageScopeReference("memory", root_id),
        schema_version=1,
        created_at=now,
        updated_at=now,
    )


def test_resolve_returns_exact_registry_scope() -> None:
    registry = CaseRegistry()
    registry.register(make_case("CASE-2025-0001", "PERSON-1", "root-1"))

    resolved = CaseScopedDriveResolver(registry).resolve("CASE-2025-0001")

    assert resolved.case_id == "CASE-2025-0001"
    assert resolved.storage_scope == StorageScopeReference("memory", "root-1")


def test_unknown_case_fails_closed() -> None:
    with pytest.raises(CaseNotFoundError):
        CaseScopedDriveResolver(CaseRegistry()).resolve("CASE-2025-9999")


def test_empty_case_id_fails_closed() -> None:
    with pytest.raises(CaseNotFoundError):
        CaseScopedDriveResolver(CaseRegistry()).resolve("   ")


def test_different_storage_root_is_rejected() -> None:
    registry = CaseRegistry()
    registry.register(make_case("CASE-2025-0001", "PERSON-1", "root-1"))
    resolver = CaseScopedDriveResolver(registry)

    with pytest.raises(OutOfScopeError):
        resolver.assert_case_object(
            "CASE-2025-0001", StorageScopeReference("memory", "root-2")
        )


def test_same_storage_scope_is_accepted() -> None:
    registry = CaseRegistry()
    registry.register(make_case("CASE-2025-0001", "PERSON-1", "root-1"))
    resolver = CaseScopedDriveResolver(registry)

    resolver.assert_case_object(
        "CASE-2025-0001", StorageScopeReference("memory", "root-1")
    )


def test_storage_move_preserves_case_identity() -> None:
    registry = CaseRegistry()
    registry.register(make_case("CASE-2025-0001", "PERSON-1", "root-1"))
    registry.update_storage_scope(
        "CASE-2025-0001", StorageScopeReference("memory", "root-2")
    )

    resolved = CaseScopedDriveResolver(registry).resolve("CASE-2025-0001")

    assert resolved.case_id == "CASE-2025-0001"
    assert resolved.storage_scope.root_id == "root-2"


def test_resolver_never_selects_a_scope_independently_of_registry() -> None:
    registry = CaseRegistry()
    registry.register(make_case("CASE-2025-0001", "PERSON-1", "root-1"))
    resolver = CaseScopedDriveResolver(registry)

    with pytest.raises(OutOfScopeError):
        resolver.assert_case_object(
            "CASE-2025-0001", StorageScopeReference("memory", "invented-root")
        )


def test_two_cases_with_same_root_are_rejected_by_registry() -> None:
    registry = CaseRegistry()
    registry.register(make_case("CASE-2025-0001", "PERSON-1", "root-1"))
    registry.register(make_case("CASE-2026-0001", "PERSON-1", "root-1"))

    with pytest.raises(ValueError, match="storage root mapped to multiple cases"):
        registry.validate()
