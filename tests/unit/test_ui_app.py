from fastapi.testclient import TestClient

from agent_lab.ui_app import create_app
from agent_lab.case_registry import CaseRegistry
from agent_lab.ui_state_contract import UIStateError
import pytest


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


def test_empty_registry_fails_closed_before_serving_ui() -> None:
    with pytest.raises(UIStateError, match="at least one registered case"):
        create_app(registry=CaseRegistry())


def test_workflow_diagnostics_are_privacy_safe_and_controls_stay_disabled() -> None:
    response = _client().get("/")
    assert "مسیر پرونده" in response.text
    assert "OFFICIAL_ERIC_ENGINE_NOT_EXECUTED" in response.text
    assert "PRODUCTION_SUBMISSION_PATH_NOT_AUTHORIZED" in response.text
    assert "private document" not in response.text
    assert response.text.count("disabled") >= 4
    assert "محدودهٔ پرونده" in response.text
    assert "بازبینی تخصصی" in response.text
    assert "در حال حاضر لازم نیست" in response.text


def test_synthetic_document_inventory_renders_without_private_content_or_upload() -> None:
    response = _client().get("/")
    assert "فهرست متادیتای مصنوعی" in response.text
    assert "مدرک مصنوعی 1" in response.text
    assert "SYNTHETIC_METADATA_ONLY" in response.text
    assert "Gehaltsabrechnung" not in response.text
    assert "type=\"file\"" not in response.text


def test_synthetic_review_and_preview_render_with_no_operational_capability() -> None:
    response = _client().get("/")
    assert "نتیجه و پیش‌نمایش فرم" in response.text
    assert "SYNTH_INCOME_REVIEWED" in response.text
    assert "EUR_SYNTHETIC" in response.text
    assert "LOCAL_E10_2024_XSD_VALIDATED" in response.text
    assert "LOCAL_THIRTY_FIVE_RULE_SUBSET_PASS" in response.text
    assert "official receipt" not in response.text.lower()

def test_decision_queue_is_display_only():
    response=_client().get("/")
    assert "صف تصمیم انسانی" in response.text and "SYNTH-GATE-" in response.text
    assert "نیازمند تصمیم انسانی" in response.text and "بازبینی پیش‌نمایش مصنوعی" in response.text
    assert "<form" not in response.text and "تأیید تصمیم" not in response.text

def test_submission_readiness_keeps_both_approvals_separate_and_unapproved():
    text=_client().get("/").text
    assert "مرحلهٔ یک · مجوز محتوا" in text and "مرحلهٔ دو · مجوز مقصد" in text
    assert text.count("NOT_APPROVED") >= 2 and "TRANSMITTER_NOT_IMPLEMENTED" in text
    assert "LOCAL_MAPPING_XSD_AND_RULE_SUBSET_PASS" in text
    assert "موتور رسمی ERiC" in text and "NOT_EXECUTED" in text


def test_support_and_recovery_diagnostics_are_display_only_and_current():
    text = _client().get("/").text
    assert "وضعیت عملیاتی امن" in text
    assert "READ_ONLY_RECOVERY_DIAGNOSTICS_AVAILABLE" in text
    assert "RECEIPT_NOT_AVAILABLE_NO_TRANSMISSION" in text
    assert "نگاشت رسمی هنوز بازیابی نشده" not in text
    assert "نگاشت محلی E10/2024 و اعتبارسنجی XSD تکمیل شده" in text


def test_all_local_responses_apply_fail_closed_browser_security_headers():
    client = _client()
    responses = (
        client.get("/"),
        client.get("/workspace", params={"case_id": "SYNTH-CASE-002", "tax_year": 2025}),
        client.get("/health"),
        client.get("/missing"),
    )
    for response in responses:
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["permissions-policy"] == "camera=(), geolocation=(), microphone=()"
        policy = response.headers["content-security-policy"]
        assert "default-src 'self'" in policy
        assert "connect-src 'self'" in policy
        assert "frame-ancestors 'none'" in policy
        assert "form-action 'none'" in policy
        assert "http:" not in policy and "https:" not in policy
