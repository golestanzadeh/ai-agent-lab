"""UI25 isolated functional smoke and restart regression."""
from fastapi.testclient import TestClient
from agent_lab.ui_dashboard import create_dashboard_app
from agent_lab.ui_functional_test_store import FunctionalTestStore


def test_functional_case_document_issue_audit_and_restart(tmp_path):
    path=tmp_path/"test.sqlite3"
    store=FunctionalTestStore(path)
    client=TestClient(create_dashboard_app(test_store=store))
    assert client.get("/?tab=cases").status_code==200
    assert client.post("/test/cases",data={"case_id":"TEST-2025-A","tax_year":"2025"},follow_redirects=False).status_code==303
    assert client.post("/test/cases",data={"case_id":"TEST-2025-B","tax_year":"2025"},follow_redirects=False).status_code==303
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
    assert len(reopened.detail("TEST-2025-A")["documents"])==1
    assert reopened.detail("TEST-2025-A")["issues"][0][3]=="ANSWERED"
    reopened.close()


def test_production_dashboard_rejects_test_mutations():
    client=TestClient(create_dashboard_app())
    assert client.post("/test/cases",data={"case_id":"TEST-X","tax_year":"2025"}).status_code==404
    assert "form-action 'none'" in client.get("/").headers["content-security-policy"]
