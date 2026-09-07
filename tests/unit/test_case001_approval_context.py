"""Synthetic artifacts only; no Drive client or approval store is needed."""

from dataclasses import replace
from unittest.mock import Mock

import pytest

from agent_lab.approval import ApprovalExecutionContext, ApprovalStore, IntendedOperation
from agent_lab.case001_approval_context import ApprovalContextCompositionError, compose_approval_context
from agent_lab.case001_live_target_preflight import GoogleDriveLiveTargetScopePreflight, LiveTargetScopeResult
from agent_lab.case001_migration import DocumentMigrationMapping
from agent_lab.case001_migration_manifest import Case001MigrationManifest
from agent_lab.case001_migration_preflight import Case001MigrationPreflight, MigrationPreflightResult


@pytest.fixture
def artifacts():
    mapping = DocumentMigrationMapping(
        "google_drive", "synthetic-object", "synthetic-document",
        "google_drive:synthetic-source", "google_drive:synthetic-target",
    )
    manifest = Case001MigrationManifest(
        "CASE-001", 2024, "google_drive", mapping.source_scope_ref,
        mapping.target_scope_ref, (mapping,),
    )
    structural = Case001MigrationPreflight().run(
        manifest, target_scope_is_actual=True, target_is_empty=True,
    )
    live = LiveTargetScopeResult(
        "synthetic-target", "Documents", "application/vnd.google-apps.folder",
        True, True, 0, structural, manifest.artifact_identity,
    )
    return manifest, live


def compose(manifest, live, **kwargs):
    return compose_approval_context(manifest, live, **({"run_id": "synthetic-run", "actor": "synthetic-actor"} | kwargs))


def test_exact_context_and_identity_preservation(artifacts):
    manifest, live = artifacts
    result = compose(manifest, live)
    assert result == ApprovalExecutionContext(
        "CASE-001", "synthetic-run", manifest.artifact_identity.kind,
        manifest.artifact_identity.version, manifest.artifact_identity.reference,
        live.structural_preflight.artifact_identity.kind,
        live.structural_preflight.artifact_identity.reference, "PASSED",
        IntendedOperation.PHYSICAL_MIGRATION, "synthetic-actor",
    )
    assert compose(manifest, live) == result


@pytest.mark.parametrize("field", ["run_id", "actor"])
@pytest.mark.parametrize("value", [None, "", " \t", 42])
def test_required_identifiers(artifacts, field, value):
    with pytest.raises(ApprovalContextCompositionError, match=field):
        compose(*artifacts, **{field: value})


def test_preserves_identifiers_without_normalizing(artifacts):
    result = compose(*artifacts, run_id=" run ", actor=" actor ")
    assert (result.run_id, result.actor) == (" run ", " actor ")


@pytest.mark.parametrize("artifact_type", [Case001MigrationManifest, MigrationPreflightResult])
@pytest.mark.parametrize("field,value", [("kind", "WRONG"), ("version", "2")])
def test_rejects_unsupported_identity(artifacts, monkeypatch, artifact_type, field, value):
    manifest, live = artifacts
    original = (manifest if artifact_type is Case001MigrationManifest else live.structural_preflight).artifact_identity
    # Controlled property override exercises unsupported future/corrupt metadata.
    monkeypatch.setattr(artifact_type, "artifact_identity", property(lambda self: replace(original, **{field: value})))
    with pytest.raises(ApprovalContextCompositionError, match=field):
        compose(manifest, live)


@pytest.mark.parametrize("field", [
    "preflight_passed", "target_scope_is_actual", "target_is_empty",
    "mapping_count_matches", "source_objects_unique", "logical_documents_unique",
])
@pytest.mark.parametrize("value", [False, 1, None])
def test_rejects_non_success_flags(artifacts, field, value):
    manifest, live = artifacts
    altered = replace(live.structural_preflight, **{field: value})
    with pytest.raises(ApprovalContextCompositionError, match=field):
        compose(manifest, replace(live, structural_preflight=altered))


@pytest.mark.parametrize("field,value", [
    ("case_id", "CASE-002"), ("tax_period_year", 2025),
    ("source_scope_ref", "google_drive:another-source"),
    ("target_scope_ref", "google_drive:another-target"), ("document_count", 2),
])
def test_rejects_artifact_disagreement(artifacts, field, value):
    manifest, live = artifacts
    with pytest.raises(ApprovalContextCompositionError, match=field):
        compose(manifest, replace(live, structural_preflight=replace(live.structural_preflight, **{field: value})))


@pytest.mark.parametrize("field,value", [("case_id", "CASE-002"), ("tax_period_year", 2025)])
def test_manifest_constructor_rejects_invalid_scope(artifacts, field, value):
    with pytest.raises(ValueError):
        replace(artifacts[0], **{field: value})


def test_missing_provenance_rejected(artifacts):
    manifest, live = artifacts
    with pytest.raises(ApprovalContextCompositionError, match="provenance"):
        compose(manifest, replace(live, manifest_identity=None))


def test_different_mappings_cannot_substitute_despite_identical_preflight_identity(artifacts):
    manifest, live = artifacts
    other = replace(manifest, mappings=(replace(manifest.mappings[0], source_object_id="another-object", logical_document_id="another-document"),))
    other_preflight = Case001MigrationPreflight().run(other, target_scope_is_actual=True, target_is_empty=True)
    assert other.artifact_identity != manifest.artifact_identity
    assert other_preflight.artifact_identity == live.structural_preflight.artifact_identity
    with pytest.raises(ApprovalContextCompositionError, match="provenance"):
        compose(other, live)


def test_equivalent_manifest_reconstruction_is_same_artifact(artifacts):
    manifest, live = artifacts
    assert compose(replace(manifest), live) == compose(manifest, live)


@pytest.mark.parametrize("field,value", [
    ("target_is_folder", False), ("target_is_empty", False), ("child_count", 1),
    ("child_count", False), ("target_object_id", "another-target"),
    ("target_object_id", ""), ("target_mime_type", "application/pdf"),
])
def test_rejects_inconsistent_live_target(artifacts, field, value):
    manifest, live = artifacts
    with pytest.raises(ApprovalContextCompositionError):
        compose(manifest, replace(live, **{field: value}))


def test_composition_has_no_approval_or_drive_side_effects(artifacts, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("composition attempted a lifecycle or Drive operation")
    for method in ("__init__", "create_pending", "grant", "consume", "reject", "revoke", "expire"):
        monkeypatch.setattr(ApprovalStore, method, forbidden)
    monkeypatch.setattr(GoogleDriveLiveTargetScopePreflight, "run", forbidden)
    manifest, live = artifacts
    before = (manifest.artifact_identity, live)
    compose(manifest, live)
    assert before == (manifest.artifact_identity, live)


def test_live_execution_records_exact_manifest_binding_using_read_only_fake(artifacts):
    manifest, _ = artifacts
    files = Mock(spec=["get", "list"])
    files.get.return_value.execute.return_value = {
        "id": "synthetic-target", "name": "Documents",
        "mimeType": "application/vnd.google-apps.folder", "trashed": False,
    }
    files.list.return_value.execute.return_value = {"files": []}
    drive = Mock(spec=["files"])
    drive.files.return_value = files
    result = GoogleDriveLiveTargetScopePreflight(drive_service=drive).run(manifest, target_object_id="synthetic-target")
    assert result.manifest_identity == manifest.artifact_identity
    assert compose(manifest, result).manifest_reference == result.manifest_identity.reference
    assert [call[0] for call in files.method_calls] == ["get", "list"]
