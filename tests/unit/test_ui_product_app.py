"""Production launcher composition and restart behavior."""

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
from agent_lab.case_persistence import SQLiteCasePersistence
from agent_lab.case_state import CaseState
from agent_lab.ui_product_app import (
    create_persistent_product_dashboard_app, create_product_dashboard_app,
)


def _registry() -> CaseRegistry:
    now = datetime.now(timezone.utc)
    registry = CaseRegistry()
    for case_id, owner_id, year in (
        ("TEST-LOCAL-2023-A", "TEST-OWNER-A", 2023),
        ("TEST-LOCAL-2023-B", "TEST-OWNER-A", 2023),
        ("TEST-LOCAL-2027-A", "TEST-OWNER-A", 2027),
        ("TEST-OTHER-2026-A", "TEST-OWNER-B", 2026),
    ):
        registry.register(CaseRecord(
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
        ))
    return registry


def test_default_product_launcher_starts_without_synthetic_fallback() -> None:
    client = TestClient(create_product_dashboard_app())
    page = client.get("/")

    assert page.status_code == 200
    assert client.get("/health").json() == {
        "status": "ok", "mode": "read-only-dashboard", "source": "unavailable"
    }
    assert "TEST-" not in page.text
    assert client.post("/test/cases").status_code == 404
    assert client.post("/submit").status_code == 404


@pytest.mark.parametrize(
    "kwargs",
    (
        {"registry": _registry()},
        {"owner_id": "TEST-OWNER-A"},
        {"allowed_case_ids": {"TEST-LOCAL-2023-A"}},
        {"registry": _registry(), "owner_id": "TEST-OWNER-A"},
    ),
)
def test_partial_persistence_configuration_fails_startup(kwargs) -> None:
    with pytest.raises(ValueError, match="configured together"):
        create_product_dashboard_app(**kwargs)


def test_authorized_registry_survives_app_restart_without_scope_expansion() -> None:
    registry = _registry()
    configuration = {
        "registry": registry,
        "owner_id": "TEST-OWNER-A",
        "allowed_case_ids": {
            "TEST-LOCAL-2023-A", "TEST-LOCAL-2023-B", "TEST-LOCAL-2027-A"
        },
    }

    first = TestClient(create_product_dashboard_app(**configuration))
    restarted = TestClient(create_product_dashboard_app(**configuration))
    for client in (first, restarted):
        page = client.get("/")
        assert page.status_code == 200
        assert client.get("/health").json()["source"] == "configured"
        assert "TEST-LOCAL-2023-A" in page.text
        assert "TEST-LOCAL-2023-B" in page.text
        assert "TEST-LOCAL-2027-A" in page.text
        assert "TEST-OTHER-2026-A" not in page.text
        assert client.get("/?case_id=TEST-OTHER-2026-A").status_code == 404


def test_restart_fails_closed_if_authorized_case_disappears() -> None:
    registry = _registry()
    configured = TestClient(create_product_dashboard_app(
        registry=registry,
        owner_id="TEST-OWNER-A",
        allowed_case_ids={"TEST-LOCAL-2023-A"},
    ))
    assert configured.get("/health").json()["source"] == "configured"

    replacement = _registry()
    # Simulate a persistence resolver that no longer returns the authorized case.
    replacement._records.pop("TEST-LOCAL-2023-A")
    restarted = TestClient(create_product_dashboard_app(
        registry=replacement,
        owner_id="TEST-OWNER-A",
        allowed_case_ids={"TEST-LOCAL-2023-A"},
    ))
    page = restarted.get("/")
    assert page.status_code == 200
    assert "TEST-LOCAL-2023-A" not in page.text
    assert restarted.get("/?case_id=TEST-LOCAL-2023-A").status_code == 503


def test_read_only_kernel_projection_uses_exact_authorized_case_year_and_run() -> None:
    calls = []

    class Projection:
        run_id = "RUN-EXACT"
        kill_switch = "ACTIVE"
        tasks = ()

    def read_projection(case_id: str, tax_year: int, run_id: str):
        calls.append((case_id, tax_year, run_id))
        if (case_id, tax_year, run_id) != ("TEST-LOCAL-2027-A", 2027, "RUN-EXACT"):
            raise LookupError("scope mismatch")
        return Projection()

    client = TestClient(create_product_dashboard_app(
        registry=_registry(),
        owner_id="TEST-OWNER-A",
        allowed_case_ids={"TEST-LOCAL-2027-A"},
        read_kernel_projection=read_projection,
    ))
    page = client.get("/", params={
        "tab": "analysis", "case_id": "TEST-LOCAL-2027-A", "run_id": "RUN-EXACT"
    })
    assert page.status_code == 200
    assert calls == [("TEST-LOCAL-2027-A", 2027, "RUN-EXACT")]
    assert "RUN-EXACT" in page.text
    assert client.post("/test/kernel/execute").status_code == 404

    denied = client.get("/", params={
        "tab": "analysis", "case_id": "TEST-OTHER-2026-A", "run_id": "RUN-EXACT"
    })
    assert denied.status_code == 404
    assert calls == [("TEST-LOCAL-2027-A", 2027, "RUN-EXACT")]


def test_kernel_projection_cannot_start_without_authorized_case_source() -> None:
    with pytest.raises(ValueError, match="configured case source"):
        create_product_dashboard_app(read_kernel_projection=lambda *_: None)


def test_persistent_product_composition_recovers_after_database_reopen(tmp_path) -> None:
    path = tmp_path / "case.sqlite3"
    key = b"product-composition-integrity-key-32-bytes"
    registry = _registry()
    store = SQLiteCasePersistence(path, integrity_key=key)
    for case_id in ("TEST-LOCAL-2023-A", "TEST-LOCAL-2023-B", "TEST-LOCAL-2027-A"):
        record = registry.get(case_id)
        assert record is not None
        store.register_case(
            record,
            CaseState(case_id, 1, "READY", record.created_at, record.updated_at),
            ui_owner_id="TEST-OWNER-A",
        )
    store.close()

    reopened = SQLiteCasePersistence(path, integrity_key=key)
    app = create_persistent_product_dashboard_app(
        persistence=reopened,
        owner_id="TEST-OWNER-A",
        allowed_case_ids={"TEST-LOCAL-2023-A", "TEST-LOCAL-2027-A"},
    )
    page = TestClient(app).get("/")
    assert page.status_code == 200
    assert "TEST-LOCAL-2023-A" in page.text
    assert "TEST-LOCAL-2027-A" in page.text
    assert "TEST-LOCAL-2023-B" not in page.text
    assert app.state.case_runtime.state("TEST-LOCAL-2027-A").lifecycle_status == "READY"
    reopened.close()
