from __future__ import annotations

import json
import sqlite3
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from agent_lab.orchestrator_kernel import (
    ContractError,
    IntegrityError,
    OrchestratorKernel,
    PermissionDenied,
    StateTransitionError,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "contracts" / "orchestrator" / "v1"


def timestamp(hours: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def task(
    *,
    task_id: str = "TASK-TEST-001",
    role_id: str = "IMPLEMENTATION_AGENT",
    actor_instance_id: str = "AGI-TEST-001",
    parent_task_id: str | None = None,
    permissions: list[str] | None = None,
    case_context: dict | None = None,
) -> dict:
    return {
        "schema_version": 1,
        "task_id": task_id,
        "parent_task_id": parent_task_id,
        "objective": "Execute a synthetic bounded task",
        "role_id": role_id,
        "actor_instance_id": actor_instance_id,
        "repository": "golestanzadeh/ai-agent-lab",
        "ref": "d021-agent-case-provisioning",
        "case_context": case_context,
        "inputs": ["artifact://input/1"],
        "expected_outputs": ["artifact://output/1"],
        "allowed_tools": ["pytest"],
        "permissions": permissions or ["write_bounded_branch", "run_tests"],
        "forbidden_actions": ["merge", "external_transfer"],
        "budget": {"token_limit": 1000, "tool_call_limit": 10, "cost_limit_usd": 2.0},
        "timeout_seconds": 600,
        "max_retries": 1,
        "acceptance_criteria": ["synthetic evidence exists"],
        "stop_conditions": ["authority ambiguity"],
        "escalation_route": ["MASTER_PROJECT_ORCHESTRATOR", "HUMAN_PROJECT_OWNER"],
        "created_at": timestamp(-1),
        "expires_at": timestamp(4),
        "status": "REGISTERED",
    }


def manifest(task_payload: dict, *, manifest_id: str = "MAN-TEST-001", tiers: list[str] | None = None) -> dict:
    return {
        "schema_version": 1,
        "manifest_id": manifest_id,
        "role_id": task_payload["role_id"],
        "actor_instance_id": task_payload["actor_instance_id"],
        "task_id": task_payload["task_id"],
        "parent_task_id": task_payload["parent_task_id"],
        "scope": {
            "repository": task_payload["repository"],
            "ref": task_payload["ref"],
            "allowed_paths": ["src/agent_lab/"],
            "case_context": task_payload["case_context"],
        },
        "inputs": list(task_payload["inputs"]),
        "expected_outputs": list(task_payload["expected_outputs"]),
        "allowed_tools": list(task_payload["allowed_tools"]),
        "requested_access_tiers": tiers or ["A2"],
        "requested_capabilities": list(task_payload["permissions"]),
        "forbidden_actions": list(task_payload["forbidden_actions"]),
        "budget": dict(task_payload["budget"]),
        "timeout_seconds": task_payload["timeout_seconds"],
        "max_retries": task_payload["max_retries"],
        "stop_conditions": list(task_payload["stop_conditions"]),
        "escalation_route": list(task_payload["escalation_route"]),
        "issued_at": timestamp(-1),
        "expires_at": timestamp(3),
        "status": "PROPOSED",
    }


def response(task_payload: dict, *, status: str = "PASS", human_required: bool = False) -> dict:
    return {
        "schema_version": 1,
        "response_id": "RESP-TEST-001",
        "task_id": task_payload["task_id"],
        "parent_task_id": task_payload["parent_task_id"],
        "role_id": task_payload["role_id"],
        "actor_instance_id": task_payload["actor_instance_id"],
        "status": status,
        "result_summary": "Synthetic task result",
        "artifact_references": ["artifact://output/1"],
        "changed_paths_or_state": ["src/agent_lab/example.py"],
        "tests": [{"name": "synthetic", "outcome": "PASS", "evidence_reference": "test://1"}],
        "evidence": ["evidence://1"],
        "authority_used": ["task://" + task_payload["task_id"]],
        "costs": {"tokens_used": 100, "tool_calls_used": 2, "cost_usd": 0.25},
        "unresolved_risks": [],
        "recommended_next_action": "independent acceptance",
        "human_required": human_required,
        "created_at": timestamp(0),
    }


@pytest.fixture
def kernel(tmp_path):
    with OrchestratorKernel(tmp_path / "kernel.sqlite3", CONTRACT_ROOT) as value:
        yield value


def prepare_active(kernel: OrchestratorKernel, task_payload: dict | None = None):
    task_payload = task_payload or task()
    manifest_payload = manifest(task_payload)
    kernel.register_task(task_payload, gate_triggers=())
    kernel.register_manifest(manifest_payload)
    kernel.validate_manifest(manifest_payload["manifest_id"])
    kernel.set_kill_switch("RUNNING", actor_id="HUMAN_PROJECT_OWNER", authority_reference="synthetic-test-authority")
    kernel.activate_manifest(manifest_payload["manifest_id"])
    return task_payload, manifest_payload


def test_kernel_starts_halted_and_persists(tmp_path):
    database = tmp_path / "kernel.sqlite3"
    with OrchestratorKernel(database, CONTRACT_ROOT) as first:
        assert first.kill_switch_state() == "HALTED"
        first.verify_audit_chain()
    with OrchestratorKernel(database, CONTRACT_ROOT) as reopened:
        assert reopened.kill_switch_state() == "HALTED"
        reopened.verify_audit_chain()


def test_manifest_validation_does_not_activate_agent(kernel):
    task_payload = task()
    manifest_payload = manifest(task_payload)
    kernel.register_task(task_payload, gate_triggers=())
    kernel.register_manifest(manifest_payload)
    assert kernel.validate_manifest(manifest_payload["manifest_id"]).outcome == "VALIDATED"
    with pytest.raises(PermissionDenied, match="kill switch"):
        kernel.activate_manifest(manifest_payload["manifest_id"])


def test_only_human_can_set_kill_switch_running(kernel):
    with pytest.raises(PermissionDenied, match="only Human"):
        kernel.set_kill_switch("RUNNING", actor_id="MASTER_PROJECT_ORCHESTRATOR", authority_reference="test")


def test_registered_human_gate_blocks_until_exact_human_decision(kernel):
    task_payload = task(
        role_id="ARCHITECTURE_AGENT",
        actor_instance_id="AGI-ARCH-001",
        permissions=["design_contract"],
    )
    manifest_payload = manifest(task_payload, tiers=["A1"])
    kernel.register_task(task_payload, gate_triggers=["accepted_architecture_change"])
    with pytest.raises(PermissionDenied, match="Human Gate"):
        kernel.register_manifest(manifest_payload)
    with pytest.raises(PermissionDenied, match="only Human"):
        kernel.record_human_gate_decision(
            task_payload["task_id"],
            "accepted_architecture_change",
            "APPROVED",
            actor_id="MASTER_PROJECT_ORCHESTRATOR",
            authority_reference="invalid",
        )
    kernel.record_human_gate_decision(
        task_payload["task_id"],
        "accepted_architecture_change",
        "APPROVED",
        actor_id="HUMAN_PROJECT_OWNER",
        authority_reference="human-approval://synthetic/1",
    )
    assert kernel.register_manifest(manifest_payload) == manifest_payload["manifest_id"]


def test_rejected_human_gate_is_terminal_for_task(kernel):
    task_payload = task(
        role_id="ARCHITECTURE_AGENT",
        actor_instance_id="AGI-ARCH-001",
        permissions=["design_contract"],
    )
    kernel.register_task(task_payload, gate_triggers=["accepted_architecture_change"])
    kernel.record_human_gate_decision(
        task_payload["task_id"],
        "accepted_architecture_change",
        "REJECTED",
        actor_id="HUMAN_PROJECT_OWNER",
        authority_reference="human-rejection://synthetic/1",
    )
    with pytest.raises(PermissionDenied, match="terminal state"):
        kernel.register_manifest(manifest(task_payload, tiers=["A1"]))


def test_active_manifest_allows_only_declared_capability(kernel):
    _, manifest_payload = prepare_active(kernel)
    assert kernel.permission_decision(manifest_payload["manifest_id"], "run_tests").allowed is True
    assert kernel.permission_decision(manifest_payload["manifest_id"], "write_tests").outcome == "DENY"
    assert kernel.permission_decision(manifest_payload["manifest_id"], "external_transfer").outcome == "HUMAN_REQUIRED"


def test_manifest_cannot_request_a6(kernel):
    task_payload = task()
    manifest_payload = manifest(task_payload, tiers=["A6"])
    kernel.register_task(task_payload, gate_triggers=())
    with pytest.raises(PermissionDenied, match="denied access tier"):
        kernel.register_manifest(manifest_payload)


def test_case_permission_requires_exact_case_context(kernel):
    context = {"case_id": "CASE-TEST", "tax_year": 2024, "run_id": "RUN-TEST"}
    task_payload = task(
        role_id="EVIDENCE_AGENT",
        actor_instance_id="AGI-EVIDENCE-001",
        permissions=["read_case_packet"],
        case_context=context,
    )
    manifest_payload = manifest(task_payload, tiers=["A3"])
    kernel.register_task(task_payload, gate_triggers=())
    kernel.register_manifest(manifest_payload)
    kernel.validate_manifest(manifest_payload["manifest_id"])
    kernel.set_kill_switch("RUNNING", actor_id="HUMAN_PROJECT_OWNER", authority_reference="synthetic-test-authority")
    kernel.activate_manifest(manifest_payload["manifest_id"])
    assert kernel.permission_decision(
        manifest_payload["manifest_id"], "read_case_packet", **context
    ).allowed is True
    assert kernel.permission_decision(
        manifest_payload["manifest_id"], "read_case_packet", case_id="OTHER", tax_year=2024, run_id="RUN-TEST"
    ).outcome == "DENY"


def test_case_tier_without_context_fails_closed(kernel):
    task_payload = task(
        role_id="EVIDENCE_AGENT",
        actor_instance_id="AGI-EVIDENCE-001",
        permissions=["read_case_packet"],
    )
    kernel.register_task(task_payload, gate_triggers=())
    with pytest.raises(PermissionDenied, match="case tiers require"):
        kernel.register_manifest(manifest(task_payload, tiers=["A3"]))


def test_dependency_cycle_and_unmet_dependency_are_blocked(kernel):
    first = task(task_id="TASK-DEP-001", actor_instance_id="AGI-DEP-001")
    second = task(task_id="TASK-DEP-002", actor_instance_id="AGI-DEP-002")
    kernel.register_task(first, gate_triggers=())
    kernel.register_task(second, gate_triggers=(), depends_on=[first["task_id"]])
    with pytest.raises(ContractError, match="cycle"):
        kernel.add_dependency(first["task_id"], second["task_id"])
    second_manifest = manifest(second, manifest_id="MAN-DEP-002")
    kernel.register_manifest(second_manifest)
    kernel.validate_manifest(second_manifest["manifest_id"])
    kernel.set_kill_switch("RUNNING", actor_id="HUMAN_PROJECT_OWNER", authority_reference="synthetic-test-authority")
    with pytest.raises(PermissionDenied, match="dependencies"):
        kernel.activate_manifest(second_manifest["manifest_id"])


def test_response_preserves_lineage_and_completes_task(kernel):
    task_payload, manifest_payload = prepare_active(kernel)
    kernel.consume_budget(manifest_payload["manifest_id"], tokens=100, tool_calls=2, cost_usd=0.25)
    assert kernel.record_response(manifest_payload["manifest_id"], response(task_payload)) == "RESP-TEST-001"
    target = kernel._connection.execute(
        "SELECT status FROM tasks WHERE task_id=?", (task_payload["task_id"],)
    ).fetchone()
    assert target["status"] == "AWAITING_ACCEPTANCE"
    reviewer_task = task(
        task_id="TASK-REVIEW-001",
        role_id="INDEPENDENT_ACCEPTANCE_AGENT",
        actor_instance_id="AGI-REVIEW-001",
        parent_task_id=task_payload["task_id"],
        permissions=["acceptance_review"],
    )
    reviewer_manifest = manifest(reviewer_task, manifest_id="MAN-REVIEW-001", tiers=["A1"])
    kernel.register_task(reviewer_task, gate_triggers=())
    kernel.register_manifest(reviewer_manifest)
    kernel.validate_manifest(reviewer_manifest["manifest_id"])
    kernel.activate_manifest(reviewer_manifest["manifest_id"])
    kernel.record_acceptance(
        task_payload["task_id"],
        reviewer_manifest["manifest_id"],
        "PASS",
        evidence_reference="acceptance://synthetic/1",
    )
    accepted = kernel._connection.execute(
        "SELECT status FROM tasks WHERE task_id=?", (task_payload["task_id"],)
    ).fetchone()
    assert accepted["status"] == "COMPLETED"
    with pytest.raises(StateTransitionError):
        kernel.record_response(manifest_payload["manifest_id"], response(task_payload))


def test_human_required_response_requires_flag(kernel):
    task_payload, manifest_payload = prepare_active(kernel)
    with pytest.raises(ContractError, match="human_required"):
        kernel.record_response(manifest_payload["manifest_id"], response(task_payload, status="HUMAN_REQUIRED"))


def test_response_cost_must_match_durable_usage(kernel):
    task_payload, manifest_payload = prepare_active(kernel)
    with pytest.raises(ContractError, match="durable budget usage"):
        kernel.record_response(manifest_payload["manifest_id"], response(task_payload))


def test_pass_response_cannot_hide_failed_test(kernel):
    task_payload, manifest_payload = prepare_active(kernel)
    payload = response(task_payload)
    payload["tests"][0]["outcome"] = "FAIL"
    with pytest.raises(ContractError, match="failed test evidence"):
        kernel.record_response(manifest_payload["manifest_id"], payload)


def test_budget_exhaustion_blocks_without_recording_overspend(kernel):
    _, manifest_payload = prepare_active(kernel)
    decision = kernel.consume_budget(manifest_payload["manifest_id"], tokens=1001)
    assert decision.outcome == "BLOCKED"
    row = kernel._connection.execute(
        "SELECT tokens_used FROM budget_usage WHERE manifest_id=?", (manifest_payload["manifest_id"],)
    ).fetchone()
    assert row["tokens_used"] == 0


def test_retry_requires_new_identity_and_retryable_failure(kernel):
    _, manifest_payload = prepare_active(kernel)
    kernel.transition_manifest(manifest_payload["manifest_id"], "FAILED", actor_id="TEST", reason="synthetic failure")
    assert kernel.authorize_retry(manifest_payload["manifest_id"], "transient_network", "ATTEMPT-002").allowed is True
    with pytest.raises(ContractError, match="already exists"):
        kernel.authorize_retry(manifest_payload["manifest_id"], "transient_network", "ATTEMPT-002")


def test_non_retryable_authority_failure_requires_human(kernel):
    _, manifest_payload = prepare_active(kernel)
    kernel.transition_manifest(manifest_payload["manifest_id"], "FAILED", actor_id="TEST", reason="synthetic failure")
    assert kernel.authorize_retry(manifest_payload["manifest_id"], "authority_failure", "ATTEMPT-002").outcome == "HUMAN_REQUIRED"


def test_halt_revokes_active_manifests_and_preserves_audit(kernel):
    _, manifest_payload = prepare_active(kernel)
    kernel.set_kill_switch("HALTED", actor_id="MASTER_PROJECT_ORCHESTRATOR", authority_reference="incident-test")
    assert kernel.permission_decision(manifest_payload["manifest_id"], "run_tests").outcome == "DENY"
    kernel.verify_audit_chain()


def test_checkpoint_survives_reopen(tmp_path):
    database = tmp_path / "kernel.sqlite3"
    with OrchestratorKernel(database, CONTRACT_ROOT) as kernel:
        kernel.register_task(task(), gate_triggers=())
        expected_hash = kernel.create_checkpoint("CHECKPOINT-001")
    with OrchestratorKernel(database, CONTRACT_ROOT) as reopened:
        recovered = reopened.recover_latest_checkpoint()
        assert recovered["checkpoint_id"] == "CHECKPOINT-001"
        assert recovered["snapshot_hash"] == expected_hash


def test_audit_tampering_is_detected(tmp_path):
    database = tmp_path / "kernel.sqlite3"
    with OrchestratorKernel(database, CONTRACT_ROOT) as kernel:
        kernel.register_task(task(), gate_triggers=())
    with sqlite3.connect(database) as connection:
        connection.execute("UPDATE audit_events SET payload_json='{}' WHERE event_id=1")
    with OrchestratorKernel(database, CONTRACT_ROOT) as reopened:
        with pytest.raises(IntegrityError, match="audit chain failed"):
            reopened.verify_audit_chain()


def bridge_request(risk_class: str = "low") -> dict:
    return {
        "protocol_version": 1,
        "task_id": "TASK-TEST-001",
        "sender": "work",
        "recipient": "codex",
        "repository": "golestanzadeh/ai-agent-lab",
        "ref": "d021-agent-case-provisioning",
        "base_commit": "0123456789abcdef",
        "status": "REQUEST",
        "task": "Execute a synthetic bounded task",
        "acceptance": ["synthetic evidence exists"],
        "allowed_scope": ["src/agent_lab/"],
        "forbidden_actions": ["merge", "external_transfer"],
        "risk_class": risk_class,
    }


def test_agent_bridge_binding_registers_exact_low_risk_task(kernel):
    decision = kernel.bind_agent_bridge_request(bridge_request(), task())
    assert decision.outcome == "REGISTERED"
    row = kernel._connection.execute("SELECT base_commit FROM bridge_bindings").fetchone()
    assert row["base_commit"] == "0123456789abcdef"


def test_agent_bridge_human_gate_does_not_register_task(kernel):
    decision = kernel.bind_agent_bridge_request(bridge_request("architecture"), task())
    assert decision.outcome == "HUMAN_REQUIRED"
    assert kernel._connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0


def test_bridge_scope_cannot_be_expanded_by_manifest(kernel):
    task_payload = task()
    kernel.bind_agent_bridge_request(bridge_request(), task_payload)
    manifest_payload = manifest(task_payload)
    manifest_payload["scope"]["allowed_paths"] = ["src/agent_lab/", "secrets/"]
    with pytest.raises(ContractError, match="Agent Bridge allowed scope"):
        kernel.register_manifest(manifest_payload)


def test_read_only_inspection_reports_integrity_without_mutation(tmp_path):
    database = tmp_path / "kernel.sqlite3"
    with OrchestratorKernel(database, CONTRACT_ROOT) as kernel:
        kernel.register_task(task(), gate_triggers=())
        kernel.create_checkpoint("CHECKPOINT-001")
    before = database.stat().st_mtime_ns
    result = OrchestratorKernel.inspect_read_only(database)
    assert result["audit_integrity"] == "PASS"
    assert result["counts"]["tasks"] == 1
    assert database.stat().st_mtime_ns == before


def test_unknown_contract_version_fails_closed(tmp_path):
    contract_copy = tmp_path / "contracts"
    contract_copy.mkdir()
    for source in CONTRACT_ROOT.iterdir():
        if source.is_file():
            (contract_copy / source.name).write_bytes(source.read_bytes())
    roles = json.loads((contract_copy / "roles.json").read_text(encoding="utf-8"))
    roles["schema_version"] = 99
    (contract_copy / "roles.json").write_text(json.dumps(roles), encoding="utf-8")
    with pytest.raises(ContractError, match="unsupported roles.json version"):
        OrchestratorKernel(tmp_path / "kernel.sqlite3", contract_copy)


def test_same_version_contract_tampering_fails_closed(tmp_path):
    contract_copy = tmp_path / "contracts"
    contract_copy.mkdir()
    for source in CONTRACT_ROOT.iterdir():
        if source.is_file():
            (contract_copy / source.name).write_bytes(source.read_bytes())
    roles = json.loads((contract_copy / "roles.json").read_text(encoding="utf-8"))
    roles["roles"][0]["can_block"] = False
    (contract_copy / "roles.json").write_text(json.dumps(roles), encoding="utf-8")
    with pytest.raises(ContractError, match="does not match accepted O2 commit"):
        OrchestratorKernel(tmp_path / "kernel.sqlite3", contract_copy)
