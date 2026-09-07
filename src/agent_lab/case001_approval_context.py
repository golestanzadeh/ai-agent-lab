"""Pure CASE-001 artifact composition; no approval lifecycle or storage access."""

from agent_lab.approval import ApprovalExecutionContext, IntendedOperation
from agent_lab.artifact_identity import ArtifactIdentity
from agent_lab.case001_live_target_preflight import LiveTargetScopeResult
from agent_lab.case001_migration_manifest import Case001MigrationManifest
from agent_lab.case001_migration_preflight import MigrationPreflightResult


class ApprovalContextCompositionError(ValueError):
    """Supplied artifacts cannot safely describe one migration operation."""


def compose_approval_context(
    manifest: Case001MigrationManifest,
    live_preflight: LiveTargetScopeResult,
    *,
    run_id: str,
    actor: str,
) -> ApprovalExecutionContext:
    """Bind exact D-018 identities without authorizing or executing anything.

    Legacy live results without manifest provenance fail closed. Run and actor
    are supplied identifiers, not assertions of registry membership or authority.
    """
    def require(condition: bool, message: str) -> None:
        if not condition:
            raise ApprovalContextCompositionError(message)

    for name, value in (("run_id", run_id), ("actor", actor)):
        require(isinstance(value, str) and bool(value.strip()), f"{name} is required")
    require(isinstance(manifest, Case001MigrationManifest), "invalid manifest type")
    require(isinstance(live_preflight, LiveTargetScopeResult), "invalid live preflight type")
    preflight = live_preflight.structural_preflight
    require(isinstance(preflight, MigrationPreflightResult), "invalid structural preflight type")
    require(manifest.case_id == "CASE-001", "manifest must be CASE-001")
    require(manifest.tax_period_year == 2024, "manifest must be for 2024")
    manifest_identity = manifest.artifact_identity
    preflight_identity = preflight.artifact_identity
    for name, identity, kind in (
        ("manifest", manifest_identity, "CASE001_MIGRATION_MANIFEST"),
        ("preflight", preflight_identity, "CASE001_MIGRATION_PREFLIGHT"),
    ):
        require(isinstance(identity, ArtifactIdentity), f"invalid {name} identity")
        require(identity.kind == kind, f"unsupported {name} kind")
        require(identity.version == "1", f"unsupported {name} version")
    require(
        isinstance(live_preflight.manifest_identity, ArtifactIdentity)
        and live_preflight.manifest_identity == manifest_identity,
        "missing or mismatched manifest provenance",
    )
    for field in (
        "preflight_passed", "target_scope_is_actual", "target_is_empty",
        "mapping_count_matches", "source_objects_unique", "logical_documents_unique",
    ):
        require(getattr(preflight, field) is True, f"preflight not successful: {field}")
    require(
        live_preflight.target_is_folder is True
        and live_preflight.target_is_empty is True
        and type(live_preflight.child_count) is int
        and live_preflight.child_count == 0,
        "live target is not an empty folder",
    )
    require(
        isinstance(live_preflight.target_object_id, str)
        and bool(live_preflight.target_object_id.strip())
        and live_preflight.target_mime_type == "application/vnd.google-apps.folder"
        and manifest.target_scope_ref == f"google_drive:{live_preflight.target_object_id}",
        "live target scope mismatch",
    )
    for field in ("case_id", "tax_period_year", "source_scope_ref", "target_scope_ref", "document_count"):
        require(getattr(preflight, field) == getattr(manifest, field), f"{field} mismatch")
    require(manifest.document_count > 0, "manifest contains no documents")
    return ApprovalExecutionContext(
        case_id=manifest.case_id, run_id=run_id,
        manifest_identity=manifest_identity.kind,
        manifest_version=manifest_identity.version,
        manifest_reference=manifest_identity.reference,
        preflight_identity=preflight_identity.kind,
        preflight_reference=preflight_identity.reference,
        preflight_result="PASSED",
        intended_operation=IntendedOperation.PHYSICAL_MIGRATION,
        actor=actor,
    )
