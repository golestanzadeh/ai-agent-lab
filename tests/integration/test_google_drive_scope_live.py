"""Read-only live Google Drive scope verification harness.

This test intentionally requires two manually prepared, unrelated Drive test
folders. It never creates, moves, renames, deletes, or modifies Drive data.
Set TEST_DRIVE_ROOT_A and TEST_DRIVE_ROOT_B to their folder IDs and use the
same local OAuth setup as the Drive smoke test.

The harness is skipped unless the environment variables are present so normal
unit-test runs remain offline and deterministic.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
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
from agent_lab.case_scoped_drive import CaseScopedDriveResolver, OutOfScopeError
from agent_lab.google_drive_auth import get_drive_credentials
from agent_lab.google_drive_storage import GoogleDriveMetadataAdapter


def _build_registry(root_a: str, root_b: str) -> CaseRegistry:
    registry = CaseRegistry()
    now = datetime.now(timezone.utc)
    for case_id, year, root_id in (
        ("LIVE-TEST-A-2024", 2024, root_a),
        ("LIVE-TEST-B-2025", 2025, root_b),
    ):
        registry.register(
            CaseRecord(
                case_id=case_id,
                owner_type=OwnerType.PERSON,
                owner_id="LIVE-TEST-PERSON",
                tax_period=TaxPeriod("CALENDAR_YEAR", year),
                case_type=CaseType.INDIVIDUAL,
                assessment_mode=AssessmentMode.INDIVIDUAL_ASSESSMENT,
                lifecycle_status=LifecycleStatus.CREATED,
                storage_scope_reference=StorageScopeReference("google_drive", root_id),
                schema_version=1,
                created_at=now,
                updated_at=now,
            )
        )
    return registry


def _drive_service():
    pytest.importorskip("googleapiclient.discovery")
    return build(
        "drive",
        "v3",
        credentials=get_drive_credentials(),
        cache_discovery=False,
    )


def test_live_google_drive_case_scope_isolation() -> None:
    root_a = os.environ.get("TEST_DRIVE_ROOT_A")
    root_b = os.environ.get("TEST_DRIVE_ROOT_B")
    if not root_a or not root_b:
        pytest.skip("Set TEST_DRIVE_ROOT_A and TEST_DRIVE_ROOT_B for live scope verification")
    if root_a == root_b:
        pytest.fail("Live test roots must be different")

    registry = _build_registry(root_a, root_b)
    resolver = CaseScopedDriveResolver(registry)
    adapter = GoogleDriveMetadataAdapter(drive_service=_drive_service(), resolver=resolver)

    a_items = adapter.list_children("LIVE-TEST-A-2024")
    b_items = adapter.list_children("LIVE-TEST-B-2025")

    a_ids = {item.object_id for item in a_items}
    b_ids = {item.object_id for item in b_items}

    assert a_ids.isdisjoint(b_ids), "test roots must not expose the same direct child object"

    if b_ids:
        with pytest.raises(OutOfScopeError):
            adapter.get_metadata("LIVE-TEST-A-2024", next(iter(b_ids)))
    if a_ids:
        with pytest.raises(OutOfScopeError):
            adapter.get_metadata("LIVE-TEST-B-2025", next(iter(a_ids)))

    with pytest.raises(OutOfScopeError):
        adapter.get_metadata("LIVE-TEST-A-2024", root_b)
    with pytest.raises(OutOfScopeError):
        adapter.get_metadata("LIVE-TEST-B-2025", root_a)
