from dataclasses import replace

import pytest

from agent_lab.ui_app import _populate_synthetic_state, build_synthetic_registry
from agent_lab.ui_state_contract import select_synthetic_workspace
from agent_lab.ui_workflow_contract import SAFE_DIAGNOSTIC_CODES, STAGE_CODES, StageStatus, UIWorkflowError, build_synthetic_ui_workflow


def _workflow(case_id: str = "SYNTH-CASE-001", year: int = 2024):
    registry = build_synthetic_registry()
    workspace = _populate_synthetic_state(select_synthetic_workspace(registry, case_id=case_id, tax_year=year))
    return build_synthetic_ui_workflow(workspace)


def test_workflow_is_exact_ordered_and_case_bound() -> None:
    workflow = _workflow()
    assert workflow.case_id == "SYNTH-CASE-001"
    assert tuple(stage.code for stage in workflow.stages) == STAGE_CODES
    assert workflow.stages[3].status is StageStatus.ACTIVE
    assert all(stage.status is StageStatus.COMPLETE for stage in workflow.stages[:3])
    assert all(stage.status is StageStatus.LOCKED for stage in workflow.stages[4:])


def test_processing_case_exposes_processing_as_only_boundary() -> None:
    workflow = _workflow("SYNTH-CASE-002", 2025)
    boundaries = [stage for stage in workflow.stages if stage.status in (StageStatus.ACTIVE, StageStatus.BLOCKED)]
    assert [(stage.code, stage.status) for stage in boundaries] == [("PROCESSING", StageStatus.ACTIVE)]


def test_only_allowlisted_privacy_safe_diagnostics_are_exposed() -> None:
    workflow = _workflow()
    assert workflow.version == "2"
    assert workflow.diagnostic_codes == SAFE_DIAGNOSTIC_CODES
    assert "LOCAL_E10_2024_XSD_AND_RULE_SUBSET_PASS" in workflow.diagnostic_codes
    assert "OFFICIAL_ERIC_ENGINE_NOT_EXECUTED" in workflow.diagnostic_codes
    assert "OFFICIAL_ERIC_MAPPING_NOT_RECOVERED" not in workflow.diagnostic_codes
    with pytest.raises(UIWorkflowError, match="allowlisted"):
        replace(workflow, diagnostic_codes=("private document text",))


def test_controls_submission_real_data_and_network_cannot_be_forged() -> None:
    workflow = _workflow()
    for change in ({"control_actions_enabled": True}, {"submission_enabled": True}, {"contains_private_content": True}, {"data_classification": "REAL"}, {"network_calls": ("https://example.invalid",)}):
        with pytest.raises(UIWorkflowError):
            replace(workflow, **change)


def test_stage_order_and_transition_shape_fail_closed() -> None:
    workflow = _workflow()
    with pytest.raises(UIWorkflowError, match="ordered"):
        replace(workflow, stages=tuple(reversed(workflow.stages)))
    malformed = tuple(replace(stage, status=StageStatus.ACTIVE) if stage.code == "CHIEF_REVIEW" else stage for stage in workflow.stages)
    with pytest.raises(UIWorkflowError, match="exactly one"):
        replace(workflow, stages=malformed)
