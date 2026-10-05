"""Deterministic capacity decisions for the governed continuation controller."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum


class CapacityEvidenceError(ValueError):
    """Raised when capacity evidence or an operation estimate is malformed."""


class CapacityState(StrEnum):
    RUN = "RUN"
    CAUTION = "CAUTION"
    TOKEN_PAUSED = "TOKEN_PAUSED"
    UNKNOWN_PAUSED = "UNKNOWN_PAUSED"
    CAPACITY_DEFERRED = "CAPACITY_DEFERRED"


class OperationCostClass(StrEnum):
    """Closed, versioned estimate classes; callers cannot invent percentages."""

    CHEAP = "CHEAP"
    BOUNDED = "BOUNDED"
    EXPENSIVE = "EXPENSIVE"


ESTIMATE_BASIS_VERSION = 1
_OPERATION_COSTS: dict[OperationCostClass, tuple[float, float]] = {
    OperationCostClass.CHEAP: (5, 1),
    OperationCostClass.BOUNDED: (15, 5),
    OperationCostClass.EXPENSIVE: (35, 15),
}


@dataclass(frozen=True)
class CapacityObservation:
    five_hour_remaining_percent: float | None
    weekly_remaining_percent: float | None
    observed_at: datetime
    valid_until: datetime
    five_hour_resets_at: datetime
    weekly_resets_at: datetime

    def validate(self, *, now: datetime) -> None:
        for name, value in (
            ("five_hour_remaining_percent", self.five_hour_remaining_percent),
            ("weekly_remaining_percent", self.weekly_remaining_percent),
        ):
            if value is not None and (isinstance(value, bool) or not 0 <= value <= 100):
                raise CapacityEvidenceError(f"{name} must be between 0 and 100")
        for name, value in (
            ("observed_at", self.observed_at),
            ("valid_until", self.valid_until),
            ("five_hour_resets_at", self.five_hour_resets_at),
            ("weekly_resets_at", self.weekly_resets_at),
            ("now", now),
        ):
            if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
                raise CapacityEvidenceError(f"{name} must be timezone-aware")
        if self.valid_until < self.observed_at:
            raise CapacityEvidenceError("valid_until cannot precede observed_at")
        if self.five_hour_resets_at <= self.observed_at or self.weekly_resets_at <= self.observed_at:
            raise CapacityEvidenceError("reset timestamps must follow observed_at")
        if self.valid_until > min(self.five_hour_resets_at, self.weekly_resets_at):
            raise CapacityEvidenceError("observation validity cannot cross a reset timestamp")

    def is_current(self, *, now: datetime) -> bool:
        self.validate(now=now)
        return self.observed_at <= now <= self.valid_until


@dataclass(frozen=True)
class DeferredOperation:
    operation_id: str
    reason: str
    continuation_checkpoint: str
    estimate_class: OperationCostClass
    estimate_basis_version: int = ESTIMATE_BASIS_VERSION

    def validate(self) -> None:
        for name in ("operation_id", "reason", "continuation_checkpoint"):
            if not getattr(self, name).strip():
                raise CapacityEvidenceError(f"{name} must be non-empty")
        if not isinstance(self.estimate_class, OperationCostClass):
            raise CapacityEvidenceError("estimate_class must use the closed operation-cost catalog")
        if self.estimate_basis_version != ESTIMATE_BASIS_VERSION:
            raise CapacityEvidenceError("unsupported estimate basis version")

    @property
    def estimated_costs(self) -> tuple[float, float]:
        return _OPERATION_COSTS[self.estimate_class]


@dataclass(frozen=True)
class CapacityDecision:
    state: CapacityState
    can_start_operation: bool
    reason_code: str
    observation: CapacityObservation
    deferred_operation: DeferredOperation | None = None


def _base_state(observation: CapacityObservation, *, now: datetime) -> CapacityState:
    if not observation.is_current(now=now):
        return CapacityState.UNKNOWN_PAUSED
    five = observation.five_hour_remaining_percent
    weekly = observation.weekly_remaining_percent
    if five is None or weekly is None:
        return CapacityState.UNKNOWN_PAUSED
    if five <= 15 or weekly <= 10:
        return CapacityState.TOKEN_PAUSED
    if five <= 25 or weekly <= 20:
        return CapacityState.CAUTION
    return CapacityState.RUN


def evaluate_capacity(
    observation: CapacityObservation,
    *,
    now: datetime,
    next_operation: DeferredOperation | None = None,
) -> CapacityDecision:
    """Classify live capacity and, only from explicit estimates, defer unsafe work.

    Proactive deferral is deterministic: an operation is deferred when its declared
    cost would leave either window at or below the hard pause boundary. It never
    changes the underlying observation into ``TOKEN_PAUSED``.
    """

    state = _base_state(observation, now=now)
    if state is CapacityState.UNKNOWN_PAUSED:
        return CapacityDecision(state, False, "USAGE_UNAVAILABLE_OR_STALE", observation)
    if state is CapacityState.TOKEN_PAUSED:
        return CapacityDecision(state, False, "HARD_THRESHOLD_REACHED", observation)
    if next_operation is None:
        if state is CapacityState.CAUTION:
            return CapacityDecision(state, False, "CAUTION_CHECKPOINT_ONLY", observation)
        return CapacityDecision(state, True, "RUN_CAPACITY_AVAILABLE", observation)

    next_operation.validate()
    five = observation.five_hour_remaining_percent
    weekly = observation.weekly_remaining_percent
    assert five is not None and weekly is not None
    estimated_five, estimated_weekly = next_operation.estimated_costs
    if five - estimated_five <= 15 or weekly - estimated_weekly <= 10:
        return CapacityDecision(
            CapacityState.CAPACITY_DEFERRED,
            False,
            "PROJECTED_HARD_THRESHOLD_CROSSING",
            observation,
            next_operation,
        )
    if state is CapacityState.CAUTION:
        return CapacityDecision(state, False, "CAUTION_CHECKPOINT_ONLY", observation, next_operation)
    return CapacityDecision(state, True, "RUN_OPERATION_FITS", observation)


def can_resume(
    previous_state: CapacityState,
    observation: CapacityObservation,
    *,
    now: datetime,
    repository_recovery_safe: bool,
    exact_authorized_continuation: bool,
    deferred_operation: DeferredOperation | None = None,
) -> bool:
    """Return whether a paused/deferred continuation may resume."""

    if not repository_recovery_safe or not exact_authorized_continuation:
        return False
    base = _base_state(observation, now=now)
    five = observation.five_hour_remaining_percent
    weekly = observation.weekly_remaining_percent
    if five is None or weekly is None or base is CapacityState.UNKNOWN_PAUSED:
        return False
    if previous_state is CapacityState.TOKEN_PAUSED:
        return five >= 80 and weekly > 10
    if previous_state is CapacityState.CAPACITY_DEFERRED:
        if deferred_operation is None:
            return False
        return evaluate_capacity(observation, now=now, next_operation=deferred_operation).can_start_operation
    return False


def fresh_observation(
    five: float | None,
    weekly: float | None,
    *,
    five_hour_resets_at: datetime,
    weekly_resets_at: datetime,
    observed_at: datetime | None = None,
    validity: timedelta = timedelta(minutes=15),
) -> CapacityObservation:
    """Construct an observation from service-provided values; reset times are never inferred."""

    at = observed_at or datetime.now(timezone.utc)
    return CapacityObservation(
        five,
        weekly,
        at,
        at + validity,
        five_hour_resets_at,
        weekly_resets_at,
    )
