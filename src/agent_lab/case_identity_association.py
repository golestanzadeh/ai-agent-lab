"""Deterministic bridge between persistent identities and tax cases.

This module validates the boundary between Person/Entity Registry and Case
Registry. It never reads case documents or storage contents.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock

from agent_lab.case_registry import CaseRegistry, OwnerType
from agent_lab.person_entity_registry import PersonEntityRegistry


@dataclass(frozen=True, slots=True)
class AssociationResult:
    identity_id: str
    case_id: str
    owner_type: OwnerType


class CaseIdentityAssociationService:
    """Associate identities with existing cases only after deterministic checks."""

    def __init__(
        self,
        identity_registry: PersonEntityRegistry,
        case_registry: CaseRegistry,
    ) -> None:
        self._identity_registry = identity_registry
        self._case_registry = case_registry
        self._associations: set[tuple[str, str]] = set()
        self._lock = RLock()

    def associate(self, identity_id: str, case_id: str) -> AssociationResult:
        if not identity_id.strip() or not case_id.strip():
            raise ValueError("identity_id and case_id are required")

        with self._lock:
            person = self._identity_registry.get_person(identity_id)
            entity = self._identity_registry.get_entity(identity_id)
            if person is None and entity is None:
                raise KeyError(f"unknown identity_id: {identity_id}")
            if person is not None and entity is not None:
                raise ValueError("identity cannot resolve to both PERSON and ENTITY")

            case = self._case_registry.get(case_id)
            if case is None:
                raise KeyError(f"unknown case_id: {case_id}")

            expected_owner_type = OwnerType.PERSON if person is not None else OwnerType.ENTITY
            if case.owner_type is not expected_owner_type:
                raise ValueError(
                    "identity type does not match case owner_type"
                )
            if case.owner_id != identity_id:
                raise ValueError(
                    "identity_id does not match case owner_id"
                )

            self._associations.add((identity_id, case_id))
            return AssociationResult(identity_id, case_id, case.owner_type)

    def list_cases(self, identity_id: str) -> tuple[str, ...]:
        with self._lock:
            return tuple(
                sorted(
                    case_id
                    for associated_identity, case_id in self._associations
                    if associated_identity == identity_id
                )
            )

    def validate(self) -> None:
        """Validate every association against both registries."""
        with self._lock:
            for identity_id, case_id in self._associations:
                person = self._identity_registry.get_person(identity_id)
                entity = self._identity_registry.get_entity(identity_id)
                case = self._case_registry.get(case_id)
                if case is None:
                    raise ValueError(f"association references unknown case: {case_id}")
                if (person is None) == (entity is None):
                    raise ValueError(f"association has invalid identity: {identity_id}")
                expected = OwnerType.PERSON if person is not None else OwnerType.ENTITY
                if case.owner_type is not expected or case.owner_id != identity_id:
                    raise ValueError(
                        f"association does not match case owner: {identity_id} -> {case_id}"
                    )
