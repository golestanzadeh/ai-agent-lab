"""Fail-closed projection of the project plan over the existing Kernel boundary.

This module does not dispatch work, grant authority, persist a second queue, or
schedule anything.  It validates the versioned plan and deterministically
identifies the next action which the existing Orchestrator Kernel may consider.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .plan_limit_controller import CapacityDecision, DeferredOperation, OperationCostClass, evaluate_capacity


GRAPH_VERSION = 1
NODE_STATUSES = {
    "ACCEPTED", "READY", "BLOCKED_DEPENDENCY", "AUTHORITY_REQUIRED", "HUMAN_GATE",
}
ELIGIBILITY_STATES = {"COMPLETED", "ELIGIBLE", "ELIGIBLE_AFTER_INDEPENDENT_REVIEW", "AFTER_R6_PASS", "AFTER_DR05", "AFTER_REAL_WORKFLOW", "AFTER_OFFICIAL_VALIDATION", "AFTER_APPROVAL_LIFECYCLE", "AFTER_AUTHORIZED_TRANSMISSION", "AFTER_RECEIPT", "AFTER_E2E", "AFTER_DEPLOYMENT_READINESS", "AFTER_RELEASE_ACCEPTANCE", "HUMAN_GATE", "FUTURE_ONLY", "BLOCKED"}
AUTHORITY_STATES = {"ACTIVE", "CONDITIONAL", "NOT_APPROVED"}
COMPLETION_STATES = {
    "PACKAGE_COMPLETE", "MILESTONE_COMPLETE", "CURRENT_SUPPORTED_PRODUCT_COMPLETE",
    "MASTER_PLAN_FUTURE_SCOPE_REMAINING", "PROJECT_COMPLETE",
}
NODE_FIELDS = {
    "id", "goal", "depends_on", "status", "required_authority",
    "available_authority", "execution_eligibility", "inputs", "outputs", "definition_of_done",
    "required_tests", "independent_acceptance", "cost_class",
    "allowed_remediation", "retry_boundary", "human_gate_conditions",
    "external_boundary", "next_states", "terminal_semantics",
}
GRAPH_FIELDS = {
    "schema_version", "graph_id", "project", "repository", "branch",
    "completion_boundary", "nodes", "future_scope", "forbidden_actions",
}


class ProjectGraphError(ValueError):
    """Raised when project-control evidence is incomplete or contradictory."""


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def load_graph(path: Path | str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != GRAPH_FIELDS:
        raise ProjectGraphError("master graph top-level schema mismatch")
    if payload["schema_version"] != GRAPH_VERSION:
        raise ProjectGraphError("unsupported master graph version")
    if payload["completion_boundary"] not in COMPLETION_STATES:
        raise ProjectGraphError("unknown completion boundary")
    nodes = payload["nodes"]
    if not isinstance(nodes, list) or not nodes:
        raise ProjectGraphError("master graph requires nodes")
    ids: list[str] = []
    for node in nodes:
        if not isinstance(node, dict) or set(node) != NODE_FIELDS:
            raise ProjectGraphError("master graph node schema mismatch")
        if not isinstance(node["id"], str) or not node["id"]:
            raise ProjectGraphError("node id must be non-empty")
        for scalar in ("goal", "required_authority", "available_authority", "execution_eligibility", "definition_of_done", "retry_boundary", "terminal_semantics"):
            if not isinstance(node[scalar], str) or not node[scalar]:
                raise ProjectGraphError(f"{node['id']}.{scalar} must be non-empty")
        if node["status"] not in NODE_STATUSES:
            raise ProjectGraphError(f"unknown node status: {node['id']}")
        if node["cost_class"] not in {"CHEAP", "BOUNDED", "EXPENSIVE"}:
            raise ProjectGraphError(f"unknown cost class: {node['id']}")
        if node["available_authority"] not in AUTHORITY_STATES or node["execution_eligibility"] not in ELIGIBILITY_STATES:
            raise ProjectGraphError(f"unknown authority or eligibility state: {node['id']}")
        for field in ("depends_on", "inputs", "outputs", "required_tests", "allowed_remediation", "human_gate_conditions", "external_boundary", "next_states"):
            if not isinstance(node[field], list):
                raise ProjectGraphError(f"{node['id']}.{field} must be a list")
        ids.append(node["id"])
        if not isinstance(node["independent_acceptance"], bool):
            raise ProjectGraphError(f"{node['id']}.independent_acceptance must be boolean")
        if node["terminal_semantics"] not in COMPLETION_STATES:
            raise ProjectGraphError(f"unknown terminal semantics: {node['id']}")
    if len(ids) != len(set(ids)):
        raise ProjectGraphError("duplicate node id")
    seen: set[str] = set()
    for node in nodes:
        if any(dep not in seen for dep in node["depends_on"]):
            raise ProjectGraphError(f"unknown, forward, or cyclic dependency: {node['id']}")
        seen.add(node["id"])
    known = set(ids)
    for node in nodes:
        if any(target not in known for target in node["next_states"]):
            raise ProjectGraphError(f"unknown next state: {node['id']}")
    return payload


@dataclass(frozen=True)
class NextAuthorizedAction:
    outcome: str
    action_id: str | None
    authority: str | None
    dependencies: str
    human_gate: str
    cost_class: str | None
    recovery_checkpoint: str
    graph_digest: str
    reset_timestamp: str | None = None


def next_authorized_action(
    graph: dict[str, Any], *, branch: str, repository_safe: bool,
    recovery_checkpoint: str, capacity: CapacityDecision,
    now: datetime | None = None,
) -> NextAuthorizedAction:
    """Return one deterministic query result; never dispatch or mutate state."""
    loadable = json.loads(_canonical(graph))
    _validate_graph_payload(loadable)
    if branch != graph["branch"] or not repository_safe:
        return NextAuthorizedAction("STOP_DIAGNOSTIC", None, None, "UNKNOWN", "NONE", None, recovery_checkpoint, digest(graph))
    evaluation_time = now or datetime.now(capacity.observation.observed_at.tzinfo)
    refreshed_base = evaluate_capacity(capacity.observation, now=evaluation_time)
    accepted = {node["id"] for node in graph["nodes"] if node["status"] == "ACCEPTED"}
    ready: list[dict[str, Any]] = []
    for node in graph["nodes"]:
        if node["status"] == "READY" and set(node["depends_on"]).issubset(accepted):
            ready.append(node)
    if len(ready) > 1:
        raise ProjectGraphError("ambiguous next action")
    if ready:
        node = ready[0]
        if node["available_authority"] != "ACTIVE":
            raise ProjectGraphError("ready node lacks active authority")
        if refreshed_base.state.value in {"TOKEN_PAUSED", "UNKNOWN_PAUSED"}:
            five = capacity.observation.five_hour_remaining_percent
            weekly = capacity.observation.weekly_remaining_percent
            resets = []
            if five is None or five <= 15:
                resets.append(capacity.observation.five_hour_resets_at)
            if weekly is None or weekly <= 10:
                resets.append(capacity.observation.weekly_resets_at)
            reset = max(resets).isoformat() if resets else None
            return NextAuthorizedAction(refreshed_base.state.value, node["id"], node["required_authority"], "SATISFIED", "NONE", node["cost_class"], recovery_checkpoint, digest(graph), reset)
        cost_checked = evaluate_capacity(
            capacity.observation,
            now=evaluation_time,
            next_operation=DeferredOperation(
                operation_id=node["id"], reason="MASTER_GRAPH_COST_GATE",
                continuation_checkpoint=recovery_checkpoint,
                estimate_class=OperationCostClass(node["cost_class"]),
            ),
        )
        if not cost_checked.can_start_operation:
            five_cost, weekly_cost = DeferredOperation(operation_id=node["id"], reason="MASTER_GRAPH_COST_GATE", continuation_checkpoint=recovery_checkpoint, estimate_class=OperationCostClass(node["cost_class"])).estimated_costs
            relevant_resets = []
            if capacity.observation.five_hour_remaining_percent - five_cost <= 15:
                relevant_resets.append(capacity.observation.five_hour_resets_at)
            if capacity.observation.weekly_remaining_percent - weekly_cost <= 10:
                relevant_resets.append(capacity.observation.weekly_resets_at)
            reset = max(relevant_resets)
            return NextAuthorizedAction(cost_checked.state.value, node["id"], node["required_authority"], "SATISFIED", "NONE", node["cost_class"], recovery_checkpoint, digest(graph), reset.isoformat())
        return NextAuthorizedAction(
            "READY_PACKAGE", node["id"], node["required_authority"], "SATISFIED",
            "NONE", node["cost_class"], recovery_checkpoint, digest(graph),
        )
    gates = [node for node in graph["nodes"] if node["status"] in {"AUTHORITY_REQUIRED", "HUMAN_GATE"} and set(node["depends_on"]).issubset(accepted)]
    if len(gates) > 1:
        raise ProjectGraphError("ambiguous human gate")
    if gates:
        node = gates[0]
        return NextAuthorizedAction("HUMAN_GATE", node["id"], node["required_authority"], "SATISFIED", node["status"], node["cost_class"], recovery_checkpoint, digest(graph))
    return NextAuthorizedAction("QUEUE_COMPLETE", None, None, "SATISFIED", "NONE", None, recovery_checkpoint, digest(graph))


def build_hot_context(graph: dict[str, Any], action: NextAuthorizedAction, *, head: str, capacity_observation: dict[str, Any]) -> dict[str, Any]:
    context = {
        "schema_version": 1,
        "project": graph["project"],
        "repository": graph["repository"],
        "branch": graph["branch"],
        "head": head,
        "recovery_checkpoint": action.recovery_checkpoint,
        "graph_digest": action.graph_digest,
        "next_authorized_action": action.__dict__,
        "capacity": capacity_observation,
        "supporting_contract": "contracts/project-execution/v1/master-execution-graph.json",
    }
    return {**context, "context_digest": digest(context)}


def notification_decision(contract: dict[str, Any], *, event: str, event_identity: str, stage_one: bool, stage_two: bool, delivered_identities: Iterable[str]) -> str:
    """Authorize only a deduplicated, two-stage-approved notification attempt."""
    if type(stage_one) is not bool or type(stage_two) is not bool:
        raise ProjectGraphError("notification approvals must be exact booleans")
    if not event_identity or not isinstance(event_identity, str):
        raise ProjectGraphError("notification event identity is required")
    if event not in contract["eligible_events"]:
        return "NOT_ELIGIBLE"
    if event_identity in set(delivered_identities):
        return "DEDUPLICATED"
    if not stage_one:
        return "ARTICLE_1_STAGE_ONE_REQUIRED"
    if not stage_two:
        return "ARTICLE_1_STAGE_TWO_REQUIRED"
    return "AUTHORIZED_ONCE"


def _validate_graph_payload(payload: dict[str, Any]) -> None:
    """Validate an in-memory graph by the same rules as a loaded graph."""
    if not isinstance(payload, dict) or set(payload) != GRAPH_FIELDS or payload.get("schema_version") != GRAPH_VERSION:
        raise ProjectGraphError("master graph top-level schema mismatch")
    # Validation through a temporary-free recursive implementation.
    nodes = payload.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise ProjectGraphError("master graph requires nodes")
    ids: list[str] = []
    seen: set[str] = set()
    for node in nodes:
        if not isinstance(node, dict) or set(node) != NODE_FIELDS:
            raise ProjectGraphError("master graph node schema mismatch")
        if node.get("status") not in NODE_STATUSES or node.get("cost_class") not in {"CHEAP", "BOUNDED", "EXPENSIVE"}:
            raise ProjectGraphError("unknown node state or cost class")
        if node.get("terminal_semantics") not in COMPLETION_STATES:
            raise ProjectGraphError("unknown terminal semantics")
        if type(node.get("independent_acceptance")) is not bool:
            raise ProjectGraphError("independent_acceptance must be boolean")
        for scalar in ("goal", "required_authority", "available_authority", "execution_eligibility", "definition_of_done", "retry_boundary", "terminal_semantics"):
            if not isinstance(node.get(scalar), str) or not node[scalar]:
                raise ProjectGraphError(f"{node.get('id', 'UNKNOWN')}.{scalar} must be non-empty")
        if node["available_authority"] not in AUTHORITY_STATES or node["execution_eligibility"] not in ELIGIBILITY_STATES:
            raise ProjectGraphError("unknown authority or eligibility state")
        if not isinstance(node.get("id"), str) or not node["id"] or node["id"] in ids:
            raise ProjectGraphError("invalid or duplicate node id")
        for field in ("depends_on", "inputs", "outputs", "required_tests", "allowed_remediation", "human_gate_conditions", "external_boundary", "next_states"):
            if not isinstance(node.get(field), list):
                raise ProjectGraphError(f"{node['id']}.{field} must be a list")
        if any(dep not in seen for dep in node["depends_on"]):
            raise ProjectGraphError(f"unknown, forward, or cyclic dependency: {node['id']}")
        ids.append(node["id"]); seen.add(node["id"])
    known = set(ids)
    for node in nodes:
        if any(not isinstance(target, str) or not target or target not in known for target in node["next_states"]):
            raise ProjectGraphError(f"unknown next state: {node['id']}")


@dataclass(frozen=True)
class LoopStepResult:
    outcome: str
    completed_actions: tuple[str, ...]
    checkpoints: tuple[str, ...]
    remediation_count: int


class TechnicalRecoverable(RuntimeError):
    pass


def run_closed_loop_action(
    *, kernel: Any, action_id: str, execute: Any, remediate: Any, run_tests: Any,
    independent_accept: Any, publish_checkpoint: Any, checkpoint_id: str,
) -> LoopStepResult:
    """Execute one bounded action through the existing Kernel checkpoint boundary."""
    remediation_count = 0
    try:
        execute(action_id)
    except TechnicalRecoverable as failure:
        remediate(action_id, str(failure))
        remediation_count = 1
        execute(action_id)
    if run_tests(action_id) is not True:
        raise ProjectGraphError("closed-loop tests did not pass")
    if independent_accept(action_id) is not True:
        raise ProjectGraphError("independent acceptance did not pass")
    kernel.create_checkpoint(checkpoint_id)
    publish_checkpoint(checkpoint_id)
    return LoopStepResult("PACKAGE_COMPLETE", (action_id,), (checkpoint_id,), remediation_count)


def arm_capacity_continuation(*, kernel: Any, action_id: str, capacity_state: str, cost_class: str, reset_timestamp: str, checkpoint_id: str, arm: Any, verify: Any) -> LoopStepResult:
    """Persist a continuation capsule before arming and verifying the sole scheduler."""
    kernel.record_continuation_capsule(action_id=action_id, capacity_state=capacity_state, cost_class=cost_class, reset_timestamp=reset_timestamp, checkpoint_id=checkpoint_id)
    try:
        arm(action_id, reset_timestamp)
        verified = verify(action_id, reset_timestamp) is True
    except Exception as exc:
        kernel.record_scheduler_arm_failure(action_id=action_id, checkpoint_id=checkpoint_id, technical_cause=type(exc).__name__)
        raise ProjectGraphError("SCHEDULER_ARM_FAILURE") from exc
    if not verified:
        kernel.record_scheduler_arm_failure(action_id=action_id, checkpoint_id=checkpoint_id, technical_cause="READ_BACK_MISMATCH")
        raise ProjectGraphError("SCHEDULER_ARM_FAILURE")
    return LoopStepResult(capacity_state, (), (checkpoint_id,), 0)


def run_until_boundary(
    *, kernel: Any, derive_next: Any, execute: Any, remediate: Any,
    run_tests: Any, independent_accept: Any, publish_checkpoint: Any,
    arm_scheduler: Any, verify_scheduler: Any, max_actions: int,
) -> LoopStepResult:
    """Drive ordinary transitions until a governed terminal boundary."""
    completed: list[str] = []
    checkpoints: list[str] = []
    remediations = 0
    for ordinal in range(1, max_actions + 1):
        decision = derive_next()
        if decision.outcome == "READY_PACKAGE":
            checkpoint_id = f"AUTO-{ordinal}-{decision.action_id}"
            result = run_closed_loop_action(
                kernel=kernel, action_id=decision.action_id, execute=execute,
                remediate=remediate, run_tests=run_tests,
                independent_accept=independent_accept,
                publish_checkpoint=publish_checkpoint, checkpoint_id=checkpoint_id,
            )
            completed.extend(result.completed_actions); checkpoints.extend(result.checkpoints)
            remediations += result.remediation_count
            continue
        if decision.outcome == "UNKNOWN_PAUSED":
            if not decision.action_id:
                raise ProjectGraphError("unknown pause is missing exact action")
            kernel.record_unknown_capacity_pause(action_id=decision.action_id, checkpoint_id=decision.recovery_checkpoint)
            checkpoints.append(decision.recovery_checkpoint)
            return LoopStepResult("UNKNOWN_PAUSED", tuple(completed), tuple(checkpoints), remediations)
        if decision.outcome in {"TOKEN_PAUSED", "CAPACITY_DEFERRED"}:
            if not decision.action_id or not decision.cost_class or not decision.reset_timestamp:
                raise ProjectGraphError("capacity continuation is missing exact action evidence")
            arm_capacity_continuation(
                kernel=kernel, action_id=decision.action_id,
                capacity_state=decision.outcome, cost_class=decision.cost_class,
                reset_timestamp=decision.reset_timestamp,
                checkpoint_id=decision.recovery_checkpoint, arm=arm_scheduler,
                verify=verify_scheduler,
            )
            checkpoints.append(decision.recovery_checkpoint)
            return LoopStepResult(decision.outcome, tuple(completed), tuple(checkpoints), remediations)
        return LoopStepResult(decision.outcome, tuple(completed), tuple(checkpoints), remediations)
    raise ProjectGraphError("closed-loop action budget exhausted")
