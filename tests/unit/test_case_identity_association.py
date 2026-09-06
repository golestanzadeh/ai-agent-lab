from datetime import datetime, timezone

import pytest

from agent_lab.case_identity_association import CaseIdentityAssociationService
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
from agent_lab.person_entity_registry import (
    EntityRecord,
    PersonEntityRegistry,
    PersonRecord,
    RegistryStatus,
)


def ts() -> datetime:
    return datetime(2026, 1, 1, tzinfo=timezone.utc)


def person(person_id: str) -> PersonRecord:
    return PersonRecord(
        person_id=person_id,
        status=RegistryStatus.ACTIVE,
        preferred_display_name="Test Person",
        created_at=ts(),
        updated_at=ts(),
        schema_version=1,
    )


def entity(entity_id: str) -> EntityRecord:
    return EntityRecord(
        entity_id=entity_id,
        status=RegistryStatus.ACTIVE,
        preferred_display_name="Test GmbH",
        created_at=ts(),
        updated_at=ts(),
        schema_version=1,
    )


def case(
    case_id: str,
    owner_type: OwnerType,
    owner_id: str,
    year: int = 2025,
) -> CaseRecord:
    return CaseRecord(
        case_id=case_id,
        owner_type=owner_type,
        owner_id=owner_id,
        tax_period=TaxPeriod("CALENDAR_YEAR", year),
        case_type=(
            CaseType.INDIVIDUAL
            if owner_type is OwnerType.PERSON
            else CaseType.LEGAL_ENTITY
        ),
        assessment_mode=(
            AssessmentMode.INDIVIDUAL_ASSESSMENT
            if owner_type is OwnerType.PERSON
            else AssessmentMode.NOT_APPLICABLE
        ),
        lifecycle_status=LifecycleStatus.CREATED,
        storage_scope_reference=StorageScopeReference("drive", case_id),
        schema_version=1,
        created_at=ts(),
        updated_at=ts(),
    )


def service() -> tuple[PersonEntityRegistry, CaseRegistry, CaseIdentityAssociationService]:
    identities = PersonEntityRegistry()
    cases = CaseRegistry()
    return identities, cases, CaseIdentityAssociationService(identities, cases)


def test_person_case_association_requires_matching_owner() -> None:
    identities, cases, associations = service()
    identities.register_person(person("PERSON-0001"))
    cases.register(case("CASE-2025-0001", OwnerType.PERSON, "PERSON-0001"))

    result = associations.associate("PERSON-0001", "CASE-2025-0001")

    assert result.identity_id == "PERSON-0001"
    assert result.case_id == "CASE-2025-0001"
    assert result.owner_type is OwnerType.PERSON
    assert associations.list_cases("PERSON-0001") == ("CASE-2025-0001",)


def test_entity_case_association_requires_matching_owner() -> None:
    identities, cases, associations = service()
    identities.register_entity(entity("ENTITY-0001"))
    cases.register(case("CASE-2025-0001", OwnerType.ENTITY, "ENTITY-0001"))

    result = associations.associate("ENTITY-0001", "CASE-2025-0001")

    assert result.owner_type is OwnerType.ENTITY
    assert associations.list_cases("ENTITY-0001") == ("CASE-2025-0001",)


def test_unknown_identity_is_rejected() -> None:
    _, cases, associations = service()
    cases.register(case("CASE-2025-0001", OwnerType.PERSON, "PERSON-0001"))

    with pytest.raises(KeyError, match="unknown identity_id"):
        associations.associate("PERSON-404", "CASE-2025-0001")


def test_unknown_case_is_rejected() -> None:
    identities, _, associations = service()
    identities.register_person(person("PERSON-0001"))

    with pytest.raises(KeyError, match="unknown case_id"):
        associations.associate("PERSON-0001", "CASE-404")


def test_person_cannot_associate_to_entity_case() -> None:
    identities, cases, associations = service()
    identities.register_person(person("PERSON-0001"))
    cases.register(case("CASE-2025-0001", OwnerType.ENTITY, "ENTITY-0001"))

    with pytest.raises(ValueError, match="identity type"):
        associations.associate("PERSON-0001", "CASE-2025-0001")


def test_identity_must_match_case_owner_id() -> None:
    identities, cases, associations = service()
    identities.register_person(person("PERSON-0001"))
    identities.register_person(person("PERSON-0002"))
    cases.register(case("CASE-2025-0001", OwnerType.PERSON, "PERSON-0001"))

    with pytest.raises(ValueError, match="case owner_id"):
        associations.associate("PERSON-0002", "CASE-2025-0001")


def test_same_association_is_idempotent() -> None:
    identities, cases, associations = service()
    identities.register_person(person("PERSON-0001"))
    cases.register(case("CASE-2025-0001", OwnerType.PERSON, "PERSON-0001"))

    first = associations.associate("PERSON-0001", "CASE-2025-0001")
    second = associations.associate("PERSON-0001", "CASE-2025-0001")

    assert first == second
    assert associations.list_cases("PERSON-0001") == ("CASE-2025-0001",)


def test_one_person_can_have_multiple_year_cases() -> None:
    identities, cases, associations = service()
    identities.register_person(person("PERSON-0001"))
    cases.register(case("CASE-2024-0001", OwnerType.PERSON, "PERSON-0001", 2024))
    cases.register(case("CASE-2025-0001", OwnerType.PERSON, "PERSON-0001", 2025))
    cases.register(case("CASE-2026-0001", OwnerType.PERSON, "PERSON-0001", 2026))

    for case_id in ("CASE-2024-0001", "CASE-2025-0001", "CASE-2026-0001"):
        associations.associate("PERSON-0001", case_id)

    assert associations.list_cases("PERSON-0001") == (
        "CASE-2024-0001",
        "CASE-2025-0001",
        "CASE-2026-0001",
    )


def test_validation_checks_both_registries() -> None:
    identities, cases, associations = service()
    identities.register_person(person("PERSON-0001"))
    cases.register(case("CASE-2025-0001", OwnerType.PERSON, "PERSON-0001"))
    associations.associate("PERSON-0001", "CASE-2025-0001")

    associations.validate()
