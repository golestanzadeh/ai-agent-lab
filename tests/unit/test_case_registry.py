from datetime import datetime, timezone

import pytest

from agent_lab.case_registry import (
    AssessmentMode,
    CaseRecord,
    CaseRegistry,
    CaseType,
    LifecycleStatus,
    LookupStatus,
    OwnerType,
    StorageScopeReference,
    TaxPeriod,
)


def make_case(case_id: str, owner_id: str, year: int, root_id: str) -> CaseRecord:
    timestamp = datetime(2026, 9, 6, tzinfo=timezone.utc)
    return CaseRecord(
        case_id=case_id,
        owner_type=OwnerType.PERSON,
        owner_id=owner_id,
        tax_period=TaxPeriod("CALENDAR_YEAR", year),
        case_type=CaseType.INDIVIDUAL,
        assessment_mode=AssessmentMode.UNKNOWN_PENDING_VERIFICATION,
        lifecycle_status=LifecycleStatus.CREATED,
        storage_scope_reference=StorageScopeReference("google_drive", root_id),
        schema_version=1,
        created_at=timestamp,
        updated_at=timestamp,
    )


def test_register_and_resolve_by_case_id() -> None:
    registry = CaseRegistry()
    case = make_case("CASE-2025-0001", "PERSON-0001", 2025, "root-1")

    registry.register(case)

    result = registry.resolve_by_case_id(case.case_id)
    assert result.status is LookupStatus.RESOLVED
    assert result.case_id == case.case_id


def test_case_id_must_be_unique() -> None:
    registry = CaseRegistry()
    registry.register(make_case("CASE-2025-0001", "PERSON-0001", 2025, "root-1"))

    with pytest.raises(ValueError, match="case_id already exists"):
        registry.register(make_case("CASE-2025-0001", "PERSON-0002", 2025, "root-2"))


def test_owner_and_tax_period_lookup_is_deterministic() -> None:
    registry = CaseRegistry()
    registry.register(make_case("CASE-2024-0001", "PERSON-0001", 2024, "root-1"))
    registry.register(make_case("CASE-2025-0001", "PERSON-0001", 2025, "root-2"))

    result = registry.resolve_by_owner_and_period(
        "PERSON-0001", TaxPeriod("CALENDAR_YEAR", 2025)
    )
    assert result.status is LookupStatus.RESOLVED
    assert result.case_id == "CASE-2025-0001"


def test_ambiguous_lookup_never_guesses() -> None:
    registry = CaseRegistry()
    registry.register(make_case("CASE-2025-0001", "PERSON-0001", 2025, "root-1"))
    registry.register(make_case("CASE-2025-0002", "PERSON-0001", 2025, "root-2"))

    result = registry.resolve_by_owner_and_period(
        "PERSON-0001", TaxPeriod("CALENDAR_YEAR", 2025)
    )
    assert result.status is LookupStatus.AMBIGUOUS
    assert result.case_ids == ("CASE-2025-0001", "CASE-2025-0002")
    with pytest.raises(LookupError):
        _ = result.case_id


def test_cross_year_retrieval_returns_only_that_owner_cases() -> None:
    registry = CaseRegistry()
    registry.register(make_case("CASE-2024-0001", "PERSON-0001", 2024, "root-1"))
    registry.register(make_case("CASE-2025-0001", "PERSON-0001", 2025, "root-2"))
    registry.register(make_case("CASE-2025-0002", "PERSON-0002", 2025, "root-3"))

    history = registry.list_by_owner("PERSON-0001")
    assert [case.case_id for case in history] == ["CASE-2024-0001", "CASE-2025-0001"]


def test_storage_move_does_not_change_case_identity() -> None:
    registry = CaseRegistry()
    registry.register(make_case("CASE-2025-0001", "PERSON-0001", 2025, "root-1"))

    updated = registry.update_storage_scope(
        "CASE-2025-0001", StorageScopeReference("google_drive", "root-99")
    )

    assert updated.case_id == "CASE-2025-0001"
    assert updated.storage_scope_reference.root_id == "root-99"
    assert registry.resolve_by_case_id("CASE-2025-0001").case_id == "CASE-2025-0001"


def test_cross_case_update_is_rejected() -> None:
    registry = CaseRegistry()
    registry.register(make_case("CASE-2025-0001", "PERSON-0001", 2025, "root-1"))

    with pytest.raises(KeyError, match="unknown case_id"):
        registry.update_lifecycle("CASE-2025-9999", LifecycleStatus.ACTIVE)


def test_storage_root_cannot_be_shared_by_two_cases() -> None:
    registry = CaseRegistry()
    registry.register(make_case("CASE-2025-0001", "PERSON-0001", 2025, "root-1"))
    registry.register(make_case("CASE-2025-0002", "PERSON-0002", 2025, "root-2"))
    registry.update_storage_scope(
        "CASE-2025-0002", StorageScopeReference("google_drive", "root-1")
    )

    with pytest.raises(ValueError, match="storage root mapped to multiple cases"):
        registry.validate()


def test_request_id_is_idempotent() -> None:
    registry = CaseRegistry()
    case = make_case("CASE-2025-0001", "PERSON-0001", 2025, "root-1")

    first = registry.register(case, request_id="request-1")
    second = registry.register(case, request_id="request-1")

    assert first == second
    assert len(registry.all_records()) == 1


def test_invalid_tax_period_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported tax period type"):
        TaxPeriod("FISCAL_YEAR", 2025)

    with pytest.raises(ValueError, match="between 1900 and 9999"):
        TaxPeriod("CALENDAR_YEAR", 1899)
