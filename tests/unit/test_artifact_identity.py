from agent_lab.artifact_identity import build_artifact_identity, canonical_json
from agent_lab.case001_migration_manifest import Case001MigrationManifest
from agent_lab.case001_migration import DocumentMigrationMapping
from agent_lab.case001_migration_preflight import Case001MigrationPreflight


def _manifest() -> Case001MigrationManifest:
    return Case001MigrationManifest(
        case_id="CASE-001",
        tax_period_year=2024,
        source_provider="google_drive",
        source_scope_ref="google_drive:SOURCE",
        target_scope_ref="google_drive:TARGET",
        mappings=(
            DocumentMigrationMapping(
                source_provider="google_drive",
                source_object_id="DOC-001",
                logical_document_id="DOCLOG-001",
                source_scope_ref="google_drive:SOURCE",
                target_scope_ref="google_drive:TARGET",
            ),
        ),
    )


def test_canonical_json_is_key_order_independent():
    assert canonical_json({"b": 2, "a": 1}) == canonical_json({"a": 1, "b": 2})


def test_same_payload_produces_same_identity():
    first = build_artifact_identity(kind="TEST", version="1", payload={"a": 1})
    second = build_artifact_identity(kind="TEST", version="1", payload={"a": 1})
    assert first == second


def test_content_change_produces_new_reference():
    first = build_artifact_identity(kind="TEST", version="1", payload={"a": 1})
    second = build_artifact_identity(kind="TEST", version="1", payload={"a": 2})
    assert first.reference != second.reference


def test_manifest_exposes_stable_artifact_identity():
    manifest = _manifest()
    identity = manifest.artifact_identity
    assert identity.kind == "CASE001_MIGRATION_MANIFEST"
    assert identity.version == "1"
    assert identity.reference.startswith("sha256:")
    assert identity == manifest.artifact_identity


def test_manifest_identity_changes_when_mapping_changes():
    first = _manifest()
    second = Case001MigrationManifest(
        case_id=first.case_id,
        tax_period_year=first.tax_period_year,
        source_provider=first.source_provider,
        source_scope_ref=first.source_scope_ref,
        target_scope_ref=first.target_scope_ref,
        mappings=(
            DocumentMigrationMapping(
                source_provider="google_drive",
                source_object_id="DOC-002",
                logical_document_id="DOCLOG-001",
                source_scope_ref="google_drive:SOURCE",
                target_scope_ref="google_drive:TARGET",
            ),
        ),
    )
    assert first.artifact_identity.reference != second.artifact_identity.reference


def test_preflight_exposes_stable_artifact_identity():
    result = Case001MigrationPreflight().run(
        _manifest(), target_scope_is_actual=True, target_is_empty=True
    )
    identity = result.artifact_identity
    assert identity.kind == "CASE001_MIGRATION_PREFLIGHT"
    assert identity.version == "1"
    assert identity.reference.startswith("sha256:")
    assert identity == result.artifact_identity


def test_preflight_identity_changes_when_result_changes():
    preflight = Case001MigrationPreflight()
    empty_target = preflight.run(_manifest(), target_scope_is_actual=True, target_is_empty=True)
    non_empty_target = object.__new__(type(empty_target))
    for field in (
        "case_id", "tax_period_year", "document_count", "source_scope_ref",
        "target_scope_ref", "target_scope_is_actual", "target_is_empty",
        "mapping_count_matches", "source_objects_unique", "logical_documents_unique",
        "preflight_passed",
    ):
        object.__setattr__(non_empty_target, field, getattr(empty_target, field))
    object.__setattr__(non_empty_target, "target_is_empty", False)
    assert empty_target.artifact_identity.reference != non_empty_target.artifact_identity.reference


def test_artifact_reference_is_sha256_of_canonical_payload():
    identity = build_artifact_identity(kind="TEST", version="1", payload={"b": 2, "a": 1})
    assert len(identity.reference.removeprefix("sha256:")) == 64
