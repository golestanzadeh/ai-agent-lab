"""UI25-01 dashboard must never present invented cases as live."""
import pytest
from fastapi.testclient import TestClient
from agent_lab.ui_dashboard import DashboardCase, DashboardUnavailable, create_dashboard_app


def test_default_unavailable_has_no_synthetic_or_real_case():
    client = TestClient(create_dashboard_app())
    response = client.get("/")
    assert response.status_code == 200
    assert "منبع پرونده متصل نیست" in response.text
    assert "SYNTH-CASE" not in response.text
    assert "CASE-001" not in response.text
    assert 'lang="fa" dir="rtl"' in response.text
    assert client.get("/?case_id=CASE-001").status_code == 503
    assert client.get("/health").json()["source"] == "unavailable"


def test_authorized_read_only_source_shows_exact_cases_and_scopes():
    records = (DashboardCase("CASE-A", 2024, "REVIEW_REQUIRED"), DashboardCase("CASE-B", 2025, "ACTIVE"))
    client = TestClient(create_dashboard_app(read_cases=lambda: records))
    page = client.get("/")
    assert page.status_code == 200
    assert "CASE-A" in page.text and "CASE-B" in page.text
    assert "منبع تأییدشده" in page.text
    assert page.text.index("CASE-B") < page.text.index("CASE-A")
    assert client.get("/?case_id=CASE-A").status_code == 200
    assert client.get("/?case_id=CASE-UNKNOWN").status_code == 404
    assert client.post("/submit").status_code == 404


def test_bad_or_ambiguous_source_fails_closed():
    bad_sources = [
        lambda: (DashboardCase("CASE-A", 2024, "ACTIVE"), DashboardCase("CASE-A", 2025, "ACTIVE")),
        lambda: ("invalid",),
        lambda: (_ for _ in ()).throw(DashboardUnavailable("offline")),
    ]
    for source in bad_sources:
        page = TestClient(create_dashboard_app(read_cases=source)).get("/")
        assert page.status_code == 200
        assert "منبع پرونده متصل نیست" in page.text
        assert "CASE-A" not in page.text
        assert TestClient(create_dashboard_app(read_cases=source)).get("/?case_id=CASE-A").status_code == 503


def test_security_headers_and_no_external_calls():
    client = TestClient(create_dashboard_app())
    response = client.get("/")
    assert response.headers["cache-control"] == "no-store"
    assert "connect-src 'self'" in response.headers["content-security-policy"]
    assert "https://" not in response.text
    assert "ارسال به ELSTER غیرفعال است" in response.text


def test_rejects_synthetic_identity_and_unknown_status():
    with pytest.raises(ValueError):
        DashboardCase("SYNTH-CASE-001", 2024, "ACTIVE")
    with pytest.raises(ValueError):
        DashboardCase("CASE-A", 2024, "APPROVED_FOR_SUBMISSION")
