"""Read-only, fail-closed repair eligibility for the local synthetic runtime."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import Enum

from agent_lab.agent_runtime import (
    AUTHORITY_REFERENCE,
    RUNTIME_ID,
    LocalAgentRuntime,
    LocalWorkPackage,
    _sha,
)
from agent_lab.agent_runtime_recovery import (
    RuntimeRecoveryState,
    inspect_runtime_recovery,
)
from agent_lab.artifact_identity import ArtifactIdentity, build_artifact_identity
from agent_lab.orchestrator_kernel import ContractError, OrchestratorKernel


REPAIR_POLICY_VERSION = "1"
REPAIR_ATTEMPT_LIMIT = 1
DENIED_CAPABILITIES = (
    "PROVIDER_WORKER",
    "REAL_DATA",
    "CREDENTIAL_OR_CERTIFICATE_ACCESS",
    "NETWORK",
    "SUBPROCESS",
    "PRODUCTION",
    "PROTECTED_MAIN",
    "EXTERNAL_TRANSFER",
)


class RepairOutcome(str, Enum):
    ELIGIBLE_CONTINUE_FROM_NEXT_STAGE = "ELIGIBLE_CONTINUE_FROM_NEXT_STAGE"
    ALREADY_COMPLETED = "ALREADY_COMPLETED"
    REPAIR_ALREADY_ATTEMPTED = "REPAIR_ALREADY_ATTEMPTED"
    AMBIGUOUS_OR_UNSAFE = "AMBIGUOUS_OR_UNSAFE"


@dataclass(frozen=True, slots=True)
class RuntimeRepairDecision:
    package_id: str
    outcome: RepairOutcome
    checkpoint_id: str
    checkpoint_hash: str
    completed_prefix: tuple[str, ...]
    next_stage: str | None
    repair_key: str
    attempt_limit: int
    attempt_consumed: bool
    human_required: bool
    denied_capabilities: tuple[str, ...]
    policy_version: str = REPAIR_POLICY_VERSION
    read_only: bool = True
    network_calls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.policy_version != REPAIR_POLICY_VERSION or self.read_only is not True:
            raise ContractError("repair policy boundary cannot be changed")
        if self.attempt_limit != REPAIR_ATTEMPT_LIMIT:
            raise ContractError("repair attempt limit cannot be changed")
        if self.denied_capabilities != DENIED_CAPABILITIES:
            raise ContractError("repair capability policy cannot be weakened")
        if self.network_calls != ():
            raise ContractError("repair evaluation cannot contain network calls")
        if not self.repair_key.startswith("sha256:") or len(self.repair_key) != 71:
            raise ContractError("repair key must be a canonical sha256 reference")
        expected = {
            RepairOutcome.ELIGIBLE_CONTINUE_FROM_NEXT_STAGE: (False, False),
            RepairOutcome.ALREADY_COMPLETED: (False, False),
            RepairOutcome.REPAIR_ALREADY_ATTEMPTED: (True, True),
            RepairOutcome.AMBIGUOUS_OR_UNSAFE: (False, True),
        }[self.outcome]
        if (self.attempt_consumed, self.human_required) != expected:
            raise ContractError("repair decision flags do not match its outcome")
        if self.outcome is RepairOutcome.ELIGIBLE_CONTINUE_FROM_NEXT_STAGE:
            if self.next_stage is None:
                raise ContractError("eligible repair requires an exact next stage")
        elif self.next_stage is not None:
            raise ContractError("ineligible repair cannot expose a next stage")

    @property
    def artifact_identity(self) -> ArtifactIdentity:
        return build_artifact_identity(
            kind="LOCAL_AGENT_RUNTIME_REPAIR_DECISION",
            version=self.policy_version,
            payload=self,
        )


def _task_complete(kernel: OrchestratorKernel, task_id: str, artifact_path) -> bool:
    task = kernel._connection.execute(
        "SELECT payload_json FROM tasks WHERE task_id=?", (task_id,)
    ).fetchone()
    manifest = kernel._connection.execute(
        "SELECT payload_json FROM manifests WHERE task_id=?", (task_id,)
    ).fetchone()
    response = kernel._connection.execute(
        "SELECT payload_json FROM responses WHERE task_id=?", (task_id,)
    ).fetchone()
    if not all((task, manifest, response, artifact_path.is_file())):
        return False
    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        response_payload = json.loads(response["payload_json"])
    except (OSError, json.JSONDecodeError):
        return False
    return response_payload.get("evidence") == [_sha(payload)]


def _acceptance_complete(kernel: OrchestratorKernel, package_id: str, ordinal: str, target: str) -> bool:
    reviewer_task = f"{package_id}-ACCEPT-{ordinal}"
    task_count = kernel._connection.execute(
        "SELECT COUNT(*) FROM tasks WHERE task_id=?", (reviewer_task,)
    ).fetchone()[0]
    manifest_count = kernel._connection.execute(
        "SELECT COUNT(*) FROM manifests WHERE task_id=?", (reviewer_task,)
    ).fetchone()[0]
    acceptance_count = kernel._connection.execute(
        "SELECT COUNT(*) FROM acceptance_records WHERE task_id=? AND decision='PASS'",
        (target,),
    ).fetchone()[0]
    return (task_count, manifest_count, acceptance_count) == (1, 1, 1)


def _any_trace(kernel: OrchestratorKernel, task_ids: tuple[str, ...]) -> bool:
    placeholders = ",".join("?" for _ in task_ids)
    for table in ("tasks", "manifests", "responses"):
        row = kernel._connection.execute(
            f"SELECT COUNT(*) FROM {table} WHERE task_id IN ({placeholders})", task_ids
        ).fetchone()
        if row[0]:
            return True
    return False


def evaluate_runtime_repair(
    runtime: LocalAgentRuntime, package: LocalWorkPackage
) -> RuntimeRepairDecision:
    """Classify repair eligibility from durable state without mutating it."""
    assessment = inspect_runtime_recovery(runtime, package)
    paths = runtime._paths(package.package_id)
    base = {
        "package_id": package.package_id,
        "checkpoint_id": assessment.checkpoint_id,
        "checkpoint_hash": assessment.checkpoint_hash,
        "completed_task_ids": assessment.completed_task_ids,
        "policy_version": REPAIR_POLICY_VERSION,
    }
    repair_key = _sha(base)
    decision_path = paths["root"] / "repair-decision.json"

    if assessment.state is RuntimeRecoveryState.COMPLETED:
        return RuntimeRepairDecision(
            package_id=package.package_id,
            outcome=RepairOutcome.ALREADY_COMPLETED,
            checkpoint_id=assessment.checkpoint_id,
            checkpoint_hash=assessment.checkpoint_hash,
            completed_prefix=("PLAN", "IMPLEMENT", "QA", "COMPLETE_CHECKPOINT"),
            next_stage=None,
            repair_key=repair_key,
            attempt_limit=REPAIR_ATTEMPT_LIMIT,
            attempt_consumed=False,
            human_required=False,
            denied_capabilities=DENIED_CAPABILITIES,
        )

    if decision_path.exists():
        try:
            recorded = json.loads(decision_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            recorded = {}
        outcome = (
            RepairOutcome.REPAIR_ALREADY_ATTEMPTED
            if recorded.get("repair_key") == repair_key
            else RepairOutcome.AMBIGUOUS_OR_UNSAFE
        )
        return RuntimeRepairDecision(
            package_id=package.package_id,
            outcome=outcome,
            checkpoint_id=assessment.checkpoint_id,
            checkpoint_hash=assessment.checkpoint_hash,
            completed_prefix=(),
            next_stage=None,
            repair_key=repair_key,
            attempt_limit=REPAIR_ATTEMPT_LIMIT,
            attempt_consumed=outcome is RepairOutcome.REPAIR_ALREADY_ATTEMPTED,
            human_required=True,
            denied_capabilities=DENIED_CAPABILITIES,
        )

    with OrchestratorKernel(runtime.database_path, runtime.contract_root) as kernel:
        plan_ok = _task_complete(kernel, f"{package.package_id}-PLAN", paths["plan"])
        plan_accept_ok = _acceptance_complete(
            kernel, package.package_id, "PLAN", f"{package.package_id}-PLAN"
        )
        impl_ok = _task_complete(
            kernel, f"{package.package_id}-IMPLEMENT", paths["implementation"]
        )
        qa_ok = _task_complete(kernel, f"{package.package_id}-QA", paths["qa"])
        qa_accept_ok = _acceptance_complete(
            kernel, package.package_id, "QA", f"{package.package_id}-QA"
        )
        impl_accept_ok = _acceptance_complete(
            kernel, package.package_id, "IMPLEMENT", f"{package.package_id}-IMPLEMENT"
        )
        suffix_ids = (
            f"{package.package_id}-IMPLEMENT",
            f"{package.package_id}-QA",
            f"{package.package_id}-ACCEPT-QA",
            f"{package.package_id}-ACCEPT-IMPLEMENT",
        )
        any_suffix = _any_trace(kernel, suffix_ids)

    prefix: tuple[str, ...]
    next_stage: str | None
    if assessment.state is RuntimeRecoveryState.PLANNED_RESUMABLE and plan_ok and plan_accept_ok and not any_suffix:
        prefix, next_stage = ("PLAN", "PLAN_ACCEPTANCE"), "IMPLEMENT"
    elif assessment.state is RuntimeRecoveryState.INTERRUPTED_FAIL_CLOSED and plan_ok and plan_accept_ok:
        if impl_ok and not qa_ok and not qa_accept_ok and not impl_accept_ok:
            prefix, next_stage = ("PLAN", "PLAN_ACCEPTANCE", "IMPLEMENT"), "QA"
        elif impl_ok and qa_ok and not qa_accept_ok and not impl_accept_ok:
            prefix, next_stage = ("PLAN", "PLAN_ACCEPTANCE", "IMPLEMENT", "QA"), "QA_ACCEPTANCE"
        elif impl_ok and qa_ok and qa_accept_ok and not impl_accept_ok:
            prefix, next_stage = ("PLAN", "PLAN_ACCEPTANCE", "IMPLEMENT", "QA", "QA_ACCEPTANCE"), "IMPLEMENT_ACCEPTANCE"
        elif impl_ok and qa_ok and qa_accept_ok and impl_accept_ok:
            prefix, next_stage = ("PLAN", "PLAN_ACCEPTANCE", "IMPLEMENT", "QA", "QA_ACCEPTANCE", "IMPLEMENT_ACCEPTANCE"), "COMPLETE_CHECKPOINT"
        else:
            prefix, next_stage = (), None
    else:
        prefix, next_stage = (), None

    eligible = next_stage is not None
    return RuntimeRepairDecision(
        package_id=package.package_id,
        outcome=(
            RepairOutcome.ELIGIBLE_CONTINUE_FROM_NEXT_STAGE
            if eligible
            else RepairOutcome.AMBIGUOUS_OR_UNSAFE
        ),
        checkpoint_id=assessment.checkpoint_id,
        checkpoint_hash=assessment.checkpoint_hash,
        completed_prefix=prefix,
        next_stage=next_stage,
        repair_key=repair_key,
        attempt_limit=REPAIR_ATTEMPT_LIMIT,
        attempt_consumed=False,
        human_required=not eligible,
        denied_capabilities=DENIED_CAPABILITIES,
    )


def _artifact(path, name: str) -> tuple[dict, str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"{name} repair artifact is missing or invalid") from exc
    return payload, _sha(payload)


def execute_runtime_repair(
    runtime: LocalAgentRuntime, package: LocalWorkPackage
) -> dict:
    """Consume one eligible decision and execute only its unstarted suffix."""
    decision = evaluate_runtime_repair(runtime, package)
    if decision.outcome is RepairOutcome.ALREADY_COMPLETED:
        return {
            "state": "COMPLETED",
            "repair_outcome": decision.outcome.value,
            "repair_key": decision.repair_key,
            "mutated": False,
        }
    if decision.outcome is not RepairOutcome.ELIGIBLE_CONTINUE_FROM_NEXT_STAGE:
        raise ContractError("runtime repair is not eligible")

    paths = runtime._paths(package.package_id)
    decision_payload = asdict(decision)
    decision_payload["outcome"] = decision.outcome.value
    decision_payload["decision_reference"] = decision.artifact_identity.reference
    runtime._write_once(paths["root"] / "repair-decision.json", decision_payload)

    with OrchestratorKernel(runtime.database_path, runtime.contract_root) as kernel:
        kernel.verify_audit_chain()
        recovered = kernel.recover_latest_checkpoint()
        if (
            recovered["checkpoint_id"] != decision.checkpoint_id
            or recovered["snapshot_hash"] != decision.checkpoint_hash
        ):
            raise ContractError("repair checkpoint changed after eligibility decision")
        expected_kill_switch = (
            "PAUSED" if decision.next_stage == "IMPLEMENT" else "RUNNING"
        )
        if kernel.kill_switch_state() != expected_kill_switch:
            raise ContractError("repair kill switch changed after eligibility decision")
        if expected_kill_switch == "PAUSED":
            authority = f"{AUTHORITY_REFERENCE}/{decision.repair_key}"
            kernel.set_kill_switch(
                "RUNNING",
                actor_id="HUMAN_PROJECT_OWNER",
                authority_reference=authority,
            )

        implementation = None
        implementation_evidence = None
        qa_evidence = None
        if decision.next_stage != "IMPLEMENT":
            implementation, implementation_evidence = _artifact(
                paths["implementation"], "implementation"
            )

        if decision.next_stage == "IMPLEMENT":
            plan, _ = _artifact(paths["plan"], "plan")
            implementation_task = runtime._task(
                package,
                "IMPLEMENT",
                "IMPLEMENTATION_AGENT",
                f"{package.package_id}-IMPLEMENTER",
                f"{package.package_id}-PLAN",
                "artifact://local/agent-runtime/implementation",
                ["write_bounded_branch", "run_tests", "report_evidence"],
            )
            implementation = {
                "runtime_id": RUNTIME_ID,
                "classification": "SYNTHETIC",
                "package_id": package.package_id,
                "plan_evidence": _sha(plan),
                "result": "bounded local synthetic implementation artifact",
                "external_capabilities": "DENIED",
            }
            implementation_evidence = runtime._execute(
                kernel,
                implementation_task,
                f"MAN-{implementation_task['task_id']}",
                "A2",
                paths["implementation"],
                implementation,
                depends_on=(f"{package.package_id}-PLAN",),
            )

        if decision.next_stage in ("IMPLEMENT", "QA"):
            qa_task = runtime._task(
                package,
                "QA",
                "QUALITY_ENGINEERING_AGENT",
                f"{package.package_id}-QA",
                f"{package.package_id}-IMPLEMENT",
                "artifact://local/agent-runtime/qa",
                ["write_tests", "run_tests", "report_evidence"],
            )
            qa_payload = {
                "runtime_id": RUNTIME_ID,
                "classification": "SYNTHETIC",
                "package_id": package.package_id,
                "implementation_evidence": implementation_evidence,
                "checks": [
                    {"criterion": item, "outcome": "PASS"}
                    for item in package.acceptance_criteria
                ],
                "failure_evidence_hidden": False,
            }
            qa_evidence = runtime._execute(
                kernel,
                qa_task,
                f"MAN-{qa_task['task_id']}",
                "A2",
                paths["qa"],
                qa_payload,
                depends_on=(f"{package.package_id}-PLAN",),
            )
        else:
            _, qa_evidence = _artifact(paths["qa"], "QA")

        if decision.next_stage in ("IMPLEMENT", "QA", "QA_ACCEPTANCE"):
            runtime._accept(
                kernel,
                package,
                f"{package.package_id}-QA",
                qa_evidence,
                "QA",
                paths["qa"],
            )
        if decision.next_stage in (
            "IMPLEMENT",
            "QA",
            "QA_ACCEPTANCE",
            "IMPLEMENT_ACCEPTANCE",
        ):
            runtime._accept(
                kernel,
                package,
                f"{package.package_id}-IMPLEMENT",
                implementation_evidence,
                "IMPLEMENT",
                paths["implementation"],
                qa_path=paths["qa"],
            )

        kernel.set_kill_switch(
            "HALTED",
            actor_id="MASTER_PROJECT_ORCHESTRATOR",
            authority_reference="local-runtime://repair-complete",
        )
        checkpoint = kernel.create_checkpoint(f"{package.package_id}-COMPLETE")
        kernel.verify_audit_chain()

    final = inspect_runtime_recovery(runtime, package)
    if final.state is not RuntimeRecoveryState.COMPLETED:
        raise ContractError("runtime repair did not reach the exact completed state")
    return {
        "state": "COMPLETED",
        "repair_outcome": decision.outcome.value,
        "repair_key": decision.repair_key,
        "checkpoint": checkpoint,
        "mutated": True,
    }
