"""Read Codex account rate-limit telemetry without invoking model inference."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_lab.plan_limit_controller import CapacityEvidenceError, CapacityObservation, fresh_observation


class UsageTelemetryError(RuntimeError):
    """Raised when Codex usage telemetry is unavailable, ambiguous, or malformed."""


@dataclass(frozen=True)
class UsageWindow:
    used_percent: float
    remaining_percent: float
    window_duration_mins: int
    reset_at: datetime


@dataclass(frozen=True)
class CodexUsageSnapshot:
    measured_at: datetime
    five_hour: UsageWindow
    weekly: UsageWindow
    ordinary_usage_allowed: bool
    source: str = "codex_app_server"

    def as_dict(self) -> dict[str, Any]:
        def window(value: UsageWindow) -> dict[str, Any]:
            return {
                "used_percent": value.used_percent,
                "remaining_percent": value.remaining_percent,
                "window_duration_mins": value.window_duration_mins,
                "reset_at": value.reset_at.isoformat(),
            }

        return {
            "schema_version": 1,
            "measured_at": self.measured_at.isoformat(),
            "source": self.source,
            "ordinary_usage_allowed": self.ordinary_usage_allowed,
            "five_hour": window(self.five_hour),
            "weekly": window(self.weekly),
        }


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise UsageTelemetryError(f"{name} must be numeric")
    number = float(value)
    if not 0 <= number <= 100:
        raise UsageTelemetryError(f"{name} must be between 0 and 100")
    return number


def _window(raw: Any, expected_minutes: int, name: str) -> UsageWindow:
    if not isinstance(raw, dict):
        raise UsageTelemetryError(f"{name} window is missing")
    duration = raw.get("windowDurationMins")
    if duration != expected_minutes:
        raise UsageTelemetryError(f"{name} window duration is ambiguous: {duration!r}")
    used = _number(raw.get("usedPercent"), f"{name}.usedPercent")
    reset = raw.get("resetsAt")
    if isinstance(reset, bool) or not isinstance(reset, (int, float)):
        raise UsageTelemetryError(f"{name}.resetsAt must be a Unix timestamp")
    reset_at = datetime.fromtimestamp(reset, tz=timezone.utc)
    return UsageWindow(used, max(0.0, 100.0 - used), duration, reset_at)


def normalize_rate_limits(result: Any, *, measured_at: datetime | None = None) -> CodexUsageSnapshot:
    if not isinstance(result, dict):
        raise UsageTelemetryError("rate-limit result must be an object")
    limits = result.get("rateLimits")
    if not isinstance(limits, dict):
        raise UsageTelemetryError("rateLimits is missing")
    if limits.get("limitId") != "codex":
        raise UsageTelemetryError("unexpected rate-limit identity")
    allowed = result.get("ordinaryUsageAllowed")
    if not isinstance(allowed, bool):
        raise UsageTelemetryError("ordinaryUsageAllowed is missing")
    at = measured_at or datetime.now(timezone.utc)
    if at.tzinfo is None or at.utcoffset() is None:
        raise UsageTelemetryError("measured_at must be timezone-aware")
    five = _window(limits.get("primary"), 300, "five_hour")
    weekly = _window(limits.get("secondary"), 10080, "weekly")
    if five.reset_at <= at or weekly.reset_at <= at:
        raise UsageTelemetryError("reset timestamps must follow measurement time")
    return CodexUsageSnapshot(at, five, weekly, allowed)


def read_codex_usage(*, executable: str = "codex") -> CodexUsageSnapshot:
    resolved = shutil.which(executable)
    if resolved is None:
        raise UsageTelemetryError(f"{executable!r} is not installed or not on PATH")
    command = [resolved, "app-server", "--stdio"]
    if os.name == "nt" and resolved.lower().endswith((".cmd", ".bat")):
        command = ["cmd.exe", "/d", "/s", "/c", resolved, "app-server", "--stdio"]
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    assert process.stdin is not None and process.stdout is not None

    def send(payload: dict[str, Any]) -> None:
        process.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
        process.stdin.flush()

    def read_response(request_id: int) -> dict[str, Any]:
        for _ in range(200):
            line = process.stdout.readline()
            if not line:
                raise UsageTelemetryError("Codex app-server closed before responding")
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            if message.get("id") == request_id:
                if "error" in message:
                    raise UsageTelemetryError(f"Codex app-server error: {message['error']}")
                result = message.get("result")
                if not isinstance(result, dict):
                    raise UsageTelemetryError("Codex app-server returned no result")
                return result
        raise UsageTelemetryError("Codex app-server response limit exceeded")

    try:
        send({"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "ai-tax-agent-usage-reader", "version": "1"}}})
        read_response(1)
        send({"method": "initialized"})
        send({
            "id": 2,
            "method": "account/rateLimits/read",
            "params": {"excludeResetCreditDetails": True, "supportsLunaReserve": False},
        })
        return normalize_rate_limits(read_response(2))
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()


def to_capacity_observation(snapshot: CodexUsageSnapshot) -> CapacityObservation:
    try:
        return fresh_observation(
            snapshot.five_hour.remaining_percent,
            snapshot.weekly.remaining_percent,
            observed_at=snapshot.measured_at,
            five_hour_resets_at=snapshot.five_hour.reset_at,
            weekly_resets_at=snapshot.weekly.reset_at,
        )
    except CapacityEvidenceError as exc:
        raise UsageTelemetryError(str(exc)) from exc


def write_snapshot(snapshot: CodexUsageSnapshot, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(snapshot.as_dict(), indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
