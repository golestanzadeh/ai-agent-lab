from datetime import datetime, timedelta, timezone

import pytest

from agent_lab.plan_limit_controller import (
    CapacityEvidenceError,
    CapacityState,
    DeferredOperation,
    OperationCostClass,
    can_resume,
    evaluate_capacity,
    fresh_observation,
)


NOW = datetime(2026, 10, 4, 12, 0, tzinfo=timezone.utc)


def observation(five=50, weekly=92):
    return fresh_observation(five, weekly, observed_at=NOW,
        five_hour_resets_at=NOW + timedelta(hours=5),
        weekly_resets_at=NOW + timedelta(days=7))


def test_constructor_never_infers_service_reset_timestamps():
    with pytest.raises(TypeError):
        fresh_observation(50, 92, observed_at=NOW)


def operation(estimate_class=OperationCostClass.BOUNDED):
    return DeferredOperation("DR-03", "bounded package estimate", "a" * 40, estimate_class)


def test_healthy_50_92_is_run_not_token_paused():
    decision = evaluate_capacity(observation(), now=NOW)
    assert decision.state is CapacityState.RUN
    assert decision.can_start_operation is True


@pytest.mark.parametrize(("five", "weekly"), [(15, 92), (1, 100), (50, 10), (100, 0)])
def test_hard_thresholds_token_pause(five, weekly):
    decision = evaluate_capacity(observation(five, weekly), now=NOW)
    assert decision.state is CapacityState.TOKEN_PAUSED
    assert decision.can_start_operation is False


@pytest.mark.parametrize(("five", "weekly"), [(16, 92), (25, 92), (50, 11), (50, 20)])
def test_caution_range_allows_only_checkpoint_work(five, weekly):
    decision = evaluate_capacity(observation(five, weekly), now=NOW)
    assert decision.state is CapacityState.CAUTION
    assert decision.can_start_operation is False


def test_explicit_projected_crossing_is_capacity_deferred_not_token_paused():
    decision = evaluate_capacity(observation(50, 92), now=NOW, next_operation=operation(OperationCostClass.EXPENSIVE))
    assert decision.state is CapacityState.CAPACITY_DEFERRED
    assert decision.reason_code == "PROJECTED_HARD_THRESHOLD_CROSSING"
    assert decision.deferred_operation == operation(OperationCostClass.EXPENSIVE)


def test_operation_that_fits_remains_run():
    assert evaluate_capacity(observation(), now=NOW, next_operation=operation()).state is CapacityState.RUN


def test_token_pause_resume_requires_80_percent_and_repository_contract():
    assert not can_resume(CapacityState.TOKEN_PAUSED, observation(79, 92), now=NOW, repository_recovery_safe=True, exact_authorized_continuation=True)
    assert can_resume(CapacityState.TOKEN_PAUSED, observation(80, 11), now=NOW, repository_recovery_safe=True, exact_authorized_continuation=True)
    assert not can_resume(CapacityState.TOKEN_PAUSED, observation(90, 92), now=NOW, repository_recovery_safe=False, exact_authorized_continuation=True)


def test_capacity_deferred_does_not_inherit_80_percent_resume_floor():
    deferred = operation(OperationCostClass.BOUNDED)
    assert can_resume(CapacityState.CAPACITY_DEFERRED, observation(31, 92), now=NOW, repository_recovery_safe=True, exact_authorized_continuation=True, deferred_operation=deferred)


@pytest.mark.parametrize("obs", [observation(None, 92), observation(50, None)])
def test_unavailable_usage_fails_closed(obs):
    assert evaluate_capacity(obs, now=NOW).state is CapacityState.UNKNOWN_PAUSED


def test_stale_observation_fails_closed():
    stale_now = NOW + timedelta(minutes=16)
    decision = evaluate_capacity(observation(), now=stale_now)
    assert decision.state is CapacityState.UNKNOWN_PAUSED
    assert decision.can_start_operation is False


def test_free_form_estimate_class_fails_closed():
    with pytest.raises(CapacityEvidenceError, match="closed operation-cost catalog"):
        evaluate_capacity(observation(), now=NOW, next_operation=operation("invented"))


def test_unknown_estimate_basis_version_fails_closed():
    with pytest.raises(CapacityEvidenceError, match="estimate basis version"):
        evaluate_capacity(
            observation(),
            now=NOW,
            next_operation=DeferredOperation("DR-03", "reason", "a" * 40, OperationCostClass.CHEAP, 2),
        )


@pytest.mark.parametrize("reset_field", ["five_hour_resets_at", "weekly_resets_at"])
def test_missing_reset_timestamp_is_rejected(reset_field):
    values = observation().__dict__ | {reset_field: None}
    with pytest.raises(CapacityEvidenceError, match=f"{reset_field} must be timezone-aware"):
        evaluate_capacity(type(observation())(**values), now=NOW)


def test_naive_reset_timestamp_is_rejected():
    values = observation().__dict__ | {"five_hour_resets_at": datetime(2026, 10, 4, 17, 0)}
    with pytest.raises(CapacityEvidenceError, match="five_hour_resets_at must be timezone-aware"):
        evaluate_capacity(type(observation())(**values), now=NOW)


def test_reset_before_observation_is_rejected():
    values = observation().__dict__ | {"five_hour_resets_at": NOW - timedelta(seconds=1)}
    with pytest.raises(CapacityEvidenceError, match="reset timestamps must follow"):
        evaluate_capacity(type(observation())(**values), now=NOW)


def test_validity_crossing_reset_is_rejected():
    values = observation().__dict__ | {
        "valid_until": NOW + timedelta(hours=2),
        "five_hour_resets_at": NOW + timedelta(hours=1),
    }
    with pytest.raises(CapacityEvidenceError, match="validity cannot cross"):
        evaluate_capacity(type(observation())(**values), now=NOW)
