from datetime import datetime, timezone

import pytest

from agent_lab.person_entity_registry import (
    EntityRecord,
    IdentityLookupResult,
    PersonEntityRegistry,
    PersonRecord,
    RegistryStatus,
    ResolutionStatus,
)


def ts() -> datetime:
    return datetime(2026, 1, 1, tzinfo=timezone.utc)


def person(person_id: str, name: str, **attrs: str) -> PersonRecord:
    return PersonRecord(
        person_id=person_id,
        status=RegistryStatus.ACTIVE,
        preferred_display_name=name,
        created_at=ts(),
        updated_at=ts(),
        schema_version=1,
        lookup_attributes=tuple(sorted(attrs.items())),
    )


def entity(entity_id: str, name: str, **attrs: str) -> EntityRecord:
    return EntityRecord(
        entity_id=entity_id,
        status=RegistryStatus.ACTIVE,
        preferred_display_name=name,
        created_at=ts(),
        updated_at=ts(),
        schema_version=1,
        lookup_attributes=tuple(sorted(attrs.items())),
    )


def test_register_and_resolve_person() -> None:
    registry = PersonEntityRegistry()
    registry.register_person(person("PERSON-0001", "Alice"))

    result = registry.resolve_person("PERSON-0001")

    assert isinstance(result, IdentityLookupResult)
    assert result.status is ResolutionStatus.RESOLVED
    assert result.identity_id == "PERSON-0001"


def test_register_and_resolve_entity() -> None:
    registry = PersonEntityRegistry()
    registry.register_entity(entity("ENTITY-0001", "Example GmbH"))

    result = registry.resolve_entity("ENTITY-0001")

    assert result.status is ResolutionStatus.RESOLVED
    assert result.identity_id == "ENTITY-0001"


def test_person_and_entity_namespaces_are_distinct() -> None:
    registry = PersonEntityRegistry()
    registry.register_person(person("SUBJECT-0001", "Alice"))

    with pytest.raises(ValueError, match="cannot be shared"):
        registry.register_entity(entity("SUBJECT-0001", "Example GmbH"))


def test_duplicate_person_id_is_rejected() -> None:
    registry = PersonEntityRegistry()
    registry.register_person(person("PERSON-0001", "Alice"))

    with pytest.raises(ValueError, match="person_id already exists"):
        registry.register_person(person("PERSON-0001", "Alice Again"))


def test_attribute_lookup_resolves_exactly_one_person() -> None:
    registry = PersonEntityRegistry()
    registry.register_person(person("PERSON-0001", "Alice", reference="verified-001"))

    result = registry.find_person_by_attribute("reference", "verified-001")

    assert result.status is ResolutionStatus.RESOLVED
    assert result.identity_id == "PERSON-0001"


def test_attribute_lookup_reports_ambiguity_instead_of_guessing() -> None:
    registry = PersonEntityRegistry()
    registry.register_person(person("PERSON-0001", "Alice", name_key="same"))
    registry.register_person(person("PERSON-0002", "Bob", name_key="same"))

    result = registry.find_person_by_attribute("name_key", "same")

    assert result.status is ResolutionStatus.AMBIGUOUS
    assert result.identity_ids == ("PERSON-0001", "PERSON-0002")


def test_missing_identity_is_explicitly_not_found() -> None:
    registry = PersonEntityRegistry()

    result = registry.resolve_person("PERSON-404")

    assert result.status is ResolutionStatus.NOT_FOUND
    assert result.identity_ids == ()


def test_case_association_and_cross_year_case_listing() -> None:
    registry = PersonEntityRegistry()
    registry.register_person(person("PERSON-0001", "Alice"))
    registry.associate_case("PERSON-0001", "CASE-2024-0001")
    registry.associate_case("PERSON-0001", "CASE-2025-0007")

    assert registry.list_cases("PERSON-0001") == (
        "CASE-2024-0001",
        "CASE-2025-0007",
    )


def test_case_association_requires_known_identity() -> None:
    registry = PersonEntityRegistry()

    with pytest.raises(KeyError, match="unknown identity_id"):
        registry.associate_case("PERSON-404", "CASE-2025-0001")


def test_status_change_preserves_identity() -> None:
    registry = PersonEntityRegistry()
    registry.register_person(person("PERSON-0001", "Alice"))

    updated = registry.update_person_status("PERSON-0001", RegistryStatus.ARCHIVED)

    assert updated.person_id == "PERSON-0001"
    assert updated.status is RegistryStatus.ARCHIVED
    assert registry.resolve_person("PERSON-0001").identity_id == "PERSON-0001"


def test_validation_rejects_orphaned_case_association() -> None:
    registry = PersonEntityRegistry()
    registry.register_person(person("PERSON-0001", "Alice"))
    registry.associate_case("PERSON-0001", "CASE-2025-0001")

    registry._case_associations.add(
        type(next(iter(registry._case_associations))) (
            "PERSON-404", "CASE-2025-9999"
        )
    )

    with pytest.raises(ValueError, match="unknown identity"):
        registry.validate()
