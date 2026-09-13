"""Validate the Phase O2 contract set without activating runtime authority."""

from __future__ import annotations

import json
import sys
from collections import deque
from pathlib import Path
from typing import Any

CONTRACT_ROOT = Path("contracts/orchestrator/v1")
CONTRACT_PATHS = (
    "contract-set.json",
    "roles.json",
    "agent-manifest.schema.json",
    "permission-matrix.json",
    "task.schema.json",
    "response.schema.json",
    "lifecycle.json",
    "human-gates.json",
    "execution-policy.json",
)

EXPECTED_PERMANENT_ROLES = {
    "GOVERNANCE_GUARD_AGENT",
    "SECURITY_PRIVACY_AGENT",
    "INDEPENDENT_ACCEPTANCE_AGENT",
    "AUDIT_CONTINUITY_AGENT",
    "MASTER_PROJECT_ORCHESTRATOR",
    "PLANNING_DEPENDENCY_AGENT",
    "AGENT_FACTORY_SUPERVISOR",
    "DOCUMENTATION_STATE_AGENT",
    "OPERATIONS_INTEGRATION_AGENT",
    "ARCHITECTURE_AGENT",
    "IMPLEMENTATION_AGENT",
    "QUALITY_ENGINEERING_AGENT",
    "CASE_ORCHESTRATOR_AGENT",
    "CHIEF_TAX_AUDITOR_AGENT",
    "EVIDENCE_AGENT",
    "TAX_LAW_AGENT",
    "OPPORTUNITY_AGENT",
    "CALCULATION_AGENT",
    "ADVERSARIAL_REVIEWER_AGENT",
    "ELSTER_FORM_AGENT",
}
EXPECTED_TEMPLATE_ROLES = {
    "PERSONAL_TAX_SPECIALIST_AGENT",
    "BUSINESS_TAX_SPECIALIST_AGENT",
    "CORPORATE_TAX_SPECIALIST_AGENT",
}
EXPECTED_REPORTS_TO = {
    "GOVERNANCE_GUARD_AGENT": "HUMAN_PROJECT_OWNER",
    "SECURITY_PRIVACY_AGENT": "HUMAN_PROJECT_OWNER",
    "INDEPENDENT_ACCEPTANCE_AGENT": "HUMAN_PROJECT_OWNER",
    "AUDIT_CONTINUITY_AGENT": "HUMAN_PROJECT_OWNER",
    "MASTER_PROJECT_ORCHESTRATOR": "HUMAN_PROJECT_OWNER",
    "PLANNING_DEPENDENCY_AGENT": "MASTER_PROJECT_ORCHESTRATOR",
    "AGENT_FACTORY_SUPERVISOR": "MASTER_PROJECT_ORCHESTRATOR",
    "DOCUMENTATION_STATE_AGENT": "MASTER_PROJECT_ORCHESTRATOR",
    "OPERATIONS_INTEGRATION_AGENT": "MASTER_PROJECT_ORCHESTRATOR",
    "ARCHITECTURE_AGENT": "MASTER_PROJECT_ORCHESTRATOR",
    "IMPLEMENTATION_AGENT": "MASTER_PROJECT_ORCHESTRATOR",
    "QUALITY_ENGINEERING_AGENT": "MASTER_PROJECT_ORCHESTRATOR",
    "CASE_ORCHESTRATOR_AGENT": "MASTER_PROJECT_ORCHESTRATOR",
    "CHIEF_TAX_AUDITOR_AGENT": "CASE_ORCHESTRATOR_AGENT",
    "EVIDENCE_AGENT": "CHIEF_TAX_AUDITOR_AGENT",
    "TAX_LAW_AGENT": "CHIEF_TAX_AUDITOR_AGENT",
    "OPPORTUNITY_AGENT": "CHIEF_TAX_AUDITOR_AGENT",
    "CALCULATION_AGENT": "CHIEF_TAX_AUDITOR_AGENT",
    "ADVERSARIAL_REVIEWER_AGENT": "CHIEF_TAX_AUDITOR_AGENT",
    "ELSTER_FORM_AGENT": "CHIEF_TAX_AUDITOR_AGENT",
}
EXPECTED_GATE_TRIGGERS = {
    "constitutional_change",
    "governance_change",
    "accepted_architecture_change",
    "credential_change",
    "permission_expansion",
    "protected_main_merge",
    "production_release",
    "destructive_or_irreversible_action",
    "tax_declaration_signing_or_submission",
    "ELSTER_or_Finanzamt_contact",
    "external_content_release",
    "external_destination_transmission",
    "authority_ambiguity",
}


