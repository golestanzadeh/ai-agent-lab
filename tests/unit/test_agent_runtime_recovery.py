from dataclasses import replace

import pytest

from agent_lab.agent_runtime import AUTHORITY_REFERENCE
from agent_lab.agent_runtime_recovery import (
    RuntimeRecoveryState,
    inspect_runtime_recovery,
)
from agent_lab.orchestrator_kernel import ContractError, OrchestratorKernel
from tests.unit.test_agent_runtime import CONTRACT_ROOT, package, runtime


def test_planned_state_is_classified_as_resumable_without_replay(tmp_path):
    subject = runtime(tmp_path)
    subject.start(package())
    result = inspect_runtime_recovery(runtime(tmp_path), package())
    assert result.state is RuntimeRecoveryState.PLANNED_RESUMABLE
    assert result.kill_switch == "PAUSED"
    assert result.completed_task_ids == ("RUNTIME_TEST_001-PLAN",)
    assert result.automatic_replay_permitted is False
    assert result.human_repair_required is False


def test_completed_state_is_classified_without_mutation(tmp_path):
    subject = runtime(tmp_path)
    subject.start(package())
    subject.resume(package())
    first = inspect_runtime_recovery(runtime(tmp_path), package())
    second = inspect_runtime_recovery(runtime(tmp_path), package())
    assert first.state is RuntimeRecoveryState.COMPLETED
    assert first.kill_switch == "HALTED"
    assert first == second
    assert first.artifact_identity == second.artifact_identity
    assert first.completed_task_ids == (
        "RUNTIME_TEST_001-PLAN",
        "RUNTIME_TEST_001-IMPLEMENT",
        "RUNTIME_TEST_001-QA",
    )


def test_mid_resume_state_fails_closed_with_exact_completed_stage_evidence(tmp_path):
    subject = runtime(tmp_path)
    work = package()
    subject.start(work)
    paths = subject._paths(work.package_id)
    with OrchestratorKernel(subject.database_path, CONTRACT_ROOT) as kernel:
        kernel.set_kill_switch(
            "RUNNING",
            actor_id="HUMAN_PROJECT_OWNER",
            authority_reference=f"{AUTHORITY_REFERENCE}/synthetic-interruption-test",
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
                "plan_evidence": "synthetic-interruption",
                "result": "bounded local synthetic implementation artifact",
                "external_capabilities": "DENIED",
            },
            depends_on=("RUNTIME_TEST_001-PLAN",),
        )
    result = inspect_runtime_recovery(runtime(tmp_path), work)
    assert result.state is RuntimeRecoveryState.INTERRUPTED_FAIL_CLOSED
    assert result.completed_task_ids == (
        "RUNTIME_TEST_001-PLAN",
        "RUNTIME_TEST_001-IMPLEMENT",
    )
    assert result.automatic_replay_permitted is False
    assert result.human_repair_required is True


def test_tampered_plan_or_audit_is_rejected(tmp_path):
    subject = runtime(tmp_path)
    subject.start(package())
    plan_path = subject._paths(package().package_id)["plan"]
    plan_path.write_text("{}", encoding="utf-8")
    with pytest.raises(ContractError, match="immutable plan"):
        inspect_runtime_recovery(runtime(tmp_path), package())


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("read_only", False),
        ("network_calls", ("https://example.invalid",)),
        ("automatic_replay_permitted", True),
    ],
)
def test_assessment_boundary_cannot_be_forged(tmp_path, field, value):
    subject = runtime(tmp_path)
    subject.start(package())
    result = inspect_runtime_recovery(runtime(tmp_path), package())
    with pytest.raises(ContractError):
        replace(result, **{field: value})
