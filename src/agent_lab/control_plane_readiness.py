"""Deterministic Phase O5 production-control-plane readiness evaluator."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


EXPECTED_REPOSITORY = "golestanzadeh/ai-agent-lab"
EXPECTED_BRANCH = "d021-agent-case-provisioning"
EXPECTED_REMOTE = "https://github.com/golestanzadeh/ai-agent-lab.git"
READY_TASK_STATES = {"READY", "RUNNING"}
EXPECTED_FIELDS = {
    "schema_version", "repository", "branch", "git_remote", "head_sha", "pr_number",
    "pr_is_draft", "work_automation_repository", "work_automation_enabled",
    "codex_available", "github_reachable", "local_sync_task_state",
    "windows_relay_task_state", "monitoring_state", "restart_recovery_verified",
    "protected_main_human_gate", "collected_at", "evidence_references",
}
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class ReadinessEvidenceError(ValueError):
    """Raised when readiness evidence is malformed or ambiguous."""


@dataclass(frozen=True)
class ReadinessResult:
    outcome: str
    ready: bool
    blockers: tuple[str, ...]
    verified: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "ready": self.ready,
            "blockers": list(self.blockers),
            "verified": list(self.verified),
        }


def _require_bool(evidence: dict[str, Any], field: str) -> bool:
    value = evidence[field]
    if not isinstance(value, bool):
        raise ReadinessEvidenceError(f"{field} must be boolean")
    return value


def _require_string(evidence: dict[str, Any], field: str) -> str:
    value = evidence[field]
    if not isinstance(value, str) or not value.strip():
        raise ReadinessEvidenceError(f"{field} must be a non-empty string")
    return value


def evaluate_readiness(evidence: dict[str, Any]) -> ReadinessResult:
    """Evaluate exact non-secret evidence; incomplete or unknown evidence blocks."""
    if not isinstance(evidence, dict) or set(evidence) != EXPECTED_FIELDS:
        raise ReadinessEvidenceError("readiness evidence schema mismatch")
    if evidence["schema_version"] != 1:
        raise ReadinessEvidenceError("unsupported readiness evidence version")
    strings = (
        "repository", "branch", "git_remote", "head_sha", "local_sync_task_state",
        "windows_relay_task_state", "monitoring_state", "collected_at",
    )
    for field in strings:
        _require_string(evidence, field)
    for field in (
        "pr_is_draft", "work_automation_enabled", "codex_available", "github_reachable",
        "restart_recovery_verified", "protected_main_human_gate",
    ):
        _require_bool(evidence, field)
    if evidence["work_automation_repository"] is not None and (
        not isinstance(evidence["work_automation_repository"], str)
        or not evidence["work_automation_repository"].strip()
    ):
        raise ReadinessEvidenceError("work_automation_repository must be null or a non-empty string")
    if not isinstance(evidence["pr_number"], int) or isinstance(evidence["pr_number"], bool):
        raise ReadinessEvidenceError("pr_number must be an integer")
    references = evidence["evidence_references"]
    if not isinstance(references, list) or not references or any(
        not isinstance(item, str) or not item.strip() for item in references
    ):
        raise ReadinessEvidenceError("evidence_references must contain non-empty references")
    if not _SHA_RE.fullmatch(evidence["head_sha"]):
        raise ReadinessEvidenceError("head_sha must be a full lowercase Git SHA")

    blockers: list[str] = []
    verified: list[str] = []

    def exact(field: str, expected: Any, label: str) -> None:
        if evidence[field] == expected:
            verified.append(label)
        else:
            blockers.append(f"{label}: expected {expected!r}, got {evidence[field]!r}")

    exact("repository", EXPECTED_REPOSITORY, "main repository binding")
    exact("branch", EXPECTED_BRANCH, "development branch binding")
    exact("git_remote", EXPECTED_REMOTE, "GitHub remote binding")
    exact("pr_number", 1, "governed pull request binding")
    exact("pr_is_draft", True, "draft pull request boundary")
    exact("work_automation_repository", EXPECTED_REPOSITORY, "Work automation repository scope")
    exact("work_automation_enabled", True, "Work automation enabled state")
    exact("codex_available", True, "Codex availability")
    exact("github_reachable", True, "GitHub reachability")
    exact("monitoring_state", "CONFIGURED", "monitoring configuration")
    exact("restart_recovery_verified", True, "restart and recovery verification")
    exact("protected_main_human_gate", True, "protected-main Human Gate")
    for field, label in (
        ("local_sync_task_state", "Local Sync scheduled task"),
        ("windows_relay_task_state", "Windows Relay scheduled task"),
    ):
        if evidence[field] in READY_TASK_STATES:
            verified.append(label)
        else:
            blockers.append(f"{label}: state {evidence[field]!r} is not ready")
    return ReadinessResult("PASS" if not blockers else "BLOCKED", not blockers, tuple(blockers), tuple(verified))
