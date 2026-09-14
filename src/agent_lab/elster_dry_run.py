"""Synthetic-only Phase P1 ELSTER control boundary with no transmitter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from agent_lab.artifact_identity import ArtifactIdentity, build_artifact_identity


SUPPORTED_TAX_YEAR = 2024
SUPPORTED_PROCEDURE_CODE = "UFA10"
SUPPORTED_ERIC_VERSION = "41.2"
SYNTHETIC_CLASSIFICATION = "SYNTHETIC"
SYNTHETIC_DESTINATION = "SYNTH-ELSTER-ACCEPTANCE-SERVER"
SYNTHETIC_CHANNEL = "SYNTH-ERIC"


class SubmissionControlError(ValueError):
    """Raised when a non-production submission-control artifact is invalid."""


class GateOutcome(str, Enum):
    HUMAN_REQUIRED = "HUMAN_REQUIRED"
    BLOCKED = "BLOCKED"
    DRY_RUN_READY = "DRY_RUN_READY"


class ApprovalStatus(str, Enum):
    APPROVED = "APPROVED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


def _required(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SubmissionControlError(f"{name} is required")


def _synthetic(name: str, value: str) -> None:
    _required(name, value)
    if not value.startswith("SYNTH-"):
        raise SubmissionControlError(f"{name} must use the SYNTH- namespace")


def _aware(name: str, value: datetime) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise SubmissionControlError(f"{name} must be timezone-aware")


@dataclass(frozen=True, slots=True)
class SyntheticTaxSummary:
    gross_wages_eur: int
    withheld_wage_tax_eur: int
    deductible_expenses_eur: int

    def __post_init__(self) -> None:
        for name, value in (
            ("gross_wages_eur", self.gross_wages_eur),
            ("withheld_wage_tax_eur", self.withheld_wage_tax_eur),
            ("deductible_expenses_eur", self.deductible_expenses_eur),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise SubmissionControlError(f"{name} must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class SyntheticSubmissionEnvelope:
    case_id: str
    run_id: str
    tax_year: int
    procedure_code: str
    eric_version: str
    purpose: str
    data_classification: str
    payload: SyntheticTaxSummary
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise SubmissionControlError("unsupported envelope schema_version")
        _synthetic("case_id", self.case_id)
        _synthetic("run_id", self.run_id)
        _required("purpose", self.purpose)
        if self.tax_year != SUPPORTED_TAX_YEAR:
            raise SubmissionControlError("unsupported tax_year for Phase P1 package 1")
        if self.procedure_code != SUPPORTED_PROCEDURE_CODE:
            raise SubmissionControlError("unsupported ELSTER procedure_code")
        if self.eric_version != SUPPORTED_ERIC_VERSION:
            raise SubmissionControlError("unsupported ERiC version")
        if self.data_classification != SYNTHETIC_CLASSIFICATION:
            raise SubmissionControlError("only SYNTHETIC data is permitted")
        if not isinstance(self.payload, SyntheticTaxSummary):
            raise SubmissionControlError("payload must be SyntheticTaxSummary")

    @property
    def artifact_identity(self) -> ArtifactIdentity:
        return build_artifact_identity(
            kind="SYNTHETIC_ELSTER_SUBMISSION_ENVELOPE",
            version=str(self.schema_version),
            payload=self,
        )


@dataclass(frozen=True, slots=True)
class ContentReleaseApproval:
    approval_id: str
    approver_id: str
    case_id: str
    run_id: str
    artifact_reference: str
    artifact_version: str
    data_classification: str
    purpose: str
    issued_at: datetime
    expires_at: datetime
    status: ApprovalStatus

    def __post_init__(self) -> None:
        _synthetic("approval_id", self.approval_id)
        _synthetic("approver_id", self.approver_id)
        _aware("issued_at", self.issued_at)
        _aware("expires_at", self.expires_at)
        if self.expires_at <= self.issued_at:
            raise SubmissionControlError("content approval expiry must follow issuance")


@dataclass(frozen=True, slots=True)
class DestinationTransmissionApproval:
    approval_id: str
    approver_id: str
    content_release_approval_id: str
    case_id: str
    run_id: str
    artifact_reference: str
    artifact_version: str
    destination_identity: str
    channel: str
    purpose: str
    issued_at: datetime
    expires_at: datetime
    single_retry_permitted: bool
    status: ApprovalStatus

    def __post_init__(self) -> None:
        _synthetic("approval_id", self.approval_id)
        _synthetic("approver_id", self.approver_id)
        _synthetic("content_release_approval_id", self.content_release_approval_id)
        _aware("issued_at", self.issued_at)
        _aware("expires_at", self.expires_at)
        if self.expires_at <= self.issued_at:
            raise SubmissionControlError("destination approval expiry must follow issuance")
        if not isinstance(self.single_retry_permitted, bool):
            raise SubmissionControlError("single_retry_permitted must be boolean")


@dataclass(frozen=True, slots=True)
class DryRunDecision:
    outcome: GateOutcome
    artifact_reference: str
    required_gate: str | None
    blockers: tuple[str, ...]
    limitations: tuple[str, ...] = ()
    transmission_permitted: bool = False
    network_calls: tuple[str, ...] = ()
    credential_access: bool = False


def _content_blockers(
    envelope: SyntheticSubmissionEnvelope,
    approval: ContentReleaseApproval,
    now: datetime,
) -> list[str]:
    identity = envelope.artifact_identity
    blockers: list[str] = []
    if approval.status is not ApprovalStatus.APPROVED:
        blockers.append("content release approval is not APPROVED")
    if approval.issued_at > now or approval.expires_at <= now:
        blockers.append("content release approval is not currently valid")
    if (approval.case_id, approval.run_id) != (envelope.case_id, envelope.run_id):
        blockers.append("content release case/run binding mismatch")
    if approval.artifact_reference != identity.reference:
        blockers.append("content release artifact binding mismatch")
    if approval.artifact_version != identity.version:
        blockers.append("content release artifact version mismatch")
    if approval.data_classification != envelope.data_classification:
        blockers.append("content release classification mismatch")
    if approval.purpose != envelope.purpose:
        blockers.append("content release purpose mismatch")
    return blockers


def _destination_blockers(
    envelope: SyntheticSubmissionEnvelope,
    content: ContentReleaseApproval,
    approval: DestinationTransmissionApproval,
    now: datetime,
) -> list[str]:
    identity = envelope.artifact_identity
    blockers: list[str] = []
    if approval.status is not ApprovalStatus.APPROVED:
        blockers.append("destination approval is not APPROVED")
    if approval.issued_at > now or approval.expires_at <= now:
        blockers.append("destination approval is not currently valid")
    if approval.approval_id == content.approval_id:
        blockers.append("the two approval events must be distinct")
    if approval.content_release_approval_id != content.approval_id:
        blockers.append("destination approval is not bound to content approval")
    if approval.issued_at < content.issued_at:
        blockers.append("destination approval predates content approval")
    if (approval.case_id, approval.run_id) != (envelope.case_id, envelope.run_id):
        blockers.append("destination approval case/run binding mismatch")
    if approval.artifact_reference != identity.reference:
        blockers.append("destination approval artifact binding mismatch")
    if approval.artifact_version != identity.version:
        blockers.append("destination approval artifact version mismatch")
    if approval.destination_identity != SYNTHETIC_DESTINATION:
        blockers.append("destination identity mismatch")
    if approval.channel != SYNTHETIC_CHANNEL:
        blockers.append("destination channel mismatch")
    if approval.purpose != envelope.purpose:
        blockers.append("destination approval purpose mismatch")
    return blockers


def evaluate_synthetic_dry_run(
    envelope: SyntheticSubmissionEnvelope,
    *,
    now: datetime,
    content_approval: ContentReleaseApproval | None = None,
    destination_approval: DestinationTransmissionApproval | None = None,
) -> DryRunDecision:
    """Evaluate approval bindings without exposing any transmission capability."""
    if not isinstance(envelope, SyntheticSubmissionEnvelope):
        raise SubmissionControlError("invalid synthetic submission envelope")
    _aware("now", now)
    identity = envelope.artifact_identity
    if content_approval is None:
        return DryRunDecision(
            outcome=GateOutcome.HUMAN_REQUIRED,
            artifact_reference=identity.reference,
            required_gate="CONTENT_RELEASE_APPROVAL",
            blockers=("content release approval is absent",),
        )
    content_blockers = _content_blockers(envelope, content_approval, now)
    if content_blockers:
        return DryRunDecision(
            outcome=GateOutcome.BLOCKED,
            artifact_reference=identity.reference,
            required_gate="CONTENT_RELEASE_APPROVAL",
            blockers=tuple(content_blockers),
        )
    if destination_approval is None:
        return DryRunDecision(
            outcome=GateOutcome.HUMAN_REQUIRED,
            artifact_reference=identity.reference,
            required_gate="DESTINATION_TRANSMISSION_APPROVAL",
            blockers=("destination transmission approval is absent",),
        )
    destination_blockers = _destination_blockers(
        envelope, content_approval, destination_approval, now
    )
    if destination_blockers:
        return DryRunDecision(
            outcome=GateOutcome.BLOCKED,
            artifact_reference=identity.reference,
            required_gate="DESTINATION_TRANSMISSION_APPROVAL",
            blockers=tuple(destination_blockers),
        )
    return DryRunDecision(
        outcome=GateOutcome.DRY_RUN_READY,
        artifact_reference=identity.reference,
        required_gate=None,
        blockers=(),
        limitations=(
            "NON_PRODUCTION_ONLY",
            "OFFICIAL_XML_MAPPING_NOT_IMPLEMENTED",
            "TRANSMITTER_NOT_IMPLEMENTED",
        ),
    )
