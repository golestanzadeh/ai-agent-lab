from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any

PROTOCOL_VERSION = 1
REQUEST_FIELDS = {
    "protocol_version", "task_id", "sender", "recipient", "repository",
    "ref", "base_commit", "status", "task", "acceptance", "allowed_scope",
    "forbidden_actions", "risk_class",
}
HUMAN_GATE_RISKS = {"architecture", "governance", "security", "consequential", "destructive"}


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    outcome: str
    reason: str


def validate_request(payload: dict[str, Any]) -> ValidationResult:
    missing = sorted(REQUEST_FIELDS - payload.keys())
    if missing:
        return ValidationResult(False, "BLOCKED", f"missing fields: {', '.join(missing)}")
    if payload["protocol_version"] != PROTOCOL_VERSION:
        return ValidationResult(False, "BLOCKED", "unsupported protocol version")
    if payload["status"] != "REQUEST" or payload["sender"] != "work" or payload["recipient"] != "codex":
        return ValidationResult(False, "BLOCKED", "invalid routing/status")
    for key in ("task_id", "repository", "ref", "base_commit", "task", "risk_class"):
        if not isinstance(payload[key], str) or not payload[key].strip():
            return ValidationResult(False, "BLOCKED", f"invalid {key}")
    if not isinstance(payload["acceptance"], list) or not payload["acceptance"]:
        return ValidationResult(False, "BLOCKED", "acceptance must be non-empty")
    if not isinstance(payload["allowed_scope"], list) or not isinstance(payload["forbidden_actions"], list):
        return ValidationResult(False, "BLOCKED", "scope fields must be lists")
    if payload["risk_class"].lower() in HUMAN_GATE_RISKS:
        return ValidationResult(True, "HUMAN_REQUIRED", "risk class requires human authority")
    return ValidationResult(True, "PASSIVE_VALID", "request is structurally valid; no execution authorized")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")
        result = validate_request(payload)
    except Exception as exc:
        result = ValidationResult(False, "BLOCKED", str(exc))
    print(json.dumps(result.__dict__, sort_keys=True))
    return 0 if result.valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
