"""Framework-neutral, synthetic-only presentation state for the UI phase."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum

from agent_lab.case_registry import CaseRegistry, LifecycleStatus, LookupStatus


UI_STATE_VERSION = "1"
SUBMISSION_DISABLED_REASON = "PRODUCTION_SUBMISSION_PATH_NOT_AUTHORIZED"


class UIStateError(ValueError):
    """Raised when presentation state would cross its governed boundary."""


class HumanGateStatus(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    REQUIRED = "REQUIRED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


def _required(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise UIStateError(f"{name} is required")


def _synthetic(name: str, value: str) -> None:
    _required(name, value)
    if not value.startswith("SYNTH-"):
        raise UIStateError(f"{name} must use the SYNTH- namespace")


def _reference(name: str, value: str) -> None:
    _required(name, value)
    digest = value[7:] if value.startswith("sha256:") else ""
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise UIStateError(f"{name} must be a canonical sha256 reference")


@dataclass(frozen=True, slots=True)
class HumanGateView:
    status: HumanGateStatus
    action: str | None = None
    artifact_reference: str | None = None
    destination: str | None = None
    expires_at: datetime | None = None

    def __post_init__(self) -> None:
        fields = (self.action, self.artifact_reference, self.destination, self.expires_at)
        if self.status is HumanGateStatus.NOT_REQUIRED:
            if any(value is not None for value in fields):
                raise UIStateError("NOT_REQUIRED gate cannot carry authority fields")
            return
        _required("gate action", self.action or "")
        _reference("gate artifact_reference", self.artifact_reference or "")
        _required("gate destination", self.destination or "")
        if self.expires_at is None or self.expires_at.tzinfo is None:
            raise UIStateError("gate expiry must be timezone-aware")


@dataclass(frozen=True, slots=True)
class UIWorkspaceState:
    case_id: str
    owner_id: str
    tax_year: int
    lifecycle_status: LifecycleStatus
    run_id: str | None = None
    document_references: tuple[str, ...] = ()
    finding_references: tuple[str, ...] = ()
    evidence_gap_codes: tuple[str, ...] = ()
    preview_reference: str | None = None
    human_gate: HumanGateView = HumanGateView(HumanGateStatus.NOT_REQUIRED)
    submission_enabled: bool = False
    submission_disabled_reason: str = SUBMISSION_DISABLED_REASON
    official_receipt_reference: str | None = None
    state_version: str = UI_STATE_VERSION
    data_classification: str = "SYNTHETIC"
    network_calls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _synthetic("case_id", self.case_id)
        _synthetic("owner_id", self.owner_id)
        if self.run_id is not None:
            _synthetic("run_id", self.run_id)
        for name, values in (
            ("document_references", self.document_references),
            ("finding_references", self.finding_references),
        ):
            if not isinstance(values, tuple):
                raise UIStateError(f"{name} must be a tuple")
            for value in values:
                _reference(name, value)
        if len(set(self.document_references)) != len(self.document_references):
            raise UIStateError("document references must be unique")
        if len(set(self.finding_references)) != len(self.finding_references):
            raise UIStateError("finding references must be unique")
        if not isinstance(self.evidence_gap_codes, tuple) or any(
            not isinstance(code, str) or not code.strip() for code in self.evidence_gap_codes
        ):
            raise UIStateError("evidence gap codes must be a tuple of non-empty strings")
        if self.preview_reference is not None:
            _reference("preview_reference", self.preview_reference)
        if self.state_version != UI_STATE_VERSION:
            raise UIStateError("unsupported state_version")
        if self.data_classification != "SYNTHETIC":
            raise UIStateError("UI package 2 accepts synthetic data only")
        if self.submission_enabled is not False:
            raise UIStateError("submission cannot be enabled")
        if self.submission_disabled_reason != SUBMISSION_DISABLED_REASON:
            raise UIStateError("submission disabled reason cannot be weakened")
        if self.official_receipt_reference is not None:
            raise UIStateError("an official receipt cannot exist in synthetic UI state")
        if self.network_calls != ():
            raise UIStateError("UI state cannot contain network calls")

    def with_case_scoped_content(
        self,
        *,
        case_id: str,
        run_id: str,
        document_references: tuple[str, ...] = (),
        finding_references: tuple[str, ...] = (),
        evidence_gap_codes: tuple[str, ...] = (),
        preview_reference: str | None = None,
        human_gate: HumanGateView | None = None,
    ) -> "UIWorkspaceState":
        if case_id != self.case_id:
            raise UIStateError("case-scoped content does not match selected case")
        return replace(
            self,
            run_id=run_id,
            document_references=document_references,
            finding_references=finding_references,
            evidence_gap_codes=evidence_gap_codes,
            preview_reference=preview_reference,
            human_gate=human_gate or HumanGateView(HumanGateStatus.NOT_REQUIRED),
        )


def select_synthetic_workspace(
    registry: CaseRegistry, *, case_id: str, tax_year: int
) -> UIWorkspaceState:
    """Resolve exact case scope and return a fresh state with no stale case content."""
    if not isinstance(registry, CaseRegistry):
        raise UIStateError("CaseRegistry is required")
    _synthetic("case_id", case_id)
    result = registry.resolve_by_case_id(case_id)
    if result.status is not LookupStatus.RESOLVED:
        raise UIStateError("case_id is not resolved by the Case Registry")
    record = registry.get(result.case_id)
    if record is None:
        raise UIStateError("resolved case record is unavailable")
    _synthetic("owner_id", record.owner_id)
    if record.tax_period.year != tax_year:
        raise UIStateError("tax year does not match the selected case")
    return UIWorkspaceState(
        case_id=record.case_id,
        owner_id=record.owner_id,
        tax_year=record.tax_period.year,
        lifecycle_status=record.lifecycle_status,
    )
