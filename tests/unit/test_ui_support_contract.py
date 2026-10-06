from dataclasses import replace

import pytest

from agent_lab.ui_app import _populate_synthetic_state, build_synthetic_registry
from agent_lab.ui_state_contract import select_synthetic_workspace
from agent_lab.ui_support_contract import SAFE_SUPPORT_CODES, UISupportError, build_synthetic_ui_support


def _support(case_id: str = "SYNTH-CASE-001", year: int = 2024):
    workspace = _populate_synthetic_state(
        select_synthetic_workspace(build_synthetic_registry(), case_id=case_id, tax_year=year)
    )
    return build_synthetic_ui_support(workspace)


def test_support_is_exact_case_run_bound_and_privacy_safe() -> None:
    support = _support()
    assert support.case_id == "SYNTH-CASE-001"
    assert support.run_id == "SYNTH-RUN-001"
    assert support.status_codes == SAFE_SUPPORT_CODES
    assert support.version == "1"


def test_support_controls_receipt_and_network_fail_closed() -> None:
    support = _support()
    for change in (
        {"controls_enabled": True},
        {"receipt_present": True},
        {"network_calls": ("https://example.invalid",)},
        {"status_codes": ("arbitrary private text",)},
        {"data_classification": "REAL"},
    ):
        with pytest.raises(UISupportError):
            replace(support, **change)


def test_support_scope_changes_with_selected_case() -> None:
    support = _support("SYNTH-CASE-002", 2025)
    assert support.case_id == "SYNTH-CASE-002"
    assert support.run_id == "SYNTH-RUN-002"
