from fastapi.testclient import TestClient

from agent_lab.ui_app import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_home_is_persian_synthetic_local_shell() -> None:
    response = _client().get("/")
    assert response.status_code == 200
    assert 'lang="fa" dir="rtl"' in response.text
    assert "نمونهٔ مصنوعی · محلی" in response.text
    assert "SYNTH-CASE-001" in response.text
    assert "ارسال تولیدی مجاز و پیاده‌سازی نشده است" in response.text
    assert "https://" not in response.text


def test_workspace_returns_only_requested_case_partial() -> None:
    response = _client().get(
        "/workspace", params={"case_id": "SYNTH-CASE-002", "tax_year": 2025},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert "SYNTH-CASE-002" in response.text
    assert "SYNTH-CASE-001" not in response.text
    assert "<html" not in response.text
    assert "PROCESSING" in response.text
    assert "LOCAL_SYNTHETIC_RUNTIME_READY" in response.text


def test_unknown_or_wrong_year_fails_closed_without_case_data() -> None:
    client = _client()
    unknown = client.get("/workspace", params={"case_id": "SYNTH-CASE-999", "tax_year": 2024})
    mismatch = client.get("/workspace", params={"case_id": "SYNTH-CASE-001", "tax_year": 2025})
    assert unknown.status_code == 404
    assert mismatch.status_code == 404
    assert "SYNTH-PERSON" not in unknown.text
    assert "SYNTH-PERSON" not in mismatch.text


def test_no_submission_route_exists() -> None:
    response = _client().post("/submit", json={"case_id": "SYNTH-CASE-001"})
    assert response.status_code == 404


def test_health_declares_synthetic_local_mode() -> None:
    assert _client().get("/health").json() == {
        "status": "ok", "mode": "synthetic-local-only"
    }


def test_runtime_api_documentation_is_disabled() -> None:
    client = _client()
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_workflow_diagnostics_are_privacy_safe_and_controls_stay_disabled() -> None:
    response = _client().get("/")
    assert "مسیر پرونده" in response.text
    assert "OFFICIAL_ERIC_MAPPING_NOT_RECOVERED" in response.text
    assert "PRODUCTION_SUBMISSION_PATH_NOT_AUTHORIZED" in response.text
    assert "private document" not in response.text
    assert response.text.count("disabled") >= 4
