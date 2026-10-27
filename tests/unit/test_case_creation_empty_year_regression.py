from fastapi.testclient import TestClient
from agent_lab.ui_dashboard import DashboardCase, create_dashboard_app


def test_empty_year_confirmation_can_commit_once():
    created = []
    records = (DashboardCase("CASE-2025-0001", 2025, "CREATED"),)
    app = create_dashboard_app(read_cases=lambda: records, create_real_case=lambda year, mode: created.append((year, mode)) or "CASE-2026-0001")
    client = TestClient(app, base_url="http://127.0.0.1:8766", headers={"Origin": "http://127.0.0.1:8766"})
    payload = {"tax_year": "2026", "assessment_mode": "JOINT_ASSESSMENT", "lang": "de-DE"}
    preview = client.post("/cases/create", data=payload, headers={"Accept": "application/json"})
    assert preview.status_code == 200
    token = preview.json()
    assert token["confirmed_cases"] == ""
    assert token["requires_confirmation"] is True
    response = client.post("/cases/create", data={**payload, "confirmed_cases": token["confirmed_cases"], "confirmation_token": token["confirmation_token"]}, follow_redirects=False)
    assert response.status_code == 303
    assert "CASE-2026-0001" in response.headers["location"]
    assert created == [(2026, "JOINT_ASSESSMENT")]


def test_case_year_picker_contains_case_options():
    records = tuple(DashboardCase(f"CASE-2025-{n:04d}", 2025, "CREATED") for n in range(1, 5))
    page = TestClient(create_dashboard_app(read_cases=lambda: records)).get("/?tab=cases&case_id=CASE-2025-0004")
    assert page.status_code == 200
    assert 'id="case-id-select"' in page.text
    for n in range(1, 5):
        assert f'value="CASE-2025-{n:04d}"' in page.text