"""Deterministic in-memory Person/Entity Registry model.

The registry owns persistent subject identity and identity-to-case mappings. It
is deliberately independent of tax documents, Drive access, and case data.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from threading import RLock


class RecordType(str, Enum):
    PERSON = "PERSON"
    ENTITY = "ENTITY"


class RegistryStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"
    UNRESOLVED = "UNRESOLVED"


class ResolutionStatus(str, Enum):
    NOT_FOUND = "NOT_FOUND"
    RESOLVED = "RESOLVED"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True, slots=True)
class PersonRecord:
    person_id: str
    status: RegistryStatus
    preferred_display_name: str | None
    created_at: datetime
    updated_at: datetime
    schema_version: int
    lookup_attributes: tuple[tuple[str, str], ...] = ()

    @property
    def record_type(self) -> RecordType:
        return RecordType.PERSON

    def __post_init__(self) -> None:
        _validate_identity_record(
            self.person_id,
            self.created_at,
            self.updated_at,
            self.schema_version,
        )


@dataclass(frozen=True, slots=True)
class EntityRecord:
    entity_id: str
    status: RegistryStatus
    preferred_display_name: str | None
    created_at: datetime
    updated_at: datetime
    schema_version: int
    lookup_attributes: tuple[tuple[str, str], ...] = ()

    @property
    def record_type(self) -> RecordType:
        return RecordType.ENTITY

    def __post_init__(self) -> None:
        _validate_identity_record(
            self.entity_id,
            self.created_at,
            self.updated_at,
            self.schema_version,
        )


@dataclass(frozen=True, slots=True)
class IdentityLookupResult:
    status: ResolutionStatus
    identity_ids: tuple[str, ...]

    @property
    def identity_id(self) -> str:
        if self.status is not ResolutionStatus.RESOLVED:
            raise LookupError(f"lookup is {self.status.value.lower()}")
        return self.identity_ids[0]


@dataclass(frozen=True, slots=True)
class CaseAssociation:
    identity_id: str
    case_id: str


def _validate_identity_record(
    identity_id: str,
    created_at: datetime,
    updated_at: datetime,
    schema_version: int,
) -> None:
    if not identity_id.strip():
        raise ValueError("identity id is required")
    if schema_version < 1:
        raise ValueError("schema_version must be >= 1")
    if created_at.tzinfo is None or updated_at.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    if updated_at < created_at:
        raise ValueError("updated_at cannot precede created_at")


class PersonEntityRegistry:
    """Deterministic registry with separate PERSON and ENTITY namespaces."""

    def __init__(self, *, schema_version: int = 1) -> None:
        if schema_version < 1:
            raise ValueError("schema_version must be >= 1")
        self._schema_version = schema_version
        self._persons: dict[str, PersonRecord] = {}
        self._entities: dict[str, EntityRecord] = {}
        self._case_associations: set[CaseAssociation] = set()
        self._lock = RLock()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def register_person(self, record: PersonRecord) -> PersonRecord:
        with self._lock:
            if record.person_id in self._persons:
                raise ValueError(f"person_id already exists: {record.person_id}")
            if record.person_id in self._entities:
                raise ValueError("identity id cannot be shared across PERSON and ENTITY")
            self._persons[record.person_id] = record
            return record

    def register_entity(self, record: EntityRecord) -> EntityRecord:
        with self._lock:
            if record.entity_id in self._entities:
                raise ValueError(f"entity_id already exists: {record.entity_id}")
            if record.entity_id in self._persons:
                raise ValueError("identity id cannot be shared across PERSON and ENTITY")
            self._entities[record.entity_id] = record
            return record

    def get_person(self, person_id: str) -> PersonRecord | None:
        with self._lock:
            return self._persons.get(person_id)

    def get_entity(self, entity_id: str) -> EntityRecord | None:
        with self._lock:
            return self._entities.get(entity_id)

    def resolve_person(self, person_id: str) -> IdentityLookupResult:
        with self._lock:
            return _lookup((person_id,) if person_id in self._persons else ())

    def resolve_entity(self, entity_id: str) -> IdentityLookupResult:
        with self._lock:
            return _lookup((entity_id,) if entity_id in self._entities else ())

    def find_person_by_attribute(self, key: str, value: str) -> IdentityLookupResult:
        return self._find(self._persons.values(), key, value)

    def find_entity_by_attribute(self, key: str, value: str) -> IdentityLookupResult:
        return self._find(self._entities.values(), key, value)

    def associate_case(self, identity_id: str, case_id: str) -> CaseAssociation:
        if not identity_id.strip() or not case_id.strip():
            raise ValueError("identity_id and case_id are required")
        with self._lock:
            if identity_id not in self._persons and identity_id not in self._entities:
                raise KeyError(f"unknown identity_id: {identity_id}")
            association = CaseAssociation(identity_id, case_id)
            self._case_associations.add(association)
            return association

    def list_cases(self, identity_id: str) -> tuple[str, ...]:
        with self._lock:
            return tuple(
                sorted(
                    association.case_id
                    for association in self._case_associations
                    if association.identity_id == identity_id
                )
            )

    def update_person_status(self, person_id: str, status: RegistryStatus) -> PersonRecord:
        with self._lock:
            record = self._persons.get(person_id)
            if record is None:
                raise KeyError(f"unknown person_id: {person_id}")
            updated = replace(record, status=status, updated_at=self._now())
            self._persons[person_id] = updated
            return updated

    def update_entity_status(self, entity_id: str, status: RegistryStatus) -> EntityRecord:
        with self._lock:
            record = self._entities.get(entity_id)
            if record is None:
                raise KeyError(f"unknown entity_id: {entity_id}")
            updated = replace(record, status=status, updated_at=self._now())
            self._entities[entity_id] = updated
            return updated

    def all_persons(self) -> tuple[PersonRecord, ...]:
        with self._lock:
            return tuple(sorted(self._persons.values(), key=lambda record: record.person_id))

    def all_entities(self) -> tuple[EntityRecord, ...]:
        with self._lock:
            return tuple(sorted(self._entities.values(), key=lambda record: record.entity_id))

    def validate(self) -> None:
        with self._lock:
            for association in self._case_associations:
                if association.identity_id not in self._persons and association.identity_id not in self._entities:
                    raise ValueError(f"association references unknown identity: {association.identity_id}")

    @staticmethod
    def _find(records, key: str, value: str) -> IdentityLookupResult:
        matches = tuple(
            sorted(
                record.person_id if isinstance(record, PersonRecord) else record.entity_id
                for record in records
                if any(attribute_key == key and attribute_value == value for attribute_key, attribute_value in record.lookup_attributes)
            )
        )
        return _lookup(matches)


def _lookup(identity_ids: tuple[str, ...]) -> IdentityLookupResult:
    if not identity_ids:
        return IdentityLookupResult(ResolutionStatus.NOT_FOUND, ())
    if len(identity_ids) > 1:
        return IdentityLookupResult(ResolutionStatus.AMBIGUOUS, identity_ids)
    return IdentityLookupResult(ResolutionStatus.RESOLVED, identity_ids)
