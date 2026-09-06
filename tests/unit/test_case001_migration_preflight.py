from dataclasses import replace

import pytest

from agent_lab.case001_migration import DocumentMigrationMapping
from agent_lab.case001_migration_manifest import Case001MigrationManifest
from agent_lab.case001_migration_preflight import (
    Case001MigrationPreflight,
    MigrationPreflightError,
)


SOURCE = "google_drive:legacy-root"
TARGET = "google_drive:target-root"


def manifest() -> Case001MigrationManifest:
    mappings = tuple(
        DocumentMigrationMapping(
            source_provider="google_drive",
            source_object_id=f"source-{index}",
            logical_document_id=f"DOC-CASE-001-{index:08d}",
            source_scope_ref=SOURCE,
            target_scope_ref=TARGET,
        )
        for index in range(1, 16)
    )
    return Case001MigrationManifest(
        case_id="CASE-001",
        tax_period_year=2024,
        source_provider="google_drive",
        source_scope_ref=SOURCE,
        target_scope_ref=TARGET,
        mappings=mappings,
    )


def test_passes_for_actual_empty_target() -> None:
    result = Case001MigrationPreflight().run(
        manifest(), target_scope_is_actual=True, target_is_empty=True
    )
    assert result.preflight_passed is True
    assert result.document_count == 15
    assert result.source_objects_unique is True
    assert result.logical_documents_unique is True


def test_rejects_planned_target() -> None:
    with pytest.raises(MigrationPreflightError, match="actual storage scope"):
        Case001MigrationPreflight().run(
            manifest(), target_scope_is_actual=False, target_is_empty=True
        )


def test_rejects_non_empty_target() -> None:
    with pytest.raises(MigrationPreflightError, match="not empty"):
        Case001MigrationPreflight().run(
            manifest(), target_scope_is_actual=True, target_is_empty=False
        )


def test_rejects_duplicate_source_object() -> None:
    current = manifest()
    duplicate = replace(
        current.mappings[1], source_object_id=current.mappings[0].source_object_id
    )
    bad = replace(current, mappings=(current.mappings[0], duplicate, *current.mappings[2:]))
    with pytest.raises(MigrationPreflightError, match="duplicate source object"):
        Case001MigrationPreflight().run(
            bad, target_scope_is_actual=True, target_is_empty=True
        )


def test_rejects_duplicate_logical_document() -> None:
    current = manifest()
    duplicate = replace(
        current.mappings[1], logical_document_id=current.mappings[0].logical_document_id
    )
    bad = replace(current, mappings=(current.mappings[0], duplicate, *current.mappings[2:]))
    with pytest.raises(MigrationPreflightError, match="duplicate logical document"):
        Case001MigrationPreflight().run(
            bad, target_scope_is_actual=True, target_is_empty=True
        )


def test_rejects_empty_manifest() -> None:
    current = replace(manifest(), mappings=())
    with pytest.raises(MigrationPreflightError, match="no documents"):
        Case001MigrationPreflight().run(
            current, target_scope_is_actual=True, target_is_empty=True
        )
