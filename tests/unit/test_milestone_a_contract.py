from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import pytest

from agent_lab.milestone_a import EXPECTED_AUTHORITY_HASH, EXPECTED_JOURNEY_HASH, canonical_hash, load_json, register_queue, validate_golden_journey
from agent_lab.orchestrator_kernel import ContractError, OrchestratorKernel

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "contracts/orchestrator/v1"
JOURNEY_PATH = ROOT / "contracts/product/milestone-a/v1/golden-journey.json"
AUTHORITY_PATH = CONTRACT_ROOT / "milestone-a-authority.json"


def test_golden_journey_binds_exact_existing_components():
    assert validate_golden_journey(load_json(JOURNEY_PATH)) == EXPECTED_JOURNEY_HASH


def test_golden_journey_rejects_unknown_fields_and_capability_weakening():
    journey = load_json(JOURNEY_PATH)
    unknown = deepcopy(journey)
    unknown["extra"] = True
    with pytest.raises(ContractError, match="fields are not exact"):
        validate_golden_journey(unknown)
    weakened = deepcopy(journey)
    weakened["blocked_capabilities"].remove("external_transfer")
    with pytest.raises(ContractError, match="capability boundary"):
        validate_golden_journey(weakened)
    for field, value in (("contract_id", "ARBITRARY"), ("required_identities", []), ("acceptance", [])):
        mutated = deepcopy(journey)
        mutated[field] = value
        with pytest.raises(ContractError):
            validate_golden_journey(mutated)


def test_authority_registers_five_dependency_ordered_packages(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Prove historical bounded registration inside the authority window. Kernel
    # expiry behavior is tested separately; this regression must not expire with wall time.
    monkeypatch.setattr("agent_lab.orchestrator_kernel._utc_now", lambda: datetime(2026, 9, 28, tzinfo=timezone.utc))
    authority = load_json(AUTHORITY_PATH)
    with OrchestratorKernel(tmp_path / "kernel.sqlite3", CONTRACT_ROOT) as kernel:
        result = register_queue(kernel, authority)
        assert result["ready_package_id"] == "PKG-MA-01-GOLDEN-JOURNEY-CONTRACT"
        assert result["task_ids"] == ["TASK-MA-01-GOLDEN-JOURNEY-CONTRACT", "TASK-MA-02-COMPOSITION-AND-STORE", "TASK-MA-03-INTAKE-REVIEW-DECLARATION", "TASK-MA-04-APPROVAL-SUBMISSION-RECEIPT", "TASK-MA-05-E2E-FAILURE-CI"]
        assert result["authority_hash"] == EXPECTED_AUTHORITY_HASH


def test_authority_rejects_permission_amplification(tmp_path: Path):
    authority = load_json(AUTHORITY_PATH)
    authority["package_templates"][0]["permissions"].append("external_transfer")
    with OrchestratorKernel(tmp_path / "kernel.sqlite3", CONTRACT_ROOT) as kernel:
        with pytest.raises(ContractError, match="hash"):
            register_queue(kernel, authority)


@pytest.mark.parametrize("mutation", ["budget", "timeout", "retry", "replans", "dependency", "criteria", "recovery", "package_id", "exclusion"])
def test_owner_authority_mutations_are_rejected_before_registration(tmp_path: Path, mutation: str):
    authority = load_json(AUTHORITY_PATH)
    template = authority["package_templates"][0]
    if mutation == "budget": template["budget"]["token_limit"] += 1
    elif mutation == "timeout": template["timeout_seconds"] += 1
    elif mutation == "retry": template["max_retries"] = 0
    elif mutation == "replans": authority["max_replans"] = 1
    elif mutation == "dependency": authority["package_templates"][1]["depends_on"] = []
    elif mutation == "criteria": template["acceptance_criteria"].pop()
    elif mutation == "recovery": template["stop_conditions"].pop()
    elif mutation == "package_id": template["package_id"] = "PKG-CHANGED"
    elif mutation == "exclusion": authority["forbidden_actions"].remove("external_transfer")
    assert canonical_hash(authority) != EXPECTED_AUTHORITY_HASH
    with OrchestratorKernel(tmp_path / "kernel.sqlite3", CONTRACT_ROOT) as kernel:
        with pytest.raises(ContractError, match="hash"):
            register_queue(kernel, authority)
