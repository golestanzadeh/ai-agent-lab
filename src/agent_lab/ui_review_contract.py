"""Immutable synthetic review and form-preview presentation contract."""

from __future__ import annotations

from dataclasses import dataclass

from agent_lab.ui_state_contract import UIWorkspaceState

REVIEW_VIEW_VERSION = "3"
ALLOWED_FINDING_CODES = ("SYNTH_INCOME_REVIEWED", "SYNTH_EXPENSE_REVIEWED")
ALLOWED_GAP_CODES = (
    "OFFICIAL_ERIC_ENGINE_NOT_EXECUTED",
    "REAL_PAYLOAD_NOT_AUTHORIZED",
)


class UIReviewError(ValueError):
    pass


def _ref(value: str) -> None:
    digest = value[7:] if isinstance(value, str) and value.startswith("sha256:") else ""
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise UIReviewError("reference must be canonical sha256")


@dataclass(frozen=True, slots=True)
class SyntheticReviewView:
    case_id: str
    run_id: str
    findings: tuple[str, ...]
    evidence_gaps: tuple[str, ...]
    calculation_total: int
    currency: str
    preview_reference: str
    official_mapping_status: str = "LOCAL_E10_2024_XSD_VALIDATED"
    local_plausibility_status: str = "LOCAL_THIRTY_TWO_RULE_SUBSET_PASS"
    version: str = REVIEW_VIEW_VERSION
    data_classification: str = "SYNTHETIC_SUMMARY_ONLY"
    authentication_enabled: bool = False
    persistence_enabled: bool = False
    network_calls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.case_id.startswith("SYNTH-") or not self.run_id.startswith("SYNTH-"):
            raise UIReviewError("review scope must be synthetic")
        if not self.findings or any(item not in ALLOWED_FINDING_CODES for item in self.findings):
            raise UIReviewError("findings must use the closed allowlist")
        if len(set(self.findings)) != len(self.findings):
            raise UIReviewError("findings must be unique")
        if self.evidence_gaps != ALLOWED_GAP_CODES:
            raise UIReviewError("evidence gaps must preserve the official-material boundary")
        if isinstance(self.calculation_total, bool) or not isinstance(self.calculation_total, int) or self.calculation_total < 0:
            raise UIReviewError("calculation total must be a nonnegative synthetic integer")
        if self.currency != "EUR_SYNTHETIC":
            raise UIReviewError("currency must remain explicitly synthetic")
        _ref(self.preview_reference)
        if self.official_mapping_status != "LOCAL_E10_2024_XSD_VALIDATED":
            raise UIReviewError("local mapping status cannot change")
        if self.local_plausibility_status != "LOCAL_THIRTY_TWO_RULE_SUBSET_PASS":
            raise UIReviewError("local plausibility status cannot change")
        if self.version != REVIEW_VIEW_VERSION or self.data_classification != "SYNTHETIC_SUMMARY_ONLY":
            raise UIReviewError("review contract identity cannot change")
        if self.authentication_enabled or self.persistence_enabled or self.network_calls != ():
            raise UIReviewError("authentication, persistence, and networking remain disabled")


def build_synthetic_review(workspace: UIWorkspaceState) -> SyntheticReviewView:
    if not isinstance(workspace, UIWorkspaceState) or workspace.run_id is None or workspace.preview_reference is None:
        raise UIReviewError("a populated workspace preview is required")
    if workspace.evidence_gap_codes != ALLOWED_GAP_CODES:
        raise UIReviewError("workspace evidence gaps do not match the review contract")
    return SyntheticReviewView(
        case_id=workspace.case_id,
        run_id=workspace.run_id,
        findings=ALLOWED_FINDING_CODES,
        evidence_gaps=ALLOWED_GAP_CODES,
        calculation_total=1250 if workspace.case_id.endswith("001") else 980,
        currency="EUR_SYNTHETIC",
        preview_reference=workspace.preview_reference,
    )
