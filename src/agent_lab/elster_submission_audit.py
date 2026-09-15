"""Privacy-minimized synthetic lifecycle audit and restart recovery."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json

from agent_lab.artifact_identity import ArtifactIdentity, build_artifact_identity, canonical_json
from agent_lab.elster_preview import SyntheticElsterPreview
from agent_lab.elster_submission_lifecycle import (
    LIFECYCLE_VERSION,
    SyntheticAttemptOutcome,
    SyntheticSubmissionAttemptPlan,
    SyntheticSubmissionAttemptResult,
)


AUDIT_VERSION = "1"
GENESIS_DIGEST = "sha256:" + "0" * 64


class ElsterSubmissionAuditError(ValueError):
    """Raised when synthetic lifecycle audit evidence cannot be trusted."""


class LifecycleAuditEventType(str, Enum):
    ATTEMPT_PLAN_RECORDED = "ATTEMPT_PLAN_RECORDED"
    ATTEMPT_RESULT_RECORDED = "ATTEMPT_RESULT_RECORDED"
    RECEIPT_PLACEHOLDER_RECORDED = "RECEIPT_PLACEHOLDER_RECORDED"


class RecoveredLifecycleState(str, Enum):
    AWAITING_SYNTHETIC_RESULT = "AWAITING_SYNTHETIC_RESULT"
    DEFINITE_FAILURE_RECORDED = "DEFINITE_FAILURE_RECORDED"
    UNCERTAIN_BLOCKED = "UNCERTAIN_BLOCKED"
    COMPLETE_WITH_PLACEHOLDER = "COMPLETE_WITH_PLACEHOLDER"
    RETRY_EXHAUSTED = "RETRY_EXHAUSTED"


def _required(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ElsterSubmissionAuditError(f"{name} is required")


def _synthetic(name: str, value: str) -> None:
    _required(name, value)
    if not value.startswith("SYNTH-"):
        raise ElsterSubmissionAuditError(f"{name} must use the SYNTH- namespace")


def _reference(name: str, value: str) -> None:
    _required(name, value)
    digest = value[7:] if value.startswith("sha256:") else ""
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ElsterSubmissionAuditError(f"{name} must be a canonical sha256 reference")


def _aware(name: str, value: datetime) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ElsterSubmissionAuditError(f"{name} must be timezone-aware")


@dataclass(frozen=True, slots=True)
class SyntheticLifecycleAuditEvent:
    sequence: int
    event_type: LifecycleAuditEventType
    case_id: str
    run_id: str
    idempotency_key: str
    attempt_number: int
    artifact_reference: str
    occurred_at: datetime
    previous_digest: str
    outcome: SyntheticAttemptOutcome | None = None
    event_digest: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.sequence, int) or isinstance(self.sequence, bool) or self.sequence < 1:
            raise ElsterSubmissionAuditError("sequence must be a positive integer")
        if not isinstance(self.event_type, LifecycleAuditEventType):
            raise ElsterSubmissionAuditError("unknown lifecycle audit event type")
        _synthetic("case_id", self.case_id)
        _synthetic("run_id", self.run_id)
        _reference("idempotency_key", self.idempotency_key)
        if self.attempt_number not in (1, 2):
            raise ElsterSubmissionAuditError("attempt_number must be 1 or 2")
        _reference("artifact_reference", self.artifact_reference)
        _aware("occurred_at", self.occurred_at)
        _reference("previous_digest", self.previous_digest)
        if self.event_type is LifecycleAuditEventType.ATTEMPT_RESULT_RECORDED:
            if not isinstance(self.outcome, SyntheticAttemptOutcome):
                raise ElsterSubmissionAuditError("result event requires a synthetic outcome")
        elif self.outcome is not None:
            raise ElsterSubmissionAuditError("only a result event may contain an outcome")
        if self.event_digest:
            _reference("event_digest", self.event_digest)
            if self.event_digest != self.calculated_digest:
                raise ElsterSubmissionAuditError("lifecycle audit event digest mismatch")

    @property
    def digest_payload(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "event_type": self.event_type.value,
            "case_id": self.case_id,
            "run_id": self.run_id,
            "idempotency_key": self.idempotency_key,
            "attempt_number": self.attempt_number,
            "artifact_reference": self.artifact_reference,
            "occurred_at": self.occurred_at.isoformat(),
            "previous_digest": self.previous_digest,
            "outcome": self.outcome.value if self.outcome is not None else None,
        }

    @property
    def calculated_digest(self) -> str:
        return build_artifact_identity(
            kind="SYNTHETIC_ELSTER_LIFECYCLE_AUDIT_EVENT",
            version=AUDIT_VERSION,
            payload=self.digest_payload,
        ).reference

    @property
    def identity(self) -> ArtifactIdentity:
        return ArtifactIdentity(
            kind="SYNTHETIC_ELSTER_LIFECYCLE_AUDIT_EVENT",
            version=AUDIT_VERSION,
            reference=self.calculated_digest,
        )


@dataclass(frozen=True, slots=True)
class SyntheticLifecycleAuditSnapshot:
    case_id: str
    run_id: str
    preview_reference: str
    idempotency_key: str
    events: tuple[SyntheticLifecycleAuditEvent, ...]
    head_digest: str
    audit_version: str = AUDIT_VERSION
    data_classification: str = "SYNTHETIC"
    contains_tax_values: bool = False
    restart_recovery_only: bool = True
    transmission_permitted: bool = False
    credential_access: bool = False
    network_calls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _synthetic("case_id", self.case_id)
        _synthetic("run_id", self.run_id)
        _reference("preview_reference", self.preview_reference)
        _reference("idempotency_key", self.idempotency_key)
        if not isinstance(self.events, tuple) or not self.events:
            raise ElsterSubmissionAuditError("audit snapshot requires events")
        if not all(isinstance(item, SyntheticLifecycleAuditEvent) for item in self.events):
            raise ElsterSubmissionAuditError("invalid lifecycle audit event")
        _reference("head_digest", self.head_digest)
        if self.audit_version != AUDIT_VERSION:
            raise ElsterSubmissionAuditError("unsupported audit_version")
        if self.data_classification != "SYNTHETIC":
            raise ElsterSubmissionAuditError("only SYNTHETIC audit data is permitted")
        if self.contains_tax_values is not False or self.restart_recovery_only is not True:
            raise ElsterSubmissionAuditError("audit privacy boundary cannot be weakened")
        if self.transmission_permitted is not False or self.credential_access is not False:
            raise ElsterSubmissionAuditError("audit cannot enable an external capability")
        if self.network_calls != ():
            raise ElsterSubmissionAuditError("audit cannot contain network calls")
        validate_synthetic_lifecycle_audit(self)

    @property
    def identity(self) -> ArtifactIdentity:
        return build_artifact_identity(
            kind="SYNTHETIC_ELSTER_LIFECYCLE_AUDIT_SNAPSHOT",
            version=self.audit_version,
            payload=self.to_payload(),
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "audit_version": self.audit_version,
            "case_id": self.case_id,
            "run_id": self.run_id,
            "preview_reference": self.preview_reference,
            "idempotency_key": self.idempotency_key,
            "events": [dict(event.digest_payload, event_digest=event.calculated_digest) for event in self.events],
            "head_digest": self.head_digest,
            "data_classification": self.data_classification,
            "contains_tax_values": self.contains_tax_values,
            "restart_recovery_only": self.restart_recovery_only,
            "transmission_permitted": self.transmission_permitted,
            "credential_access": self.credential_access,
            "network_calls": list(self.network_calls),
        }

    def to_json(self) -> str:
        return canonical_json(self.to_payload())


@dataclass(frozen=True, slots=True)
class SyntheticLifecycleRecovery:
    snapshot_reference: str
    case_id: str
    run_id: str
    idempotency_key: str
    state: RecoveredLifecycleState
    completed_attempts: int
    open_attempt_number: int | None
    receipt_placeholder_reference: str | None
    restart_safe: bool = True
    transmission_permitted: bool = False
    credential_access: bool = False
    network_calls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _reference("snapshot_reference", self.snapshot_reference)
        _synthetic("case_id", self.case_id)
        _synthetic("run_id", self.run_id)
        _reference("idempotency_key", self.idempotency_key)
        if not isinstance(self.state, RecoveredLifecycleState):
            raise ElsterSubmissionAuditError("unknown recovered lifecycle state")
        if self.completed_attempts not in (0, 1, 2):
            raise ElsterSubmissionAuditError("invalid completed_attempts")
        if self.open_attempt_number not in (None, 1, 2):
            raise ElsterSubmissionAuditError("invalid open_attempt_number")
        if self.receipt_placeholder_reference is not None:
            _reference("receipt_placeholder_reference", self.receipt_placeholder_reference)
        if self.restart_safe is not True:
            raise ElsterSubmissionAuditError("validated recovery must remain restart-safe")
        if self.transmission_permitted is not False or self.credential_access is not False:
            raise ElsterSubmissionAuditError("recovery cannot enable an external capability")
        if self.network_calls != ():
            raise ElsterSubmissionAuditError("recovery cannot contain network calls")


def _event(
    *,
    sequence: int,
    event_type: LifecycleAuditEventType,
    preview: SyntheticElsterPreview,
    idempotency_key: str,
    attempt_number: int,
    artifact_reference: str,
    occurred_at: datetime,
    previous_digest: str,
    outcome: SyntheticAttemptOutcome | None = None,
) -> SyntheticLifecycleAuditEvent:
    candidate = SyntheticLifecycleAuditEvent(
        sequence=sequence,
        event_type=event_type,
        case_id=preview.case_id,
        run_id=preview.run_id,
        idempotency_key=idempotency_key,
        attempt_number=attempt_number,
        artifact_reference=artifact_reference,
        occurred_at=occurred_at,
        previous_digest=previous_digest,
        outcome=outcome,
    )
    return SyntheticLifecycleAuditEvent(
        sequence=candidate.sequence,
        event_type=candidate.event_type,
        case_id=candidate.case_id,
        run_id=candidate.run_id,
        idempotency_key=candidate.idempotency_key,
        attempt_number=candidate.attempt_number,
        artifact_reference=candidate.artifact_reference,
        occurred_at=candidate.occurred_at,
        previous_digest=candidate.previous_digest,
        outcome=candidate.outcome,
        event_digest=candidate.calculated_digest,
    )


def build_synthetic_lifecycle_audit(
    preview: SyntheticElsterPreview,
    plans: tuple[SyntheticSubmissionAttemptPlan, ...],
    results: tuple[SyntheticSubmissionAttemptResult, ...],
) -> SyntheticLifecycleAuditSnapshot:
    """Build a privacy-minimized hash chain from validated synthetic artifacts."""
    if not isinstance(preview, SyntheticElsterPreview):
        raise ElsterSubmissionAuditError("a SyntheticElsterPreview is required")
    if not isinstance(plans, tuple) or not plans or not all(
        isinstance(item, SyntheticSubmissionAttemptPlan) for item in plans
    ):
        raise ElsterSubmissionAuditError("one or two attempt plans are required")
    if not isinstance(results, tuple) or not all(
        isinstance(item, SyntheticSubmissionAttemptResult) for item in results
    ):
        raise ElsterSubmissionAuditError("results must be attempt-result artifacts")
    if len(plans) > 2 or len(results) > len(plans):
        raise ElsterSubmissionAuditError("invalid lifecycle cardinality")
    key = plans[0].idempotency_key
    events: list[SyntheticLifecycleAuditEvent] = []
    previous = GENESIS_DIGEST
    sequence = 1
    for index, plan in enumerate(plans):
        if (
            plan.attempt_number != index + 1
            or plan.case_id != preview.case_id
            or plan.run_id != preview.run_id
            or plan.preview_reference != preview.artifact_identity.reference
            or plan.idempotency_key != key
        ):
            raise ElsterSubmissionAuditError("attempt plan audit binding mismatch")
        plan_event = _event(
            sequence=sequence,
            event_type=LifecycleAuditEventType.ATTEMPT_PLAN_RECORDED,
            preview=preview,
            idempotency_key=key,
            attempt_number=plan.attempt_number,
            artifact_reference=plan.identity.reference,
            occurred_at=plan.planned_at,
            previous_digest=previous,
        )
        events.append(plan_event)
        previous = plan_event.calculated_digest
        sequence += 1
        if index >= len(results):
            continue
        result = results[index]
        if (
            result.attempt_number != plan.attempt_number
            or result.plan_reference != plan.identity.reference
            or result.idempotency_key != key
            or result.observed_at < plan.planned_at
        ):
            raise ElsterSubmissionAuditError("attempt result audit binding mismatch")
        result_event = _event(
            sequence=sequence,
            event_type=LifecycleAuditEventType.ATTEMPT_RESULT_RECORDED,
            preview=preview,
            idempotency_key=key,
            attempt_number=result.attempt_number,
            artifact_reference=result.identity.reference,
            occurred_at=result.observed_at,
            previous_digest=previous,
            outcome=result.outcome,
        )
        events.append(result_event)
        previous = result_event.calculated_digest
        sequence += 1
        if result.receipt_placeholder is not None:
            receipt_event = _event(
                sequence=sequence,
                event_type=LifecycleAuditEventType.RECEIPT_PLACEHOLDER_RECORDED,
                preview=preview,
                idempotency_key=key,
                attempt_number=result.attempt_number,
                artifact_reference=result.receipt_placeholder.identity.reference,
                occurred_at=result.receipt_placeholder.recorded_at,
                previous_digest=previous,
            )
            events.append(receipt_event)
            previous = receipt_event.calculated_digest
            sequence += 1
    return SyntheticLifecycleAuditSnapshot(
        case_id=preview.case_id,
        run_id=preview.run_id,
        preview_reference=preview.artifact_identity.reference,
        idempotency_key=key,
        events=tuple(events),
        head_digest=previous,
    )


def validate_synthetic_lifecycle_audit(snapshot: SyntheticLifecycleAuditSnapshot) -> None:
    """Validate chain, scope, ordering, and lifecycle semantics."""
    previous = GENESIS_DIGEST
    expected_attempt = 1
    open_attempt: int | None = None
    terminal = False
    success_pending_receipt = False
    for sequence, event in enumerate(snapshot.events, start=1):
        if event.sequence != sequence or event.previous_digest != previous:
            raise ElsterSubmissionAuditError("lifecycle audit chain ordering mismatch")
        if (
            event.case_id != snapshot.case_id
            or event.run_id != snapshot.run_id
            or event.idempotency_key != snapshot.idempotency_key
        ):
            raise ElsterSubmissionAuditError("lifecycle audit scope mismatch")
        if event.event_digest != event.calculated_digest:
            raise ElsterSubmissionAuditError("lifecycle audit event digest mismatch")
        if terminal or (
            success_pending_receipt
            and event.event_type is not LifecycleAuditEventType.RECEIPT_PLACEHOLDER_RECORDED
        ):
            raise ElsterSubmissionAuditError("event recorded after terminal lifecycle outcome")
        if event.event_type is LifecycleAuditEventType.ATTEMPT_PLAN_RECORDED:
            if open_attempt is not None or event.attempt_number != expected_attempt:
                raise ElsterSubmissionAuditError("invalid attempt-plan sequence")
            open_attempt = event.attempt_number
        elif event.event_type is LifecycleAuditEventType.ATTEMPT_RESULT_RECORDED:
            if open_attempt != event.attempt_number:
                raise ElsterSubmissionAuditError("result has no matching open attempt")
            open_attempt = None
            if event.outcome is SyntheticAttemptOutcome.SUCCESS_PLACEHOLDER:
                success_pending_receipt = True
            elif event.outcome is SyntheticAttemptOutcome.UNCERTAIN:
                terminal = True
            elif event.attempt_number == 2:
                terminal = True
            else:
                expected_attempt = 2
        else:
            if (
                not success_pending_receipt
                or event.attempt_number != expected_attempt
                or sequence < 2
                or snapshot.events[sequence - 2].event_type
                is not LifecycleAuditEventType.ATTEMPT_RESULT_RECORDED
                or snapshot.events[sequence - 2].outcome
                is not SyntheticAttemptOutcome.SUCCESS_PLACEHOLDER
            ):
                raise ElsterSubmissionAuditError("receipt placeholder event is out of sequence")
            success_pending_receipt = False
            terminal = True
        previous = event.calculated_digest
    if snapshot.head_digest != previous:
        raise ElsterSubmissionAuditError("lifecycle audit head digest mismatch")
    success_results = [
        event
        for event in snapshot.events
        if event.event_type is LifecycleAuditEventType.ATTEMPT_RESULT_RECORDED
        and event.outcome is SyntheticAttemptOutcome.SUCCESS_PLACEHOLDER
    ]
    receipts = [
        event
        for event in snapshot.events
        if event.event_type is LifecycleAuditEventType.RECEIPT_PLACEHOLDER_RECORDED
    ]
    if len(success_results) != len(receipts):
        raise ElsterSubmissionAuditError("synthetic success and receipt evidence mismatch")


def restore_synthetic_lifecycle_audit(
    serialized_snapshot: str,
    *,
    expected_case_id: str,
    expected_run_id: str,
    expected_idempotency_key: str,
) -> SyntheticLifecycleRecovery:
    """Recover validated state from serialized evidence in a fresh process boundary."""
    _synthetic("expected_case_id", expected_case_id)
    _synthetic("expected_run_id", expected_run_id)
    _reference("expected_idempotency_key", expected_idempotency_key)
    try:
        payload = json.loads(serialized_snapshot)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ElsterSubmissionAuditError("invalid lifecycle audit JSON") from exc
    expected_keys = {
        "audit_version", "case_id", "run_id", "preview_reference", "idempotency_key",
        "events", "head_digest", "data_classification", "contains_tax_values",
        "restart_recovery_only", "transmission_permitted", "credential_access", "network_calls",
    }
    if not isinstance(payload, dict) or set(payload) != expected_keys:
        raise ElsterSubmissionAuditError("unexpected lifecycle audit snapshot fields")
    event_keys = {
        "sequence", "event_type", "case_id", "run_id", "idempotency_key",
        "attempt_number", "artifact_reference", "occurred_at", "previous_digest",
        "outcome", "event_digest",
    }
    try:
        raw_events = payload["events"]
        if not isinstance(raw_events, list):
            raise ElsterSubmissionAuditError("events must be a list")
        events = tuple(
            SyntheticLifecycleAuditEvent(
                sequence=item["sequence"],
                event_type=LifecycleAuditEventType(item["event_type"]),
                case_id=item["case_id"],
                run_id=item["run_id"],
                idempotency_key=item["idempotency_key"],
                attempt_number=item["attempt_number"],
                artifact_reference=item["artifact_reference"],
                occurred_at=datetime.fromisoformat(item["occurred_at"]),
                previous_digest=item["previous_digest"],
                outcome=(SyntheticAttemptOutcome(item["outcome"]) if item["outcome"] is not None else None),
                event_digest=item["event_digest"],
            )
            for item in raw_events
            if isinstance(item, dict) and set(item) == event_keys
        )
        if len(events) != len(raw_events):
            raise ElsterSubmissionAuditError("unexpected lifecycle audit event fields")
        snapshot = SyntheticLifecycleAuditSnapshot(
            case_id=payload["case_id"],
            run_id=payload["run_id"],
            preview_reference=payload["preview_reference"],
            idempotency_key=payload["idempotency_key"],
            events=events,
            head_digest=payload["head_digest"],
            audit_version=payload["audit_version"],
            data_classification=payload["data_classification"],
            contains_tax_values=payload["contains_tax_values"],
            restart_recovery_only=payload["restart_recovery_only"],
            transmission_permitted=payload["transmission_permitted"],
            credential_access=payload["credential_access"],
            network_calls=tuple(payload["network_calls"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ElsterSubmissionAuditError):
            raise
        raise ElsterSubmissionAuditError("malformed lifecycle audit snapshot") from exc
    if (
        snapshot.case_id != expected_case_id
        or snapshot.run_id != expected_run_id
        or snapshot.idempotency_key != expected_idempotency_key
    ):
        raise ElsterSubmissionAuditError("restart recovery scope mismatch")
    results = [
        event for event in snapshot.events
        if event.event_type is LifecycleAuditEventType.ATTEMPT_RESULT_RECORDED
    ]
    plans = [
        event for event in snapshot.events
        if event.event_type is LifecycleAuditEventType.ATTEMPT_PLAN_RECORDED
    ]
    receipts = [
        event for event in snapshot.events
        if event.event_type is LifecycleAuditEventType.RECEIPT_PLACEHOLDER_RECORDED
    ]
    open_attempt = plans[-1].attempt_number if len(plans) > len(results) else None
    if open_attempt is not None:
        state = RecoveredLifecycleState.AWAITING_SYNTHETIC_RESULT
    elif results[-1].outcome is SyntheticAttemptOutcome.SUCCESS_PLACEHOLDER:
        state = RecoveredLifecycleState.COMPLETE_WITH_PLACEHOLDER
    elif results[-1].outcome is SyntheticAttemptOutcome.UNCERTAIN:
        state = RecoveredLifecycleState.UNCERTAIN_BLOCKED
    elif results[-1].attempt_number == 2:
        state = RecoveredLifecycleState.RETRY_EXHAUSTED
    else:
        state = RecoveredLifecycleState.DEFINITE_FAILURE_RECORDED
    return SyntheticLifecycleRecovery(
        snapshot_reference=snapshot.identity.reference,
        case_id=snapshot.case_id,
        run_id=snapshot.run_id,
        idempotency_key=snapshot.idempotency_key,
        state=state,
        completed_attempts=len(results),
        open_attempt_number=open_attempt,
        receipt_placeholder_reference=(receipts[-1].artifact_reference if receipts else None),
    )
