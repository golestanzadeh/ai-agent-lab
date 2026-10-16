"""One-shot synthetic UI worker governed by the existing Orchestrator Kernel."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from agent_lab.orchestrator_kernel import ContractError, OrchestratorKernel, PermissionDenied


AUTHORITY_REFERENCE = "human-authorization://UI25-05/synthetic-kernel-execution"
WORKER_ID = "UI25-SYNTHETIC-WORKER-V1"
_IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class SyntheticCaseKernelExecutor:
    """Explicit one-task adapter; it is neither a scheduler nor an authority store."""

    def __init__(self, database_path: str | Path, contract_root: str | Path):
        self.database_path = Path(database_path).resolve()
        self.contract_root = Path(contract_root).resolve()

    @staticmethod
    def _validate_scope(case_id: str, tax_year: int, run_id: str, synthetic_value: int) -> None:
        if not isinstance(case_id, str) or not case_id.startswith("TEST-") or not _IDENTIFIER.fullmatch(case_id):
            raise PermissionDenied("synthetic execution requires an exact TEST case")
        if tax_year != 2025:
            raise PermissionDenied("synthetic UI25 execution is restricted to tax year 2025")
        if not isinstance(run_id, str) or not _IDENTIFIER.fullmatch(run_id):
            raise ContractError("run_id must be a bounded ASCII identifier")
        if isinstance(synthetic_value, bool) or not isinstance(synthetic_value, int) or not 0 <= synthetic_value <= 1_000_000:
            raise ContractError("synthetic value is outside the bounded range")

    @staticmethod
    def _identities(case_id: str, tax_year: int, run_id: str) -> tuple[str, str, str]:
        scope = f"{case_id}:{tax_year}:{run_id}".encode("ascii")
        suffix = hashlib.sha256(scope).hexdigest()[:20].upper()
        return f"TASK-UI25-{suffix}", f"MAN-UI25-{suffix}", f"RESP-UI25-{suffix}"

    @staticmethod
    def _run_worker(
        kernel: OrchestratorKernel, *, manifest_id: str, case_id: str,
        tax_year: int, run_id: str, synthetic_value: int,
    ) -> tuple[int, str]:
        decision = kernel.permission_decision(
            manifest_id, "report_evidence", case_id=case_id,
            tax_year=tax_year, run_id=run_id,
        )
        if not decision.allowed:
            raise PermissionDenied("Kernel denied the fixed synthetic worker")
        if not kernel.consume_budget(
            manifest_id, tokens=0, tool_calls=1, cost_usd=0.0
        ).allowed:
            raise PermissionDenied("Kernel denied the fixed worker budget")
        result = synthetic_value * 2
        evidence = "sha256:" + hashlib.sha256(_canonical({
            "worker_id": WORKER_ID, "case_id": case_id, "tax_year": tax_year,
            "run_id": run_id, "synthetic_value": synthetic_value,
            "deterministic_result": result,
        }).encode("utf-8")).hexdigest()
        return result, evidence

    def execute(
        self, *, case_id: str, tax_year: int, run_id: str, synthetic_value: int
    ) -> dict[str, Any]:
        self._validate_scope(case_id, tax_year, run_id, synthetic_value)
        task_id, manifest_id, response_id = self._identities(case_id, tax_year, run_id)
        now = datetime.now(timezone.utc)
        context = {"case_id": case_id, "tax_year": tax_year, "run_id": run_id}
        task = {
            "schema_version": 1, "task_id": task_id, "parent_task_id": None,
            "objective": "Execute one bounded deterministic UI25 synthetic calculation",
            "role_id": "IMPLEMENTATION_AGENT", "actor_instance_id": WORKER_ID,
            "repository": "golestanzadeh/ai-agent-lab", "ref": "oi0002-identity-persistence",
            "case_context": context,
            "inputs": [f"synthetic://ui25/value/{synthetic_value}"],
            "expected_outputs": [f"kernel://ui25/result/{task_id}"],
            "allowed_tools": ["synthetic_ui25_deterministic_worker"],
            "permissions": ["report_evidence"],
            "forbidden_actions": [
                "external_transfer", "use_real_data", "protected_persistence",
                "agent_spawn", "subprocess", "network_io",
            ],
            "budget": {"token_limit": 1, "tool_call_limit": 1, "cost_limit_usd": 0.01},
            "timeout_seconds": 30, "max_retries": 0,
            "acceptance_criteria": ["deterministic synthetic result is durably recorded"],
            "stop_conditions": ["scope mismatch", "kill switch not RUNNING", "duplicate task"],
            "escalation_route": ["MASTER_PROJECT_ORCHESTRATOR", "HUMAN_PROJECT_OWNER"],
            "created_at": now.isoformat(), "expires_at": (now + timedelta(minutes=10)).isoformat(),
            "status": "REGISTERED",
        }
        manifest = {
            "schema_version": 1, "manifest_id": manifest_id,
            "role_id": task["role_id"], "actor_instance_id": task["actor_instance_id"],
            "task_id": task_id, "parent_task_id": None,
            "scope": {
                "repository": task["repository"], "ref": task["ref"],
                "allowed_paths": [], "case_context": context,
            },
            "inputs": task["inputs"], "expected_outputs": task["expected_outputs"],
            "allowed_tools": task["allowed_tools"], "requested_access_tiers": ["A1"],
            "requested_capabilities": task["permissions"],
            "forbidden_actions": task["forbidden_actions"], "budget": task["budget"],
            "timeout_seconds": task["timeout_seconds"], "max_retries": 0,
            "stop_conditions": task["stop_conditions"],
            "escalation_route": task["escalation_route"],
            "issued_at": task["created_at"], "expires_at": task["expires_at"],
            "status": "PROPOSED",
        }
        with OrchestratorKernel(self.database_path, self.contract_root) as kernel:
            kernel.verify_audit_chain()
            if kernel.kill_switch_state() != "HALTED":
                raise PermissionDenied("one-shot synthetic execution requires the HALTED boundary")
            for row in kernel._connection.execute(
                "SELECT task_id, payload_json FROM tasks ORDER BY task_id"
            ).fetchall():
                existing = json.loads(row["payload_json"])
                existing_context = existing.get("case_context")
                if row["task_id"] == task_id:
                    raise ContractError("synthetic task identity was already executed or registered")
                if (
                    isinstance(existing_context, dict)
                    and existing_context.get("run_id") == run_id
                    and existing_context != context
                ):
                    raise PermissionDenied("run identity is already bound to another case or year")
            # The explicit UI POST is the bounded Owner action represented here.
            kernel.set_kill_switch(
                "RUNNING", actor_id="HUMAN_PROJECT_OWNER",
                authority_reference=AUTHORITY_REFERENCE,
            )
            try:
                kernel.register_task(task, gate_triggers=())
                kernel.register_manifest(manifest)
                kernel.validate_manifest(manifest_id)
                kernel.activate_manifest(manifest_id)
                result, evidence = self._run_worker(
                    kernel, manifest_id=manifest_id, case_id=case_id,
                    tax_year=tax_year, run_id=run_id, synthetic_value=synthetic_value,
                )
                response = {
                    "schema_version": 1, "response_id": response_id,
                    "task_id": task_id, "parent_task_id": None,
                    "role_id": task["role_id"], "actor_instance_id": WORKER_ID,
                    "status": "PASS",
                    "result_summary": f"SYNTHETIC_RESULT={result}; WORKER={WORKER_ID}",
                    "artifact_references": task["expected_outputs"],
                    "changed_paths_or_state": [f"kernel://response/{response_id}"],
                    "tests": [{
                        "name": "deterministic-synthetic-double", "outcome": "PASS",
                        "evidence_reference": evidence,
                    }],
                    "evidence": [evidence], "authority_used": [AUTHORITY_REFERENCE],
                    "costs": {"tokens_used": 0, "tool_calls_used": 1, "cost_usd": 0.0},
                    "unresolved_risks": [],
                    "recommended_next_action": "independent acceptance remains separate",
                    "human_required": False, "created_at": datetime.now(timezone.utc).isoformat(),
                }
                kernel.record_response(manifest_id, response)
                kernel.verify_audit_chain()
            finally:
                kernel.set_kill_switch(
                    "HALTED", actor_id="MASTER_PROJECT_ORCHESTRATOR",
                    authority_reference="ui25://synthetic-one-shot-complete",
                )
        return {
            "task_id": task_id, "run_id": run_id, "result": result,
            "evidence": evidence, "status": "AWAITING_ACCEPTANCE",
        }
