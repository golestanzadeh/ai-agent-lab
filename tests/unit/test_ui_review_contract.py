from dataclasses import replace

import pytest

from agent_lab.ui_app import _populate_synthetic_state, build_synthetic_registry
from agent_lab.ui_review_contract import ALLOWED_GAP_CODES, ALLOWED_FINDING_CODES, UIReviewError, build_synthetic_review
from agent_lab.ui_state_contract import select_synthetic_workspace


def _workspace(case_id="SYNTH-CASE-001", year=2024):
    return _populate_synthetic_state(select_synthetic_workspace(build_synthetic_registry(), case_id=case_id, tax_year=year))


def test_review_is_exactly_case_run_bound_and_preview_bound():
    workspace = _workspace()
    review = build_synthetic_review(workspace)
    assert (review.case_id, review.run_id) == (workspace.case_id, workspace.run_id)
    assert review.preview_reference == workspace.preview_reference
    assert review.findings == ALLOWED_FINDING_CODES
    assert review.evidence_gaps == ALLOWED_GAP_CODES
    assert review.official_mapping_status == "LOCAL_E10_2024_XSD_VALIDATED"
    assert review.local_plausibility_status == "LOCAL_THIRTY_SIX_RULE_SUBSET_PASS"


def test_case_switch_builds_fresh_scoped_summary():
    first = build_synthetic_review(_workspace())
    second = build_synthetic_review(_workspace("SYNTH-CASE-002", 2025))
    assert first.case_id != second.case_id and first.run_id != second.run_id
    assert first.calculation_total != second.calculation_total


@pytest.mark.parametrize("field,value", [("calculation_total", -1), ("currency", "EUR"), ("official_mapping_status", "READY"), ("local_plausibility_status", "OFFICIAL_PASS"), ("authentication_enabled", True), ("persistence_enabled", True), ("network_calls", ("https://example.invalid",))])
def test_review_denies_boundary_weakening(field, value):
    with pytest.raises(UIReviewError):
        replace(build_synthetic_review(_workspace()), **{field: value})


def test_review_rejects_unallowlisted_or_duplicate_findings():
    review = build_synthetic_review(_workspace())
    with pytest.raises(UIReviewError):
        replace(review, findings=("PRIVATE_FREE_FORM",))
    with pytest.raises(UIReviewError):
        replace(review, findings=(ALLOWED_FINDING_CODES[0], ALLOWED_FINDING_CODES[0]))


def test_review_requires_exact_workspace_gap_boundary():
    with pytest.raises(UIReviewError):
        build_synthetic_review(replace(_workspace(), evidence_gap_codes=("OTHER",)))
