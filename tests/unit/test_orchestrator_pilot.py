from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_lab.orchestrator_kernel import ContractError, OrchestratorKernel
from agent_lab.orchestrator_pilot import (
    FINAL_CHECKPOINT_ID,
    START_CHECKPOINT_ID,
    _manifest,
    _task,
    resume_pilot,
    start_pilot,
    validate_governance_documents,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "contracts" / "orchestrator" / "v1"


def test_pilot_stops_and_resumes_across_process_boundary(tmp_path):
    database = tmp_path / "pilot.sqlite3"
    evidence = tmp_path / "evidence.json"
    started = start_pilot(database, evidence, ROOT, CONTRACT_ROOT)
    assert started["state"] == "AWAITING_INDEPENDENT_REVIEW"
    assert started["checkpoint_id"] == START_CHECKPOINT_ID
    assert started["costs"] == {"tokens_used": 0, "tool_calls_used": 6, "cost_usd": 0.0}
    paused = OrchestratorKernel.inspect_read_only(database)
    assert paused["kill_switch"] == "PAUSED"
    completed = resume_pilot(database, evidence, ROOT, CONTRACT_ROOT)
    assert completed["state"] == "COMPLETED"
    assert completed["checkpoint_id"] == FINAL_CHECKPOINT_ID
    assert completed["audit_integrity"] == "PASS"
    assert completed["kill_switch"] == "HALTED"
    inspected = OrchestratorKernel.inspect_read_only(database)
    assert inspected["counts"]["acceptance_records"] == 1
    assert inspected["counts"]["checkpoints"] == 2


def test_independent_review_fails_closed_when_evidence_changes(tmp_path):
    database = tmp_path / "pilot.sqlite3"
    evidence = tmp_path / "evidence.json"
    start_pilot(database, evidence, ROOT, CONTRACT_ROOT)
    payload = json.loads(evidence.read_text(encoding="utf-8"))
    payload["status"] = "ALTERED"
    evidence.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ContractError, match="no longer matches"):
        resume_pilot(database, evidence, ROOT, CONTRACT_ROOT)
    assert OrchestratorKernel.inspect_read_only(database)["kill_switch"] == "PAUSED"


def test_document_validator_rejects_missing_required_marker(tmp_path):
    for relative_path in ("CONSTITUTION.md", "PROJECT_CHECKPOINT.md", "AGENTS.md", "CURRENT_STATE.md", "ROADMAP.md"):
        (tmp_path / relative_path).write_text("invalid", encoding="utf-8")
    with pytest.raises(ContractError, match="required marker missing"):
        validate_governance_documents(tmp_path)


def test_pilot_start_is_not_replayable(tmp_path):
    database = tmp_path / "pilot.sqlite3"
    evidence = tmp_path / "evidence.json"
    start_pilot(database, evidence, ROOT, CONTRACT_ROOT)
    with pytest.raises(ContractError, match="requires new"):
        start_pilot(database, evidence, ROOT, CONTRACT_ROOT)


def test_kernel_retry_remains_bounded_and_audited(tmp_path):
    # O3's retry contract is exercised as a control-path acceptance check; the
    # pilot itself succeeds without an induced failure.
    database = tmp_path / "retry.sqlite3"
    with OrchestratorKernel(database, CONTRACT_ROOT) as kernel:
        task_payload = _task(
            task_id="O4-RETRY-TASK",
            role_id="IMPLEMENTATION_AGENT",
            actor_instance_id="O4-RETRY-INSTANCE",
            parent_task_id=None,
            permissions=["run_tests"],
            objective="Exercise one bounded retry",
            inputs=["artifact://synthetic/input"],
            outputs=["artifact://synthetic/output"],
        )
        manifest_payload = _manifest(
            task_payload,
            manifest_id="O4-RETRY-MANIFEST",
            allowed_paths=["tests/unit/"],
            tier="A1",
        )
        kernel.register_task(task_payload, gate_triggers=())
        kernel.register_manifest(manifest_payload)
        kernel.validate_manifest(manifest_payload["manifest_id"])
        kernel.set_kill_switch("RUNNING", actor_id="HUMAN_PROJECT_OWNER", authority_reference="o4-test")
        kernel.activate_manifest(manifest_payload["manifest_id"])
        kernel.transition_manifest(manifest_payload["manifest_id"], "FAILED", actor_id="O4-TEST", reason="retriable_process_error")
        assert kernel.authorize_retry(manifest_payload["manifest_id"], "retriable_process_error", "O4-RETRY-1").allowed
        assert kernel.authorize_retry(manifest_payload["manifest_id"], "retriable_process_error", "O4-RETRY-2").outcome == "BLOCKED"
        kernel.verify_audit_chain()
