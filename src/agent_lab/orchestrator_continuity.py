"""Bounded synthetic continuity proof for the existing Master Orchestrator.

This module exposes one closed local adapter. It cannot invoke a shell, network,
provider, credential, tax-data path, ERiC engine, scheduler, or protected branch.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .orchestrator_kernel import ContractError, OrchestratorKernel, PermissionDenied


AUTHORITY_ID = "AUTH-ORCH-CONT-20260927-001"
MILESTONE_ID = "MASTER_ORCHESTRATOR_CONTINUITY_PROOF_V1"
APPROVAL_REFERENCE = "ORCH-CONT-20260927-001"
ADAPTER_ID = "SYNTHETIC_LOCAL_V1"
FORBIDDEN_ACTIONS = ["external_transfer", "production", "protected_main", "real_data"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _template(package_id: str, sequence: int, *, depends_on: tuple[str, ...] = ()) -> dict[str, Any]:
    suffix = package_id.rsplit("-", 1)[-1]
    return {
        "package_id": package_id,
        "sequence": sequence,
        "depends_on": list(depends_on),
        "objective": f"Execute authorized synthetic continuity package {suffix}",
        "role_id": "IMPLEMENTATION_AGENT",
        "actor_instance_id": f"AGI-ORCH-CONT-{suffix}",
        "inputs": [f"synthetic://orchestrator-continuity/{suffix}"],
        "expected_outputs": [f"artifact://local/orchestrator-continuity/{suffix}"],
        "allowed_tools": ["synthetic_local_dispatch", "pytest"],
        "permissions": ["write_bounded_branch", "run_tests", "report_evidence"],
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "budget": {"token_limit": 1000, "tool_call_limit": 10, "cost_limit_usd": 1.0},
        "timeout_seconds": 600,
        "max_retries": 1,
        "acceptance_criteria": [f"synthetic package {suffix} independently accepted"],
        "stop_conditions": ["authority ambiguity", "budget exhausted", "non-recoverable failure"],
        "escalation_route": ["MASTER_PROJECT_ORCHESTRATOR", "HUMAN_PROJECT_OWNER"],
    }


def milestone_authority(*, now: datetime | None = None) -> dict[str, Any]:
    issued = now or _now()
    return {
        "schema_version": 1,
        "authority_id": AUTHORITY_ID,
        "milestone_id": MILESTONE_ID,
        "owner_approval_reference": APPROVAL_REFERENCE,
        "repository": "golestanzadeh/ai-agent-lab",
        "ref": "d021-agent-case-provisioning",
        "package_templates": [
            _template("PKG-ORCH-CONT-001", 1),
            _template("PKG-ORCH-CONT-002", 2, depends_on=("PKG-ORCH-CONT-001",)),
        ],
        "max_generated_packages": 2,
        "max_replans": 1,
        "dispatch_adapters": [ADAPTER_ID],
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "created_at": issued.isoformat(),
        "expires_at": (issued + timedelta(hours=4)).isoformat(),
        "status": "ACTIVE",
    }


def _task(template: dict[str, Any], task_id: str, authority: dict[str, Any]) -> dict[str, Any]:
    issued = _now()
    return {
        "schema_version": 1,
        "task_id": task_id,
        "parent_task_id": None,
        "objective": template["objective"],
        "role_id": template["role_id"],
        "actor_instance_id": template["actor_instance_id"],
        "repository": authority["repository"],
        "ref": authority["ref"],
        "case_context": None,
        "inputs": template["inputs"],
        "expected_outputs": template["expected_outputs"],
        "allowed_tools": template["allowed_tools"],
        "permissions": template["permissions"],
        "forbidden_actions": template["forbidden_actions"],
        "budget": template["budget"],
        "timeout_seconds": template["timeout_seconds"],
        "max_retries": template["max_retries"],
        "acceptance_criteria": template["acceptance_criteria"],
        "stop_conditions": template["stop_conditions"],
        "escalation_route": template["escalation_route"],
        "created_at": issued.isoformat(),
        "expires_at": (issued + timedelta(hours=3)).isoformat(),
        "status": "REGISTERED",
    }


class RecoverableSyntheticDispatchError(RuntimeError):
    """Closed synthetic failure used to prove bounded retry."""


@dataclass(frozen=True)
class SyntheticDispatchResult:
    artifact_reference: str
    evidence_reference: str
    changed_path: str


class SyntheticLocalDispatchAdapter:
    """Writes one deterministic JSON artifact below a fixed local root."""

    adapter_id = ADAPTER_ID

    def __init__(self, artifact_root: Path | str, *, fail_once_package_id: str | None = None) -> None:
        self.artifact_root = Path(artifact_root).resolve()
        self.fail_once_package_id = fail_once_package_id
        self._failed: set[str] = set()

    def dispatch(self, ready: dict[str, Any], attempt_id: str) -> SyntheticDispatchResult:
        package_id = ready["package_id"]
        task = ready["task"]
        if self.fail_once_package_id == package_id and package_id not in self._failed:
            self._failed.add(package_id)
            raise RecoverableSyntheticDispatchError("synthetic recoverable process failure")
        if task["allowed_tools"] != ["synthetic_local_dispatch", "pytest"]:
            raise PermissionDenied("synthetic adapter tool boundary changed")
        if any(not item.startswith("synthetic://") for item in task["inputs"]):
            raise PermissionDenied("synthetic adapter received a non-synthetic input")
        if len(task["expected_outputs"]) != 1 or not task["expected_outputs"][0].startswith("artifact://local/"):
            raise PermissionDenied("synthetic adapter output boundary changed")
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        target = (self.artifact_root / f"{package_id.lower()}.json").resolve()
        if self.artifact_root not in target.parents:
            raise PermissionDenied("synthetic artifact escaped the fixed local root")
        evidence = {
            "adapter_id": self.adapter_id,
            "attempt_id": attempt_id,
            "package_id": package_id,
            "task_id": ready["task_id"],
            "inputs": task["inputs"],
            "objective": task["objective"],
        }
        target.write_text(_canonical(evidence) + "\n", encoding="utf-8")
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        return SyntheticDispatchResult(
            task["expected_outputs"][0],
            f"sha256:{digest}",
            target.as_posix(),
        )


class OrchestratorContinuityProof:
    """Executes the fixed two-package local proof over the existing Kernel."""

    def __init__(self, database_path: Path | str, artifact_root: Path | str, contract_root: Path | str) -> None:
        self.database_path = Path(database_path)
        self.artifact_root = Path(artifact_root)
        self.contract_root = Path(contract_root)

    @staticmethod
    def _manifest(task: dict[str, Any], manifest_id: str, *, actor_id: str | None = None) -> dict[str, Any]:
        issued = _now()
        role_id = task["role_id"]
        return {
            "schema_version": 1,
            "manifest_id": manifest_id,
            "role_id": role_id,
            "actor_instance_id": actor_id or task["actor_instance_id"],
            "task_id": task["task_id"],
            "parent_task_id": task["parent_task_id"],
            "scope": {"repository": task["repository"], "ref": task["ref"], "allowed_paths": ["artifacts/orchestrator-continuity/"], "case_context": None},
            "inputs": list(task["inputs"]),
            "expected_outputs": list(task["expected_outputs"]),
            "allowed_tools": list(task["allowed_tools"]),
            "requested_access_tiers": ["A1"] if role_id == "INDEPENDENT_ACCEPTANCE_AGENT" else ["A2"],
            "requested_capabilities": list(task["permissions"]),
            "forbidden_actions": list(task["forbidden_actions"]),
            "budget": dict(task["budget"]),
            "timeout_seconds": task["timeout_seconds"],
            "max_retries": task["max_retries"],
            "stop_conditions": list(task["stop_conditions"]),
            "escalation_route": list(task["escalation_route"]),
            "issued_at": issued.isoformat(),
            "expires_at": task["expires_at"],
            "status": "PROPOSED",
        }

    @staticmethod
    def _review_task(target: dict[str, Any], ordinal: int) -> dict[str, Any]:
        issued = _now()
        task_id = f"TASK-ORCH-CONT-REVIEW-{ordinal:03d}"
        return {
            "schema_version": 1,
            "task_id": task_id,
            "parent_task_id": target["task_id"],
            "objective": f"Independently accept {target['task_id']}",
            "role_id": "INDEPENDENT_ACCEPTANCE_AGENT",
            "actor_instance_id": f"AGI-ORCH-CONT-REVIEW-{ordinal:03d}",
            "repository": target["repository"],
            "ref": target["ref"],
            "case_context": None,
            "inputs": list(target["expected_outputs"]),
            "expected_outputs": [f"artifact://local/orchestrator-continuity/acceptance-{ordinal:03d}"],
            "allowed_tools": ["pytest"],
            "permissions": ["acceptance_review", "read_test_evidence"],
            "forbidden_actions": ["implement_reviewed_change", "rewrite_failure_evidence", "merge", "release"],
            "budget": {"token_limit": 200, "tool_call_limit": 2, "cost_limit_usd": 0.1},
            "timeout_seconds": 300,
            "max_retries": 0,
            "acceptance_criteria": ["evidence identity matches the reviewed package"],
            "stop_conditions": ["evidence mismatch"],
            "escalation_route": ["MASTER_PROJECT_ORCHESTRATOR", "HUMAN_PROJECT_OWNER"],
            "created_at": issued.isoformat(),
            "expires_at": (issued + timedelta(hours=2)).isoformat(),
            "status": "REGISTERED",
        }

    def _execute_and_accept(
        self,
        kernel: OrchestratorKernel,
        ready: dict[str, Any],
        result: SyntheticDispatchResult,
        ordinal: int,
    ) -> None:
        task = ready["task"]
        manifest_id = f"MAN-ORCH-CONT-{ordinal:03d}"
        manifest = self._manifest(task, manifest_id)
        kernel.register_manifest(manifest)
        kernel.validate_manifest(manifest_id)
        kernel.activate_manifest(manifest_id)
        kernel.consume_budget(manifest_id, tool_calls=1)
        kernel.record_response(manifest_id, {
            "schema_version": 1,
            "response_id": f"RESP-ORCH-CONT-{ordinal:03d}",
            "task_id": task["task_id"],
            "parent_task_id": None,
            "role_id": task["role_id"],
            "actor_instance_id": task["actor_instance_id"],
            "status": "PASS",
            "result_summary": "Bounded synthetic local package completed",
            "artifact_references": [result.artifact_reference],
            "changed_paths_or_state": [result.changed_path],
            "tests": [{"name": "synthetic_local_dispatch", "outcome": "PASS", "evidence_reference": result.evidence_reference}],
            "evidence": [result.evidence_reference],
            "authority_used": [f"authority://{AUTHORITY_ID}"],
            "costs": {"tokens_used": 0, "tool_calls_used": 1, "cost_usd": 0.0},
            "unresolved_risks": [],
            "recommended_next_action": "independent acceptance",
            "human_required": False,
            "created_at": _now().isoformat(),
        })
        review = self._review_task(task, ordinal)
        kernel.register_task(review, gate_triggers=())
        review_manifest_id = f"MAN-ORCH-CONT-REVIEW-{ordinal:03d}"
        review_manifest = self._manifest(review, review_manifest_id)
        kernel.register_manifest(review_manifest)
        kernel.validate_manifest(review_manifest_id)
        kernel.activate_manifest(review_manifest_id)
        kernel.record_acceptance(task["task_id"], review_manifest_id, "PASS", evidence_reference=result.evidence_reference)

    def run(self) -> dict[str, Any]:
        if self.database_path.exists():
            raise ContractError("continuity proof requires a new database")
        authority = milestone_authority()
        adapter = SyntheticLocalDispatchAdapter(self.artifact_root, fail_once_package_id="PKG-ORCH-CONT-001")
        try:
            with OrchestratorKernel(self.database_path, self.contract_root) as kernel:
                kernel.register_milestone_authority(authority)
                first = _task(authority["package_templates"][0], "TASK-ORCH-CONT-001", authority)
                kernel.register_authorized_package(AUTHORITY_ID, "PKG-ORCH-CONT-001", first)
                kernel.set_kill_switch("RUNNING", actor_id="HUMAN_PROJECT_OWNER", authority_reference=APPROVAL_REFERENCE)
                ready = kernel.select_ready_package(AUTHORITY_ID)
                if ready is None or ready["package_id"] != "PKG-ORCH-CONT-001":
                    raise ContractError("first authorized package is not ready")
                try:
                    adapter.dispatch(ready, "ATTEMPT-ORCH-CONT-001-A")
                except RecoverableSyntheticDispatchError:
                    retry = kernel.record_dispatch_attempt(
                        ready["task_id"], "ATTEMPT-ORCH-CONT-001-A", status="FAILED", failure_class="retriable_process_error"
                    )
                    if retry.outcome != "RETRYABLE":
                        raise ContractError("recoverable failure did not authorize the bounded retry")
                first_result = adapter.dispatch(ready, "ATTEMPT-ORCH-CONT-001-B")
                kernel.record_dispatch_attempt(ready["task_id"], "ATTEMPT-ORCH-CONT-001-B", status="PASS")
                self._execute_and_accept(kernel, ready, first_result, 1)
                kernel.set_kill_switch("PAUSED", actor_id="MASTER_PROJECT_ORCHESTRATOR", authority_reference="SIMULATED_CAPACITY_PAUSE")
                pause_hash = kernel.create_checkpoint("ORCH-CONT-CAPACITY-PAUSED")

            with OrchestratorKernel(self.database_path, self.contract_root) as recovered:
                checkpoint = recovered.recover_latest_checkpoint()
                if checkpoint["checkpoint_id"] != "ORCH-CONT-CAPACITY-PAUSED" or checkpoint["snapshot_hash"] != pause_hash:
                    raise ContractError("capacity-pause checkpoint recovery failed")
                if recovered.kill_switch_state() != "PAUSED":
                    raise ContractError("recovered capacity pause is not durable")
                recovered.set_kill_switch("RUNNING", actor_id="HUMAN_PROJECT_OWNER", authority_reference=APPROVAL_REFERENCE)
                if recovered.select_ready_package(AUTHORITY_ID) is not None:
                    raise ContractError("queue was not exhausted before bounded replanning")
                second = _task(authority["package_templates"][1], "TASK-ORCH-CONT-002", authority)
                recovered.replan_authorized_package(AUTHORITY_ID, "PKG-ORCH-CONT-002", second)
                ready = recovered.select_ready_package(AUTHORITY_ID)
                if ready is None or ready["package_id"] != "PKG-ORCH-CONT-002":
                    raise ContractError("dependent authorized package is not ready after replanning")
                second_result = adapter.dispatch(ready, "ATTEMPT-ORCH-CONT-002-A")
                recovered.record_dispatch_attempt(ready["task_id"], "ATTEMPT-ORCH-CONT-002-A", status="PASS")
                self._execute_and_accept(recovered, ready, second_result, 2)
                recovered.set_kill_switch("HALTED", actor_id="MASTER_PROJECT_ORCHESTRATOR", authority_reference="SYNTHETIC_PROOF_COMPLETE")
                final_hash = recovered.create_checkpoint("ORCH-CONT-PROOF-COMPLETE")
                inspection = OrchestratorKernel.inspect_read_only(self.database_path)
                return {
                    "status": "PASS",
                    "authority_id": AUTHORITY_ID,
                    "adapter_id": ADAPTER_ID,
                    "packages_completed": 2,
                    "recoverable_failures": 1,
                    "dispatch_attempts": inspection["counts"]["dispatch_attempts"],
                    "independent_acceptances": inspection["counts"]["acceptance_records"],
                    "replans": recovered._connection.execute(
                        "SELECT replan_count FROM milestone_authorities WHERE authority_id=?", (AUTHORITY_ID,)
                    ).fetchone()["replan_count"],
                    "pause_checkpoint_hash": pause_hash,
                    "final_checkpoint_hash": final_hash,
                    "audit_integrity": inspection["audit_integrity"],
                    "kill_switch": inspection["kill_switch"],
                }
        except Exception as exc:
            self._persist_terminal_diagnostic(exc)
            raise

    def _persist_terminal_diagnostic(self, exc: Exception) -> None:
        if not self.database_path.exists():
            return
        try:
            with OrchestratorKernel(self.database_path, self.contract_root) as kernel:
                checkpoint = kernel._connection.execute(
                    "SELECT checkpoint_id FROM checkpoints ORDER BY created_at DESC, checkpoint_id DESC LIMIT 1"
                ).fetchone()
                kernel.record_stop_diagnostic({
                    "diagnostic_id": f"STOP-ORCH-CONT-{_now().strftime('%Y%m%d%H%M%S%f')}",
                    "category": "MATERIAL_FAILURE",
                    "summary": f"{type(exc).__name__}: {exc}",
                    "impact": "Synthetic continuity proof incomplete; no external operation was attempted",
                    "automated_recovery": "Execution stopped fail-closed and preserved the audit/checkpoint state",
                    "required_next_action": "Inspect the recorded failure evidence before an authorized retry",
                    "continuation_point": checkpoint["checkpoint_id"] if checkpoint else "NO_CHECKPOINT",
                    "created_at": _now().isoformat(),
                })
        except Exception:
            # The original failure remains authoritative when durable state itself is unavailable.
            return
