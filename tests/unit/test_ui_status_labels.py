import pytest

from agent_lab.ui_status_labels import STATUS_LABELS, UIStatusLabelError, persian_status_label
from agent_lab.ui_submission_readiness_contract import BLOCKERS
from agent_lab.ui_support_contract import SAFE_SUPPORT_CODES
from agent_lab.ui_workflow_contract import SAFE_DIAGNOSTIC_CODES


def test_critical_contract_codes_have_exact_nonempty_persian_labels() -> None:
    required = set(SAFE_DIAGNOSTIC_CODES) | set(SAFE_SUPPORT_CODES) | set(BLOCKERS)
    required |= {"NOT_APPROVED", "NOT_EXECUTED", "LOCAL_MAPPING_XSD_AND_RULE_SUBSET_PASS"}
    assert required <= STATUS_LABELS.keys()
    assert all(persian_status_label(code).strip() for code in required)


def test_unknown_or_arbitrary_text_fails_closed() -> None:
    for value in ("UNKNOWN", "private document text", "", None):
        with pytest.raises(UIStatusLabelError, match="unknown"):
            persian_status_label(value)
