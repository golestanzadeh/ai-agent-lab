"""Bilingual dashboard: no mixed Persian copy, no loss of navigation state."""
import re
from html import unescape
from fastapi.testclient import TestClient
from agent_lab.ui_dashboard import DashboardCase, create_dashboard_app, UI_TEXT

TABS = ("overview","cases","family","documents","analysis","issues","result","declaration","approval","activity")

def test_all_tabs_are_fully_localized_in_both_languages():
    client = TestClient(create_dashboard_app())
    for language, direction in (("fa-IR","rtl"),("de-DE","ltr")):
        for tab in TABS:
            response=client.get("/",params={"tab":tab,"lang":language})
            assert response.status_code == 200
            assert f'lang="{language}" dir="{direction}"' in response.text
            assert UI_TEXT[language][tab] in response.text
            assert "tab="+tab+"&lang="+UI_TEXT[language]["switch_code"] in unescape(response.text)
            assert 'aria-disabled="true"' in response.text
            if language=="de-DE":
                # German UI must not display Persian text in ordinary chrome.
                assert not re.search(r"[\u0600-\u06ff]", response.text.replace(UI_TEXT["de-DE"]["switch"], "")), tab

def test_case_selection_and_language_switch_preserve_scope():
    client=TestClient(create_dashboard_app(read_cases=lambda:(DashboardCase("CASE-A",2025,"ACTIVE"),)))
    page=client.get("/?tab=overview&lang=de-DE").text
    assert "case_id=CASE-A&tab=overview&lang=de-DE" in unescape(page)
    page=client.get("/?case_id=CASE-A&tab=documents&lang=de-DE").text
    assert "case_id=CASE-A&tab=documents&lang=fa-IR" in unescape(page)
    assert "Aktiv" in page
    assert "فعال" in client.get("/?case_id=CASE-A&tab=documents&lang=fa-IR").text

def test_catalog_parity_and_fail_closed_submission():
    assert set(UI_TEXT["fa-IR"])==set(UI_TEXT["de-DE"])
    for lang in ("fa-IR","de-DE"):
        c=TestClient(create_dashboard_app())
        assert c.post("/submit").status_code==404
        assert c.get("/?case_id=CASE-A&lang="+lang).status_code==503
