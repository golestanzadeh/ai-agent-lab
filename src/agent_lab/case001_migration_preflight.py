"""Deterministic, non-mutating CASE-001 physical migration preflight."""

from __future__ import annotations

from dataclasses import dataclass

from agent_lab.case001_migration import DocumentMigrationMapping
from agent_lab.case001_migration_manifest import Case001MigrationManifest


class MigrationPreflightError(RuntimeError):
    """Base error for fail-closed physical migration preflight."""


@dataclass(frozen=True, slots=True)
class MigrationPreflightResult:
    """Immutable result of structural preflight checks."""

    case_id: str
    tax_period_year: int
    document_count: int
    source_scope_ref: str
    target_scope_ref: str
    target_scope_is_actual: bool
    target_is_empty: bool
    mapping_count_matches: bool
    source_objects_unique: bool
    logical_documents_unique: bool
    preflight_passed: bool


class Case001MigrationPreflight:
    """Validate execution prerequisites without performing storage writes."""

    def run(
        self,
        manifest: Case001MigrationManifest,
        *,
        target_scope_is_actual: bool,
        target_is_empty: bool,
    ) -> MigrationPreflightResult:
        if manifest.case_id != "CASE-001":
            raise MigrationPreflightError("unexpected case_id")
        if manifest.tax_period_year != 2024:
            raise MigrationPreflightError("unexpected tax period")
        if not manifest.mappings:
            raise MigrationPreflightError("migration manifest contains no documents")
        if not manifest.source_scope_ref.strip() or not manifest.target_scope_ref.strip():
            raise MigrationPreflightError("source and target scopes are required")
        if manifest.source_scope_ref == manifest.target_scope_ref:
            raise MigrationPreflightError("source and target scopes must differ")

        source_keys = tuple(
            (mapping.source_provider, mapping.source_object_id)
            for mapping in manifest.mappings
        )
        logical_ids = tuple(mapping.logical_document_id for mapping in manifest.mappings)
        source_objects_unique = len(source_keys) == len(set(source_keys))
        logical_documents_unique = len(logical_ids) == len(set(logical_ids))
        mapping_count_matches = manifest.document_count == len(manifest.mappings)

        if not source_objects_unique:
            raise MigrationPreflightError("duplicate source object in manifest")
        if not logical_documents_unique:
            raise MigrationPreflightError("duplicate logical document in manifest")
        if not mapping_count_matches:
            raise MigrationPreflightError("manifest document count mismatch")
        if not target_scope_is_actual:
            raise MigrationPreflightError("target scope is not an actual storage scope")
        if not target_is_empty:
            raise MigrationPreflightError("target scope is not empty")

        return MigrationPreflightResult(
            case_id=manifest.case_id,
            tax_period_year=manifest.tax_period_year,
            document_count=manifest.document_count,
            source_scope_ref=manifest.source_scope_ref,
            target_scope_ref=manifest.target_scope_ref,
            target_scope_is_actual=target_scope_is_actual,
            target_is_empty=target_is_empty,
            mapping_count_matches=mapping_count_matches,
            source_objects_unique=source_objects_unique,
            logical_documents_unique=logical_documents_unique,
            preflight_passed=True,
        )
