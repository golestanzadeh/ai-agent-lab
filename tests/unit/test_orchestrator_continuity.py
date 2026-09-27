from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from agent_lab.orchestrator_kernel import ContractError, OrchestratorKernel, PermissionDenied, StateTransitionError


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "contracts" / "orchestrator" / "v1"


def timestamp(hours: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def package_template(package_id: str, sequence: int, *, depends_on: tuple[str, ...] = ()) -> dict:
    suffix = package_id.rsplit("-", 1)[-1]
    return {
        "package_id": package_id,
        "sequence": sequence,
        "depends_on": list(depends_on),
        "objective": f"Execute bounded synthetic package {suffix}",
        "role_id": "IMPLEMENTATION_AGENT",
        "actor_instance_id": f"AGI-CONT-{suffix}",
        "inputs": [f"synthetic://continuity/{suffix}"],
        "expected_outputs": [f"artifact://local/continuity/{suffix}"],
        "allowed_tools": ["synthetic_local_dispatch", "pytest"],
        "permissions": ["write_bounded_branch", "run_tests", "report_evidence"],
        "forbidden_actions": ["external_transfer", "production", "protected_main", "real_data"],
        "budget": {"token_limit": 1000, "tool_call_limit": 10, "cost_limit_usd": 1.0},
        "timeout_seconds": 600,
        "max_retries": 1,
        "acceptance_criteria": [f"synthetic package {suffix} independently accepted"],
        "stop_conditions": ["authority ambiguity", "budget exhausted"],
        "escalation_route": ["MASTER_PROJECT_ORCHESTRATOR", "HUMAN_PROJECT_OWNER"],
    }


def authority() -> dict:
    first = package_template("PKG-CONT-001", 1)
    second = package_template("PKG-CONT-002", 2, depends_on=("PKG-CONT-001",))
    return {
        "schema_version": 1,
        "authority_id": "AUTH-CONT-001",
        "milestone_id": "ORCH-CONT-SYNTHETIC-PROOF",
        "owner_approval_reference": "ORCH-CONT-20260927-001",
        "repository": "golestanzadeh/ai-agent-lab",
        "ref": "d021-agent-case-provisioning",
        "package_templates": [first, second],
        "max_generated_packages": 2,
        "max_replans": 1,
        "dispatch_adapters": ["SYNTHETIC_LOCAL_V1"],
        "forbidden_actions": ["external_transfer", "production", "protected_main", "real_data"],
        "created_at": timestamp(-1),
        "expires_at": timestamp(4),
        "status": "ACTIVE",
    }


def task_payload(template: dict, task_id: str) -> dict:
    return {
        "schema_version": 1,
        "task_id": task_id,
        "parent_task_id": None,
        "objective": template["objective"],
        "role_id": template["role_id"],
        "actor_instance_id": template["actor_instance_id"],
        "repository": "golestanzadeh/ai-agent-lab",
        "ref": "d021-agent-case-provisioning",
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
        "created_at": timestamp(-1),
        "expires_at": timestamp(3),
        "status": "REGISTERED",
    }


@pytest.fixture
def kernel(tmp_path: Path):
    with OrchestratorKernel(tmp_path / "kernel.sqlite3", CONTRACT_ROOT) as value:
        yield value


def test_authority_bounds_registration_and_ready_selection(kernel: OrchestratorKernel):
    contract = authority()
    kernel.register_milestone_authority(contract)
    first = task_payload(contract["package_templates"][0], "TASK-CONT-001")
    assert kernel.register_authorized_package(contract["authority_id"], "PKG-CONT-001", first) == "TASK-CONT-001"
    ready = kernel.select_ready_package(contract["authority_id"])
    assert ready is not None
    assert (ready["package_id"], ready["sequence"], ready["task_id"]) == ("PKG-CONT-001", 1, "TASK-CONT-001")

    amplified = deepcopy(task_payload(contract["package_templates"][1], "TASK-CONT-002"))
    amplified["permissions"].append("external_transfer")
    with pytest.raises(PermissionDenied, match="exceeds milestone authority"):
        kernel.register_authorized_package(contract["authority_id"], "PKG-CONT-002", amplified)


def test_queue_exhaustion_replan_is_dependency_ordered_and_bounded(kernel: OrchestratorKernel):
    contract = authority()
    kernel.register_milestone_authority(contract)
    first = task_payload(contract["package_templates"][0], "TASK-CONT-001")
    kernel.register_authorized_package(contract["authority_id"], "PKG-CONT-001", first)
    second = task_payload(contract["package_templates"][1], "TASK-CONT-002")
    with pytest.raises(StateTransitionError, match="not exhausted"):
        kernel.replan_authorized_package(contract["authority_id"], "PKG-CONT-002", second)

    with kernel._connection:
        kernel._connection.execute("UPDATE tasks SET status='COMPLETED' WHERE task_id='TASK-CONT-001'")
    assert kernel.select_ready_package(contract["authority_id"]) is None
    assert kernel.replan_authorized_package(contract["authority_id"], "PKG-CONT-002", second) == "TASK-CONT-002"
    ready = kernel.select_ready_package(contract["authority_id"])
    assert ready is not None and ready["package_id"] == "PKG-CONT-002"
    with kernel._connection:
        kernel._connection.execute("UPDATE tasks SET status='COMPLETED' WHERE task_id='TASK-CONT-002'")
    with pytest.raises(PermissionDenied, match="replan limit|generated-package limit"):
        kernel.replan_authorized_package(contract["authority_id"], "PKG-CONT-002", second)


def test_stop_diagnostic_is_durable_and_checkpoint_bound(kernel: OrchestratorKernel):
    payload = {
        "diagnostic_id": "STOP-CONT-001",
        "category": "MATERIAL_FAILURE",
        "summary": "Synthetic terminal failure",
        "impact": "No external impact",
        "automated_recovery": "Retry exhausted",
        "required_next_action": "Inspect synthetic evidence",
        "continuation_point": "checkpoint://continuity/1",
        "created_at": timestamp(0),
    }
    assert kernel.record_stop_diagnostic(payload) == payload["diagnostic_id"]
    kernel.create_checkpoint("CHECKPOINT-CONT-001")
    recovered = kernel.recover_latest_checkpoint()
    diagnostics = recovered["snapshot"]["stop_diagnostics"]
    assert json.loads(diagnostics[0]["payload_json"]) == payload
    with pytest.raises(ContractError, match="token pauses"):
        kernel.record_stop_diagnostic({**payload, "diagnostic_id": "STOP-CONT-002", "category": "TOKEN_PAUSED"})
