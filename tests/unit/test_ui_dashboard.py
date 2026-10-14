"""UI25-01 dashboard must never present invented cases as live."""
import re

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
    assert 'lang="fa-IR" dir="rtl"' in response.text
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


def test_all_tabs_are_navigable_and_truthful():
    client = TestClient(create_dashboard_app())
    names = {"overview": "نمای کلی", "cases": "پرونده‌ها", "family": "خانواده", "documents": "مدارک", "analysis": "تحلیل", "issues": "پرسش‌ها", "result": "نتیجه", "declaration": "اظهارنامه", "approval": "تأیید و ارسال", "activity": "فعالیت‌ها"}
    for tab, label in names.items():
        response = client.get("/", params={"tab": tab})
        assert response.status_code == 200
        assert label in response.text
        assert "SYNTH-CASE" not in response.text
        assert response.headers["cache-control"] == "no-store"
    approval = client.get("/?tab=approval").text
    assert "۱. تأیید صحت محتوا" in approval
    assert "۲. مجوز مقصد و ارسال" in approval
    assert 'disabled' in approval
    assert client.get("/?tab=unknown").status_code == 404


def test_german_ltr_mode_and_language_navigation_are_real():
    client = TestClient(create_dashboard_app())
    page = client.get("/", params={"lang": "de-DE"})
    assert page.status_code == 200
    assert '<html lang="de-DE" dir="ltr">' in page.text
    assert "Übersicht der Steuerfälle" in page.text
    assert "ELSTER-Übermittlung ist deaktiviert" in page.text
    assert "tab=documents&lang=de-DE" in page.text
    assert client.get("/", params={"lang": "unknown"}).status_code == 404


def test_german_product_dashboard_and_tabs_do_not_leak_persian_copy():
    records = (DashboardCase("CASE-A", 2025, "ACTIVE"),)
    client = TestClient(create_dashboard_app(read_cases=lambda: records))
    for tab in ("overview", "cases", "family", "documents", "analysis", "issues", "result", "declaration", "approval", "activity"):
        page = client.get("/", params={"lang": "de-DE", "tab": tab, "case_id": "CASE-A"})
        assert page.status_code == 200
        assert '<html lang="de-DE" dir="ltr">' in page.text
        assert "ELSTER-Übermittlung ist deaktiviert" in page.text
        assert "case_id=CASE-A" in page.text and "lang=de-DE" in page.text
        # The language switch intentionally spells the target language in Persian.
        without_switch = page.text.replace(">فارسی<", "><")
        assert re.search(r"[\u0600-\u06ff]", without_switch) is None


def test_german_empty_and_fail_closed_states_are_fully_localized():
    client = TestClient(create_dashboard_app())
    unavailable = client.get("/", params={"lang": "de-DE"}).text
    assert "Noch keine verifizierte Verbindung" in unavailable
    assert "Steuerfallquelle nicht verbunden" in unavailable
    empty = TestClient(create_dashboard_app(read_cases=lambda: ())).get(
        "/", params={"lang": "de-DE"}
    ).text
    assert "Keine Steuerfälle verfügbar" in empty


def test_submission_navigation_is_inert_and_has_no_control():
    page = TestClient(create_dashboard_app()).get("/").text
    assert 'aria-disabled="true"' in page
    assert "tab=approval&amp;lang=" not in page
    assert "ELSTER" in page


@pytest.mark.parametrize(
    ("status", "persian", "german"),
    [
        ("CREATED", "ایجادشده", "Erstellt"),
        ("ACTIVE", "فعال", "Aktiv"),
        ("PROCESSING", "در حال پردازش", "In Bearbeitung"),
        ("REVIEW_REQUIRED", "نیازمند بررسی", "Prüfung erforderlich"),
        ("COMPLETED", "تکمیل‌شده", "Abgeschlossen"),
        ("ARCHIVED", "بایگانی‌شده", "Archiviert"),
        ("BLOCKED", "مسدود", "Blockiert"),
    ],
)
def test_lifecycle_status_is_localized_without_losing_canonical_code(status, persian, german):
    records = (DashboardCase("CASE-A", 2025, status),)
    client = TestClient(create_dashboard_app(read_cases=lambda: records))
    fa = client.get("/", params={"case_id": "CASE-A", "tab": "cases"}).text
    de = client.get("/", params={"case_id": "CASE-A", "tab": "cases", "lang": "de-DE"}).text
    assert persian in fa
    assert german in de
    assert f'data-status-code="{status}"' in fa
    assert f'data-status-code="{status}"' in de


def test_selected_case_is_announced_semantically_in_both_directions():
    records = (
        DashboardCase("CASE-A", 2024, "ACTIVE"),
        DashboardCase("CASE-B", 2025, "REVIEW_REQUIRED"),
    )
    client = TestClient(create_dashboard_app(read_cases=lambda: records))
    for lang, direction in (("fa-IR", "rtl"), ("de-DE", "ltr")):
        page = client.get("/", params={"case_id": "CASE-A", "lang": lang}).text
        assert f'<html lang="{lang}" dir="{direction}">' in page
        assert page.count('aria-current="true"') == 1
        selected = re.search(r'<a class="case-row selected"[^>]+>', page)
        assert selected is not None
        assert 'case_id=CASE-A' in selected.group(0)
        assert 'aria-current="true"' in selected.group(0)


def test_collapsed_mobile_navigation_keeps_localized_accessible_names():
    client = TestClient(create_dashboard_app())
    expected = {
        "fa-IR": ("نمای کلی", "پرونده‌ها", "خانواده", "مدارک", "تحلیل", "پرسش‌ها", "نتیجه", "اظهارنامه", "فعالیت‌ها"),
        "de-DE": ("Übersicht", "Steuerfälle", "Familie", "Dokumente", "Analyse", "Rückfragen", "Ergebnis", "Steuererklärung", "Aktivitäten"),
    }
    for lang, labels in expected.items():
        page = client.get("/", params={"lang": lang}).text
        for label in labels:
            assert f'aria-label="{label}"' in page
