from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace

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


def test_case_owned_document_digest_executes_through_kernel_and_survives_restart(tmp_path):
    ui_database = tmp_path / "ui.sqlite3"
    kernel_database = tmp_path / "kernel.sqlite3"
    store = FunctionalTestStore(ui_database)
    store.create_case("TEST-2025-DOC", 2025)
    store.add_document("TEST-2025-DOC", "Synthetic wage evidence", b"synthetic bytes only")
    document = store.detail("TEST-2025-DOC")["documents"][0]
    executor = SyntheticCaseKernelExecutor(kernel_database, CONTRACT_ROOT)
    client = TestClient(
        create_dashboard_app(
            test_store=store,
            read_kernel_projection=ReadOnlyKernelProjection(kernel_database).read,
            execute_kernel_task=executor.execute,
        ),
        base_url="http://127.0.0.1:8766",
        headers={"origin": "http://127.0.0.1:8766"},
    )

    response = client.post(
        "/test/kernel/documents/validate",
        data={
            "case_id": "TEST-2025-DOC", "run_id": "RUN-DOC-001",
            "document_digest": document[1],
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    page = client.get(response.headers["location"])
    assert page.status_code == 200
    assert "SYNTHETIC_DOCUMENT_EVIDENCE=VALID" in page.text
    assert f"test-document://TEST-2025-DOC/sha256:{document[1]}" in page.text
    assert f"DOCUMENT_DIGEST=sha256:{document[1]}" in page.text
    assert "CONTENT_INTERPRETATION=NOT_PERFORMED" in page.text
    assert 'data-kernel-task-status="AWAITING_ACCEPTANCE"' in page.text

    with OrchestratorKernel(kernel_database, CONTRACT_ROOT) as kernel:
        kernel.verify_audit_chain()
        assert kernel.kill_switch_state() == "HALTED"
        task = json.loads(kernel._connection.execute(
            "SELECT payload_json FROM tasks"
        ).fetchone()[0])
        assert task["inputs"] == [
            f"test-document://TEST-2025-DOC/sha256:{document[1]}"
        ]
        assert "interpret" not in task["allowed_tools"]

    store.close()
    reopened = FunctionalTestStore(ui_database)
    restart_page = TestClient(create_dashboard_app(
        test_store=reopened,
        read_kernel_projection=ReadOnlyKernelProjection(kernel_database).read,
        execute_kernel_task=executor.execute,
    )).get("/", params={
        "tab": "analysis", "case_id": "TEST-2025-DOC", "run_id": "RUN-DOC-001",
    })
    assert "SYNTHETIC_DOCUMENT_EVIDENCE=VALID" in restart_page.text
    reopened.close()


def test_document_execution_rejects_missing_altered_cross_case_and_replay(tmp_path):
    store = FunctionalTestStore(tmp_path / "ui.sqlite3")
    for case_id in ("TEST-DOC-A", "TEST-DOC-B"):
        store.create_case(case_id, 2025)
    store.add_document("TEST-DOC-A", "A", b"case A synthetic")
    digest = store.detail("TEST-DOC-A")["documents"][0][1]
    with pytest.raises(ValueError, match="owned"):
        store.resolve_document("TEST-DOC-B", digest)
    with pytest.raises(ValueError, match="malformed"):
        store.resolve_document("TEST-DOC-A", "0" * 63)
    with pytest.raises(ValueError, match="owned"):
        store.resolve_document("TEST-DOC-A", "0" * 64)

    executor = SyntheticCaseKernelExecutor(tmp_path / "kernel.sqlite3", CONTRACT_ROOT)
    reference = f"test-document://TEST-DOC-A/sha256:{digest}"
    result = executor.execute(
        case_id="TEST-DOC-A", tax_year=2025, run_id="RUN-DOC-A",
        document_reference=reference, document_digest=digest,
    )
    assert result["result"] == "VALID"
    with pytest.raises(ContractError, match="already"):
        executor.execute(
            case_id="TEST-DOC-A", tax_year=2025, run_id="RUN-DOC-A",
            document_reference=reference, document_digest=digest,
        )
    with pytest.raises(PermissionDenied, match="another case"):
        executor.execute(
            case_id="TEST-DOC-B", tax_year=2025, run_id="RUN-DOC-A",
            document_reference=f"test-document://TEST-DOC-B/sha256:{digest}",
            document_digest=digest,
        )
    with pytest.raises(PermissionDenied, match="2025"):
        executor.execute(
            case_id="TEST-DOC-A", tax_year=2024, run_id="RUN-DOC-YEAR",
            document_reference=reference, document_digest=digest,
        )
    with pytest.raises(PermissionDenied, match="bound"):
        executor.execute(
            case_id="TEST-DOC-A", tax_year=2025, run_id="RUN-DOC-ALTERED",
            document_reference=reference, document_digest="0" * 64,
        )
    store.close()


def test_document_permission_denial_and_exception_restore_kill_switch(tmp_path, monkeypatch):
    database = tmp_path / "kernel.sqlite3"
    executor = SyntheticCaseKernelExecutor(database, CONTRACT_ROOT)
    digest = "1" * 64
    reference = f"test-document://TEST-DOC/sha256:{digest}"
    monkeypatch.setattr(
        OrchestratorKernel, "permission_decision",
        lambda *args, **kwargs: SimpleNamespace(allowed=False),
    )
    with pytest.raises(PermissionDenied, match="denied"):
        executor.execute(
            case_id="TEST-DOC", tax_year=2025, run_id="RUN-DENIED",
            document_reference=reference, document_digest=digest,
        )
    with OrchestratorKernel(database, CONTRACT_ROOT) as kernel:
        assert kernel.kill_switch_state() == "HALTED"
        kernel.verify_audit_chain()
        assert kernel._connection.execute("SELECT COUNT(*) FROM responses").fetchone()[0] == 0
        assert kernel._connection.execute(
            "SELECT COUNT(*) FROM manifests WHERE state='ACTIVE'"
        ).fetchone()[0] == 0
