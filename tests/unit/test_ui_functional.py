"""UI25 isolated functional smoke and restart regression."""
import pytest
from fastapi.testclient import TestClient
from agent_lab.ui_dashboard import DashboardCase, create_dashboard_app
from agent_lab.ui_functional_test_store import FunctionalTestStore


def test_functional_case_document_issue_audit_and_restart(tmp_path):
    path=tmp_path/"test.sqlite3"
    store=FunctionalTestStore(path)
    client=TestClient(create_dashboard_app(test_store=store))
    assert client.get("/?tab=cases").status_code==200
    assert client.post("/test/cases",data={"case_id":"TEST-2025-A","tax_year":"2025"},follow_redirects=False).status_code==303
    assert client.post("/test/cases",data={"case_id":"TEST-2025-B","tax_year":"2025"},follow_redirects=False).status_code==303
    canonical = store.case_state("TEST-2025-A")
    assert canonical.case_id == "TEST-2025-A"
    assert canonical.lifecycle_status == "READY"
    assert client.post("/test/cases",data={"case_id":"CASE-001","tax_year":"2024"}).status_code==400
    assert client.post("/test/documents",data={"case_id":"TEST-2025-A","label":"Test file"},files={"document":("test.txt",b"not private")},follow_redirects=False).status_code==303
    assert client.post("/test/documents",data={"case_id":"TEST-2025-A","label":"Duplicate"},files={"document":("test.txt",b"not private")},follow_redirects=False).headers["location"].endswith("added=0")
    assert client.post("/test/issues",data={"case_id":"TEST-2025-A","question":"Test question"},follow_redirects=False).status_code==303
    assert client.post("/test/issues/answer",data={"case_id":"TEST-2025-A","issue_id":"1","answer":"Test answer"},follow_redirects=False).status_code==303
    assert client.post("/test/issues/answer",data={"case_id":"TEST-2025-B","issue_id":"1","answer":"Cross-case"}).status_code==400
    assert client.get("/?tab=documents&case_id=TEST-2025-A").status_code==200
    assert "Test file" in client.get("/?tab=documents&case_id=TEST-2025-A").text
    assert "Test file" not in client.get("/?tab=documents&case_id=TEST-2025-B").text
    assert "Test answer" in client.get("/?tab=issues&case_id=TEST-2025-A").text
    assert "Test answer" not in client.get("/?tab=issues&case_id=TEST-2025-B").text
    assert "ISSUE_ANSWERED" in client.get("/?tab=activity&case_id=TEST-2025-A").text
    assert "form-action 'self'" in client.get("/").headers["content-security-policy"]
    assert client.post("/submit").status_code==404
    store.close()
    reopened=FunctionalTestStore(path)
    assert len(reopened.cases())==2
    assert reopened.case_state("TEST-2025-A").case_id == "TEST-2025-A"
    assert len(reopened.detail("TEST-2025-A")["documents"])==1
    assert reopened.detail("TEST-2025-A")["issues"][0][3]=="ANSWERED"
    reopened.close()


def test_2025_case_ui_uses_canonical_backend_and_is_bilingual(tmp_path):
    path = tmp_path / "test.sqlite3"
    store = FunctionalTestStore(path)
    client = TestClient(create_dashboard_app(test_store=store))
    created = client.post(
        "/test/cases",
        data={"case_id": "TEST-2025-UI", "tax_year": "2025"},
        follow_redirects=False,
    )
    assert created.status_code == 303
    assert store.case_state("TEST-2025-UI").lifecycle_status == "READY"
    for lang, marker in (("fa-IR", "فقط آزمایش"), ("de-DE", "NUR TEST")):
        page = client.get(
            "/",
            params={"tab": "cases", "case_id": "TEST-2025-UI", "lang": lang},
        )
        assert page.status_code == 200
        assert "TEST-2025-UI" in page.text
        assert 'data-status-code="CREATED"' in page.text
        assert marker in page.text
        assert "case_id=TEST-2025-UI" in page.text
        assert f"lang={lang}" in page.text
    uploaded = client.post(
        "/test/documents",
        data={"case_id": "TEST-2025-UI", "label": "Synthetic 2025 evidence"},
        files={"document": ("synthetic.txt", b"synthetic only")},
        follow_redirects=False,
    )
    assert uploaded.status_code == 303
    de_documents = client.get(
        "/", params={"tab": "documents", "case_id": "TEST-2025-UI", "lang": "de-DE"}
    ).text
    assert "Hash eines Testdokuments registrieren" in de_documents
    assert "Synthetic 2025 evidence" in de_documents
    store.close()

    reopened = FunctionalTestStore(path)
    assert reopened.cases() == (DashboardCase("TEST-2025-UI", 2025, "CREATED"),)
    assert reopened.case_state("TEST-2025-UI").case_id == "TEST-2025-UI"
    assert reopened.detail("TEST-2025-UI")["documents"][0][0] == "Synthetic 2025 evidence"
    reopened.close()


def test_corrupt_persisted_case_fails_closed_on_reopen(tmp_path):
    path = tmp_path / "test.sqlite3"
    store = FunctionalTestStore(path)
    store.create_case("TEST-2025-CORRUPT", 2025)
    store._db.execute("UPDATE test_case SET status='UNVERIFIED'")
    store._db.commit()
    store.close()

    with pytest.raises(ValueError, match="UNVERIFIED"):
        FunctionalTestStore(path)


def test_production_dashboard_rejects_test_mutations():
    client=TestClient(create_dashboard_app())
    assert client.post("/test/cases",data={"case_id":"TEST-X","tax_year":"2025"}).status_code==404
    assert "form-action 'none'" in client.get("/").headers["content-security-policy"]
