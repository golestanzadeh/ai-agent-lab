from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agent_lab.orchestrator_kernel import ContractError, OrchestratorKernel
from agent_lab.ui_dashboard import create_dashboard_app
from agent_lab.ui_functional_test_store import FunctionalTestStore
from agent_lab.ui_kernel_projection import ReadOnlyKernelProjection
from agent_lab.ui_synthetic_document_parser import PARSER_SCHEMA, parse_synthetic_wage_statement
from agent_lab.ui_synthetic_kernel_execution import (
    EXTRACTION_AUTHORITY_REFERENCE,
    WORKER_ID,
    SyntheticCaseKernelExecutor,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "contracts" / "orchestrator" / "v1"
FIXTURE = ROOT / "tests" / "fixtures" / "ui25" / "synthetic-wage-statement-owner-retest.txt"
ORIGIN = "http://127.0.0.1:8766"


def _extraction(executor: SyntheticCaseKernelExecutor, *, run_id: str):
    content = FIXTURE.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    return executor.execute(
        case_id="TEST-RECOVERY", tax_year=2025, run_id=run_id,
        document_reference=f"test-document://TEST-RECOVERY/sha256:{digest}",
        document_digest=digest, document_content=content, content_type="text/plain",
    )


def _counts(database: Path) -> dict[str, object]:
    with OrchestratorKernel(database, CONTRACT_ROOT) as kernel:
        kernel.verify_audit_chain()
        return {
            "tasks": kernel._connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],
            "manifests": kernel._connection.execute("SELECT COUNT(*) FROM manifests").fetchone()[0],
            "responses": kernel._connection.execute("SELECT COUNT(*) FROM responses").fetchone()[0],
            "budget": kernel._connection.execute("SELECT COUNT(*) FROM budget_usage").fetchone()[0],
            "kill_switch": kernel.kill_switch_state(),
        }


@pytest.mark.parametrize("boundary", [
    "after_task_registration",
    "during_manifest_registration",
    "during_manifest_validation",
    "during_worker_execution",
    "before_response_persistence",
])
def test_atomic_execution_rolls_back_every_failure_boundary_and_allows_retry(
    tmp_path, monkeypatch, boundary,
):
    database = tmp_path / f"{boundary}.sqlite3"
    executor = SyntheticCaseKernelExecutor(database, CONTRACT_ROOT)

    if boundary == "after_task_registration":
        original = OrchestratorKernel.register_task

        def fail(kernel, *args, **kwargs):
            original(kernel, *args, **kwargs)
            raise RuntimeError(boundary)

        monkeypatch.setattr(OrchestratorKernel, "register_task", fail)
    elif boundary == "during_manifest_registration":
        original = OrchestratorKernel.register_manifest

        def fail(kernel, *args, **kwargs):
            original(kernel, *args, **kwargs)
            raise RuntimeError(boundary)

        monkeypatch.setattr(OrchestratorKernel, "register_manifest", fail)
    elif boundary == "during_manifest_validation":
        original = OrchestratorKernel.validate_manifest

        def fail(kernel, *args, **kwargs):
            original(kernel, *args, **kwargs)
            raise RuntimeError(boundary)

        monkeypatch.setattr(OrchestratorKernel, "validate_manifest", fail)
    elif boundary == "during_worker_execution":
        def fail(*_args, **_kwargs):
            raise RuntimeError(boundary)

        monkeypatch.setattr(SyntheticCaseKernelExecutor, "_run_worker", staticmethod(fail))
    else:
        def fail(*_args, **_kwargs):
            raise RuntimeError(boundary)

        monkeypatch.setattr(OrchestratorKernel, "record_response", fail)

    with pytest.raises(RuntimeError, match=boundary):
        _extraction(executor, run_id="RUN-ATOMIC")
    assert _counts(database) == {
        "tasks": 0, "manifests": 0, "responses": 0, "budget": 0,
        "kill_switch": "HALTED",
    }

    monkeypatch.undo()
    result = _extraction(executor, run_id="RUN-ATOMIC")
    assert result["status"] == "AWAITING_ACCEPTANCE"
    assert result["recovered_from_task_id"] is None
    assert _counts(database) == {
        "tasks": 1, "manifests": 1, "responses": 1, "budget": 1,
        "kill_switch": "HALTED",
    }


