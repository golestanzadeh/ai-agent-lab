"""Deterministic CASE-001 migration/compatibility planning."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agent_lab.case_registry import CaseRegistry, TaxPeriod
from agent_lab.document_identity import DocumentIdentityNotFoundError, DocumentIdentityRegistry
from agent_lab.inventory_evidence import InventoryEvidence


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
        values = (self.source_provider, self.source_object_id, self.logical_document_id,
                  self.source_scope_ref, self.target_scope_ref)
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

    def __init__(self, case_registry: CaseRegistry,
                 document_identity: DocumentIdentityRegistry | None = None) -> None:
        self._case_registry = case_registry
        self._document_identity = document_identity

    def prepare(self, *, source_scope_ref: str, target_scope_ref: str,
                mappings: tuple[DocumentMigrationMapping, ...] = ()) -> Case001MigrationPlan:
        case = self._case_registry.get("CASE-001")
        if case is None:
            raise MigrationCompatibilityError("CASE-001 is not registered")
        if case.tax_period.year != 2024:
            raise MigrationCompatibilityError("CASE-001 is not a 2024 case")
        if not source_scope_ref.strip() or not target_scope_ref.strip():
            raise ValueError("source and target scope references are required")
        registered_scope = f"{case.storage_scope_reference.provider}:{case.storage_scope_reference.root_id}"
        if source_scope_ref != registered_scope:
            raise MigrationCompatibilityError("migration source scope is not the registered CASE-001 scope")
        return Case001MigrationPlan(case.case_id, case.tax_period, source_scope_ref,
                                    target_scope_ref, tuple(mappings))

    def validate(self, plan: Case001MigrationPlan, *,
                 inventory_evidence: InventoryEvidence | None = None) -> Case001MigrationPlan:
        case = self._case_registry.get(plan.case_id)
        if case is None:
            raise MigrationCompatibilityError("case is not registered")
        if case.tax_period != plan.tax_period:
            raise MigrationCompatibilityError("migration changes tax period")
        if plan.case_id != "CASE-001":
            raise MigrationCompatibilityError("unexpected case_id")
        registered_scope = f"{case.storage_scope_reference.provider}:{case.storage_scope_reference.root_id}"
        if plan.source_scope_ref != registered_scope:
            raise MigrationCompatibilityError("migration source scope is not the registered CASE-001 scope")
        if inventory_evidence is not None:
            self._validate_inventory_evidence(plan, inventory_evidence)

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
            self._validate_document_identity(plan, mapping)
            source_objects.add(source_key)
            logical_documents.add(mapping.logical_document_id)

        return Case001MigrationPlan(plan.case_id, plan.tax_period, plan.source_scope_ref,
                                    plan.target_scope_ref, plan.mappings, MigrationStatus.VALIDATED)

    def _validate_document_identity(self, plan: Case001MigrationPlan,
                                    mapping: DocumentMigrationMapping) -> None:
        if self._document_identity is None:
            return
        try:
            record = self._document_identity.get(plan.case_id, mapping.logical_document_id)
        except DocumentIdentityNotFoundError as exc:
            raise MigrationCompatibilityError("logical document is not registered") from exc
        if record.case_id != plan.case_id:
            raise MigrationCompatibilityError("document identity belongs to another case")
        if record.source_provider != mapping.source_provider:
            raise MigrationCompatibilityError("document identity provider mismatch")
        if record.source_object_id != mapping.source_object_id:
            raise MigrationCompatibilityError("document identity object mismatch")
        if record.source_scope_ref != mapping.source_scope_ref:
            raise MigrationCompatibilityError("document identity source scope mismatch")

    @staticmethod
    def _validate_inventory_evidence(plan: Case001MigrationPlan,
                                     inventory_evidence: InventoryEvidence) -> None:
        if inventory_evidence.case_id != plan.case_id:
            raise MigrationCompatibilityError("inventory evidence belongs to another case")
        if inventory_evidence.source_scope_ref != plan.source_scope_ref:
            raise MigrationCompatibilityError("inventory evidence source scope mismatch")
        if inventory_evidence.source_provider != "google_drive":
            raise MigrationCompatibilityError("unsupported inventory evidence provider")
        mapped_objects = tuple((m.source_provider, m.source_object_id) for m in plan.mappings)
        expected_objects = tuple((inventory_evidence.source_provider, object_id)
                                 for object_id in inventory_evidence.item_refs)
        if mapped_objects != expected_objects:
            raise MigrationCompatibilityError("migration mappings do not match inventory evidence")
        mapped_ids = tuple(m.logical_document_id for m in plan.mappings)
        if mapped_ids != inventory_evidence.document_identity_refs:
            raise MigrationCompatibilityError("migration logical documents do not match inventory evidence")