def load_contracts(repository_root: Path) -> dict[str, Any]:
    contracts: dict[str, Any] = {}
    for relative_path in CONTRACT_PATHS:
        path = repository_root / CONTRACT_ROOT / relative_path
        with path.open(encoding="utf-8") as handle:
            contracts[relative_path] = json.load(handle)
    return contracts


def _duplicate_values(values: list[str]) -> set[str]:
    return {value for value in values if values.count(value) > 1}


def _reachable(transitions: dict[str, list[str]], start: str) -> set[str]:
    visited: set[str] = set()
    pending: deque[str] = deque([start])
    while pending:
        state = pending.popleft()
        if state in visited:
            continue
        visited.add(state)
        pending.extend(transitions.get(state, ()))
    return visited


def validate_contracts(contracts: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    missing = sorted(set(CONTRACT_PATHS) - contracts.keys())
    if missing:
        return [f"missing contracts: {', '.join(missing)}"]

    for name, contract in contracts.items():
        if not isinstance(contract, dict):
            errors.append(f"{name}: root must be an object")
            continue
        if name.endswith(".schema.json"):
            if contract.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                errors.append(f"{name}: unsupported JSON Schema dialect")
        elif contract.get("schema_version") != 1:
            errors.append(f"{name}: schema_version must equal 1")

    contract_set = contracts["contract-set.json"]
    declared = contract_set.get("contracts", [])
    declared_paths = [item.get("path", "").removeprefix(str(CONTRACT_ROOT).replace("\\", "/") + "/") for item in declared]
    expected_declared = set(CONTRACT_PATHS) - {"contract-set.json"}
    if set(declared_paths) != expected_declared or len(declared_paths) != len(expected_declared):
        errors.append("contract-set.json: declared contract paths must match the exact v1 set")
    if contract_set.get("compatibility", {}).get("unknown_version_outcome") != "BLOCKED":
        errors.append("contract-set.json: unknown versions must fail closed")

    catalog = contracts["roles.json"]
    roles = catalog.get("roles", [])
    role_ids = [role.get("role_id") for role in roles]
    role_id_set = set(role_ids)
    if len(roles) != catalog.get("permanent_role_count") or len(roles) != 20:
        errors.append("roles.json: permanent role count must equal 20")
    if _duplicate_values(role_ids):
        errors.append("roles.json: role_id values must be unique")
    if role_id_set != EXPECTED_PERMANENT_ROLES:
        errors.append("roles.json: permanent role identifiers must exactly match the ratified organization")
    allowed_reports = role_id_set | {catalog.get("human_authority_id")}
    for role in roles:
        role_id = role.get("role_id", "<missing>")
        if role.get("reports_to") not in allowed_reports:
            errors.append(f"roles.json: {role_id} has an unknown reports_to")
        elif EXPECTED_REPORTS_TO.get(role_id) != role.get("reports_to"):
            errors.append(f"roles.json: {role_id} reporting line disagrees with the ratified organization")
        if not role.get("forbidden_actions"):
            errors.append(f"roles.json: {role_id} requires forbidden_actions")
        if role.get("requires_independent_review") is not True:
            errors.append(f"roles.json: {role_id} must require independent review")
    templates = catalog.get("inactive_templates", [])
    if len(templates) != catalog.get("template_role_count") or len(templates) != 3:
        errors.append("roles.json: inactive template count must equal 3")
    if {template.get("role_id") for template in templates} != EXPECTED_TEMPLATE_ROLES:
        errors.append("roles.json: template role identifiers must exactly match the ratified organization")
    if any(template.get("status") != "INACTIVE" for template in templates):
        errors.append("roles.json: domain templates must remain inactive")

    permissions = contracts["permission-matrix.json"]
    tiers = permissions.get("tiers", {})
    if set(tiers) != {"A0", "A1", "A2", "A3", "A4", "A5", "A6", "AX"}:
        errors.append("permission-matrix.json: access tiers must be exactly A0-A6 and AX")
    if permissions.get("default_outcome") != "DENY":
        errors.append("permission-matrix.json: default outcome must be DENY")
    capabilities = permissions.get("capabilities", {})
    for name, capability in capabilities.items():
        if capability.get("maximum_tier") == "A6":
            if capability.get("human_gate_required") is not True or capability.get("no_standing_agent_permission") is not True:
                errors.append(f"permission-matrix.json: A6 capability {name} must require a Human Gate and prohibit standing access")
    permission_rows = permissions.get("role_permissions", [])
    permission_role_ids = [row.get("role_id") for row in permission_rows]
    if set(permission_role_ids) != role_id_set or len(permission_role_ids) != len(role_id_set):
        errors.append("permission-matrix.json: role permissions must cover each permanent role exactly once")
    role_by_id = {role["role_id"]: role for role in roles if "role_id" in role}
    for row in permission_rows:
        role_id = row.get("role_id")
        all_tiers = row.get("default_tiers", []) + row.get("temporary_tiers", [])
        if "A6" in all_tiers:
            errors.append(f"permission-matrix.json: {role_id} may not receive A6")
        if any(tier not in tiers or tier == "AX" for tier in all_tiers):
            errors.append(f"permission-matrix.json: {role_id} has an invalid granted tier")
        if role_id in role_by_id and row.get("default_tiers") != role_by_id[role_id].get("default_access_tiers"):
            errors.append(f"permission-matrix.json: {role_id} default tiers disagree with role catalog")
    for role in roles:
        for capability in role.get("capabilities", []):
            if capability not in capabilities:
                errors.append(f"roles.json: {role.get('role_id')} references unknown capability {capability}")

    required_schema_fields = {
        "agent-manifest.schema.json": {"manifest_id", "role_id", "actor_instance_id", "task_id", "scope", "budget", "expires_at", "status"},
        "task.schema.json": {"task_id", "parent_task_id", "role_id", "actor_instance_id", "permissions", "acceptance_criteria", "status"},
        "response.schema.json": {"response_id", "task_id", "role_id", "actor_instance_id", "status", "evidence", "authority_used", "human_required"},
    }
    for name, expected in required_schema_fields.items():
        schema = contracts[name]
        if schema.get("additionalProperties") is not False:
            errors.append(f"{name}: unknown top-level fields must be rejected")
        if not expected <= set(schema.get("required", [])):
            errors.append(f"{name}: required lineage or control fields are missing")
    manifest_tiers = contracts["agent-manifest.schema.json"].get("properties", {}).get("requested_access_tiers", {}).get("items", {}).get("enum", [])
    if "A6" in manifest_tiers or "AX" in manifest_tiers:
        errors.append("agent-manifest.schema.json: manifests may not request A6 or AX")
    manifest_conditionals = contracts["agent-manifest.schema.json"].get("allOf", [])
    case_scope_enforced = any(
        conditional.get("then", {})
        .get("properties", {})
        .get("scope", {})
        .get("properties", {})
        .get("case_context", {})
        .get("type")
        == "object"
        for conditional in manifest_conditionals
    )
    if not case_scope_enforced:
        errors.append("agent-manifest.schema.json: A3/A4 requests must require case context")
    response_statuses = set(contracts["response.schema.json"].get("properties", {}).get("status", {}).get("enum", []))
    if response_statuses != {"PASS", "BLOCKED", "HUMAN_REQUIRED", "FAILED", "EXPIRED", "CANCELLED"}:
        errors.append("response.schema.json: terminal response statuses disagree with the organization contract")

    lifecycle = contracts["lifecycle.json"]
    states = set(lifecycle.get("states", []))
    terminal = set(lifecycle.get("terminal_states", []))
    transitions = lifecycle.get("transitions", {})
    if set(transitions) != states:
        errors.append("lifecycle.json: every state must define transitions")
    for source, destinations in transitions.items():
        unknown = set(destinations) - states
        if unknown:
            errors.append(f"lifecycle.json: {source} references unknown states")
    if any(transitions.get(state) for state in terminal):
        errors.append("lifecycle.json: terminal states may not have outgoing transitions")
    if "ACTIVE" not in _reachable(transitions, lifecycle.get("initial_state", "")):
        errors.append("lifecycle.json: ACTIVE must be reachable from the initial state")
    if lifecycle.get("rules", {}).get("terminal_state_reuse") != "PROHIBITED":
        errors.append("lifecycle.json: terminal instance reuse must be prohibited")

    gates = contracts["human-gates.json"]
    if not EXPECTED_GATE_TRIGGERS <= set(gates.get("mandatory_gate_triggers", [])):
        errors.append("human-gates.json: mandatory Human Gate triggers are incomplete")
    transfer = gates.get("external_transfer", {})
    if transfer.get("ordered_stages") != ["CONTENT_RELEASE_APPROVAL", "DESTINATION_TRANSMISSION_APPROVAL"]:
        errors.append("human-gates.json: external-transfer approval stages must remain ordered")
    if transfer.get("stages_must_be_separate_events") is not True or transfer.get("combined_approval_prohibited") is not True:
        errors.append("human-gates.json: the two external-transfer approvals must be separate")
    stage_two_bindings = transfer.get("destination_transmission_approval", {}).get("required_bindings", [])
    if "content_release_approval_id" not in stage_two_bindings:
        errors.append("human-gates.json: destination approval must bind to content release approval")
    coi = gates.get("conflict_of_interest_rules", [])
    if len(coi) < 10 or not any(rule.get("actor_role") == "IMPLEMENTATION_AGENT" and rule.get("prohibited_review_role") == "INDEPENDENT_ACCEPTANCE_AGENT" for rule in coi):
        errors.append("human-gates.json: separation-of-duties rules are incomplete")

    execution = contracts["execution-policy.json"]
    defaults = execution.get("default_limits", {})
    hard = execution.get("hard_limits", {})
    required_budget = set(execution.get("required_budget_fields", []))
    if required_budget != set(defaults) or required_budget != set(hard):
        errors.append("execution-policy.json: default and hard budget fields must match the required set")
    for field in required_budget:
        if not isinstance(defaults.get(field), (int, float)) or defaults[field] <= 0:
            errors.append(f"execution-policy.json: default {field} must be positive")
        elif not isinstance(hard.get(field), (int, float)) or hard[field] < defaults[field]:
            errors.append(f"execution-policy.json: hard {field} must be at least the default")
    if execution.get("budget_exhaustion_outcome") != "BLOCKED":
        errors.append("execution-policy.json: budget exhaustion must block")
    kill_switch = execution.get("kill_switch", {})
    required_kill_switch = ("fail_closed_on_unknown_state", "halt_blocks_new_dispatch", "halt_stops_active_continuation", "halt_revokes_temporary_permissions", "halt_preserves_audit_and_evidence")
    if not all(kill_switch.get(field) is True for field in required_kill_switch):
        errors.append("execution-policy.json: kill switch must stop safely and preserve evidence")
    if execution.get("activation_boundary") != "POLICY_ONLY_NO_RUNTIME_ACTIVATION":
        errors.append("execution-policy.json: O2 must not activate runtime authority")

    return errors


def main() -> int:
    repository_root = Path(__file__).resolve().parents[1]
    try:
        contracts = load_contracts(repository_root)
        errors = validate_contracts(contracts)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors = [str(exc)]
    if errors:
        print(json.dumps({"status": "BLOCKED", "errors": errors}, indent=2, sort_keys=True))
        return 2
    print(json.dumps({"status": "PASS", "contract_set": "ORCHESTRATOR_CONTRACT_SET_V1"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