def _seed_legacy_orphan(database: Path, *, run_id: str) -> str:
    content = FIXTURE.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    extraction = parse_synthetic_wage_statement(content, "text/plain")
    task_id, _manifest_id, _response_id = SyntheticCaseKernelExecutor._identities(
        "TEST-RECOVERY", 2025, run_id
    )
    now = datetime.now(timezone.utc)
    task = {
        "schema_version": 1, "task_id": task_id, "parent_task_id": None,
        "objective": "Extract one bounded synthetic document without tax interpretation",
        "role_id": "IMPLEMENTATION_AGENT", "actor_instance_id": WORKER_ID,
        "repository": "golestanzadeh/ai-agent-lab", "ref": "oi0002-identity-persistence",
        "case_context": {"case_id": "TEST-RECOVERY", "tax_year": 2025, "run_id": run_id},
        "inputs": [
            f"test-document://TEST-RECOVERY/sha256:{digest}", f"sha256:{digest}",
            f"parser://{PARSER_SCHEMA}", f"extraction://{extraction.digest}",
        ],
        "expected_outputs": [f"kernel://ui25/result/{task_id}"],
        "allowed_tools": ["synthetic_ui25_deterministic_worker"],
        "permissions": ["report_evidence"],
        "forbidden_actions": [
            "external_transfer", "use_real_data", "protected_persistence",
            "agent_spawn", "subprocess", "network_io",
        ],
        "budget": {"token_limit": 1, "tool_call_limit": 1, "cost_limit_usd": 0.01},
        "timeout_seconds": 30, "max_retries": 0,
        "acceptance_criteria": ["case-owned content produces a lineage-bound structured extraction"],
        "stop_conditions": ["scope mismatch", "kill switch not RUNNING", "duplicate task"],
        "escalation_route": ["MASTER_PROJECT_ORCHESTRATOR", "HUMAN_PROJECT_OWNER"],
        "created_at": now.isoformat(), "expires_at": (now + timedelta(minutes=10)).isoformat(),
        "status": "REGISTERED",
    }
    with OrchestratorKernel(database, CONTRACT_ROOT) as kernel:
        kernel.register_task(task, gate_triggers=())
        kernel.verify_audit_chain()
    return task_id


def test_restart_recovers_exact_legacy_orphan_once_without_rewriting_history(tmp_path):
    database = tmp_path / "legacy-orphan.sqlite3"
    original_task_id = _seed_legacy_orphan(database, run_id="RUN-LEGACY-ORPHAN")
    executor = SyntheticCaseKernelExecutor(database, CONTRACT_ROOT)
    result = _extraction(executor, run_id="RUN-LEGACY-ORPHAN")
    assert result["recovered_from_task_id"] == original_task_id

    with OrchestratorKernel(database, CONTRACT_ROOT) as kernel:
        kernel.verify_audit_chain()
        tasks = kernel._connection.execute(
            "SELECT task_id,parent_task_id,status,payload_json FROM tasks ORDER BY task_id"
        ).fetchall()
        assert len(tasks) == 2
        original = next(row for row in tasks if row["task_id"] == original_task_id)
        recovery = next(row for row in tasks if row["task_id"] != original_task_id)
        assert original["status"] == "REGISTERED"
        assert recovery["parent_task_id"] == original_task_id
        assert recovery["status"] == "AWAITING_ACCEPTANCE"
        assert json.loads(original["payload_json"])["actor_instance_id"] == WORKER_ID
        assert kernel._connection.execute("SELECT COUNT(*) FROM manifests").fetchone()[0] == 1
        assert kernel._connection.execute("SELECT COUNT(*) FROM responses").fetchone()[0] == 1
        assert kernel._connection.execute("SELECT COUNT(*) FROM budget_usage").fetchone()[0] == 1
        assert kernel.kill_switch_state() == "HALTED"

    with pytest.raises(ContractError, match="recovery was already attempted"):
        _extraction(executor, run_id="RUN-LEGACY-ORPHAN")
    assert _counts(database) == {
        "tasks": 2, "manifests": 1, "responses": 1, "budget": 1,
        "kill_switch": "HALTED",
    }


