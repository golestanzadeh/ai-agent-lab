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


def _advance_interrupted_runtime(tmp_path, boundary):
    subject, work = _interrupt_after_implementation(tmp_path)
    paths = subject._paths(work.package_id)
    if boundary == "IMPLEMENT":
        return subject, work
    with OrchestratorKernel(subject.database_path, CONTRACT_ROOT) as kernel:
        implementation = json.loads(paths["implementation"].read_text(encoding="utf-8"))
        from agent_lab.agent_runtime import _sha

        implementation_evidence = _sha(implementation)
        qa_task = subject._task(
            work,
            "QA",
            "QUALITY_ENGINEERING_AGENT",
            "RUNTIME_TEST_001-QA",
            "RUNTIME_TEST_001-IMPLEMENT",
            "artifact://local/agent-runtime/qa",
            ["write_tests", "run_tests", "report_evidence"],
        )
        qa_payload = {
            "runtime_id": "LOCAL_AGENT_RUNTIME_V1",
            "classification": "SYNTHETIC",
            "package_id": work.package_id,
            "implementation_evidence": implementation_evidence,
            "checks": [
                {"criterion": item, "outcome": "PASS"}
                for item in work.acceptance_criteria
            ],
            "failure_evidence_hidden": False,
        }
        qa_evidence = subject._execute(
            kernel,
            qa_task,
            "MAN-RUNTIME_TEST_001-QA",
            "A2",
            paths["qa"],
            qa_payload,
            depends_on=("RUNTIME_TEST_001-PLAN",),
        )
        if boundary == "QA":
            return subject, work
        subject._accept(
            kernel,
            work,
            "RUNTIME_TEST_001-QA",
            qa_evidence,
            "QA",
            paths["qa"],
        )
        if boundary == "QA_ACCEPTANCE":
            return subject, work
        subject._accept(
            kernel,
            work,
            "RUNTIME_TEST_001-IMPLEMENT",
            implementation_evidence,
            "IMPLEMENT",
            paths["implementation"],
            qa_path=paths["qa"],
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


@pytest.mark.parametrize(
    ("boundary", "next_stage"),
    [
        ("QA", "QA_ACCEPTANCE"),
        ("QA_ACCEPTANCE", "IMPLEMENT_ACCEPTANCE"),
        ("IMPLEMENT_ACCEPTANCE", "COMPLETE_CHECKPOINT"),
    ],
)
def test_every_later_exact_prefix_completes_only_its_suffix(tmp_path, boundary, next_stage):
    subject, work = _advance_interrupted_runtime(tmp_path, boundary)
    paths = subject._paths(work.package_id)
    implementation_before = paths["implementation"].read_bytes()
    qa_before = paths["qa"].read_bytes()
    decision = evaluate_runtime_repair(runtime(tmp_path), work)
    assert decision.next_stage == next_stage
    result = execute_runtime_repair(runtime(tmp_path), work)
    assert result["state"] == "COMPLETED"
    assert paths["implementation"].read_bytes() == implementation_before
    assert paths["qa"].read_bytes() == qa_before


def test_partial_implementation_task_trace_is_ambiguous(tmp_path):
    subject = runtime(tmp_path)
    work = package()
    subject.start(work)
    with OrchestratorKernel(subject.database_path, CONTRACT_ROOT) as kernel:
        kernel.set_kill_switch(
            "RUNNING",
            actor_id="HUMAN_PROJECT_OWNER",
            authority_reference=f"{AUTHORITY_REFERENCE}/partial-stage-test",
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
        kernel.register_task(task, gate_triggers=(), depends_on=("RUNTIME_TEST_001-PLAN",))
    decision = evaluate_runtime_repair(runtime(tmp_path), work)
    assert decision.outcome is RepairOutcome.AMBIGUOUS_OR_UNSAFE
    assert decision.next_stage is None


def test_later_stage_trace_without_required_prefix_is_ambiguous(tmp_path):
    subject = runtime(tmp_path)
    work = package()
    subject.start(work)
    with OrchestratorKernel(subject.database_path, CONTRACT_ROOT) as kernel:
        kernel.set_kill_switch(
            "RUNNING",
            actor_id="HUMAN_PROJECT_OWNER",
            authority_reference=f"{AUTHORITY_REFERENCE}/extra-stage-test",
        )
        implementation_task = subject._task(
            work,
            "IMPLEMENT",
            "IMPLEMENTATION_AGENT",
            "RUNTIME_TEST_001-IMPLEMENTER",
            "RUNTIME_TEST_001-PLAN",
            "artifact://local/agent-runtime/implementation",
            ["write_bounded_branch", "run_tests", "report_evidence"],
        )
        kernel.register_task(
            implementation_task,
            gate_triggers=(),
            depends_on=("RUNTIME_TEST_001-PLAN",),
        )
        task = subject._task(
            work,
            "QA",
            "QUALITY_ENGINEERING_AGENT",
            "RUNTIME_TEST_001-QA",
            "RUNTIME_TEST_001-IMPLEMENT",
            "artifact://local/agent-runtime/qa",
            ["write_tests", "run_tests", "report_evidence"],
        )
        kernel.register_task(task, gate_triggers=())
    decision = evaluate_runtime_repair(runtime(tmp_path), work)
    assert decision.outcome is RepairOutcome.AMBIGUOUS_OR_UNSAFE


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
