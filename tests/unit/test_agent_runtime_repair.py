import json
from dataclasses import replace

import pytest

from agent_lab.agent_runtime import AUTHORITY_REFERENCE
from agent_lab.agent_runtime_repair import (
    DENIED_CAPABILITIES,
    REPAIR_ATTEMPT_LIMIT,
    RepairOutcome,
    evaluate_runtime_repair,
    execute_runtime_repair,
)
from agent_lab.orchestrator_kernel import ContractError, OrchestratorKernel
from tests.unit.test_agent_runtime import CONTRACT_ROOT, package, runtime


def _interrupt_after_implementation(tmp_path):
    subject = runtime(tmp_path)
    work = package()
    subject.start(work)
    paths = subject._paths(work.package_id)
    with OrchestratorKernel(subject.database_path, CONTRACT_ROOT) as kernel:
        kernel.set_kill_switch(
            "RUNNING",
            actor_id="HUMAN_PROJECT_OWNER",
            authority_reference=f"{AUTHORITY_REFERENCE}/repair-test",
        )
        task = subject._task(
            work,
            "IMPLEMENT",
            "IMPLEMENTATION_AGENT",
            "RUNTIME_TEST_001-IMPLEMENTER",
            "RUNTIME_TEST_001-PLAN",
            "artifact://local/agent-runtime/implementation",
            ["write_bounded_branch", "run_tests", "report_evidence"],
        )
        subject._execute(
            kernel,
            task,
            "MAN-RUNTIME_TEST_001-IMPLEMENT",
            "A2",
            paths["implementation"],
            {
                "runtime_id": "LOCAL_AGENT_RUNTIME_V1",
                "classification": "SYNTHETIC",
                "package_id": work.package_id,
                "plan_evidence": "synthetic-repair-test",
                "result": "bounded local synthetic implementation artifact",
                "external_capabilities": "DENIED",
            },
            depends_on=("RUNTIME_TEST_001-PLAN",),
        )
    return subject, work


def test_planned_checkpoint_is_eligible_only_for_implementation(tmp_path):
    subject = runtime(tmp_path)
    work = package()
    subject.start(work)
    result = evaluate_runtime_repair(runtime(tmp_path), work)
    assert result.outcome is RepairOutcome.ELIGIBLE_CONTINUE_FROM_NEXT_STAGE
    assert result.completed_prefix == ("PLAN", "PLAN_ACCEPTANCE")
    assert result.next_stage == "IMPLEMENT"
    assert result.attempt_limit == REPAIR_ATTEMPT_LIMIT == 1
    assert result.denied_capabilities == DENIED_CAPABILITIES


def test_completed_runtime_is_idempotent_no_op(tmp_path):
    subject = runtime(tmp_path)
    work = package()
    subject.start(work)
    subject.resume(work)
    result = evaluate_runtime_repair(runtime(tmp_path), work)
    assert result.outcome is RepairOutcome.ALREADY_COMPLETED
    assert result.next_stage is None
    assert result.human_required is False


def test_completed_implementation_continues_at_qa_without_replay(tmp_path):
    subject, work = _interrupt_after_implementation(tmp_path)
    result = evaluate_runtime_repair(runtime(tmp_path), work)
    assert result.outcome is RepairOutcome.ELIGIBLE_CONTINUE_FROM_NEXT_STAGE
    assert result.completed_prefix[-1] == "IMPLEMENT"
    assert result.next_stage == "QA"


def test_repair_executor_completes_planned_runtime_once(tmp_path):
    subject = runtime(tmp_path)
    work = package()
    subject.start(work)
    result = execute_runtime_repair(runtime(tmp_path), work)
    assert result["state"] == "COMPLETED"
    assert result["mutated"] is True
    again = execute_runtime_repair(runtime(tmp_path), work)
    assert again["repair_outcome"] == "ALREADY_COMPLETED"
    assert again["mutated"] is False


def test_repair_executor_never_replays_completed_implementation(tmp_path):
    subject, work = _interrupt_after_implementation(tmp_path)
    implementation_path = subject._paths(work.package_id)["implementation"]
    original = implementation_path.read_bytes()
    result = execute_runtime_repair(runtime(tmp_path), work)
    assert result["state"] == "COMPLETED"
    assert implementation_path.read_bytes() == original
    with OrchestratorKernel(subject.database_path, CONTRACT_ROOT) as kernel:
        count = kernel._connection.execute(
            "SELECT COUNT(*) FROM responses WHERE task_id=?",
            (f"{work.package_id}-IMPLEMENT",),
        ).fetchone()[0]
    assert count == 1


def test_missing_completed_artifact_fails_closed(tmp_path):
    subject, work = _interrupt_after_implementation(tmp_path)
    subject._paths(work.package_id)["implementation"].unlink()
    result = evaluate_runtime_repair(runtime(tmp_path), work)
    assert result.outcome is RepairOutcome.AMBIGUOUS_OR_UNSAFE
    assert result.human_required is True


def test_matching_write_once_decision_marks_attempt_consumed(tmp_path):
    subject, work = _interrupt_after_implementation(tmp_path)
    first = evaluate_runtime_repair(runtime(tmp_path), work)
    decision_path = subject._paths(work.package_id)["root"] / "repair-decision.json"
    decision_path.write_text(json.dumps({"repair_key": first.repair_key}), encoding="utf-8")
    result = evaluate_runtime_repair(runtime(tmp_path), work)
    assert result.outcome is RepairOutcome.REPAIR_ALREADY_ATTEMPTED
    assert result.attempt_consumed is True
    assert result.next_stage is None


def test_foreign_repair_decision_fails_closed(tmp_path):
    subject, work = _interrupt_after_implementation(tmp_path)
    decision_path = subject._paths(work.package_id)["root"] / "repair-decision.json"
    decision_path.write_text(json.dumps({"repair_key": "sha256:" + "0" * 64}), encoding="utf-8")
    result = evaluate_runtime_repair(runtime(tmp_path), work)
    assert result.outcome is RepairOutcome.AMBIGUOUS_OR_UNSAFE


def test_executor_rejects_consumed_attempt_without_mutation(tmp_path):
    subject, work = _interrupt_after_implementation(tmp_path)
    first = evaluate_runtime_repair(runtime(tmp_path), work)
    decision_path = subject._paths(work.package_id)["root"] / "repair-decision.json"
    decision_path.write_text(json.dumps({"repair_key": first.repair_key}), encoding="utf-8")
    with pytest.raises(ContractError, match="not eligible"):
        execute_runtime_repair(runtime(tmp_path), work)
    assert not subject._paths(work.package_id)["qa"].exists()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("read_only", False),
        ("attempt_limit", 2),
        ("denied_capabilities", ()),
        ("network_calls", ("https://example.invalid",)),
        ("attempt_consumed", True),
    ],
)
def test_decision_boundary_cannot_be_forged(tmp_path, field, value):
    subject = runtime(tmp_path)
    work = package()
    subject.start(work)
    decision = evaluate_runtime_repair(runtime(tmp_path), work)
    with pytest.raises(ContractError):
        replace(decision, **{field: value})
