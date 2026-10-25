"""Read-only CaseRegistry to dashboard integration tests."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

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
from agent_lab.ui_case_registry_reader import CaseRegistryDashboardReader
from agent_lab.ui_dashboard import DashboardUnavailable, create_dashboard_app


def _record(case_id: str, owner_id: str, year: int) -> CaseRecord:
    now = datetime.now(timezone.utc)
    return CaseRecord(
        case_id=case_id,
        owner_type=OwnerType.PERSON,
        owner_id=owner_id,
        tax_period=TaxPeriod("CALENDAR_YEAR", year),
        case_type=CaseType.INDIVIDUAL,
        assessment_mode=AssessmentMode.UNKNOWN_PENDING_VERIFICATION,
        lifecycle_status=LifecycleStatus.ACTIVE,
        storage_scope_reference=StorageScopeReference("synthetic_local", case_id),
        schema_version=1,
        created_at=now,
        updated_at=now,
    )


def _registry() -> CaseRegistry:
    registry = CaseRegistry()
    registry.register(_record("TEST-A-2024-01", "TEST-OWNER-A", 2024))
    registry.register(_record("TEST-A-2024-02", "TEST-OWNER-A", 2024))
    registry.register(_record("TEST-A-2026-01", "TEST-OWNER-A", 2026))
    registry.register(_record("TEST-B-2025-01", "TEST-OWNER-B", 2025))
    return registry


def test_reader_projects_multiple_cases_across_all_registered_years() -> None:
    reader = CaseRegistryDashboardReader(
        _registry(),
        "TEST-OWNER-A",
        frozenset({"TEST-A-2024-01", "TEST-A-2024-02", "TEST-A-2026-01"}),
    )
    page = TestClient(create_dashboard_app(read_cases=reader)).get("/")

    assert page.status_code == 200
    assert "TEST-A-2024-01" in page.text
    assert "TEST-A-2024-02" in page.text
    assert "TEST-A-2026-01" in page.text
    assert "TEST-B-2025-01" not in page.text
    assert page.text.index("TEST-A-2026-01") < page.text.index("TEST-A-2024-01")


def test_reader_requires_both_owner_scope_and_case_allowlist() -> None:
    registry = _registry()
    reader = CaseRegistryDashboardReader(
        registry,
        "TEST-OWNER-A",
        frozenset({"TEST-A-2024-01"}),
    )

    assert tuple(item.case_id for item in reader()) == ("TEST-A-2024-01",)
    assert "TEST-A-2024-02" not in TestClient(
        create_dashboard_app(read_cases=reader)
    ).get("/").text


def test_reader_fails_closed_for_cross_owner_or_missing_authorization() -> None:
    registry = _registry()
    cross_owner = CaseRegistryDashboardReader(
        registry,
        "TEST-OWNER-A",
        frozenset({"TEST-B-2025-01"}),
    )
    with pytest.raises(DashboardUnavailable, match="not resolved"):
        cross_owner()
    page = TestClient(create_dashboard_app(read_cases=cross_owner)).get("/")
    assert page.status_code == 200
    assert "TEST-B-2025-01" not in page.text

    with pytest.raises(ValueError, match="allowlist"):
        CaseRegistryDashboardReader(registry, "TEST-OWNER-A", frozenset())


def test_dashboard_selection_cannot_escape_authorized_registry_scope() -> None:
    reader = CaseRegistryDashboardReader(
        _registry(),
        "TEST-OWNER-A",
        frozenset({"TEST-A-2024-01", "TEST-A-2026-01"}),
    )
    client = TestClient(create_dashboard_app(read_cases=reader))

    assert client.get("/?case_id=TEST-A-2024-01").status_code == 200
    assert client.get("/?case_id=TEST-A-2024-02").status_code == 404
    assert client.get("/?case_id=TEST-B-2025-01").status_code == 404
    assert client.post("/submit").status_code == 404
