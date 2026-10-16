"""UI25 isolated functional smoke and restart regression."""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from agent_lab.ui_dashboard import DashboardCase, create_dashboard_app
from agent_lab.ui_functional_test_store import FunctionalTestStore
from agent_lab.ui_kernel_projection import ReadOnlyKernelProjection
from agent_lab.orchestrator_kernel import OrchestratorKernel


CONTRACT_ROOT = Path(__file__).resolve().parents[2] / "contracts" / "orchestrator" / "v1"


def _kernel_task(*, case_id="TEST-2025-UI", tax_year=2025, run_id="RUN-2025-UI", task_id="TASK-UI-001"):
    now = datetime.now(timezone.utc)
    return {
        "schema_version": 1, "task_id": task_id, "parent_task_id": None,
        "objective": "Expose synthetic status without executing it",
        "role_id": "IMPLEMENTATION_AGENT", "actor_instance_id": "AGI-UI-TEST",
        "repository": "golestanzadeh/ai-agent-lab", "ref": "oi0002-identity-persistence",
        "case_context": {"case_id": case_id, "tax_year": tax_year, "run_id": run_id},
        "inputs": [], "expected_outputs": ["test://status"], "allowed_tools": [],
        "permissions": [], "forbidden_actions": ["dispatch"],
        "budget": {"token_limit": 100, "tool_call_limit": 1, "cost_limit_usd": 1.0},
        "timeout_seconds": 60, "max_retries": 0,
        "acceptance_criteria": ["read-only status visible"],
        "stop_conditions": ["scope mismatch"],
        "escalation_route": ["HUMAN_PROJECT_OWNER"],
        "created_at": (now - timedelta(minutes=1)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(), "status": "REGISTERED",
    }


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


def test_dashboard_projects_genuine_kernel_status_with_exact_scope_and_restart(tmp_path):
    ui_database = tmp_path / "ui.sqlite3"
    kernel_database = tmp_path / "kernel.sqlite3"
    store = FunctionalTestStore(ui_database)
    store.create_case("TEST-2025-UI", 2025)
    with OrchestratorKernel(kernel_database, CONTRACT_ROOT) as kernel:
        kernel.register_task(_kernel_task(), gate_triggers=())

    projection = ReadOnlyKernelProjection(kernel_database)
    client = TestClient(create_dashboard_app(
        test_store=store, read_kernel_projection=projection.read
    ))
    assert client.get("/", params={
        "tab": "analysis", "case_id": "TEST-2025-UI"
    }).status_code == 400
    page = client.get("/", params={
        "tab": "analysis", "case_id": "TEST-2025-UI", "run_id": "RUN-2025-UI",
        "lang": "fa-IR",
    })
    assert page.status_code == 200
    assert "وضعیت واقعی Kernel" in page.text
    assert "TASK-UI-001" in page.text
    assert 'data-kernel-task-status="REGISTERED"' in page.text
    assert "اجرا فقط با اقدام صریح کاربر آغاز می‌شود" in page.text
    german = client.get("/", params={
        "tab": "activity", "case_id": "TEST-2025-UI", "run_id": "RUN-2025-UI",
        "lang": "de-DE",
    })
    assert german.status_code == 200
    assert "Echter Kernel-Status" in german.text
    assert "ausdrückliche Benutzeraktion" in german.text
    assert "run_id=RUN-2025-UI" in german.text

    assert client.get("/", params={
        "tab": "analysis", "case_id": "TEST-2025-UI", "run_id": "RUN-WRONG"
    }).status_code == 403
    store.close()

    reopened = FunctionalTestStore(ui_database)
    restarted_client = TestClient(create_dashboard_app(
        test_store=reopened,
        read_kernel_projection=ReadOnlyKernelProjection(kernel_database).read,
    ))
    restarted = restarted_client.get("/", params={
        "tab": "analysis", "case_id": "TEST-2025-UI", "run_id": "RUN-2025-UI"
    })
    assert restarted.status_code == 200
    assert "TASK-UI-001" in restarted.text
    reopened.close()


def test_dashboard_kernel_projection_rejects_year_and_case_mismatch(tmp_path):
    store = FunctionalTestStore(tmp_path / "ui.sqlite3")
    store.create_case("TEST-A", 2025)
    store.create_case("TEST-B", 2025)
    kernel_database = tmp_path / "kernel.sqlite3"
    with OrchestratorKernel(kernel_database, CONTRACT_ROOT) as kernel:
        kernel.register_task(_kernel_task(case_id="TEST-A", run_id="RUN-A"), gate_triggers=())
    client = TestClient(create_dashboard_app(
        test_store=store,
        read_kernel_projection=ReadOnlyKernelProjection(kernel_database).read,
    ))
    assert client.get("/", params={
        "tab": "analysis", "case_id": "TEST-B", "run_id": "RUN-A"
    }).status_code == 403
    store.close()
