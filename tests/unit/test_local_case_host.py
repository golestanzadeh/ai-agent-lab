"""Real local case workflow integration without modifying the user's database."""
from fastapi.testclient import TestClient

from agent_lab.local_case_host import LocalCaseHost, create_local_case_app


def test_local_case_create_reopen_and_duplicate_rejection(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    drive = tmp_path / "drive" / "AI-Tax-Agent"
    (drive / "Tax_Years" / "2024").mkdir(parents=True)
    (drive / "System").mkdir()
    monkeypatch.setenv("AI_TAX_DRIVE_ROOT", str(drive))
    first = LocalCaseHost()
    created = first.create_case(2026, "JOINT_ASSESSMENT")
    assert created == "CASE-2026-0001"
    second = LocalCaseHost()
    assert [c.case_id for c in second.read_cases()] == [created]
    assert (drive / "Tax_Years" / "2026" / "Cases" / created / "Documents").is_dir()
    assert first.persistence.load_completed_storage_references(
        owner_id=first.owner_id, allowed_case_ids=frozenset({created}))[0].scope.provider == "google_drive_desktop"
    try:
        second.create_case(2026, "INDIVIDUAL_ASSESSMENT")
    except ValueError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("duplicate owner/year must fail")


def test_browser_case_create_and_csrf(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    drive = tmp_path / "drive" / "AI-Tax-Agent"
    (drive / "Tax_Years" / "2024").mkdir(parents=True)
    (drive / "System").mkdir()
    monkeypatch.setenv("AI_TAX_DRIVE_ROOT", str(drive))
    app = create_local_case_app()
    client = TestClient(app)
    form = {"tax_year": "2027", "assessment_mode": "INDIVIDUAL_ASSESSMENT", "lang": "fa-IR"}
    assert client.post("/cases/create", data=form, follow_redirects=False).status_code == 403
    response = client.post("/cases/create", data=form, follow_redirects=False,
                           headers={"origin": "http://127.0.0.1:8766", "host": "127.0.0.1:8766"})
    assert response.status_code == 303
    assert "CASE-2027-0001" in response.headers["location"]
    assert "CASE-2027-0001" in client.get("/?tab=cases").text
