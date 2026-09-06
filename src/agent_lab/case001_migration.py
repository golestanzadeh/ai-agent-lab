"""Deterministic CASE-001 migration/compatibility planning.

This module prepares and validates a migration plan between the legacy and
future CASE-001 storage scopes. It deliberately performs no physical storage
mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agent_lab.case_registry import CaseRegistry, TaxPeriod


class MigrationStatus(str, Enum):
    PREPARED = "PREPARED"
    VALIDATED = "VALIDATED"


class MigrationCompatibilityError(RuntimeError):
    """Base error for fail-closed migration planning."""


@dataclass(frozen=True, slots=True)
class DocumentMigrationMapping:
    source_provider: str
    source_object_id: str
    logical_document_id: str
    source_scope_ref: str
    target_scope_ref: str

    def __post_init__(self) -> None:
        values = (
            self.source_provider,
            self.source_object_id,
            self.logical_document_id,
            self.source_scope_ref,
            self.target_scope_ref,
        )
        if any(not value.strip() for value in values):
            raise ValueError("migration mapping fields are required")


@dataclass(frozen=True, slots=True)
class Case001MigrationPlan:
    case_id: str
    tax_period: TaxPeriod
    source_scope_ref: str
    target_scope_ref: str
    mappings: tuple[DocumentMigrationMapping, ...] = ()
    status: MigrationStatus = MigrationStatus.PREPARED

    def __post_init__(self) -> None:
        if self.case_id != "CASE-001":
            raise ValueError("CASE-001 migration plan requires case_id CASE-001")
        if self.tax_period.year != 2024:
            raise ValueError("CASE-001 migration plan requires tax period 2024")
        if not self.source_scope_ref.strip() or not self.target_scope_ref.strip():
            raise ValueError("source and target scope references are required")
        if self.source_scope_ref == self.target_scope_ref:
            raise ValueError("source and target scopes must differ")


class Case001MigrationCompatibility:
    """Prepare and validate CASE-001 migration plans without storage mutation."""

    def __init__(self, case_registry: CaseRegistry) -> None:
        self._case_registry = case_registry

    def prepare(
        self,
        *,
        source_scope_ref: str,
        target_scope_ref: str,
        mappings: tuple[DocumentMigrationMapping, ...] = (),
    ) -> Case001MigrationPlan:
        case = self._case_registry.get("CASE-001")
        if case is None:
            raise MigrationCompatibilityError("CASE-001 is not registered")
        if case.tax_period.year != 2024:
            raise MigrationCompatibilityError("CASE-001 is not a 2024 case")
        if not source_scope_ref.strip() or not target_scope_ref.strip():
            raise ValueError("source and target scope references are required")
        return Case001MigrationPlan(
            case_id=case.case_id,
            tax_period=case.tax_period,
            source_scope_ref=source_scope_ref,
            target_scope_ref=target_scope_ref,
            mappings=tuple(mappings),
        )

    def validate(self, plan: Case001MigrationPlan) -> Case001MigrationPlan:
        case = self._case_registry.get(plan.case_id)
        if case is None:
            raise MigrationCompatibilityError("case is not registered")
        if case.tax_period != plan.tax_period:
            raise MigrationCompatibilityError("migration changes tax period")
        if plan.case_id != "CASE-001":
            raise MigrationCompatibilityError("unexpected case_id")

        source_objects: set[tuple[str, str]] = set()
        logical_documents: set[str] = set()
        for mapping in plan.mappings:
            if mapping.source_scope_ref != plan.source_scope_ref:
                raise MigrationCompatibilityError("mapping source scope mismatch")
            if mapping.target_scope_ref != plan.target_scope_ref:
                raise MigrationCompatibilityError("mapping target scope mismatch")
            source_key = (mapping.source_provider, mapping.source_object_id)
            if source_key in source_objects:
                raise MigrationCompatibilityError("duplicate source object mapping")
            if mapping.logical_document_id in logical_documents:
                raise MigrationCompatibilityError("duplicate logical document mapping")
            source_objects.add(source_key)
            logical_documents.add(mapping.logical_document_id)

        return Case001MigrationPlan(
            case_id=plan.case_id,
            tax_period=plan.tax_period,
            source_scope_ref=plan.source_scope_ref,
            target_scope_ref=plan.target_scope_ref,
            mappings=plan.mappings,
            status=MigrationStatus.VALIDATED,
        )
