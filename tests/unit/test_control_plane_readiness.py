from __future__ import annotations

from copy import deepcopy

import pytest

from agent_lab.control_plane_readiness import ReadinessEvidenceError, evaluate_readiness


def ready_evidence() -> dict:
    return {
        "schema_version": 1,
        "repository": "golestanzadeh/ai-agent-lab",
        "branch": "d021-agent-case-provisioning",
        "git_remote": "https://github.com/golestanzadeh/ai-agent-lab.git",
        "head_sha": "a" * 40,
        "pr_number": 1,
        "pr_is_draft": True,
        "work_automation_repository": "golestanzadeh/ai-agent-lab",
        "work_automation_enabled": True,
        "codex_available": True,
        "github_reachable": True,
        "local_sync_task_state": "READY",
        "windows_relay_task_state": "RUNNING",
        "monitoring_state": "CONFIGURED",
        "restart_recovery_verified": True,
        "protected_main_human_gate": True,
        "collected_at": "2026-09-14T09:55:00+02:00",
        "evidence_references": ["git://head", "windows-task://local-sync"],
    }


def test_complete_exact_evidence_passes():
    result = evaluate_readiness(ready_evidence())
    assert result.outcome == "PASS"
    assert result.ready is True
    assert result.blockers == ()


@pytest.mark.parametrize(
    ("field", "value", "fragment"),
    [
        ("work_automation_repository", None, "Work automation repository scope"),
        ("work_automation_enabled", False, "Work automation enabled state"),
        ("windows_relay_task_state", "NOT_INSTALLED", "Windows Relay scheduled task"),
        ("local_sync_task_state", "DISABLED", "Local Sync scheduled task"),
        ("monitoring_state", "NOT_VERIFIED", "monitoring configuration"),
        ("restart_recovery_verified", False, "restart and recovery verification"),
        ("protected_main_human_gate", False, "protected-main Human Gate"),
    ],
)
def test_missing_readiness_condition_blocks(field, value, fragment):
    evidence = deepcopy(ready_evidence())
    evidence[field] = value
    result = evaluate_readiness(evidence)
    assert result.outcome == "BLOCKED"
    assert any(fragment in blocker for blocker in result.blockers)


def test_repository_scope_mismatch_blocks():
    evidence = ready_evidence()
    evidence["repository"] = "golestanzadeh/agent-bridge-poc"
    assert evaluate_readiness(evidence).outcome == "BLOCKED"


def test_unknown_or_malformed_evidence_fails_closed():
    evidence = ready_evidence()
    evidence["unexpected"] = True
    with pytest.raises(ReadinessEvidenceError, match="schema mismatch"):
        evaluate_readiness(evidence)


def test_short_head_identity_fails_closed():
    evidence = ready_evidence()
    evidence["head_sha"] = "abc123"
    with pytest.raises(ReadinessEvidenceError, match="full lowercase"):
        evaluate_readiness(evidence)
