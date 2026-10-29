"""Reproduce the frozen Kernel boundary; never use credentials or real cases."""
import pytest

from agent_lab.orchestrator_kernel import OrchestratorKernel
from test_orchestrator_kernel import CONTRACT_ROOT, task, manifest


@pytest.mark.parametrize("role,capabilities,tiers", [
    ("IMPLEMENTATION_AGENT", ["report_evidence"], ["A1"]),
    ("EVIDENCE_AGENT", ["read_case_packet", "write_derived_case_artifact"], ["A3", "A4"]),
])
@pytest.mark.parametrize("capability", ["external_transfer", "gemini_extraction"])
def test_tool_name_and_candidate_role_cannot_grant_provider_authority(
    tmp_path, role, capabilities, tiers, capability,
):
    context = {"case_id": "TEST-UI03-A", "tax_year": 2025, "run_id": "RUN-UI03-TEST"}
    payload = task(role_id=role, permissions=capabilities, case_context=context)
    payload["allowed_tools"] = ["gemini_document_extraction"]
    proposed = manifest(payload, tiers=tiers)
    with OrchestratorKernel(tmp_path / "kernel.sqlite", CONTRACT_ROOT) as kernel:
        kernel.register_task(payload, gate_triggers=())
        kernel.register_manifest(proposed)
        kernel.validate_manifest(proposed["manifest_id"])
        # Explicitly synthetic authority in a disposable test database only.
        kernel.set_kill_switch("RUNNING", actor_id="HUMAN_PROJECT_OWNER",
                               authority_reference="synthetic-ui03-negative-test")
        kernel.activate_manifest(proposed["manifest_id"])
        decision = kernel.permission_decision(proposed["manifest_id"], capability, **context)
        assert not decision.allowed
        assert decision.outcome in {"DENY", "HUMAN_REQUIRED"}
        kernel.verify_audit_chain()