def test_actor_instance_is_unique_per_run_and_prevents_original_orphan_bug(tmp_path):
    database = tmp_path / "sequential.sqlite3"
    executor = SyntheticCaseKernelExecutor(database, CONTRACT_ROOT)
    executor.execute(
        case_id="TEST-RECOVERY", tax_year=2025, run_id="RUN-FIRST", synthetic_value=1
    )
    _extraction(executor, run_id="RUN-SECOND")
    with OrchestratorKernel(database, CONTRACT_ROOT) as kernel:
        actors = [row[0] for row in kernel._connection.execute(
            "SELECT actor_instance_id FROM manifests ORDER BY manifest_id"
        )]
        assert len(actors) == len(set(actors)) == 2
        assert kernel._connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 2
        assert kernel._connection.execute("SELECT COUNT(*) FROM responses").fetchone()[0] == 2
        assert kernel.kill_switch_state() == "HALTED"
        kernel.verify_audit_chain()


def test_ui_recovers_legacy_orphan_and_restart_projects_verified_result(tmp_path):
    case_database = tmp_path / "ui.sqlite3"
    kernel_database = tmp_path / "kernel.sqlite3"
    content = FIXTURE.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    store = FunctionalTestStore(case_database)
    store.create_case("TEST-RECOVERY", 2025)
    store.add_document("TEST-RECOVERY", "Recovery fixture", content, "text/plain")
    original_task_id = _seed_legacy_orphan(kernel_database, run_id="RUN-OWNER-RECOVERY")

    executor = SyntheticCaseKernelExecutor(kernel_database, CONTRACT_ROOT)
    app = create_dashboard_app(
        test_store=store,
        read_kernel_projection=ReadOnlyKernelProjection(kernel_database).read,
        execute_kernel_task=executor.execute,
    )
    test_client = TestClient(app, base_url=ORIGIN, headers={"origin": ORIGIN})
    response = test_client.post(
        "/test/kernel/documents/extract",
        data={
            "case_id": "TEST-RECOVERY", "run_id": "RUN-OWNER-RECOVERY",
            "document_digest": digest, "lang": "fa-IR",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    analysis = test_client.get(response.headers["location"])
    assert original_task_id in analysis.text
    assert "TEST-EMPLOYER-OWNER" in analysis.text
    assert "55000.00" in analysis.text
    assert "10250.00" in analysis.text
    store.close()

    reopened = FunctionalTestStore(case_database)
    restarted = TestClient(
        create_dashboard_app(
            test_store=reopened,
            read_kernel_projection=ReadOnlyKernelProjection(kernel_database).read,
            execute_kernel_task=SyntheticCaseKernelExecutor(
                kernel_database, CONTRACT_ROOT
            ).execute,
        ),
        base_url=ORIGIN, headers={"origin": ORIGIN},
    )
    restart_page = restarted.get(
        "/",
        params={
            "tab": "analysis", "case_id": "TEST-RECOVERY",
            "run_id": "RUN-OWNER-RECOVERY", "lang": "de-DE",
        },
    )
    assert restart_page.status_code == 200
    assert "TEST-EMPLOYER-OWNER" in restart_page.text
    assert '<html lang="de-DE" dir="ltr">' in restart_page.text
    replay = restarted.post(
        "/test/kernel/documents/extract",
        data={
            "case_id": "TEST-RECOVERY", "run_id": "RUN-OWNER-RECOVERY",
            "document_digest": digest, "lang": "de-DE",
        },
        follow_redirects=False,
    )
    assert replay.status_code == 303
    assert "error=execution_conflict" in replay.headers["location"]
    assert _counts(kernel_database) == {
        "tasks": 2, "manifests": 1, "responses": 1, "budget": 1,
        "kill_switch": "HALTED",
    }
    reopened.close()
