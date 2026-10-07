from datetime import datetime, timedelta, timezone

import pytest

from agent_lab.codex_usage_reader import (
    UsageTelemetryError,
    normalize_rate_limits,
    to_capacity_observation,
)


NOW = datetime(2026, 10, 7, 15, 0, tzinfo=timezone.utc)


def payload(five=0, weekly=0):
    return {
        "ordinaryUsageAllowed": True,
        "rateLimits": {
            "limitId": "codex",
            "primary": {
                "usedPercent": five,
                "windowDurationMins": 300,
                "resetsAt": int((NOW + timedelta(hours=5)).timestamp()),
            },
            "secondary": {
                "usedPercent": weekly,
                "windowDurationMins": 10080,
                "resetsAt": int((NOW + timedelta(days=7)).timestamp()),
            },
        },
    }


def test_normalizes_authoritative_windows():
    snapshot = normalize_rate_limits(payload(7, 31), measured_at=NOW)
    assert snapshot.five_hour.remaining_percent == 93
    assert snapshot.weekly.remaining_percent == 69
    assert snapshot.five_hour.window_duration_mins == 300
    assert snapshot.weekly.window_duration_mins == 10080


def test_snapshot_adapts_to_existing_capacity_contract():
    observation = to_capacity_observation(normalize_rate_limits(payload(7, 31), measured_at=NOW))
    assert observation.five_hour_remaining_percent == 93
    assert observation.weekly_remaining_percent == 69
    assert observation.five_hour_resets_at == NOW + timedelta(hours=5)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["rateLimits"].update(limitId="other"),
        lambda value: value["rateLimits"]["primary"].update(windowDurationMins=301),
        lambda value: value["rateLimits"]["secondary"].update(windowDurationMins=999),
        lambda value: value["rateLimits"]["primary"].update(usedPercent=None),
        lambda value: value.update(ordinaryUsageAllowed=None),
    ],
)
def test_malformed_or_ambiguous_usage_fails_closed(mutation):
    value = payload()
    mutation(value)
    with pytest.raises(UsageTelemetryError):
        normalize_rate_limits(value, measured_at=NOW)


def test_expired_reset_fails_closed():
    value = payload()
    value["rateLimits"]["primary"]["resetsAt"] = int((NOW - timedelta(seconds=1)).timestamp())
    with pytest.raises(UsageTelemetryError, match="reset timestamps"):
        normalize_rate_limits(value, measured_at=NOW)
