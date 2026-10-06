"""Bounded Phase O4 pilot for the accepted deterministic Orchestrator Kernel.

The pilot validates an explicit set of public repository governance documents.
It uses local SQLite state and JSON evidence only; it has no network, case-data,
credential, merge, release, or external-transfer capability.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from agent_lab.orchestrator_kernel import ContractError, OrchestratorKernel


PILOT_ID = "O4-GOVERNANCE-DOC-CONSISTENCY-V1"
IMPLEMENTATION_TASK_ID = "O4-PILOT-IMPLEMENTATION"
IMPLEMENTATION_MANIFEST_ID = "O4-MANIFEST-IMPLEMENTATION"
REVIEW_TASK_ID = "O4-PILOT-INDEPENDENT-REVIEW"
REVIEW_MANIFEST_ID = "O4-MANIFEST-INDEPENDENT-REVIEW"
START_CHECKPOINT_ID = "O4-CHECKPOINT-AWAITING-REVIEW"
FINAL_CHECKPOINT_ID = "O4-CHECKPOINT-COMPLETE"
O4_AUTHORITY_REFERENCE = "human-approval://phase-o4/d70a28b9b33710a81881855048baccb63f3fc176"

DOCUMENT_RULES = {
    "CONSTITUTION.md": ("# Project Constitution v2", "## Article 10 — Human Gates"),
    "PROJECT_CHECKPOINT.md": ("# Project Checkpoint", "## Mandatory startup protocol"),
    "AGENTS.md": ("# AGENTS.md", "## Mandatory cross-session startup"),
    "CURRENT_STATE.md": ("# Current State", "## Exact next action"),
    "ROADMAP.md": ("# Roadmap", "## Current position"),
}


def _timestamp(hours: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _task(
    *,
    task_id: str,
    role_id: str,
    actor_instance_id: str,
    parent_task_id: str | None,
    permissions: list[str],
    objective: str,
    inputs: list[str],
    outputs: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "task_id": task_id,
        "parent_task_id": parent_task_id,
        "objective": objective,
        "role_id": role_id,
        "actor_instance_id": actor_instance_id,
        "repository": "golestanzadeh/ai-agent-lab",
        "ref": "d021-agent-case-provisioning",
        "case_context": None,
        "inputs": inputs,
        "expected_outputs": outputs,
        "allowed_tools": ["python"],
        "permissions": permissions,
        "forbidden_actions": [
            "access_case_data", "network_access", "use_credentials", "write_protected_main",
            "merge", "release", "external_transfer",
        ],
        "budget": {"token_limit": 1000, "tool_call_limit": 10, "cost_limit_usd": 1.0},
        "timeout_seconds": 600,
        "max_retries": 1,
        "acceptance_criteria": [
            "all allowlisted governance documents exist",
            "all required markers are present",
            "evidence hashes match during independent review",
        ],
        "stop_conditions": ["scope mismatch", "authority ambiguity", "evidence mismatch"],
        "escalation_route": ["MASTER_PROJECT_ORCHESTRATOR", "HUMAN_PROJECT_OWNER"],
        "created_at": _timestamp(-1),
        "expires_at": _timestamp(4),
        "status": "REGISTERED",
    }


def _manifest(task: dict[str, Any], *, manifest_id: str, allowed_paths: list[str], tier: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "manifest_id": manifest_id,
        "role_id": task["role_id"],
        "actor_instance_id": task["actor_instance_id"],
        "task_id": task["task_id"],
        "parent_task_id": task["parent_task_id"],
        "scope": {
            "repository": task["repository"],
            "ref": task["ref"],
            "allowed_paths": allowed_paths,
            "case_context": None,
        },
        "inputs": task["inputs"],
        "expected_outputs": task["expected_outputs"],
        "allowed_tools": task["allowed_tools"],
        "requested_access_tiers": [tier],
        "requested_capabilities": task["permissions"],
        "forbidden_actions": task["forbidden_actions"],
        "budget": task["budget"],
        "timeout_seconds": task["timeout_seconds"],
        "max_retries": task["max_retries"],
        "stop_conditions": task["stop_conditions"],
        "escalation_route": task["escalation_route"],
        "issued_at": _timestamp(-1),
        "expires_at": _timestamp(3),
        "status": "PROPOSED",
    }


def validate_governance_documents(repository_root: Path | str) -> dict[str, Any]:
    """Validate only the fixed public-document allowlist and return hash evidence."""
    root = Path(repository_root).resolve()
    documents: list[dict[str, Any]] = []
    for relative_path, markers in DOCUMENT_RULES.items():
        path = (root / relative_path).resolve()
        if path.parent != root:
            raise ContractError("pilot document escaped repository root")
        try:
            data = path.read_bytes()
            text = data.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise ContractError(f"unable to read allowlisted document {relative_path}") from exc
        missing = [marker for marker in markers if marker not in text]
        if missing:
            raise ContractError(f"required marker missing from {relative_path}: {missing[0]}")
        documents.append({"path": relative_path, "sha256": _sha256(data), "markers": list(markers)})
    return {"pilot_id": PILOT_ID, "status": "PASS", "documents": documents}


def start_pilot(
    database_path: Path | str,
    evidence_path: Path | str,
    repository_root: Path | str,
    contract_root: Path | str,
) -> dict[str, Any]:
    """Run the bounded work package and pause at an auditable review checkpoint."""
    database = Path(database_path)
    evidence = Path(evidence_path)
    if database.exists() or evidence.exists():
        raise ContractError("pilot start requires new database and evidence paths")
    evidence.parent.mkdir(parents=True, exist_ok=True)
    output_ref = f"artifact://local/{evidence.name}"
    inputs = [f"repo://{path}" for path in DOCUMENT_RULES]
    implementation_task = _task(
        task_id=IMPLEMENTATION_TASK_ID,
        role_id="DOCUMENTATION_STATE_AGENT",
        actor_instance_id="O4-DOCUMENTATION-INSTANCE",
        parent_task_id=None,
        permissions=["propose_checkpoint"],
        objective="Validate the allowlisted public governance documents and preserve local evidence",
        inputs=inputs,
        outputs=[output_ref],
    )
    implementation_manifest = _manifest(
        implementation_task,
        manifest_id=IMPLEMENTATION_MANIFEST_ID,
        allowed_paths=list(DOCUMENT_RULES),
        tier="A2",
    )
    with OrchestratorKernel(database, contract_root) as kernel:
        kernel.register_task(implementation_task, gate_triggers=())
        kernel.register_manifest(implementation_manifest)
        kernel.validate_manifest(IMPLEMENTATION_MANIFEST_ID)
        kernel.set_kill_switch(
            "RUNNING", actor_id="HUMAN_PROJECT_OWNER", authority_reference=O4_AUTHORITY_REFERENCE
        )
        kernel.activate_manifest(IMPLEMENTATION_MANIFEST_ID)
        if not kernel.permission_decision(IMPLEMENTATION_MANIFEST_ID, "propose_checkpoint").allowed:
            raise ContractError("pilot permission was not granted")
        result = validate_governance_documents(repository_root)
        evidence.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        kernel.consume_budget(IMPLEMENTATION_MANIFEST_ID, tokens=0, tool_calls=6, cost_usd=0.0)
        kernel.record_response(
            IMPLEMENTATION_MANIFEST_ID,
            {
                "schema_version": 1,
                "response_id": "O4-RESPONSE-IMPLEMENTATION",
                "task_id": IMPLEMENTATION_TASK_ID,
                "parent_task_id": None,
                "role_id": "DOCUMENTATION_STATE_AGENT",
                "actor_instance_id": "O4-DOCUMENTATION-INSTANCE",
                "status": "PASS",
                "result_summary": "Allowlisted governance-document consistency check passed",
                "artifact_references": [output_ref],
                "changed_paths_or_state": [str(evidence.resolve())],
                "tests": [{"name": PILOT_ID, "outcome": "PASS", "evidence_reference": output_ref}],
                "evidence": [_sha256(evidence.read_bytes())],
                "authority_used": [O4_AUTHORITY_REFERENCE],
                "costs": {"tokens_used": 0, "tool_calls_used": 6, "cost_usd": 0.0},
                "unresolved_risks": [],
                "recommended_next_action": "independent acceptance after checkpoint recovery",
                "human_required": False,
                "created_at": _timestamp(0),
            },
        )
        review_task = _task(
            task_id=REVIEW_TASK_ID,
            role_id="INDEPENDENT_ACCEPTANCE_AGENT",
            actor_instance_id="O4-INDEPENDENT-REVIEW-INSTANCE",
            parent_task_id=IMPLEMENTATION_TASK_ID,
            permissions=["acceptance_review"],
            objective="Independently verify the O4 pilot evidence after recovery",
            inputs=[output_ref],
            outputs=["acceptance://o4-pilot"],
        )
        review_manifest = _manifest(
            review_task,
            manifest_id=REVIEW_MANIFEST_ID,
            allowed_paths=list(DOCUMENT_RULES),
            tier="A1",
        )
        kernel.register_task(review_task, gate_triggers=())
        kernel.register_manifest(review_manifest)
        kernel.validate_manifest(REVIEW_MANIFEST_ID)
        kernel.set_kill_switch(
            "PAUSED", actor_id="MASTER_PROJECT_ORCHESTRATOR", authority_reference="o4-pilot://review-boundary"
        )
        checkpoint_hash = kernel.create_checkpoint(START_CHECKPOINT_ID)
    return {
        "pilot_id": PILOT_ID,
        "state": "AWAITING_INDEPENDENT_REVIEW",
        "checkpoint_id": START_CHECKPOINT_ID,
        "checkpoint_hash": checkpoint_hash,
        "evidence_sha256": _sha256(evidence.read_bytes()),
        "costs": {"tokens_used": 0, "tool_calls_used": 6, "cost_usd": 0.0},
    }


def resume_pilot(
    database_path: Path | str,
    evidence_path: Path | str,
    repository_root: Path | str,
    contract_root: Path | str,
) -> dict[str, Any]:
    """Recover, independently verify, accept, checkpoint, and halt the pilot."""
    database = Path(database_path)
    evidence = Path(evidence_path)
    with OrchestratorKernel(database, contract_root) as kernel:
        recovered = kernel.recover_latest_checkpoint()
        if recovered["checkpoint_id"] != START_CHECKPOINT_ID:
            raise ContractError("pilot is not at the independent-review checkpoint")
        try:
            recorded = json.loads(evidence.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ContractError("pilot evidence is missing or invalid") from exc
        current = validate_governance_documents(repository_root)
        if recorded != current:
            raise ContractError("pilot evidence no longer matches the allowlisted documents")
        kernel.set_kill_switch(
            "RUNNING", actor_id="HUMAN_PROJECT_OWNER", authority_reference=O4_AUTHORITY_REFERENCE
        )
        kernel.activate_manifest(REVIEW_MANIFEST_ID)
        if not kernel.permission_decision(REVIEW_MANIFEST_ID, "acceptance_review").allowed:
            raise ContractError("independent-review permission was not granted")
        kernel.consume_budget(REVIEW_MANIFEST_ID, tokens=0, tool_calls=6, cost_usd=0.0)
        kernel.record_acceptance(
            IMPLEMENTATION_TASK_ID,
            REVIEW_MANIFEST_ID,
            "PASS",
            evidence_reference=_sha256(evidence.read_bytes()),
        )
        kernel.set_kill_switch(
            "HALTED", actor_id="MASTER_PROJECT_ORCHESTRATOR", authority_reference="o4-pilot://complete"
        )
        checkpoint_hash = kernel.create_checkpoint(FINAL_CHECKPOINT_ID)
        kernel.verify_audit_chain()
    inspection = OrchestratorKernel.inspect_read_only(database)
    return {
        "pilot_id": PILOT_ID,
        "state": "COMPLETED",
        "checkpoint_id": FINAL_CHECKPOINT_ID,
        "checkpoint_hash": checkpoint_hash,
        "audit_integrity": inspection["audit_integrity"],
        "kill_switch": inspection["kill_switch"],
        "costs": {"tokens_used": 0, "tool_calls_used": 12, "cost_usd": 0.0},
    }
