from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agent_lab.orchestrator_kernel import ContractError, OrchestratorKernel, PermissionDenied
from agent_lab.ui_dashboard import create_dashboard_app
from agent_lab.ui_functional_test_store import FunctionalTestStore
from agent_lab.ui_kernel_projection import KernelProjectionUnavailable, ReadOnlyKernelProjection
from agent_lab.ui_synthetic_kernel_execution import SyntheticCaseKernelExecutor, WORKER_ID


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "contracts" / "orchestrator" / "v1"


def test_explicit_ui_action_executes_once_and_displays_durable_result_after_restart(tmp_path):
    ui_database = tmp_path / "ui.sqlite3"
    kernel_database = tmp_path / "kernel.sqlite3"
    store = FunctionalTestStore(ui_database)
    store.create_case("TEST-2025-EXEC", 2025)
    executor = SyntheticCaseKernelExecutor(kernel_database, CONTRACT_ROOT)
    projection = ReadOnlyKernelProjection(kernel_database)
    client = TestClient(
        create_dashboard_app(
            test_store=store, read_kernel_projection=projection.read,
            execute_kernel_task=executor.execute,
        ),
        base_url="http://127.0.0.1:8766",
        headers={"origin": "http://127.0.0.1:8766"},
    )

    response = client.post("/test/kernel/execute", data={
        "case_id": "TEST-2025-EXEC", "run_id": "RUN-EXEC-001",
        "synthetic_value": "21",
    }, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].endswith(
        "tab=analysis&case_id=TEST-2025-EXEC&run_id=RUN-EXEC-001"
    )
    page = client.get(response.headers["location"])
    assert page.status_code == 200
    assert "SYNTHETIC_RESULT=42" in page.text
    assert WORKER_ID in page.text
    assert 'data-kernel-task-status="AWAITING_ACCEPTANCE"' in page.text

    with OrchestratorKernel(kernel_database, CONTRACT_ROOT) as kernel:
        assert kernel.kill_switch_state() == "HALTED"
        kernel.verify_audit_chain()
        assert kernel._connection.execute("SELECT COUNT(*) FROM responses").fetchone()[0] == 1
        assert kernel._connection.execute(
            "SELECT status FROM tasks"
        ).fetchone()[0] == "AWAITING_ACCEPTANCE"

    duplicate = client.post("/test/kernel/execute", data={
        "case_id": "TEST-2025-EXEC", "run_id": "RUN-EXEC-001",
        "synthetic_value": "99",
    })
    assert duplicate.status_code == 400
    with OrchestratorKernel(kernel_database, CONTRACT_ROOT) as kernel:
        assert kernel._connection.execute("SELECT COUNT(*) FROM responses").fetchone()[0] == 1
        manifest_id = kernel._connection.execute("SELECT manifest_id FROM manifests").fetchone()[0]
        with pytest.raises(PermissionDenied, match="denied"):
            executor._run_worker(
                kernel, manifest_id=manifest_id, case_id="TEST-2025-EXEC",
                tax_year=2025, run_id="RUN-EXEC-001", synthetic_value=21,
            )
    store.close()

    reopened = FunctionalTestStore(ui_database)
    restarted = TestClient(create_dashboard_app(
        test_store=reopened,
        read_kernel_projection=ReadOnlyKernelProjection(kernel_database).read,
        execute_kernel_task=SyntheticCaseKernelExecutor(kernel_database, CONTRACT_ROOT).execute,
    ))
    restart_page = restarted.get("/", params={
        "tab": "analysis", "case_id": "TEST-2025-EXEC", "run_id": "RUN-EXEC-001",
        "lang": "de-DE",
    })
    assert restart_page.status_code == 200
    assert "SYNTHETIC_RESULT=42" in restart_page.text
    reopened.close()


def test_execution_rejects_unauthorized_scope_and_cross_scope_run_reuse(tmp_path):
    database = tmp_path / "kernel.sqlite3"
    executor = SyntheticCaseKernelExecutor(database, CONTRACT_ROOT)
    with pytest.raises(PermissionDenied, match="TEST"):
        executor.execute(case_id="CASE-001", tax_year=2025, run_id="RUN-A", synthetic_value=1)
    with pytest.raises(PermissionDenied, match="2025"):
        executor.execute(case_id="TEST-A", tax_year=2024, run_id="RUN-A", synthetic_value=1)
    with pytest.raises(ContractError, match="run_id"):
        executor.execute(case_id="TEST-A", tax_year=2025, run_id="bad/run", synthetic_value=1)
    assert not database.exists()

    first = executor.execute(case_id="TEST-A", tax_year=2025, run_id="RUN-SHARED", synthetic_value=1)
    assert first["result"] == 2
    with pytest.raises(PermissionDenied, match="another case"):
        executor.execute(case_id="TEST-B", tax_year=2025, run_id="RUN-SHARED", synthetic_value=1)
    with OrchestratorKernel(database, CONTRACT_ROOT) as kernel:
        assert kernel._connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 1
        kernel.verify_audit_chain()


def test_production_dashboard_cannot_receive_execution_adapter(tmp_path):
    executor = SyntheticCaseKernelExecutor(tmp_path / "kernel.sqlite3", CONTRACT_ROOT)
    with pytest.raises(ValueError, match="isolated test"):
        create_dashboard_app(execute_kernel_task=executor.execute)


def test_one_shot_execution_rejects_non_halted_kernel(tmp_path):
    database = tmp_path / "kernel.sqlite3"
    with OrchestratorKernel(database, CONTRACT_ROOT) as kernel:
        kernel.set_kill_switch(
            "RUNNING", actor_id="HUMAN_PROJECT_OWNER", authority_reference="test"
        )
        kernel.set_kill_switch(
            "PAUSED", actor_id="MASTER_PROJECT_ORCHESTRATOR", authority_reference="test"
        )
    executor = SyntheticCaseKernelExecutor(database, CONTRACT_ROOT)
    with pytest.raises(PermissionDenied, match="HALTED"):
        executor.execute(case_id="TEST-A", tax_year=2025, run_id="RUN-A", synthetic_value=1)
    with OrchestratorKernel(database, CONTRACT_ROOT) as kernel:
        assert kernel.kill_switch_state() == "PAUSED"
        assert kernel._connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0


def test_readback_rejects_response_rewrite_even_with_valid_json(tmp_path):
    database = tmp_path / "kernel.sqlite3"
    executor = SyntheticCaseKernelExecutor(database, CONTRACT_ROOT)
    executor.execute(case_id="TEST-A", tax_year=2025, run_id="RUN-A", synthetic_value=2)
    with sqlite3.connect(database) as connection:
        payload = json.loads(connection.execute(
            "SELECT payload_json FROM responses"
        ).fetchone()[0])
        payload["result_summary"] = "SYNTHETIC_RESULT=999999; WORKER=ATTACKER"
        connection.execute(
            "UPDATE responses SET payload_json=?", (json.dumps(payload),)
        )
    with pytest.raises(KernelProjectionUnavailable, match="bound to its audit"):
        ReadOnlyKernelProjection(database).read("TEST-A", 2025, "RUN-A")
