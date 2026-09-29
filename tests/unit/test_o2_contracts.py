from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from scripts.validate_o2_contracts import load_contracts, validate_contracts


ROOT = Path(__file__).resolve().parents[2]


def contracts():
    return load_contracts(ROOT)


def test_phase_o2_contract_set_is_consistent():
    assert validate_contracts(contracts()) == []


def test_role_count_mismatch_fails_closed():
    changed = contracts()
    changed["roles.json"]["permanent_role_count"] = 19
    assert "roles.json: permanent role count must equal 20" in validate_contracts(changed)


def test_role_identifier_substitution_fails_closed():
    changed = contracts()
    changed["roles.json"]["roles"][0]["role_id"] = "UNRATIFIED_ROLE"
    assert "roles.json: permanent role identifiers must exactly match the ratified organization" in validate_contracts(changed)


def test_reporting_line_change_fails_closed():
    changed = contracts()
    changed["roles.json"]["roles"][4]["reports_to"] = "GOVERNANCE_GUARD_AGENT"
    assert "roles.json: MASTER_PROJECT_ORCHESTRATOR reporting line disagrees with the ratified organization" in validate_contracts(changed)


def test_role_cannot_receive_a6_standing_access():
    changed = contracts()
    changed["permission-matrix.json"]["role_permissions"][0]["default_tiers"].append("A6")
    errors = validate_contracts(changed)
    assert any("may not receive A6" in error for error in errors)


def test_manifest_schema_cannot_request_a6():
    changed = contracts()
    tiers = changed["agent-manifest.schema.json"]["properties"]["requested_access_tiers"]["items"]["enum"]
    tiers.append("A6")
    assert "agent-manifest.schema.json: manifests may not request A6 or AX" in validate_contracts(changed)


def test_case_access_requires_case_context():
    changed = contracts()
    changed["agent-manifest.schema.json"]["allOf"] = []
    assert "agent-manifest.schema.json: A3/A4 requests must require case context" in validate_contracts(changed)


def test_external_transfer_approvals_cannot_be_collapsed():
    changed = contracts()
    changed["human-gates.json"]["external_transfer"]["stages_must_be_separate_events"] = False
    assert "human-gates.json: the two external-transfer approvals must be separate" in validate_contracts(changed)


def test_terminal_lifecycle_state_cannot_restart():
    changed = contracts()
    changed["lifecycle.json"]["transitions"]["COMPLETED"] = ["ACTIVE"]
    assert "lifecycle.json: terminal states may not have outgoing transitions" in validate_contracts(changed)


def test_budget_hard_limit_cannot_be_lower_than_default():
    changed = contracts()
    changed["execution-policy.json"]["hard_limits"]["max_retries"] = 1
    assert "execution-policy.json: hard max_retries must be at least the default" in validate_contracts(changed)


def test_unknown_top_level_schema_fields_must_be_rejected():
    changed = contracts()
    changed["task.schema.json"]["additionalProperties"] = True
    assert "task.schema.json: unknown top-level fields must be rejected" in validate_contracts(changed)


def test_missing_contract_fails_closed():
    changed = contracts()
    del changed["roles.json"]
    assert validate_contracts(changed) == ["missing contracts: roles.json"]
