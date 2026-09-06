"""Run the CASE-001 metadata-only inventory against the exact Documents scope.

This is an execution harness for the current in-memory Case Registry model.
The exact CASE-001 Documents folder ID must be supplied locally through
CASE_001_DOCUMENTS_ROOT_ID. No Drive-wide discovery is performed.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict

from googleapiclient.discovery import build

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
from agent_lab.document_inventory import DocumentInventoryService
from agent_lab.google_drive_auth import get_drive_credentials
from agent_lab.google_drive_storage import GoogleDriveMetadataAdapter

CASE_ID = "CASE-001"


def _build_registry(root_id: str) -> CaseRegistry:
    registry = CaseRegistry()
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    registry.register(
        CaseRecord(
            case_id=CASE_ID,
            owner_type=OwnerType.PERSON,
            owner_id="CASE-001-OWNER",
            tax_period=TaxPeriod("CALENDAR_YEAR", 2024),
            case_type=CaseType.INDIVIDUAL,
            assessment_mode=AssessmentMode.UNKNOWN_PENDING_VERIFICATION,
            lifecycle_status=LifecycleStatus.CREATED,
            storage_scope_reference=StorageScopeReference("google_drive", root_id),
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

    service = build(
        "drive",
        "v3",
        credentials=get_drive_credentials(),
        cache_discovery=False,
    )
    registry = _build_registry(root_id)
    resolver = CaseScopedDriveResolver(registry)
    adapter = GoogleDriveMetadataAdapter(drive_service=service, resolver=resolver)
    inventory = DocumentInventoryService(adapter).build(CASE_ID)

    payload = {
        "case_id": inventory.case_id,
        "generated_at": inventory.generated_at.isoformat(),
        "document_count": inventory.document_count,
        "folder_count": inventory.folder_count,
        "items": [asdict(item) for item in inventory.items],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
