"""Deterministic CASE-001 migration manifest generation.

The manifest is derived from a case-scoped inventory plus the existing logical
Document Identity registry. It performs no physical storage mutation.
"""

from __future__ import annotations

from dataclasses import dataclass

from agent_lab.artifact_identity import ArtifactIdentity, build_artifact_identity
from agent_lab.case001_migration import (
    Case001MigrationCompatibility,
    Case001MigrationPlan,
    DocumentMigrationMapping,
    MigrationStatus,
)
from agent_lab.case_registry import CaseRegistry
from agent_lab.document_identity import DocumentIdentityRegistry, SourceStatus
from agent_lab.document_inventory import DocumentInventory
from agent_lab.inventory_evidence import InventoryEvidence


class MigrationManifestError(RuntimeError):
    """Base error for fail-closed manifest generation."""


@dataclass(frozen=True, slots=True)
class Case001MigrationManifest:
    """Immutable migration manifest for one CASE-001 source snapshot."""

    case_id: str
    tax_period_year: int
    source_provider: str
    source_scope_ref: str
    target_scope_ref: str
    mappings: tuple[DocumentMigrationMapping, ...]
    inventory_evidence_id: str | None = None

    def __post_init__(self) -> None:
        if self.case_id != "CASE-001":
            raise ValueError("manifest requires case_id CASE-001")
        if self.tax_period_year != 2024:
            raise ValueError("manifest requires tax period 2024")
        if not self.source_provider.strip() or not self.source_scope_ref.strip():
            raise ValueError("source provider and scope are required")
        if not self.target_scope_ref.strip() or self.target_scope_ref == self.source_scope_ref:
            raise ValueError("target scope must be present and differ from source scope")

    @property
    def document_count(self) -> int:
        return len(self.mappings)

    @property
    def artifact_identity(self) -> ArtifactIdentity:
        payload = {
            "case_id": self.case_id,
            "tax_period_year": self.tax_period_year,
            "source_provider": self.source_provider,
            "source_scope_ref": self.source_scope_ref,
            "target_scope_ref": self.target_scope_ref,
            "mappings": self.mappings,
            "inventory_evidence_id": self.inventory_evidence_id,
        }
        return build_artifact_identity(
            kind="CASE001_MIGRATION_MANIFEST",
            version="1",
            payload=payload,
        )


class Case001MigrationManifestGenerator:
    """Build and validate a CASE-001 manifest from existing case-scoped state."""

    def __init__(
        self,
        case_registry: CaseRegistry,
        document_identity: DocumentIdentityRegistry,
    ) -> None:
        self._case_registry = case_registry
        self._document_identity = document_identity

    def generate(
        self,
        inventory: DocumentInventory,
        *,
        source_provider: str,
        source_scope_ref: str,
        target_scope_ref: str,
        inventory_evidence: InventoryEvidence | None = None,
    ) -> Case001MigrationManifest:
        case = self._case_registry.get("CASE-001")
        if case is None:
            raise MigrationManifestError("CASE-001 is not registered")
        if case.tax_period.year != 2024:
            raise MigrationManifestError("CASE-001 is not a 2024 case")
        if inventory.case_id != "CASE-001":
            raise MigrationManifestError("inventory belongs to another case")
        if not source_provider.strip() or not source_scope_ref.strip() or not target_scope_ref.strip():
            raise ValueError("provider and scope references are required")
        if source_scope_ref == target_scope_ref:
            raise MigrationManifestError("source and target scopes must differ")

        mappings: list[DocumentMigrationMapping] = []
        for item in inventory.items:
            if item.is_folder:
                continue
            try:
                records = self._document_identity.list_for_case("CASE-001")
                record = next(r for r in records if r.source_provider == source_provider and r.source_object_id == item.object_id)
            except StopIteration as exc:
                raise MigrationManifestError("inventory document has no logical identity") from exc
            if record.source_scope_ref != source_scope_ref:
                raise MigrationManifestError("document identity source scope mismatch")
            if record.source_status is not SourceStatus.ACTIVE:
                raise MigrationManifestError("inactive document cannot enter migration manifest")
            mappings.append(
                DocumentMigrationMapping(
                    source_provider=source_provider,
                    source_object_id=item.object_id,
                    logical_document_id=record.document_id,
                    source_scope_ref=source_scope_ref,
                    target_scope_ref=target_scope_ref,
                )
            )

        manifest = Case001MigrationManifest(
            case_id="CASE-001",
            tax_period_year=2024,
            source_provider=source_provider,
            source_scope_ref=source_scope_ref,
            target_scope_ref=target_scope_ref,
            mappings=tuple(mappings),
            inventory_evidence_id=inventory_evidence.evidence_id if inventory_evidence else None,
        )

        plan = Case001MigrationCompatibility(
            self._case_registry, self._document_identity
        ).prepare(
            source_scope_ref=source_scope_ref,
            target_scope_ref=target_scope_ref,
            mappings=manifest.mappings,
        )
        if inventory_evidence is not None:
            if inventory_evidence.document_count != manifest.document_count:
                raise MigrationManifestError("inventory evidence document count mismatch")
            if inventory_evidence.folder_count != inventory.folder_count:
                raise MigrationManifestError("inventory evidence folder count mismatch")
        validated = Case001MigrationCompatibility(
            self._case_registry, self._document_identity
        ).validate(plan, inventory_evidence=inventory_evidence)
        if validated.status is not MigrationStatus.VALIDATED:
            raise MigrationManifestError("manifest preflight did not validate")
        return manifest
