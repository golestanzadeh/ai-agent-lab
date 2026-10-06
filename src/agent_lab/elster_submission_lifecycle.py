"""Synthetic-only submission lifecycle with no transmitter or external capability."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum

from agent_lab.artifact_identity import ArtifactIdentity, build_artifact_identity
from agent_lab.elster_dry_run import (
    ApprovalStatus,
    ContentReleaseApproval,
    DestinationTransmissionApproval,
    GateOutcome,
    SyntheticSubmissionEnvelope,
    evaluate_synthetic_dry_run,
)
from agent_lab.elster_preview import SyntheticElsterPreview


LIFECYCLE_VERSION = "1"
RECEIPT_PLACEHOLDER_MARKER = "SYNTHETIC_PLACEHOLDER_NO_EXTERNAL_RECEIPT"


class ElsterSubmissionLifecycleError(ValueError):
    """Raised when a lifecycle artifact violates the synthetic-only boundary."""


class SyntheticAttemptOutcome(str, Enum):
    DEFINITE_FAILURE = "SYNTHETIC_DEFINITE_FAILURE"
    UNCERTAIN = "SYNTHETIC_UNCERTAIN"
    SUCCESS_PLACEHOLDER = "SYNTHETIC_SUCCESS_PLACEHOLDER"


class LifecycleOutcome(str, Enum):
    ATTEMPT_PLANNED_NO_TRANSMITTER = "ATTEMPT_PLANNED_NO_TRANSMITTER"
    COMPLETE_WITH_PLACEHOLDER = "COMPLETE_WITH_PLACEHOLDER"
    RETRY_NOT_AUTHORIZED = "RETRY_NOT_AUTHORIZED"
    RETRY_EXHAUSTED = "RETRY_EXHAUSTED"
    UNCERTAIN_BLOCKED = "UNCERTAIN_BLOCKED"


def _required(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ElsterSubmissionLifecycleError(f"{name} is required")


def _synthetic(name: str, value: str) -> None:
    _required(name, value)
    if not value.startswith("SYNTH-"):
        raise ElsterSubmissionLifecycleError(f"{name} must use the SYNTH- namespace")


def _aware(name: str, value: datetime) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ElsterSubmissionLifecycleError(f"{name} must be timezone-aware")


def _reference(name: str, value: str) -> None:
    _required(name, value)
    digest = value[7:] if value.startswith("sha256:") else ""
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ElsterSubmissionLifecycleError(f"{name} must be a canonical sha256 reference")


@dataclass(frozen=True, slots=True)
class SyntheticSubmissionAttemptPlan:
    plan_id: str
    case_id: str
    run_id: str
    preview_reference: str
    envelope_reference: str
    destination_approval_id: str
    idempotency_key: str
    attempt_number: int
    planned_at: datetime
    lifecycle_version: str = LIFECYCLE_VERSION
    transmitter_available: bool = False
    transmission_permitted: bool = False
    credential_access: bool = False
    network_calls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("plan_id", self.plan_id),
            ("case_id", self.case_id),
            ("run_id", self.run_id),
            ("destination_approval_id", self.destination_approval_id),
        ):
            _synthetic(name, value)
        for name, value in (
            ("preview_reference", self.preview_reference),
            ("envelope_reference", self.envelope_reference),
            ("idempotency_key", self.idempotency_key),
        ):
            _reference(name, value)
        if self.attempt_number not in (1, 2):
            raise ElsterSubmissionLifecycleError("attempt_number must be 1 or 2")
        _aware("planned_at", self.planned_at)
        if self.lifecycle_version != LIFECYCLE_VERSION:
            raise ElsterSubmissionLifecycleError("unsupported lifecycle_version")
        if any(
            value is not False
            for value in (
                self.transmitter_available,
                self.transmission_permitted,
                self.credential_access,
            )
        ):
            raise ElsterSubmissionLifecycleError("attempt plan cannot enable transmission")
        if self.network_calls != ():
            raise ElsterSubmissionLifecycleError("attempt plan cannot contain network calls")

    @property
    def identity(self) -> ArtifactIdentity:
        payload = asdict(self)
        payload["planned_at"] = self.planned_at.isoformat()
        return build_artifact_identity(
            kind="SYNTHETIC_ELSTER_ATTEMPT_PLAN",
            version=self.lifecycle_version,
            payload=payload,
        )


@dataclass(frozen=True, slots=True)
class SyntheticReceiptPlaceholder:
    receipt_id: str
    plan_reference: str
    idempotency_key: str
    recorded_at: datetime
    marker: str = RECEIPT_PLACEHOLDER_MARKER
    external_receipt_received: bool = False
    network_calls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _synthetic("receipt_id", self.receipt_id)
        _reference("plan_reference", self.plan_reference)
        _reference("idempotency_key", self.idempotency_key)
        _aware("recorded_at", self.recorded_at)
        if self.marker != RECEIPT_PLACEHOLDER_MARKER:
            raise ElsterSubmissionLifecycleError("receipt placeholder marker cannot be weakened")
        if self.external_receipt_received is not False or self.network_calls != ():
            raise ElsterSubmissionLifecycleError("placeholder cannot claim an external receipt")

    @property
    def identity(self) -> ArtifactIdentity:
        return build_artifact_identity(
            kind="SYNTHETIC_ELSTER_RECEIPT_PLACEHOLDER",
            version=LIFECYCLE_VERSION,
            payload={
                "receipt_id": self.receipt_id,
                "plan_reference": self.plan_reference,
                "idempotency_key": self.idempotency_key,
                "recorded_at": self.recorded_at.isoformat(),
                "marker": self.marker,
                "external_receipt_received": self.external_receipt_received,
                "network_calls": self.network_calls,
            },
        )


@dataclass(frozen=True, slots=True)
class SyntheticSubmissionAttemptResult:
    result_id: str
    plan_reference: str
    idempotency_key: str
    attempt_number: int
    outcome: SyntheticAttemptOutcome
    observed_at: datetime
    receipt_placeholder: SyntheticReceiptPlaceholder | None = None
    credential_access: bool = False
    network_calls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _synthetic("result_id", self.result_id)
        _reference("plan_reference", self.plan_reference)
        _reference("idempotency_key", self.idempotency_key)
        if self.attempt_number not in (1, 2):
            raise ElsterSubmissionLifecycleError("attempt_number must be 1 or 2")
        if not isinstance(self.outcome, SyntheticAttemptOutcome):
            raise ElsterSubmissionLifecycleError("unknown synthetic attempt outcome")
        _aware("observed_at", self.observed_at)
        if self.outcome is SyntheticAttemptOutcome.SUCCESS_PLACEHOLDER:
            if not isinstance(self.receipt_placeholder, SyntheticReceiptPlaceholder):
                raise ElsterSubmissionLifecycleError("success requires a receipt placeholder")
            if (
                self.receipt_placeholder.plan_reference != self.plan_reference
                or self.receipt_placeholder.idempotency_key != self.idempotency_key
                or self.receipt_placeholder.recorded_at != self.observed_at
            ):
                raise ElsterSubmissionLifecycleError("receipt placeholder binding mismatch")
        elif self.receipt_placeholder is not None:
            raise ElsterSubmissionLifecycleError("only synthetic success may have a placeholder")
        if self.credential_access is not False or self.network_calls != ():
            raise ElsterSubmissionLifecycleError("attempt result cannot contain external activity")

    @property
    def identity(self) -> ArtifactIdentity:
        return build_artifact_identity(
            kind="SYNTHETIC_ELSTER_ATTEMPT_RESULT",
            version=LIFECYCLE_VERSION,
            payload={
                "result_id": self.result_id,
                "plan_reference": self.plan_reference,
                "idempotency_key": self.idempotency_key,
                "attempt_number": self.attempt_number,
                "outcome": self.outcome.value,
                "observed_at": self.observed_at.isoformat(),
                "receipt_placeholder_reference": (
                    self.receipt_placeholder.identity.reference
                    if self.receipt_placeholder is not None
                    else None
                ),
            },
        )


@dataclass(frozen=True, slots=True)
class SyntheticSubmissionLifecycleDecision:
    outcome: LifecycleOutcome
    idempotency_key: str
    next_plan: SyntheticSubmissionAttemptPlan | None
    receipt_placeholder_reference: str | None
    blockers: tuple[str, ...]
    transmission_permitted: bool = False
    transmitter_available: bool = False
    credential_access: bool = False
    network_calls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, LifecycleOutcome):
            raise ElsterSubmissionLifecycleError("unknown lifecycle outcome")
        _reference("idempotency_key", self.idempotency_key)
        if self.next_plan is not None and not isinstance(
            self.next_plan, SyntheticSubmissionAttemptPlan
        ):
            raise ElsterSubmissionLifecycleError("next_plan must be an attempt-plan artifact")
        if self.next_plan is not None and self.next_plan.idempotency_key != self.idempotency_key:
            raise ElsterSubmissionLifecycleError("next plan idempotency binding mismatch")
        if self.receipt_placeholder_reference is not None:
            _reference("receipt_placeholder_reference", self.receipt_placeholder_reference)
        if not isinstance(self.blockers, tuple) or not all(
            isinstance(item, str) and item for item in self.blockers
        ):
            raise ElsterSubmissionLifecycleError("blockers must be non-empty strings")
        if self.outcome is LifecycleOutcome.COMPLETE_WITH_PLACEHOLDER:
            if self.receipt_placeholder_reference is None or self.next_plan is not None:
                raise ElsterSubmissionLifecycleError("complete lifecycle binding mismatch")
        elif self.receipt_placeholder_reference is not None:
            raise ElsterSubmissionLifecycleError("only complete lifecycle may bind a receipt")
        if self.outcome is not LifecycleOutcome.ATTEMPT_PLANNED_NO_TRANSMITTER:
            if self.next_plan is not None:
                raise ElsterSubmissionLifecycleError("terminal lifecycle cannot contain a next plan")
        if any(
            value is not False
            for value in (
                self.transmission_permitted,
                self.transmitter_available,
                self.credential_access,
            )
        ):
            raise ElsterSubmissionLifecycleError("lifecycle cannot enable transmission")
        if self.network_calls != ():
            raise ElsterSubmissionLifecycleError("lifecycle cannot contain network calls")


def _idempotency_key(
    preview: SyntheticElsterPreview,
    destination_approval: DestinationTransmissionApproval,
) -> str:
    return build_artifact_identity(
        kind="SYNTHETIC_ELSTER_IDEMPOTENCY_KEY",
        version=LIFECYCLE_VERSION,
        payload={
            "case_id": preview.case_id,
            "run_id": preview.run_id,
            "preview_reference": preview.artifact_identity.reference,
            "envelope_reference": preview.envelope_reference,
            "destination_approval_id": destination_approval.approval_id,
        },
    ).reference


def _plan(
    preview: SyntheticElsterPreview,
    destination_approval: DestinationTransmissionApproval,
    *,
    attempt_number: int,
    planned_at: datetime,
    idempotency_key: str,
) -> SyntheticSubmissionAttemptPlan:
    suffix = idempotency_key.removeprefix("sha256:")[:16]
    return SyntheticSubmissionAttemptPlan(
        plan_id=f"SYNTH-ATTEMPT-{suffix}-{attempt_number}",
        case_id=preview.case_id,
        run_id=preview.run_id,
        preview_reference=preview.artifact_identity.reference,
        envelope_reference=preview.envelope_reference,
        destination_approval_id=destination_approval.approval_id,
        idempotency_key=idempotency_key,
        attempt_number=attempt_number,
        planned_at=planned_at,
    )


def evaluate_synthetic_submission_lifecycle(
    preview: SyntheticElsterPreview,
    envelope: SyntheticSubmissionEnvelope,
    content_approval: ContentReleaseApproval,
    destination_approval: DestinationTransmissionApproval,
    *,
    now: datetime,
    plans: tuple[SyntheticSubmissionAttemptPlan, ...] = (),
    results: tuple[SyntheticSubmissionAttemptResult, ...] = (),
) -> SyntheticSubmissionLifecycleDecision:
    """Plan at most two inert attempts while preventing duplicate or uncertain replay."""
    if not isinstance(preview, SyntheticElsterPreview):
        raise ElsterSubmissionLifecycleError("a SyntheticElsterPreview is required")
    if not isinstance(envelope, SyntheticSubmissionEnvelope):
        raise ElsterSubmissionLifecycleError("a SyntheticSubmissionEnvelope is required")
    if not isinstance(content_approval, ContentReleaseApproval):
        raise ElsterSubmissionLifecycleError("a ContentReleaseApproval is required")
    if not isinstance(destination_approval, DestinationTransmissionApproval):
        raise ElsterSubmissionLifecycleError("a DestinationTransmissionApproval is required")
    _aware("now", now)
    if (
        preview.envelope_reference != envelope.artifact_identity.reference
        or (preview.case_id, preview.run_id) != (envelope.case_id, envelope.run_id)
    ):
        raise ElsterSubmissionLifecycleError("preview and envelope binding mismatch")
    dry_run = evaluate_synthetic_dry_run(
        envelope,
        now=now,
        content_approval=content_approval,
        destination_approval=destination_approval,
    )
    if dry_run.outcome is not GateOutcome.DRY_RUN_READY:
        raise ElsterSubmissionLifecycleError("synthetic approval boundary is not ready")
    if destination_approval.status is not ApprovalStatus.APPROVED:
        raise ElsterSubmissionLifecycleError("destination approval is not approved")
    if not isinstance(plans, tuple) or not all(
        isinstance(item, SyntheticSubmissionAttemptPlan) for item in plans
    ):
        raise ElsterSubmissionLifecycleError("plans must be attempt-plan artifacts")
    if not isinstance(results, tuple) or not all(
        isinstance(item, SyntheticSubmissionAttemptResult) for item in results
    ):
        raise ElsterSubmissionLifecycleError("results must be attempt-result artifacts")

    key = _idempotency_key(preview, destination_approval)
    if len(plans) > 2 or len(results) > len(plans):
        raise ElsterSubmissionLifecycleError("invalid lifecycle cardinality")
    if tuple(item.attempt_number for item in plans) != tuple(range(1, len(plans) + 1)):
        raise ElsterSubmissionLifecycleError("attempt plans must be unique and sequential")
    if len({item.identity.reference for item in plans}) != len(plans):
        raise ElsterSubmissionLifecycleError("duplicate attempt plan")
    for item in plans:
        expected_plan_id = (
            f"SYNTH-ATTEMPT-{key.removeprefix('sha256:')[:16]}-{item.attempt_number}"
        )
        if (
            item.plan_id != expected_plan_id
            or item.case_id != preview.case_id
            or item.run_id != preview.run_id
            or item.preview_reference != preview.artifact_identity.reference
            or item.envelope_reference != preview.envelope_reference
            or item.destination_approval_id != destination_approval.approval_id
            or item.idempotency_key != key
        ):
            raise ElsterSubmissionLifecycleError("attempt plan binding mismatch")
    for index, result in enumerate(results):
        plan = plans[index]
        if (
            result.attempt_number != plan.attempt_number
            or result.plan_reference != plan.identity.reference
            or result.idempotency_key != key
            or result.observed_at < plan.planned_at
        ):
            raise ElsterSubmissionLifecycleError("attempt result binding mismatch")

    if not plans:
        next_plan = _plan(
            preview,
            destination_approval,
            attempt_number=1,
            planned_at=now,
            idempotency_key=key,
        )
        return SyntheticSubmissionLifecycleDecision(
            outcome=LifecycleOutcome.ATTEMPT_PLANNED_NO_TRANSMITTER,
            idempotency_key=key,
            next_plan=next_plan,
            receipt_placeholder_reference=None,
            blockers=(),
        )
    if len(results) < len(plans):
        return SyntheticSubmissionLifecycleDecision(
            outcome=LifecycleOutcome.ATTEMPT_PLANNED_NO_TRANSMITTER,
            idempotency_key=key,
            next_plan=None,
            receipt_placeholder_reference=None,
            blockers=("PLANNED_ATTEMPT_HAS_NO_SYNTHETIC_RESULT",),
        )

    last = results[-1]
    if last.outcome is SyntheticAttemptOutcome.SUCCESS_PLACEHOLDER:
        return SyntheticSubmissionLifecycleDecision(
            outcome=LifecycleOutcome.COMPLETE_WITH_PLACEHOLDER,
            idempotency_key=key,
            next_plan=None,
            receipt_placeholder_reference=last.receipt_placeholder.identity.reference,
            blockers=(),
        )
    if last.outcome is SyntheticAttemptOutcome.UNCERTAIN:
        return SyntheticSubmissionLifecycleDecision(
            outcome=LifecycleOutcome.UNCERTAIN_BLOCKED,
            idempotency_key=key,
            next_plan=None,
            receipt_placeholder_reference=None,
            blockers=("UNCERTAIN_OUTCOME_MUST_NEVER_AUTO_RETRY",),
        )
    if len(plans) == 2:
        return SyntheticSubmissionLifecycleDecision(
            outcome=LifecycleOutcome.RETRY_EXHAUSTED,
            idempotency_key=key,
            next_plan=None,
            receipt_placeholder_reference=None,
            blockers=("MAXIMUM_TWO_SYNTHETIC_ATTEMPTS_REACHED",),
        )
    if destination_approval.single_retry_permitted is not True:
        return SyntheticSubmissionLifecycleDecision(
            outcome=LifecycleOutcome.RETRY_NOT_AUTHORIZED,
            idempotency_key=key,
            next_plan=None,
            receipt_placeholder_reference=None,
            blockers=("SINGLE_RETRY_NOT_AUTHORIZED",),
        )
    next_plan = _plan(
        preview,
        destination_approval,
        attempt_number=2,
        planned_at=now,
        idempotency_key=key,
    )
    return SyntheticSubmissionLifecycleDecision(
        outcome=LifecycleOutcome.ATTEMPT_PLANNED_NO_TRANSMITTER,
        idempotency_key=key,
        next_plan=next_plan,
        receipt_placeholder_reference=None,
        blockers=(),
    )
