import pytest

from agent_lab.ui_status_labels import STATUS_LABELS, UIStatusLabelError, persian_status_label
from agent_lab.ui_submission_readiness_contract import BLOCKERS
from agent_lab.ui_support_contract import SAFE_SUPPORT_CODES
from agent_lab.ui_workflow_contract import SAFE_DIAGNOSTIC_CODES
from agent_lab.ui_workflow_contract import RecoveryStatus, STAGE_CODES, StageStatus
from agent_lab.case_registry import LifecycleStatus
from agent_lab.ui_document_contract import ALLOWED_CATEGORIES, DocumentViewStatus
from agent_lab.ui_state_contract import HumanGateStatus


def test_critical_contract_codes_have_exact_nonempty_persian_labels() -> None:
    required = set(SAFE_DIAGNOSTIC_CODES) | set(SAFE_SUPPORT_CODES) | set(BLOCKERS)
    required |= {"NOT_APPROVED", "NOT_EXECUTED", "LOCAL_MAPPING_XSD_AND_RULE_SUBSET_PASS"}
    assert required <= STATUS_LABELS.keys()
    assert all(persian_status_label(code).strip() for code in required)


def test_unknown_or_arbitrary_text_fails_closed() -> None:
    for value in ("UNKNOWN", "private document text", "", None):
        with pytest.raises(UIStatusLabelError, match="unknown"):
            persian_status_label(value)


def test_every_workflow_stage_and_state_has_a_closed_persian_label() -> None:
    required = set(STAGE_CODES)
    required |= {status.value for status in StageStatus}
    required |= {status.value for status in RecoveryStatus}
    assert required <= STATUS_LABELS.keys()
    assert all(persian_status_label(code).strip() for code in required)


def test_case_document_and_human_gate_values_have_closed_persian_labels() -> None:
    required = set(ALLOWED_CATEGORIES)
    required |= {status.value for status in DocumentViewStatus}
    required |= {status.value for status in LifecycleStatus}
    required |= {status.value for status in HumanGateStatus}
    required |= {"REVIEW_SYNTHETIC_PREVIEW", "LOCAL_SYNTHETIC_PREVIEW"}
    assert required <= STATUS_LABELS.keys()
