from __future__ import annotations

from dataclasses import replace

import pytest

from agent_lab.case001_live_target_preflight import (
    GoogleDriveLiveTargetScopePreflight,
    LiveTargetPreflightError,
)
from agent_lab.case001_migration import DocumentMigrationMapping
from agent_lab.case001_migration_manifest import Case001MigrationManifest


class FakeRequest:
    def __init__(self, payload):
        self.payload = payload

    def execute(self):
        return self.payload


class FakeFiles:
    def __init__(self, metadata, children):
        self.metadata = metadata
        self.children = children

    def get(self, **kwargs):
        return FakeRequest(self.metadata)

    def list(self, **kwargs):
        return FakeRequest({"files": self.children})


class FakeDrive:
    def __init__(self, metadata, children):
        self._files = FakeFiles(metadata, children)

    def files(self):
        return self._files


FOLDER_MIME = "application/vnd.google-apps.folder"


def manifest() -> Case001MigrationManifest:
    mapping = DocumentMigrationMapping(
        source_provider="google_drive",
        source_object_id="source-1",
        logical_document_id="DOC-CASE-001-00000001",
        source_scope_ref="google_drive:legacy-root",
        target_scope_ref="google_drive:target-root",
    )
    return Case001MigrationManifest(
        case_id="CASE-001",
        tax_period_year=2024,
        source_provider="google_drive",
        source_scope_ref="google_drive:legacy-root",
        target_scope_ref="google_drive:target-root",
        mappings=(mapping,),
        inventory_evidence_id=None,
    )


def test_passes_for_explicit_empty_folder():
    drive = FakeDrive(
        {"id": "target-root", "name": "Documents", "mimeType": FOLDER_MIME, "trashed": False},
        [],
    )
    result = GoogleDriveLiveTargetScopePreflight(drive_service=drive).run(
        manifest(), target_object_id="target-root"
    )
    assert result.target_is_folder is True
    assert result.target_is_empty is True
    assert result.child_count == 0
    assert result.structural_preflight.preflight_passed is True


def test_rejects_missing_target_id():
    drive = FakeDrive({}, [])
    with pytest.raises(LiveTargetPreflightError):
        GoogleDriveLiveTargetScopePreflight(drive_service=drive).run(
            manifest(), target_object_id="  "
        )


def test_rejects_non_folder_target():
    drive = FakeDrive(
        {"id": "target-root", "name": "file.pdf", "mimeType": "application/pdf", "trashed": False},
        [],
    )
    with pytest.raises(LiveTargetPreflightError):
        GoogleDriveLiveTargetScopePreflight(drive_service=drive).run(
            manifest(), target_object_id="target-root"
        )


def test_rejects_trashed_target():
    drive = FakeDrive(
        {"id": "target-root", "name": "Documents", "mimeType": FOLDER_MIME, "trashed": True},
        [],
    )
    with pytest.raises(LiveTargetPreflightError):
        GoogleDriveLiveTargetScopePreflight(drive_service=drive).run(
            manifest(), target_object_id="target-root"
        )


def test_rejects_non_empty_target():
    drive = FakeDrive(
        {"id": "target-root", "name": "Documents", "mimeType": FOLDER_MIME, "trashed": False},
        [{"id": "child", "name": "existing.pdf", "mimeType": "application/pdf", "parents": ["target-root"]}],
    )
    with pytest.raises(LiveTargetPreflightError):
        GoogleDriveLiveTargetScopePreflight(drive_service=drive).run(
            manifest(), target_object_id="target-root"
        )


def test_rejects_invalid_manifest_before_target_success():
    drive = FakeDrive(
        {"id": "target-root", "name": "Documents", "mimeType": FOLDER_MIME, "trashed": False},
        [],
    )
    invalid = replace(manifest(), case_id="CASE-002")
    with pytest.raises(Exception):
        GoogleDriveLiveTargetScopePreflight(drive_service=drive).run(
            invalid, target_object_id="target-root"
        )
