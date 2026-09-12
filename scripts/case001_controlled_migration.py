"""Local controlled CASE-001 migration harness.

Default mode is DRY_RUN. Real Drive mutation is impossible unless the caller
selects LIVE, supplies the exact authorization sentinel, and provides a fresh
human authorization reference. Provider IDs are never printed.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import uuid

from googleapiclient.discovery import build

from agent_lab.approval import ActorType
from agent_lab.case001_approval_context import compose_approval_context
from agent_lab.case001_live_target_preflight import GoogleDriveLiveTargetScopePreflight
from agent_lab.case001_migration_manifest import Case001MigrationManifestGenerator
from agent_lab.case001_physical_migration import (
    Case001PhysicalMigrationExecutor,
    MigrationMode,
)
from agent_lab.case_registry import (
    AssessmentMode,
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
from agent_lab.durable_approval import DurableApprovalStore
from agent_lab.google_drive_auth import get_drive_credentials
from agent_lab.google_drive_mutation import GoogleDriveMutationAdapter
from agent_lab.google_drive_storage import GoogleDriveMetadataAdapter

CASE_ID = "CASE-001"
TAX_YEAR = 2024
PROVIDER = "google_drive"
EXPECTED_DOCUMENTS = 15
EXPECTED_FOLDERS = 0
DEFAULT_SNAPSHOT = Path("artifacts/case001/document_identity.json")
DEFAULT_DB = Path("artifacts/case001/durable-approval.sqlite3")
LIVE_SENTINEL = "YES-I-AUTHORIZE-CASE-001-PHYSICAL-MIGRATION"
EXECUTION_ACTOR = "case001-controlled-migration-executor"


class ControlledMigrationHarnessError(RuntimeError):
    pass


def build_case_registry(source_root_id: str) -> CaseRegistry:
    source_root_id = require_value("CASE_001_DOCUMENTS_ROOT_ID", source_root_id)
    now = datetime.now(timezone.utc)
    registry = CaseRegistry()
    registry.register(
        CaseRecord(
            case_id=CASE_ID,
            owner_type=OwnerType.PERSON,
            owner_id="CASE-001-OWNER",
            tax_period=TaxPeriod("CALENDAR_YEAR", TAX_YEAR),
            case_type=CaseType.INDIVIDUAL,
            assessment_mode=AssessmentMode.UNKNOWN_PENDING_VERIFICATION,
            lifecycle_status=LifecycleStatus.CREATED,
            storage_scope_reference=StorageScopeReference(PROVIDER, source_root_id),
            schema_version=1,
            created_at=now,
            updated_at=now,
        )
    )
    return registry


def require_value(name: str, value: str | None) -> str:
    value = (value or "").strip()
    if not value:
        raise ControlledMigrationHarnessError(f"{name} is required")
    return value


def validate_live_authorization(*, sentinel: str | None, approver: str | None,
                                authorization_reference: str | None) -> tuple[str, str]:
    if (sentinel or "").strip() != LIVE_SENTINEL:
        raise ControlledMigrationHarnessError("live migration authorization sentinel is missing")
    return (
        require_value("CASE_001_HUMAN_APPROVER", approver),
        require_value("CASE_001_AUTHORIZATION_REFERENCE", authorization_reference),
    )


def safe_summary(*, mode: MigrationMode, document_count: int, folder_count: int,
                 manifest_reference: str, preflight_reference: str,
                 approval_status: str | None, approval_consumed: bool,
                 drive_mutation: bool) -> dict[str, object]:
    """Return evidence without provider object IDs, folder IDs, or filenames."""
    return {
        "case_id": CASE_ID,
        "tax_period": TAX_YEAR,
        "mode": mode.value,
        "document_count": document_count,
        "folder_count": folder_count,
        "manifest_reference": manifest_reference,
        "preflight_reference": preflight_reference,
        "approval_status": approval_status,
        "approval_consumed": approval_consumed,
        "drive_mutation": drive_mutation,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Controlled CASE-001 physical migration")
    parser.add_argument(
        "--mode",
        choices=("dry-run", "live"),
        default="dry-run",
        help="dry-run is the default and performs zero mutations",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    mode = MigrationMode.LIVE if args.mode == "live" else MigrationMode.DRY_RUN

    source_root_id = require_value(
        "CASE_001_DOCUMENTS_ROOT_ID", os.environ.get("CASE_001_DOCUMENTS_ROOT_ID")
    )
    target_root_id = require_value(
        "CASE_001_TARGET_DOCUMENTS_ROOT_ID",
        os.environ.get("CASE_001_TARGET_DOCUMENTS_ROOT_ID"),
    )
    if source_root_id == target_root_id:
        raise ControlledMigrationHarnessError("source and target root IDs must differ")

    snapshot_path = Path(os.environ.get("CASE_001_IDENTITY_SNAPSHOT", str(DEFAULT_SNAPSHOT)))
    if not snapshot_path.is_file():
        raise ControlledMigrationHarnessError("CASE-001 identity snapshot is unavailable")

    db_path = Path(os.environ.get("CASE_001_DURABLE_APPROVAL_DB", str(DEFAULT_DB)))
    if mode is MigrationMode.LIVE and db_path.exists():
        raise ControlledMigrationHarnessError(
            "live durable approval database already exists; human recovery/review is required"
        )

    approver = authorization_reference = None
    if mode is MigrationMode.LIVE:
        approver, authorization_reference = validate_live_authorization(
            sentinel=os.environ.get("CASE_001_LIVE_MIGRATION_AUTHORIZED"),
            approver=os.environ.get("CASE_001_HUMAN_APPROVER"),
            authorization_reference=os.environ.get("CASE_001_AUTHORIZATION_REFERENCE"),
        )

    cases = build_case_registry(source_root_id)
    states = CaseStateStore(cases)
    run = states.create_run(
        CASE_ID,
        request_id=f"controlled-migration-{uuid.uuid4()}",
    )

    credentials = get_drive_credentials()
    drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
    metadata = GoogleDriveMetadataAdapter(
        drive_service=drive,
        resolver=CaseScopedDriveResolver(cases),
    )
    inventory = DocumentInventoryService(metadata).build(CASE_ID)
    if (
        inventory.document_count != EXPECTED_DOCUMENTS
        or inventory.folder_count != EXPECTED_FOLDERS
    ):
        raise ControlledMigrationHarnessError(
            "fresh CASE-001 inventory does not match the accepted 15-document boundary"
        )

    identities = DocumentIdentityRegistry(cases, states)
    identities.load_snapshot(CASE_ID, snapshot_path)
    records = identities.list_for_case(CASE_ID)
    expected_source_scope = f"{PROVIDER}:{source_root_id}"
    if len(records) != EXPECTED_DOCUMENTS or any(
        record.source_scope_ref != expected_source_scope for record in records
    ):
        raise ControlledMigrationHarnessError(
            "identity snapshot does not match the fresh source scope/count"
        )

    target_scope_ref = f"{PROVIDER}:{target_root_id}"
    manifest = Case001MigrationManifestGenerator(cases, identities).generate(
        inventory,
        source_provider=PROVIDER,
        source_scope_ref=expected_source_scope,
        target_scope_ref=target_scope_ref,
    )
    live_preflight = GoogleDriveLiveTargetScopePreflight(drive_service=drive).run(
        manifest,
        target_object_id=target_root_id,
    )
    if not live_preflight.target_is_empty or live_preflight.child_count != 0:
        raise ControlledMigrationHarnessError("fresh target preflight is not empty")

    context = compose_approval_context(
        manifest,
        live_preflight,
        run_id=run.run_id,
        actor=EXECUTION_ACTOR,
    )

    executor = Case001PhysicalMigrationExecutor(
        storage=GoogleDriveMutationAdapter(drive_service=drive)
    )

    if mode is MigrationMode.DRY_RUN:
        result = executor.execute(
            manifest,
            source_parent_id=source_root_id,
            target_parent_id=target_root_id,
            mode=MigrationMode.DRY_RUN,
        )
        print(json.dumps(safe_summary(
            mode=mode,
            document_count=inventory.document_count,
            folder_count=inventory.folder_count,
            manifest_reference=manifest.artifact_identity.reference,
            preflight_reference=live_preflight.structural_preflight.artifact_identity.reference,
            approval_status=None,
            approval_consumed=result.approval_consumed,
            drive_mutation=False,
        ), indent=2))
        return 0

    db_path.parent.mkdir(parents=True, exist_ok=True)
    with DurableApprovalStore(db_path, case_registry=cases, case_state=states) as approvals:
        pending = approvals.create_pending(
            **asdict(context),
            requester_actor_type=ActorType.AGENT,
        )
        approved = approvals.grant(
            pending.approval_id,
            approver=approver,
            authorization_reference=authorization_reference,
        )
        result = executor.execute(
            manifest,
            source_parent_id=source_root_id,
            target_parent_id=target_root_id,
            mode=MigrationMode.LIVE,
            live_enabled=True,
            approval_store=approvals,
            approval_id=approved.approval_id,
            approval_context=context,
        )
        final_approval = approvals.get(approved.approval_id)

    print(json.dumps(safe_summary(
        mode=mode,
        document_count=inventory.document_count,
        folder_count=inventory.folder_count,
        manifest_reference=manifest.artifact_identity.reference,
        preflight_reference=live_preflight.structural_preflight.artifact_identity.reference,
        approval_status=final_approval.approval_status.value,
        approval_consumed=result.approval_consumed,
        drive_mutation=True,
    ), indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ControlledMigrationHarnessError as exc:
        print(f"CASE-001 migration blocked: {exc}")
        raise SystemExit(2) from None
    except Exception as exc:
        # Provider exceptions may contain private identifiers/URLs. Keep stdout safe.
        print(f"CASE-001 migration stopped: {type(exc).__name__}; private diagnostics required")
        raise SystemExit(1) from None
