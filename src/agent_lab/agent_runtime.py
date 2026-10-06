"""Local, non-production Agent runtime bound to the accepted Orchestrator Kernel.

This module deliberately exposes no provider, network, subprocess, credential, or
arbitrary callable boundary.  Its four workers are deterministic in-process
adapters used to prove dispatch, recovery, QA, and independent acceptance.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from agent_lab.orchestrator_kernel import ContractError, OrchestratorKernel, PermissionDenied


RUNTIME_ID = "LOCAL_AGENT_RUNTIME_V1"
AUTHORITY_REFERENCE = "human-authorization://D-067/local-non-production"
DEMO_OBJECTIVE = "Prove the bounded local four-role execution loop"
DEMO_ACCEPTANCE_CRITERIA = (
    "plan is immutable",
    "QA evidence is bound",
    "independent acceptance is separate",
)
ALLOWED_ROLES = frozenset(
    {
        "PLANNING_DEPENDENCY_AGENT",
        "IMPLEMENTATION_AGENT",
        "QUALITY_ENGINEERING_AGENT",
        "INDEPENDENT_ACCEPTANCE_AGENT",
    }
)
FORBIDDEN_CAPABILITIES = frozenset(
    {
        "credential_administration",
        "protected_main_merge",
        "production_release",
        "destructive_action",
        "content_release_approval",
        "destination_transmission_approval",
        "external_transfer",
    }
)
_PACKAGE_ID = re.compile(r"^[A-Z][A-Z0-9_-]{2,40}$")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class LocalWorkPackage:
    package_id: str
    objective: str
    synthetic_inputs: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]

    def validate(self) -> None:
        if not _PACKAGE_ID.fullmatch(self.package_id):
            raise ContractError("package_id must be a stable uppercase local identifier")
        if self.objective != DEMO_OBJECTIVE or self.acceptance_criteria != DEMO_ACCEPTANCE_CRITERIA:
            raise PermissionDenied("local runtime accepts only the D-067 synthetic proof contract")
        if not self.synthetic_inputs or any(not value.startswith("synthetic://") for value in self.synthetic_inputs):
            raise PermissionDenied("runtime accepts only explicit synthetic:// inputs")
        if not self.acceptance_criteria or any(not item.strip() for item in self.acceptance_criteria):
            raise ContractError("acceptance criteria must not be empty")


class LocalAgentRuntime:
    """Two-invocation local workflow: plan/checkpoint, then recover/execute/accept."""

    def __init__(self, database_path: Path | str, artifact_root: Path | str, repository_root: Path | str, contract_root: Path | str) -> None:
        self.database_path = Path(database_path).resolve()
        self.repository_root = Path(repository_root).resolve()
        self.artifact_root = Path(artifact_root).resolve()
        approved_root = (self.repository_root / "artifacts").resolve()
        if self.artifact_root == approved_root or approved_root not in self.artifact_root.parents:
            raise PermissionDenied("artifact_root must be a child of the repository artifacts directory")
        self.contract_root = Path(contract_root).resolve()

    def _paths(self, package_id: str) -> dict[str, Path]:
        package_root = (self.artifact_root / package_id.lower()).resolve()
        if self.artifact_root not in package_root.parents:
            raise PermissionDenied("package artifact path escaped the approved runtime root")
        return {
            "root": package_root,
            "state": package_root / "runtime-state.json",
            "plan": package_root / "plan.json",
            "implementation": package_root / "implementation.json",
            "qa": package_root / "qa.json",
        }

    @staticmethod
    def _task(package: LocalWorkPackage, stage: str, role: str, actor: str, parent: str | None, output: str, capabilities: list[str]) -> dict[str, Any]:
        if role not in ALLOWED_ROLES or set(capabilities) & FORBIDDEN_CAPABILITIES:
            raise PermissionDenied("role or capability is outside the local runtime allowlist")
        created = _now()
        return {
            "schema_version": 1,
            "task_id": f"{package.package_id}-{stage}",
            "parent_task_id": parent,
            "objective": f"{stage}: {package.objective}",
            "role_id": role,
            "actor_instance_id": actor,
            "repository": "golestanzadeh/ai-agent-lab",
            "ref": "d021-agent-case-provisioning",
            "case_context": None,
            "inputs": list(package.synthetic_inputs),
            "expected_outputs": [output],
            "allowed_tools": ["local_json_artifact"],
            "permissions": capabilities,
            "forbidden_actions": sorted(FORBIDDEN_CAPABILITIES | {"write_protected_main", "use_real_data", "invoke_subprocess"}),
            "budget": {"token_limit": 1000, "tool_call_limit": 10, "cost_limit_usd": 1.0},
            "timeout_seconds": 300,
            "max_retries": 0,
            "acceptance_criteria": list(package.acceptance_criteria),
            "stop_conditions": ["kill switch not RUNNING", "scope mismatch", "non-synthetic input", "authority ambiguity"],
            "escalation_route": ["MASTER_PROJECT_ORCHESTRATOR", "HUMAN_PROJECT_OWNER"],
            "created_at": created.isoformat(),
            "expires_at": (created + timedelta(hours=1)).isoformat(),
            "status": "REGISTERED",
        }

    @staticmethod
    def _manifest(task: dict[str, Any], manifest_id: str, tier: str) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "manifest_id": manifest_id,
            "role_id": task["role_id"],
            "actor_instance_id": task["actor_instance_id"],
            "task_id": task["task_id"],
            "parent_task_id": task["parent_task_id"],
            "scope": {"repository": task["repository"], "ref": task["ref"], "allowed_paths": ["artifacts/agent-runtime/"], "case_context": None},
            "inputs": list(task["inputs"]),
            "expected_outputs": list(task["expected_outputs"]),
            "allowed_tools": list(task["allowed_tools"]),
            "requested_access_tiers": [tier],
            "requested_capabilities": list(task["permissions"]),
            "forbidden_actions": list(task["forbidden_actions"]),
            "budget": dict(task["budget"]),
            "timeout_seconds": task["timeout_seconds"],
            "max_retries": task["max_retries"],
            "stop_conditions": list(task["stop_conditions"]),
            "escalation_route": list(task["escalation_route"]),
            "issued_at": task["created_at"],
            "expires_at": task["expires_at"],
            "status": "PROPOSED",
        }

    @staticmethod
    def _write_once(path: Path, payload: dict[str, Any]) -> str:
        if path.exists():
            raise ContractError(f"refusing to overwrite runtime artifact: {path.name}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return _sha(payload)

    @staticmethod
    def _response(task: dict[str, Any], artifact_ref: str, evidence: str, summary: str) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "response_id": f"RESP-{task['task_id']}",
            "task_id": task["task_id"],
            "parent_task_id": task["parent_task_id"],
            "role_id": task["role_id"],
            "actor_instance_id": task["actor_instance_id"],
            "status": "PASS",
            "result_summary": summary,
            "artifact_references": [artifact_ref],
            "changed_paths_or_state": [artifact_ref],
            "tests": [{"name": "local-runtime-contract", "outcome": "PASS", "evidence_reference": evidence}],
            "evidence": [evidence],
            "authority_used": [AUTHORITY_REFERENCE],
            "costs": {"tokens_used": 0, "tool_calls_used": 1, "cost_usd": 0.0},
            "unresolved_risks": [],
            "recommended_next_action": "independent acceptance",
            "human_required": False,
            "created_at": _now().isoformat(),
        }

    def _execute(
        self,
        kernel: OrchestratorKernel,
        task: dict[str, Any],
        manifest_id: str,
        tier: str,
        artifact_path: Path,
        payload: dict[str, Any],
        *,
        depends_on: tuple[str, ...] = (),
    ) -> str:
        kernel.register_task(task, gate_triggers=(), depends_on=depends_on)
        manifest = self._manifest(task, manifest_id, tier)
        kernel.register_manifest(manifest)
        kernel.validate_manifest(manifest_id)
        kernel.activate_manifest(manifest_id)
        for capability in task["permissions"]:
            if not kernel.permission_decision(manifest_id, capability).allowed:
                raise PermissionDenied(f"runtime capability denied: {capability}")
        started = time.monotonic()
        if not kernel.consume_budget(manifest_id, tokens=0, tool_calls=1, cost_usd=0.0).allowed:
            raise PermissionDenied("runtime budget denied")
        evidence = self._write_once(artifact_path, payload)
        if time.monotonic() - started > task["timeout_seconds"] or _now() >= datetime.fromisoformat(task["expires_at"]):
            raise PermissionDenied("runtime worker exceeded its timeout or expiry")
        artifact_ref = task["expected_outputs"][0]
        kernel.record_response(manifest_id, self._response(task, artifact_ref, evidence, f"{task['role_id']} completed local synthetic work"))
        return evidence

    def _accept(
        self,
        kernel: OrchestratorKernel,
        package: LocalWorkPackage,
        target_task: str,
        target_evidence: str,
        ordinal: str,
        target_path: Path,
        *,
        qa_path: Path | None = None,
    ) -> None:
        review_task = self._task(
            package,
            f"ACCEPT-{ordinal}",
            "INDEPENDENT_ACCEPTANCE_AGENT",
            f"{package.package_id}-IA-{ordinal}",
            target_task,
            f"acceptance://{target_task.lower()}",
            ["acceptance_review", "read_test_evidence"],
        )
        review_manifest_id = f"MAN-{review_task['task_id']}"
        kernel.register_task(review_task, gate_triggers=())
        kernel.register_manifest(self._manifest(review_task, review_manifest_id, "A1"))
        kernel.validate_manifest(review_manifest_id)
        kernel.activate_manifest(review_manifest_id)
        for capability in review_task["permissions"]:
            if not kernel.permission_decision(review_manifest_id, capability).allowed:
                raise PermissionDenied(f"review capability denied: {capability}")
        try:
            artifact = json.loads(target_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ContractError("independent review target is missing or invalid") from exc
        if _sha(artifact) != target_evidence or artifact.get("classification") != "SYNTHETIC":
            raise ContractError("independent review target evidence or classification does not match")
        response_row = kernel._connection.execute(
            "SELECT payload_json FROM responses WHERE task_id=?", (target_task,)
        ).fetchone()
        task_row = kernel._connection.execute("SELECT payload_json FROM tasks WHERE task_id=?", (target_task,)).fetchone()
        if response_row is None or task_row is None:
            raise ContractError("independent review lineage is incomplete")
        response = json.loads(response_row["payload_json"])
        durable_task = json.loads(task_row["payload_json"])
        if response["evidence"] != [target_evidence] or response["artifact_references"] != durable_task["expected_outputs"]:
            raise ContractError("independent review response is not bound to the task output")
        if any(test["outcome"] != "PASS" for test in response["tests"]):
            raise ContractError("independent review found non-passing test evidence")
        if ordinal == "PLAN":
            if artifact.get("acceptance_criteria") != list(package.acceptance_criteria) or artifact.get("inputs") != list(package.synthetic_inputs):
                raise ContractError("plan does not match the authorized package")
        if ordinal == "QA":
            expected_checks = [{"criterion": item, "outcome": "PASS"} for item in package.acceptance_criteria]
            if artifact.get("checks") != expected_checks or artifact.get("failure_evidence_hidden") is not False:
                raise ContractError("QA evidence does not prove every exact acceptance criterion")
        if ordinal == "IMPLEMENT":
            if qa_path is None:
                raise ContractError("implementation acceptance requires QA evidence")
            try:
                qa = json.loads(qa_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ContractError("implementation acceptance QA evidence is missing") from exc
            expected_checks = [{"criterion": item, "outcome": "PASS"} for item in package.acceptance_criteria]
            if qa.get("implementation_evidence") != target_evidence or qa.get("checks") != expected_checks:
                raise ContractError("QA evidence is not bound to the implementation")
            qa_digest = _sha(qa)
            qa_task_id = f"{package.package_id}-QA"
            qa_response = kernel._connection.execute(
                "SELECT payload_json FROM responses WHERE task_id=?", (qa_task_id,)
            ).fetchone()
            qa_acceptance = kernel._connection.execute(
                "SELECT decision FROM acceptance_records WHERE task_id=? ORDER BY acceptance_id DESC LIMIT 1",
                (qa_task_id,),
            ).fetchone()
            if qa_response is None or json.loads(qa_response["payload_json"])["evidence"] != [qa_digest]:
                raise ContractError("implementation acceptance QA digest is not durable")
            if qa_acceptance is None or qa_acceptance["decision"] != "PASS":
                raise ContractError("implementation acceptance requires accepted QA")
        acceptance_evidence = _sha({"target_task": target_task, "target_evidence": target_evidence, "response": response["response_id"], "criteria": package.acceptance_criteria})
        kernel.record_acceptance(target_task, review_manifest_id, "PASS", evidence_reference=acceptance_evidence)

    def start(self, package: LocalWorkPackage) -> dict[str, Any]:
        package.validate()
        paths = self._paths(package.package_id)
        if self.database_path.exists() or paths["root"].exists():
            raise ContractError("runtime start requires new database and package artifact paths")
        plan_task = self._task(package, "PLAN", "PLANNING_DEPENDENCY_AGENT", f"{package.package_id}-PLANNER", None, "artifact://local/agent-runtime/plan", ["plan_tasks", "propose_acceptance_criteria"])
        plan_payload = {
            "runtime_id": RUNTIME_ID,
            "classification": "SYNTHETIC",
            "package_id": package.package_id,
            "objective": package.objective,
            "ordered_stages": ["PLAN", "IMPLEMENT", "QA", "INDEPENDENT_ACCEPTANCE"],
            "inputs": list(package.synthetic_inputs),
            "acceptance_criteria": list(package.acceptance_criteria),
            "external_capabilities": "DENIED",
        }
        with OrchestratorKernel(self.database_path, self.contract_root) as kernel:
            package_authority = f"{AUTHORITY_REFERENCE}/{_sha({'package': package.package_id, 'inputs': package.synthetic_inputs})}"
            kernel.set_kill_switch("RUNNING", actor_id="HUMAN_PROJECT_OWNER", authority_reference=package_authority)
            plan_evidence = self._execute(kernel, plan_task, f"MAN-{plan_task['task_id']}", "A1", paths["plan"], plan_payload)
            self._accept(kernel, package, plan_task["task_id"], plan_evidence, "PLAN", paths["plan"])
            state = {"runtime_id": RUNTIME_ID, "package_id": package.package_id, "state": "PLANNED", "plan_evidence": plan_evidence, "package_digest": _sha({"objective": package.objective, "inputs": package.synthetic_inputs, "criteria": package.acceptance_criteria})}
            self._write_once(paths["state"], state)
            kernel.set_kill_switch("PAUSED", actor_id="MASTER_PROJECT_ORCHESTRATOR", authority_reference="local-runtime://recovery-boundary")
            checkpoint = kernel.create_checkpoint(f"{package.package_id}-PLANNED")
        return {"state": "PLANNED", "checkpoint": checkpoint, "plan_evidence": plan_evidence}

    def resume(self, package: LocalWorkPackage) -> dict[str, Any]:
        package.validate()
        paths = self._paths(package.package_id)
        try:
            state = json.loads(paths["state"].read_text(encoding="utf-8"))
            plan = json.loads(paths["plan"].read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ContractError("runtime recovery artifacts are missing or invalid") from exc
        expected_state = {"runtime_id": RUNTIME_ID, "package_id": package.package_id, "state": "PLANNED", "plan_evidence": _sha(plan), "package_digest": _sha({"objective": package.objective, "inputs": package.synthetic_inputs, "criteria": package.acceptance_criteria})}
        if state != expected_state:
            raise ContractError("runtime recovery state does not match the immutable plan")
        if plan.get("objective") != package.objective or plan.get("inputs") != list(package.synthetic_inputs) or plan.get("acceptance_criteria") != list(package.acceptance_criteria):
            raise ContractError("runtime package changed after the immutable plan")
        with OrchestratorKernel(self.database_path, self.contract_root) as kernel:
            recovered = kernel.recover_latest_checkpoint()
            if recovered["checkpoint_id"] != f"{package.package_id}-PLANNED":
                raise ContractError("runtime is not at the planned recovery checkpoint")
            checkpoint_event = kernel._connection.execute(
                "SELECT event_id, event_type, entity_id FROM audit_events WHERE event_id>? ORDER BY event_id",
                (recovered["snapshot"]["last_event_id"],),
            ).fetchall()
            if (
                len(checkpoint_event) != 1
                or checkpoint_event[0]["event_type"] != "CHECKPOINT_CREATED"
                or checkpoint_event[0]["entity_id"] != recovered["checkpoint_id"]
                or kernel._state_snapshot(recovered["snapshot"]["last_event_id"]) != recovered["snapshot"]
            ):
                raise ContractError("runtime state changed after the exact recovery checkpoint")
            if kernel.kill_switch_state() != "PAUSED":
                raise ContractError("runtime recovery requires the exact PAUSED boundary")
            package_authority = f"{AUTHORITY_REFERENCE}/{_sha({'package': package.package_id, 'inputs': package.synthetic_inputs})}"
            kernel.set_kill_switch("RUNNING", actor_id="HUMAN_PROJECT_OWNER", authority_reference=package_authority)
            impl_task = self._task(package, "IMPLEMENT", "IMPLEMENTATION_AGENT", f"{package.package_id}-IMPLEMENTER", f"{package.package_id}-PLAN", "artifact://local/agent-runtime/implementation", ["write_bounded_branch", "run_tests", "report_evidence"])
            impl_payload = {"runtime_id": RUNTIME_ID, "classification": "SYNTHETIC", "package_id": package.package_id, "plan_evidence": state["plan_evidence"], "result": "bounded local synthetic implementation artifact", "external_capabilities": "DENIED"}
            impl_evidence = self._execute(
                kernel,
                impl_task,
                f"MAN-{impl_task['task_id']}",
                "A2",
                paths["implementation"],
                impl_payload,
                depends_on=(f"{package.package_id}-PLAN",),
            )

            qa_task = self._task(package, "QA", "QUALITY_ENGINEERING_AGENT", f"{package.package_id}-QA", impl_task["task_id"], "artifact://local/agent-runtime/qa", ["write_tests", "run_tests", "report_evidence"])
            qa_payload = {"runtime_id": RUNTIME_ID, "classification": "SYNTHETIC", "package_id": package.package_id, "implementation_evidence": impl_evidence, "checks": [{"criterion": item, "outcome": "PASS"} for item in package.acceptance_criteria], "failure_evidence_hidden": False}
            qa_evidence = self._execute(
                kernel,
                qa_task,
                f"MAN-{qa_task['task_id']}",
                "A2",
                paths["qa"],
                qa_payload,
                depends_on=(f"{package.package_id}-PLAN",),
            )
            self._accept(kernel, package, qa_task["task_id"], qa_evidence, "QA", paths["qa"])
            self._accept(kernel, package, impl_task["task_id"], impl_evidence, "IMPLEMENT", paths["implementation"], qa_path=paths["qa"])
            kernel.set_kill_switch("HALTED", actor_id="MASTER_PROJECT_ORCHESTRATOR", authority_reference="local-runtime://complete")
            checkpoint = kernel.create_checkpoint(f"{package.package_id}-COMPLETE")
            kernel.verify_audit_chain()
        inspection = OrchestratorKernel.inspect_read_only(self.database_path)
        return {"state": "COMPLETED", "checkpoint": checkpoint, "audit_integrity": inspection["audit_integrity"], "kill_switch": inspection["kill_switch"], "counts": inspection["counts"]}
