from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_lab.agent_runtime import DEMO_ACCEPTANCE_CRITERIA, DEMO_OBJECTIVE, LocalAgentRuntime, LocalWorkPackage
from agent_lab.orchestrator_kernel import ContractError, OrchestratorKernel, PermissionDenied


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "contracts" / "orchestrator" / "v1"


def package() -> LocalWorkPackage:
    return LocalWorkPackage("RUNTIME_TEST_001", DEMO_OBJECTIVE, ("synthetic://input/one",), DEMO_ACCEPTANCE_CRITERIA)


def runtime(tmp_path: Path) -> LocalAgentRuntime:
    repository = tmp_path / "repository"
    return LocalAgentRuntime(repository / "runtime.sqlite3", repository / "artifacts" / "agent-runtime", repository, CONTRACT_ROOT)


def test_four_role_runtime_pauses_recovers_accepts_and_halts(tmp_path):
    subject = runtime(tmp_path)
    started = subject.start(package())
    assert started["state"] == "PLANNED"
    with OrchestratorKernel(subject.database_path, CONTRACT_ROOT) as kernel:
        assert kernel.kill_switch_state() == "PAUSED"
        assert kernel.recover_latest_checkpoint()["checkpoint_id"] == "RUNTIME_TEST_001-PLANNED"
        planned_snapshot = json.loads(kernel._connection.execute("SELECT snapshot_json FROM checkpoints WHERE checkpoint_id='RUNTIME_TEST_001-PLANNED'").fetchone()[0])
        assert planned_snapshot["kill_switch"][0]["state"] == "PAUSED"

    recovered_subject = runtime(tmp_path)
    completed = recovered_subject.resume(package())
    assert completed["state"] == "COMPLETED"
    assert completed["audit_integrity"] == "PASS"
    assert completed["kill_switch"] == "HALTED"
    assert completed["counts"]["tasks"] == 6
    assert completed["counts"]["acceptance_records"] == 3
    assert completed["counts"]["dependencies"] == 2
    with OrchestratorKernel(subject.database_path, CONTRACT_ROOT) as kernel:
        actors = {row[0] for row in kernel._connection.execute("SELECT actor_instance_id FROM manifests")}
        assert len(actors) == 6
        roles = {row[0] for row in kernel._connection.execute("SELECT role_id FROM manifests")}
        assert roles == {"PLANNING_DEPENDENCY_AGENT", "IMPLEMENTATION_AGENT", "QUALITY_ENGINEERING_AGENT", "INDEPENDENT_ACCEPTANCE_AGENT"}
        completed_snapshot = json.loads(kernel._connection.execute("SELECT snapshot_json FROM checkpoints WHERE checkpoint_id='RUNTIME_TEST_001-COMPLETE'").fetchone()[0])
        assert completed_snapshot["kill_switch"][0]["state"] == "HALTED"
        for task_json, response_json in kernel._connection.execute(
            "SELECT t.payload_json, r.payload_json FROM tasks t JOIN responses r ON r.task_id=t.task_id"
        ):
            assert json.loads(response_json)["artifact_references"] == json.loads(task_json)["expected_outputs"]


def test_runtime_rejects_non_synthetic_input_before_state_creation(tmp_path):
    subject = runtime(tmp_path)
    invalid = LocalWorkPackage("RUNTIME_TEST_002", DEMO_OBJECTIVE, ("file://private/data",), DEMO_ACCEPTANCE_CRITERIA)
    with pytest.raises(PermissionDenied, match="synthetic"):
        subject.start(invalid)
    assert not subject.database_path.exists()


def test_runtime_rejects_artifact_root_outside_repository_artifacts(tmp_path):
    repository = tmp_path / "repository"
    with pytest.raises(PermissionDenied, match="artifact_root"):
        LocalAgentRuntime(repository / "runtime.sqlite3", tmp_path / "outside", repository, CONTRACT_ROOT)


def test_recovery_detects_plan_tampering(tmp_path):
    subject = runtime(tmp_path)
    subject.start(package())
    plan_path = subject.artifact_root / "runtime_test_001" / "plan.json"
    data = json.loads(plan_path.read_text(encoding="utf-8"))
    data["objective"] = "tampered"
    plan_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ContractError, match="immutable plan"):
        runtime(tmp_path).resume(package())


def test_duplicate_start_and_resume_replay_fail_closed(tmp_path):
    subject = runtime(tmp_path)
    subject.start(package())
    with pytest.raises(ContractError, match="requires new"):
        subject.start(package())
    subject.resume(package())
    with pytest.raises(ContractError):
        subject.resume(package())


def test_changed_package_contract_cannot_resume(tmp_path):
    subject = runtime(tmp_path)
    subject.start(package())
    changed = LocalWorkPackage("RUNTIME_TEST_001", DEMO_OBJECTIVE, ("synthetic://input/changed",), DEMO_ACCEPTANCE_CRITERIA)
    with pytest.raises(ContractError, match="recovery state"):
        runtime(tmp_path).resume(changed)


def test_free_form_contract_is_not_authorized(tmp_path):
    subject = runtime(tmp_path)
    changed = LocalWorkPackage("RUNTIME_TEST_003", "Process a caller-defined task", ("synthetic://input/one",), DEMO_ACCEPTANCE_CRITERIA)
    with pytest.raises(PermissionDenied, match="D-067"):
        subject.start(changed)


def test_valid_post_checkpoint_mutation_blocks_resume(tmp_path):
    subject = runtime(tmp_path)
    work = package()
    subject.start(work)
    extra = subject._task(
        work,
        "EXTRA",
        "PLANNING_DEPENDENCY_AGENT",
        "RUNTIME_TEST_001-EXTRA",
        None,
        "artifact://local/agent-runtime/extra",
        ["plan_tasks"],
    )
    with OrchestratorKernel(subject.database_path, CONTRACT_ROOT) as kernel:
        kernel.register_task(extra, gate_triggers=())
    with pytest.raises(ContractError, match="changed after"):
        runtime(tmp_path).resume(work)
