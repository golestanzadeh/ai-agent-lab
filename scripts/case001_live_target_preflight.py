"""Read-only CASE-001 live target-scope preflight.

The harness combines the already-validated live migration manifest with an
explicit Google Drive target folder. It performs metadata reads only and
never creates, moves, renames, deletes, overwrites, or copies Drive objects.

Required environment:
    CASE_001_DOCUMENTS_ROOT_ID
    CASE_001_TARGET_ROOT_ID

Optional:
    CASE_001_IDENTITY_SNAPSHOT
        Defaults to artifacts/case001/document_identity.json.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from googleapiclient.discovery import build

from agent_lab.case001_live_target_preflight import GoogleDriveLiveTargetScopePreflight
from agent_lab.case001_migration_manifest import Case001MigrationManifestGenerator
from agent_lab.case_registry import (
    CaseRecord,
    CaseRegistry,
    CaseType,
    LifecycleStatus,
    OwnerType,
    StorageScopeReference,
    TaxPeriod,
)
from agent_lab.case_scoped_drive import CaseScopedDriveResolver
from agent_lab.case_state import CaseStateStore
from agent_lab.document_identity import DocumentIdentityRegistry
from agent_lab.document_inventory import DocumentInventoryService
from agent_lab.google_drive_auth import get_drive_credentials
from agent_lab.google_drive_storage import GoogleDriveMetadataAdapter

CASE_ID = "CASE-001"
TAX_YEAR = 2024
PROVIDER = "google_drive"
DEFAULT_SNAPSHOT = Path("artifacts/case001/document_identity.json")


def build_case_registry(root_id: str) -> CaseRegistry:
    registry = CaseRegistry()
    now = datetime.now(timezone.utc)
    registry.register(
        CaseRecord(
            case_id=CASE_ID,
            owner_type=OwnerType.PERSON,
            owner_id="CASE-001-OWNER",
            tax_period=TaxPeriod("CALENDAR_YEAR", TAX_YEAR),
            case_type=CaseType.INDIVIDUAL,
            assessment_mode="UNKNOWN_PENDING_VERIFICATION",
            lifecycle_status=LifecycleStatus.CREATED,
            storage_scope_reference=StorageScopeReference(PROVIDER, root_id),
            schema_version=1,
            created_at=now,
            updated_at=now,
        )
    )
    return registry


def main() -> None:
    source_root_id = os.environ.get("CASE_001_DOCUMENTS_ROOT_ID", "").strip()
    target_root_id = os.environ.get("CASE_001_TARGET_ROOT_ID", "").strip()
    if not source_root_id:
        raise SystemExit("CASE_001_DOCUMENTS_ROOT_ID is required")
    if not target_root_id:
        raise SystemExit("CASE_001_TARGET_ROOT_ID is required")
    if source_root_id == target_root_id:
        raise SystemExit("source and target roots must differ")

    snapshot_path = Path(os.environ.get("CASE_001_IDENTITY_SNAPSHOT", DEFAULT_SNAPSHOT))
    if not snapshot_path.exists():
        raise SystemExit(f"identity snapshot not found: {snapshot_path}")

    source_scope_ref = f"{PROVIDER}:{source_root_id}"
    target_scope_ref = f"{PROVIDER}:{target_root_id}"
    case_registry = build_case_registry(source_root_id)
    case_state = CaseStateStore(case_registry)
    case_state.create_run(
        CASE_ID,
        request_id=f"case001-live-target-preflight-{datetime.now(timezone.utc).isoformat()}",
    )

    credentials = get_drive_credentials()
    drive_service = build("drive", "v3", credentials=credentials, cache_discovery=False)
    resolver = CaseScopedDriveResolver(case_registry)
    storage = GoogleDriveMetadataAdapter(drive_service=drive_service, resolver=resolver)
    inventory = DocumentInventoryService(storage).build(CASE_ID)

    identity = DocumentIdentityRegistry(case_registry, case_state)
    identity.load_snapshot(CASE_ID, snapshot_path)

    manifest = Case001MigrationManifestGenerator(
        case_registry,
        identity,
    ).generate(
        inventory,
        source_provider=PROVIDER,
        source_scope_ref=source_scope_ref,
        target_scope_ref=target_scope_ref,
    )

    live = GoogleDriveLiveTargetScopePreflight(
        drive_service=drive_service,
    ).run(
        manifest,
        target_object_id=target_root_id,
    )

    print(json.dumps({
        "case_id": live.structural_preflight.case_id,
        "tax_period": live.structural_preflight.tax_period_year,
        "document_count": live.structural_preflight.document_count,
        "target_name": live.target_name,
        "target_is_folder": live.target_is_folder,
        "target_is_empty": live.target_is_empty,
        "target_child_count": live.child_count,
        "target_scope_is_actual": live.structural_preflight.target_scope_is_actual,
        "mapping_count_matches": live.structural_preflight.mapping_count_matches,
        "source_objects_unique": live.structural_preflight.source_objects_unique,
        "logical_documents_unique": live.structural_preflight.logical_documents_unique,
        "preflight_passed": live.structural_preflight.preflight_passed,
        "drive_mutation": False,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
