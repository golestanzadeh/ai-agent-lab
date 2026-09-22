"""Read-only recovery classification for the local synthetic Agent Runtime."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum

from agent_lab.agent_runtime import LocalAgentRuntime, LocalWorkPackage, RUNTIME_ID, _sha
from agent_lab.artifact_identity import ArtifactIdentity, build_artifact_identity
from agent_lab.orchestrator_kernel import ContractError, IntegrityError, OrchestratorKernel


RECOVERY_INSPECTOR_VERSION = "1"


class RuntimeRecoveryState(str, Enum):
    PLANNED_RESUMABLE = "PLANNED_RESUMABLE"
    COMPLETED = "COMPLETED"
    INTERRUPTED_FAIL_CLOSED = "INTERRUPTED_FAIL_CLOSED"


@dataclass(frozen=True, slots=True)
class RuntimeRecoveryAssessment:
    package_id: str
    state: RuntimeRecoveryState
    checkpoint_id: str
    checkpoint_hash: str
    kill_switch: str
    completed_task_ids: tuple[str, ...]
    automatic_replay_permitted: bool
    human_repair_required: bool
    inspector_version: str = RECOVERY_INSPECTOR_VERSION
    read_only: bool = True
    network_calls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.package_id or not isinstance(self.state, RuntimeRecoveryState):
            raise ContractError("recovery assessment identity is invalid")
        _digest(self.checkpoint_hash)
        if self.inspector_version != RECOVERY_INSPECTOR_VERSION or self.read_only is not True:
            raise ContractError("recovery inspector boundary cannot be changed")
        if self.network_calls != ():
            raise ContractError("recovery inspection cannot contain network calls")
        expected = {
            RuntimeRecoveryState.PLANNED_RESUMABLE: ("PAUSED", False, False),
            RuntimeRecoveryState.COMPLETED: ("HALTED", False, False),
            RuntimeRecoveryState.INTERRUPTED_FAIL_CLOSED: ("RUNNING", False, True),
        }[self.state]
        if (self.kill_switch, self.automatic_replay_permitted, self.human_repair_required) != expected:
            raise ContractError("recovery assessment flags do not match its state")

    @property
    def artifact_identity(self) -> ArtifactIdentity:
        return build_artifact_identity(
            kind="LOCAL_AGENT_RUNTIME_RECOVERY_ASSESSMENT",
            version=self.inspector_version,
            payload=self,
        )


def _digest(value: str) -> None:
    digest = value.removeprefix("sha256:") if isinstance(value, str) else ""
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ContractError("checkpoint_hash must be a canonical sha256 reference")


def inspect_runtime_recovery(
    runtime: LocalAgentRuntime, package: LocalWorkPackage
) -> RuntimeRecoveryAssessment:
    """Classify durable runtime state without replaying or mutating any stage."""
    if not isinstance(runtime, LocalAgentRuntime):
        raise ContractError("a LocalAgentRuntime is required")
    if not isinstance(package, LocalWorkPackage):
        raise ContractError("a LocalWorkPackage is required")
    package.validate()
    paths = runtime._paths(package.package_id)
    try:
        state = json.loads(paths["state"].read_text(encoding="utf-8"))
        plan = json.loads(paths["plan"].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError("runtime recovery artifacts are missing or invalid") from exc
    expected_state = {
        "runtime_id": RUNTIME_ID,
        "package_id": package.package_id,
        "state": "PLANNED",
        "plan_evidence": _sha(plan),
        "package_digest": _sha(
            {
                "objective": package.objective,
                "inputs": package.synthetic_inputs,
                "criteria": package.acceptance_criteria,
            }
        ),
    }
    if state != expected_state:
        raise ContractError("runtime recovery state does not match the immutable plan")

    try:
        with OrchestratorKernel(runtime.database_path, runtime.contract_root) as kernel:
            kernel.verify_audit_chain()
            recovered = kernel.recover_latest_checkpoint()
            kill_switch = kernel.kill_switch_state()
            completed = tuple(
                row[0]
                for row in kernel._connection.execute(
                    "SELECT task_id FROM responses ORDER BY rowid"
                ).fetchall()
            )
            events_after = kernel._connection.execute(
                "SELECT event_type, entity_id FROM audit_events WHERE event_id>? ORDER BY event_id",
                (recovered["snapshot"]["last_event_id"],),
            ).fetchall()
    except IntegrityError as exc:
        raise ContractError("runtime audit or checkpoint integrity failed") from exc

    planned_id = f"{package.package_id}-PLANNED"
    complete_id = f"{package.package_id}-COMPLETE"
    checkpoint_id = recovered["checkpoint_id"]
    checkpoint_hash = recovered["snapshot_hash"]
    if (
        checkpoint_id == complete_id
        and kill_switch == "HALTED"
        and len(events_after) == 1
        and events_after[0]["event_type"] == "CHECKPOINT_CREATED"
        and events_after[0]["entity_id"] == complete_id
    ):
        state_value = RuntimeRecoveryState.COMPLETED
    elif (
        checkpoint_id == planned_id
        and kill_switch == "PAUSED"
        and len(events_after) == 1
        and events_after[0]["event_type"] == "CHECKPOINT_CREATED"
        and events_after[0]["entity_id"] == planned_id
    ):
        state_value = RuntimeRecoveryState.PLANNED_RESUMABLE
    elif checkpoint_id == planned_id and kill_switch == "RUNNING":
        state_value = RuntimeRecoveryState.INTERRUPTED_FAIL_CLOSED
    else:
        raise ContractError("runtime recovery state is unsupported or ambiguous")
    return RuntimeRecoveryAssessment(
        package_id=package.package_id,
        state=state_value,
        checkpoint_id=checkpoint_id,
        checkpoint_hash=checkpoint_hash,
        kill_switch=kill_switch,
        completed_task_ids=completed,
        automatic_replay_permitted=False,
        human_repair_required=state_value is RuntimeRecoveryState.INTERRUPTED_FAIL_CLOSED,
    )
