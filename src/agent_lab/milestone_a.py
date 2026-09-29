"""Fail-closed Milestone A contract loading and Kernel registration."""

from __future__ import annotations

import hashlib
import importlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .orchestrator_kernel import ContractError, OrchestratorKernel

AUTHORITY_ID = "AUTH-MILESTONE-A-20260927-001"
AUTHORITY_REFERENCE = "MILESTONE-A-20260927-001"
EXPECTED_AUTHORITY_HASH = "sha256:2a6d89b6c350b5a1b653bfb7b8b1ddf472188785104389967786e23d97249d09"
EXPECTED_JOURNEY_HASH = "sha256:62fea6ef5936cb6897b7ff54a37a43ba98bc90e6adbae20b1c5e9bb64565d6ad"
JOURNEY_STAGES = (
    "CREATE_CASE", "INTAKE", "PROCESS", "SPECIALIST_REVIEW", "CHIEF_REVIEW",
    "CALCULATION", "FORM_PREVIEW", "APPROVAL_STAGE_1", "APPROVAL_STAGE_2",
    "SYNTHETIC_SUBMISSION", "RECEIPT", "RECOVERY",
)
JOURNEY_FIELDS = {"schema_version", "contract_id", "authority_reference", "data_class", "stages", "required_identities", "blocked_capabilities", "acceptance"}
STAGE_FIELDS = {"stage_id", "sequence", "component", "status", "depends_on"}
BLOCKED = {"real_data", "provider_credentials", "manufacturer_id", "certificates", "protected_document_copying", "official_eric_execution", "signing", "networking", "elster_finanzamt_contact", "external_transfer", "production", "protected_main", "release", "destructive_action", "duplicate_orchestrator_bridge_scheduler", "general_purpose_shell"}
REQUIRED_IDENTITIES = ["case_id", "tax_year", "run_id", "artifact_identity"]
ACCEPTANCE = ["closed_stage_catalog", "exact_component_reuse", "dependency_order", "unknown_field_rejected", "unsupported_capability_rejected"]


def canonical_hash(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def load_json(path: Path | str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ContractError("contract root must be an object")
    return payload


def validate_golden_journey(payload: dict[str, Any]) -> str:
    if set(payload) != JOURNEY_FIELDS:
        raise ContractError("golden journey fields are not exact")
    if payload["schema_version"] != 1 or payload["contract_id"] != "MILESTONE_A_GOLDEN_JOURNEY_V1" or payload["authority_reference"] != AUTHORITY_REFERENCE or payload["data_class"] != "SYNTHETIC_LOCAL_ONLY":
        raise ContractError("golden journey identity or data boundary changed")
    stages = payload["stages"]
    if not isinstance(stages, list) or tuple(item.get("stage_id") for item in stages) != JOURNEY_STAGES:
        raise ContractError("golden journey stage catalog/order changed")
    seen: set[str] = set()
    for sequence, stage in enumerate(stages, 1):
        if not isinstance(stage, dict) or set(stage) != STAGE_FIELDS:
            raise ContractError("golden journey stage fields are not exact")
        if stage["sequence"] != sequence or stage["status"] not in {"REUSE", "COMPOSE"}:
            raise ContractError("golden journey sequence/status is invalid")
        if set(stage["depends_on"]) - seen:
            raise ContractError("golden journey dependency is not prior")
        module_name, symbol = stage["component"].rsplit(".", 1)
        if not hasattr(importlib.import_module(module_name), symbol):
            raise ContractError(f"golden journey component is unavailable: {stage['component']}")
        seen.add(stage["stage_id"])
    if set(payload["blocked_capabilities"]) != BLOCKED:
        raise ContractError("golden journey capability boundary changed")
    if payload["required_identities"] != REQUIRED_IDENTITIES or payload["acceptance"] != ACCEPTANCE:
        raise ContractError("golden journey identity/acceptance boundary changed")
    digest = canonical_hash(payload)
    if digest != EXPECTED_JOURNEY_HASH:
        raise ContractError("golden journey hash does not match the Owner-approved contract")
    return digest


def materialize_task(template: dict[str, Any], authority: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    issued = now or datetime.now(timezone.utc)
    return {
        "schema_version": 1,
        "task_id": "TASK-" + template["package_id"].removeprefix("PKG-"),
        "parent_task_id": None,
        "objective": template["objective"],
        "role_id": template["role_id"],
        "actor_instance_id": template["actor_instance_id"],
        "repository": authority["repository"],
        "ref": authority["ref"],
        "case_context": None,
        "inputs": template["inputs"],
        "expected_outputs": template["expected_outputs"],
        "allowed_tools": template["allowed_tools"],
        "permissions": template["permissions"],
        "forbidden_actions": template["forbidden_actions"],
        "budget": template["budget"],
        "timeout_seconds": template["timeout_seconds"],
        "max_retries": template["max_retries"],
        "acceptance_criteria": template["acceptance_criteria"],
        "stop_conditions": template["stop_conditions"],
        "escalation_route": template["escalation_route"],
        "created_at": issued.isoformat(),
        "expires_at": (issued + timedelta(hours=2)).isoformat(),
        "status": "REGISTERED",
    }


def register_queue(kernel: OrchestratorKernel, authority: dict[str, Any]) -> dict[str, Any]:
    if authority.get("authority_id") != AUTHORITY_ID or authority.get("owner_approval_reference") != AUTHORITY_REFERENCE:
        raise ContractError("Milestone A authority identity changed")
    authority_hash = canonical_hash(authority)
    if authority_hash != EXPECTED_AUTHORITY_HASH:
        raise ContractError("Milestone A authority hash does not match the Owner-approved envelope")
    kernel.register_milestone_authority(authority)
    task_ids = []
    for template in authority["package_templates"]:
        task = materialize_task(template, authority)
        task_ids.append(kernel.register_authorized_package(AUTHORITY_ID, template["package_id"], task))
    ready = kernel.select_ready_package(AUTHORITY_ID)
    if ready is None or ready["package_id"] != "PKG-MA-01-GOLDEN-JOURNEY-CONTRACT":
        raise ContractError("Milestone A queue did not select MA-01 first")
    return {"authority_id": AUTHORITY_ID, "authority_hash": authority_hash, "task_ids": task_ids, "ready_package_id": ready["package_id"]}
