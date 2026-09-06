"""Live CASE-001 Document Identity bootstrap.

This read-only harness builds metadata inventory from the exact CASE-001
Documents scope, loads any prior local identity snapshot, resolves identities,
and persists the identity snapshot locally. It never mutates Google Drive.

Required environment:
    CASE_001_DOCUMENTS_ROOT_ID

Optional:
    CASE_001_IDENTITY_SNAPSHOT
        Local JSON path. Defaults to artifacts/case001/document_identity.json.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from googleapiclient.discovery import build

from agent_lab.audit import AuditStore
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
    root_id = os.environ.get("CASE_001_DOCUMENTS_ROOT_ID", "").strip()
    if not root_id:
        raise SystemExit("CASE_001_DOCUMENTS_ROOT_ID is required")

    snapshot_path = Path(os.environ.get("CASE_001_IDENTITY_SNAPSHOT", DEFAULT_SNAPSHOT))
    source_scope_ref = f"{PROVIDER}:{root_id}"

    case_registry = build_case_registry(root_id)
    case_state = CaseStateStore(case_registry)
    audit = AuditStore(case_registry, case_state)
    run_id = case_state.create_run(
        CASE_ID,
        request_id=f"case001-identity-bootstrap-{datetime.now(timezone.utc).isoformat()}",
    ).run_id

    credentials = get_drive_credentials()
    drive_service = build("drive", "v3", credentials=credentials, cache_discovery=False)
    resolver = CaseScopedDriveResolver(case_registry)
    storage = GoogleDriveMetadataAdapter(drive_service=drive_service, resolver=resolver)
    inventory = DocumentInventoryService(storage).build(CASE_ID)

    identity = DocumentIdentityRegistry(case_registry, case_state)
    if snapshot_path.exists():
        identity.load_snapshot(CASE_ID, snapshot_path)

    resolved = []
    for item in inventory.items:
        record, _ = identity.resolve_inventory_item(
            CASE_ID,
            run_id,
            item,
            source_provider=PROVIDER,
            source_scope_ref=source_scope_ref,
        )
        resolved.append({"document_id": record.document_id, "name": item.name})

    identity.save_snapshot(CASE_ID, snapshot_path)
    audit.validate()

    print(json.dumps({
        "case_id": CASE_ID,
        "tax_period": TAX_YEAR,
        "run_id": run_id,
        "inventory_document_count": inventory.document_count,
        "inventory_folder_count": inventory.folder_count,
        "identity_count": len(identity.list_for_case(CASE_ID)),
        "snapshot_path": str(snapshot_path),
        "documents": resolved,
        "drive_mutation": False,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
