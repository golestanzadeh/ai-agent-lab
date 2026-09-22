"""Deterministic, persistent control kernel for the accepted O2 contracts.

The kernel records and validates authority. It does not execute an Agent, grant a
real tool credential, perform external transfer, or replace a Human Gate.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

KERNEL_SCHEMA_VERSION = 1
CONTRACT_SET_ID = "ORCHESTRATOR_CONTRACT_SET_V1"
ACCEPTED_O2_COMMIT = "382a140e42496ad9edd92dc2016cfde51d091575"
ACCEPTED_O2_DIGEST = "sha256:361c3dbd2e8750fb8985a2d6f52e9330ff42f398cdc792dbd85a2573d831674e"
CONTRACT_FILES = (
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
CONTROL_ROLES = {
    "GOVERNANCE_GUARD_AGENT",
    "SECURITY_PRIVACY_AGENT",
    "INDEPENDENT_ACCEPTANCE_AGENT",
    "AUDIT_CONTINUITY_AGENT",
}


class KernelError(RuntimeError):
    """Base class for fail-closed Kernel errors."""


class ContractError(KernelError):
    """Raised when a contract or payload is missing, malformed, or incompatible."""


class StateTransitionError(KernelError):
    """Raised when a lifecycle transition is not allowed."""


class PermissionDenied(KernelError):
    """Raised when deterministic permission evaluation denies an action."""


class IntegrityError(KernelError):
    """Raised when durable state or audit integrity cannot be proven."""


@dataclass(frozen=True)
class KernelDecision:
    allowed: bool
    outcome: str
    reason: str


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ContractError(f"{field} must be a non-empty date-time string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError(f"{field} must be a valid ISO-8601 date-time") from exc
    if parsed.tzinfo is None:
        raise ContractError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _require_exact_fields(payload: dict[str, Any], expected: set[str], name: str) -> None:
    actual = set(payload)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        details = []
        if missing:
            details.append(f"missing={','.join(missing)}")
        if unknown:
            details.append(f"unknown={','.join(unknown)}")
        raise ContractError(f"{name} schema mismatch ({'; '.join(details)})")


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{field} must be a non-empty string")
    return value


def _require_string_list(value: Any, field: str, *, non_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ContractError(f"{field} must be a list of non-empty strings")
    if non_empty and not value:
        raise ContractError(f"{field} must not be empty")
    if len(value) != len(set(value)):
        raise ContractError(f"{field} must not contain duplicates")
    return value


class OrchestratorKernel:
    """SQLite-backed deterministic state and policy boundary."""

    TASK_FIELDS = {
        "schema_version", "task_id", "parent_task_id", "objective", "role_id",
        "actor_instance_id", "repository", "ref", "case_context", "inputs",
        "expected_outputs", "allowed_tools", "permissions", "forbidden_actions",
        "budget", "timeout_seconds", "max_retries", "acceptance_criteria",
        "stop_conditions", "escalation_route", "created_at", "expires_at", "status",
    }
    MANIFEST_FIELDS = {
        "schema_version", "manifest_id", "role_id", "actor_instance_id", "task_id",
        "parent_task_id", "scope", "inputs", "expected_outputs", "allowed_tools",
        "requested_access_tiers", "requested_capabilities", "forbidden_actions",
        "budget", "timeout_seconds", "max_retries", "stop_conditions",
        "escalation_route", "issued_at", "expires_at", "status",
    }
    RESPONSE_FIELDS = {
        "schema_version", "response_id", "task_id", "parent_task_id", "role_id",
        "actor_instance_id", "status", "result_summary", "artifact_references",
        "changed_paths_or_state", "tests", "evidence", "authority_used", "costs",
        "unresolved_risks", "recommended_next_action", "human_required", "created_at",
    }
    BUDGET_FIELDS = {"token_limit", "tool_call_limit", "cost_limit_usd"}

    def __init__(self, database_path: Path | str, contract_root: Path | str) -> None:
        self.database_path = Path(database_path)
        self.contract_root = Path(contract_root)
        self.contracts = self._load_contracts()
        self.roles = {role["role_id"]: role for role in self.contracts["roles.json"]["roles"]}
        self.permission_rows = {
            row["role_id"]: row
            for row in self.contracts["permission-matrix.json"]["role_permissions"]
        }
        self.capabilities = self.contracts["permission-matrix.json"]["capabilities"]
        self.lifecycle = self.contracts["lifecycle.json"]
        self.execution_policy = self.contracts["execution-policy.json"]
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.database_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._initialize_schema()

    def __enter__(self) -> "OrchestratorKernel":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._connection.close()

    def _load_contracts(self) -> dict[str, dict[str, Any]]:
        loaded: dict[str, dict[str, Any]] = {}
        for filename in CONTRACT_FILES:
            path = self.contract_root / filename
            try:
                with path.open(encoding="utf-8") as handle:
                    payload = json.load(handle)
            except (OSError, json.JSONDecodeError) as exc:
                raise ContractError(f"unable to load {filename}: {exc}") from exc
            if not isinstance(payload, dict):
                raise ContractError(f"{filename} root must be an object")
            loaded[filename] = payload
        contract_set = loaded["contract-set.json"]
        if contract_set.get("schema_version") != 1 or contract_set.get("contract_set_id") != CONTRACT_SET_ID:
            raise ContractError("unsupported contract set")
        declared = {
            Path(entry["path"]).name: entry.get("schema_version")
            for entry in contract_set.get("contracts", [])
            if isinstance(entry, dict) and isinstance(entry.get("path"), str)
        }
        required = set(CONTRACT_FILES) - {"contract-set.json"}
        if set(declared) != required or any(version != 1 for version in declared.values()):
            raise ContractError("contract set is missing, mixed, or incompatible")
        for filename in required:
            if filename.endswith(".schema.json"):
                version = loaded[filename].get("properties", {}).get("schema_version", {}).get("const")
            else:
                version = loaded[filename].get("schema_version")
            if version != 1:
                raise ContractError(f"unsupported {filename} version")
        if _digest(loaded) != ACCEPTED_O2_DIGEST:
            raise ContractError(f"contract set does not match accepted O2 commit {ACCEPTED_O2_COMMIT}")
        return loaded

    def _initialize_schema(self) -> None:
        with self._connection:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS kernel_schema (
                    component TEXT PRIMARY KEY,
                    version INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    parent_task_id TEXT,
                    role_id TEXT NOT NULL,
                    actor_instance_id TEXT NOT NULL,
                    repository TEXT NOT NULL,
                    ref TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    retry_count INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS dependencies (
                    task_id TEXT NOT NULL REFERENCES tasks(task_id),
                    depends_on_task_id TEXT NOT NULL REFERENCES tasks(task_id),
                    PRIMARY KEY(task_id, depends_on_task_id)
                );
                CREATE TABLE IF NOT EXISTS task_human_gates (
                    task_id TEXT NOT NULL REFERENCES tasks(task_id),
                    trigger TEXT NOT NULL,
                    status TEXT NOT NULL,
                    authority_reference TEXT,
                    decided_at TEXT,
                    PRIMARY KEY(task_id, trigger)
                );
                CREATE TABLE IF NOT EXISTS manifests (
                    manifest_id TEXT PRIMARY KEY,
                    actor_instance_id TEXT NOT NULL UNIQUE,
                    task_id TEXT NOT NULL REFERENCES tasks(task_id),
                    role_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    issued_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS budget_usage (
                    manifest_id TEXT PRIMARY KEY REFERENCES manifests(manifest_id),
                    tokens_used INTEGER NOT NULL DEFAULT 0,
                    tool_calls_used INTEGER NOT NULL DEFAULT 0,
                    cost_usd REAL NOT NULL DEFAULT 0,
                    child_tasks_created INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS retry_attempts (
                    attempt_id TEXT PRIMARY KEY,
                    manifest_id TEXT NOT NULL REFERENCES manifests(manifest_id),
                    ordinal INTEGER NOT NULL,
                    failure_class TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(manifest_id, ordinal)
                );
                CREATE TABLE IF NOT EXISTS responses (
                    response_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL REFERENCES tasks(task_id),
                    manifest_id TEXT NOT NULL REFERENCES manifests(manifest_id),
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS acceptance_records (
                    acceptance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL REFERENCES tasks(task_id),
                    reviewer_manifest_id TEXT NOT NULL REFERENCES manifests(manifest_id),
                    reviewer_instance_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    evidence_reference TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS bridge_bindings (
                    task_id TEXT PRIMARY KEY REFERENCES tasks(task_id),
                    bridge_task_id TEXT NOT NULL UNIQUE,
                    base_commit TEXT NOT NULL,
                    allowed_scope_json TEXT NOT NULL,
                    risk_class TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS kill_switch (
                    singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
                    state TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    authority_reference TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    previous_hash TEXT,
                    event_hash TEXT NOT NULL UNIQUE
                );
                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    last_event_id INTEGER NOT NULL,
                    contract_set_id TEXT NOT NULL,
                    snapshot_json TEXT NOT NULL,
                    snapshot_hash TEXT NOT NULL
                );
                """
            )
            row = self._connection.execute(
                "SELECT version FROM kernel_schema WHERE component='orchestrator'"
            ).fetchone()
            if row is None:
                self._connection.execute(
                    "INSERT INTO kernel_schema(component, version) VALUES('orchestrator', ?)",
                    (KERNEL_SCHEMA_VERSION,),
                )
            elif row["version"] != KERNEL_SCHEMA_VERSION:
                raise ContractError("unsupported orchestrator database schema")
            created = self._connection.execute(
                "INSERT OR IGNORE INTO kill_switch(singleton, state, updated_at, authority_reference) VALUES(1, 'HALTED', ?, 'SYSTEM_SAFE_DEFAULT')",
                (_utc_now().isoformat(),),
            ).rowcount
            if created:
                self._append_event(
                    "KILL_SWITCH_INITIALIZED", "KILL_SWITCH", "GLOBAL", "SYSTEM",
                    {"state": "HALTED", "reason": "fail-closed initial state"},
                )

    def _append_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str,
        actor_id: str,
        payload: dict[str, Any],
    ) -> int:
        previous = self._connection.execute(
            "SELECT event_hash FROM audit_events ORDER BY event_id DESC LIMIT 1"
        ).fetchone()
        previous_hash = previous["event_hash"] if previous else None
        occurred_at = _utc_now().isoformat()
        event_body = {
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "occurred_at": occurred_at,
            "actor_id": actor_id,
            "payload": payload,
            "previous_hash": previous_hash,
        }
        event_hash = _digest(event_body)
        cursor = self._connection.execute(
            """
            INSERT INTO audit_events(
                event_type, entity_type, entity_id, occurred_at, actor_id,
                payload_json, previous_hash, event_hash
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_type, entity_type, entity_id, occurred_at, actor_id,
                _canonical(payload), previous_hash, event_hash,
            ),
        )
        return int(cursor.lastrowid)

    def verify_audit_chain(self) -> None:
        previous_hash: str | None = None
        rows = self._connection.execute(
            "SELECT * FROM audit_events ORDER BY event_id"
        ).fetchall()
        for row in rows:
            payload = json.loads(row["payload_json"])
            event_body = {
                "event_type": row["event_type"],
                "entity_type": row["entity_type"],
                "entity_id": row["entity_id"],
                "occurred_at": row["occurred_at"],
                "actor_id": row["actor_id"],
                "payload": payload,
                "previous_hash": previous_hash,
            }
            if row["previous_hash"] != previous_hash or row["event_hash"] != _digest(event_body):
                raise IntegrityError(f"audit chain failed at event {row['event_id']}")
            previous_hash = row["event_hash"]

    def _validate_budget(self, budget: Any, timeout_seconds: Any, max_retries: Any) -> None:
        if not isinstance(budget, dict):
            raise ContractError("budget must be an object")
        _require_exact_fields(budget, self.BUDGET_FIELDS, "budget")
        values = {
            "token_limit": budget["token_limit"],
            "tool_call_limit": budget["tool_call_limit"],
            "cost_limit_usd": budget["cost_limit_usd"],
            "timeout_seconds": timeout_seconds,
            "max_retries": max_retries,
        }
        defaults = self.execution_policy["hard_limits"]
        for field, value in values.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                raise ContractError(f"{field} must be a non-negative number")
            if field != "max_retries" and value == 0:
                raise ContractError(f"{field} must be positive")
            if value > defaults[field]:
                raise ContractError(f"{field} exceeds hard policy limit")

    def _validate_case_context(self, context: Any) -> None:
        if context is None:
            return
        if not isinstance(context, dict):
            raise ContractError("case_context must be null or an object")
        _require_exact_fields(context, {"case_id", "tax_year", "run_id"}, "case_context")
        _require_string(context["case_id"], "case_id")
        _require_string(context["run_id"], "run_id")
        if isinstance(context["tax_year"], bool) or not isinstance(context["tax_year"], int):
            raise ContractError("tax_year must be an integer")

    def _validate_task_payload(self, payload: dict[str, Any]) -> None:
        _require_exact_fields(payload, self.TASK_FIELDS, "task")
        if payload.get("schema_version") != 1 or payload.get("status") != "REGISTERED":
            raise ContractError("task version/status is unsupported")
        for field in ("task_id", "objective", "role_id", "actor_instance_id", "repository", "ref"):
            _require_string(payload[field], field)
        if payload["role_id"] not in self.roles:
            raise ContractError("unknown role_id")
        if payload["parent_task_id"] is not None:
            _require_string(payload["parent_task_id"], "parent_task_id")
        self._validate_case_context(payload["case_context"])
        for field in ("inputs", "allowed_tools", "permissions"):
            _require_string_list(payload[field], field)
        for field in ("expected_outputs", "forbidden_actions", "acceptance_criteria", "stop_conditions", "escalation_route"):
            _require_string_list(payload[field], field, non_empty=True)
        unknown_permissions = set(payload["permissions"]) - set(self.capabilities)
        if unknown_permissions:
            raise ContractError("task requests unknown permissions")
        if not set(payload["permissions"]) <= set(self.roles[payload["role_id"]]["capabilities"]):
            raise ContractError("task permissions exceed role capabilities")
        self._validate_budget(payload["budget"], payload["timeout_seconds"], payload["max_retries"])
        created_at = _parse_timestamp(payload["created_at"], "created_at")
        expires_at = _parse_timestamp(payload["expires_at"], "expires_at")
        if expires_at <= created_at or expires_at <= _utc_now():
            raise ContractError("task expiry must be after creation and in the future")

    def register_task(
        self,
        payload: dict[str, Any],
        *,
        gate_triggers: Iterable[str],
        depends_on: Iterable[str] = (),
        actor_id: str = "MASTER_PROJECT_ORCHESTRATOR",
    ) -> str:
        self._validate_task_payload(payload)
        dependencies = tuple(depends_on)
        triggers = tuple(gate_triggers)
        if len(dependencies) != len(set(dependencies)):
            raise ContractError("dependencies must be unique")
        if len(triggers) != len(set(triggers)):
            raise ContractError("Human Gate triggers must be unique")
        allowed_triggers = set(self.contracts["human-gates.json"]["mandatory_gate_triggers"])
        if not set(triggers) <= allowed_triggers:
            raise ContractError("unknown Human Gate trigger")
        if payload["task_id"] in dependencies:
            raise ContractError("task cannot depend on itself")
        with self._connection:
            if payload["parent_task_id"] is not None and self._connection.execute(
                "SELECT 1 FROM tasks WHERE task_id=?", (payload["parent_task_id"],)
            ).fetchone() is None:
                raise ContractError("parent task is not registered")
            for dependency in dependencies:
                if self._connection.execute(
                    "SELECT 1 FROM tasks WHERE task_id=?", (dependency,)
                ).fetchone() is None:
                    raise ContractError(f"dependency {dependency} is not registered")
            try:
                self._connection.execute(
                    """
                    INSERT INTO tasks(
                        task_id, parent_task_id, role_id, actor_instance_id,
                        repository, ref, status, payload_json, created_at, expires_at
                    ) VALUES(?, ?, ?, ?, ?, ?, 'REGISTERED', ?, ?, ?)
                    """,
                    (
                        payload["task_id"], payload["parent_task_id"], payload["role_id"],
                        payload["actor_instance_id"], payload["repository"], payload["ref"],
                        _canonical(payload), payload["created_at"], payload["expires_at"],
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise ContractError("task identity already exists") from exc
            for dependency in dependencies:
                self._connection.execute(
                    "INSERT INTO dependencies(task_id, depends_on_task_id) VALUES(?, ?)",
                    (payload["task_id"], dependency),
                )
            for trigger in triggers:
                self._connection.execute(
                    "INSERT INTO task_human_gates(task_id, trigger, status) VALUES(?, ?, 'PENDING')",
                    (payload["task_id"], trigger),
                )
            if triggers:
                self._connection.execute(
                    "UPDATE tasks SET status='HUMAN_REQUIRED' WHERE task_id=?",
                    (payload["task_id"],),
                )
            self._append_event(
                "TASK_REGISTERED", "TASK", payload["task_id"], actor_id,
                {"role_id": payload["role_id"], "dependencies": list(dependencies), "human_gate_triggers": list(triggers)},
            )
        return payload["task_id"]

    def record_human_gate_decision(
        self,
        task_id: str,
        trigger: str,
        decision: str,
        *,
        actor_id: str,
        authority_reference: str,
    ) -> None:
        if actor_id != "HUMAN_PROJECT_OWNER":
            raise PermissionDenied("only Human authority may decide a Human Gate")
        if decision not in {"APPROVED", "REJECTED"}:
            raise ContractError("Human Gate decision must be APPROVED or REJECTED")
        _require_string(authority_reference, "authority_reference")
        with self._connection:
            gate = self._connection.execute(
                "SELECT status FROM task_human_gates WHERE task_id=? AND trigger=?",
                (task_id, trigger),
            ).fetchone()
            if gate is None:
                raise ContractError("Human Gate is not registered for task")
            if gate["status"] != "PENDING":
                raise StateTransitionError("Human Gate already has a terminal decision")
            self._connection.execute(
                "UPDATE task_human_gates SET status=?, authority_reference=?, decided_at=? WHERE task_id=? AND trigger=?",
                (decision, authority_reference, _utc_now().isoformat(), task_id, trigger),
            )
            if decision == "REJECTED":
                task_status = "REJECTED"
            else:
                remaining = self._connection.execute(
                    "SELECT COUNT(*) AS count FROM task_human_gates WHERE task_id=? AND status='PENDING'",
                    (task_id,),
                ).fetchone()["count"]
                task_status = "REGISTERED" if remaining == 0 else "HUMAN_REQUIRED"
            self._connection.execute(
                "UPDATE tasks SET status=? WHERE task_id=? AND status='HUMAN_REQUIRED'",
                (task_status, task_id),
            )
            self._append_event(
                "HUMAN_GATE_DECIDED", "TASK", task_id, actor_id,
                {"trigger": trigger, "decision": decision, "authority_reference": authority_reference},
            )

    def add_dependency(self, task_id: str, depends_on_task_id: str) -> None:
        if task_id == depends_on_task_id:
            raise ContractError("task cannot depend on itself")
        with self._connection:
            for value in (task_id, depends_on_task_id):
                if self._connection.execute("SELECT 1 FROM tasks WHERE task_id=?", (value,)).fetchone() is None:
                    raise ContractError(f"task {value} is not registered")
            if self._path_exists(depends_on_task_id, task_id):
                raise ContractError("dependency would create a cycle")
            try:
                self._connection.execute(
                    "INSERT INTO dependencies(task_id, depends_on_task_id) VALUES(?, ?)",
                    (task_id, depends_on_task_id),
                )
            except sqlite3.IntegrityError as exc:
                raise ContractError("dependency already exists") from exc
            self._append_event(
                "DEPENDENCY_ADDED", "TASK", task_id, "MASTER_PROJECT_ORCHESTRATOR",
                {"depends_on_task_id": depends_on_task_id},
            )

    def _path_exists(self, start: str, target: str) -> bool:
        pending = [start]
        visited: set[str] = set()
        while pending:
            current = pending.pop()
            if current == target:
                return True
            if current in visited:
                continue
            visited.add(current)
            rows = self._connection.execute(
                "SELECT depends_on_task_id FROM dependencies WHERE task_id=?", (current,)
            ).fetchall()
            pending.extend(row["depends_on_task_id"] for row in rows)
        return False

    def _validate_manifest_payload(self, payload: dict[str, Any]) -> sqlite3.Row:
        _require_exact_fields(payload, self.MANIFEST_FIELDS, "manifest")
        if payload.get("schema_version") != 1 or payload.get("status") != "PROPOSED":
            raise ContractError("manifest must be version 1 in PROPOSED state")
        for field in ("manifest_id", "role_id", "actor_instance_id", "task_id"):
            _require_string(payload[field], field)
        task = self._connection.execute(
            "SELECT * FROM tasks WHERE task_id=?", (payload["task_id"],)
        ).fetchone()
        if task is None:
            raise ContractError("manifest task is not registered")
        task_payload = json.loads(task["payload_json"])
        if task["status"] != "REGISTERED":
            raise PermissionDenied("task is not registered for execution; Human Gate or terminal state applies")
        for field in ("role_id", "actor_instance_id", "parent_task_id"):
            if payload[field] != task_payload[field]:
                raise ContractError(f"manifest {field} does not match task")
        if not isinstance(payload["scope"], dict):
            raise ContractError("scope must be an object")
        _require_exact_fields(payload["scope"], {"repository", "ref", "allowed_paths", "case_context"}, "scope")
        if payload["scope"]["repository"] != task_payload["repository"] or payload["scope"]["ref"] != task_payload["ref"]:
            raise ContractError("manifest repository/ref does not match task")
        _require_string_list(payload["scope"]["allowed_paths"], "allowed_paths")
        self._validate_case_context(payload["scope"]["case_context"])
        if payload["scope"]["case_context"] != task_payload["case_context"]:
            raise ContractError("manifest case context does not match task")
        bridge = self._connection.execute(
            "SELECT allowed_scope_json FROM bridge_bindings WHERE task_id=?", (payload["task_id"],)
        ).fetchone()
        if bridge is not None and not set(payload["scope"]["allowed_paths"]) <= set(json.loads(bridge["allowed_scope_json"])):
            raise ContractError("manifest paths exceed Agent Bridge allowed scope")
        for field in ("inputs", "allowed_tools", "requested_access_tiers", "requested_capabilities"):
            _require_string_list(payload[field], field)
        for field in ("expected_outputs", "forbidden_actions", "stop_conditions", "escalation_route"):
            _require_string_list(payload[field], field, non_empty=True)
        if not set(payload["inputs"]) <= set(task_payload["inputs"]):
            raise ContractError("manifest inputs exceed task inputs")
        if not set(payload["expected_outputs"]) <= set(task_payload["expected_outputs"]):
            raise ContractError("manifest outputs exceed task outputs")
        if not set(payload["allowed_tools"]) <= set(task_payload["allowed_tools"]):
            raise ContractError("manifest tools exceed task tools")
        if not set(task_payload["forbidden_actions"]) <= set(payload["forbidden_actions"]):
            raise ContractError("manifest weakens task forbidden actions")
        role_id = payload["role_id"]
        role = self.roles.get(role_id)
        if role is None:
            raise ContractError("unknown manifest role")
        if not set(payload["requested_capabilities"]) <= set(role["capabilities"]):
            raise ContractError("manifest capabilities exceed role")
        if not set(payload["requested_capabilities"]) <= set(task_payload["permissions"]):
            raise ContractError("manifest capabilities exceed task")
        permission_row = self.permission_rows[role_id]
        permitted_tiers = set(permission_row.get("default_tiers", [])) | set(permission_row.get("temporary_tiers", []))
        requested_tiers = set(payload["requested_access_tiers"])
        if {"A6", "AX"} & requested_tiers or not requested_tiers <= permitted_tiers:
            raise PermissionDenied("manifest requests a denied access tier")
        if {"A3", "A4"} & requested_tiers and payload["scope"]["case_context"] is None:
            raise PermissionDenied("case tiers require exact case_id, tax_year, and run_id")
        self._validate_budget(payload["budget"], payload["timeout_seconds"], payload["max_retries"])
        for field in self.BUDGET_FIELDS:
            if payload["budget"][field] > task_payload["budget"][field]:
                raise ContractError(f"manifest {field} exceeds task")
        if payload["timeout_seconds"] > task_payload["timeout_seconds"] or payload["max_retries"] > task_payload["max_retries"]:
            raise ContractError("manifest timeout/retries exceed task")
        issued_at = _parse_timestamp(payload["issued_at"], "issued_at")
        expires_at = _parse_timestamp(payload["expires_at"], "expires_at")
        if expires_at <= issued_at or expires_at <= _utc_now():
            raise ContractError("manifest expiry must be after issue and in the future")
        if expires_at > _parse_timestamp(task_payload["expires_at"], "task.expires_at"):
            raise ContractError("manifest expiry exceeds task expiry")
        return task

    def register_manifest(self, payload: dict[str, Any]) -> str:
        self._validate_manifest_payload(payload)
        with self._connection:
            try:
                self._connection.execute(
                    """
                    INSERT INTO manifests(
                        manifest_id, actor_instance_id, task_id, role_id, state,
                        payload_json, issued_at, expires_at
                    ) VALUES(?, ?, ?, ?, 'PROPOSED', ?, ?, ?)
                    """,
                    (
                        payload["manifest_id"], payload["actor_instance_id"], payload["task_id"],
                        payload["role_id"], _canonical(payload), payload["issued_at"], payload["expires_at"],
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise ContractError("manifest or actor instance identity already exists") from exc
            self._connection.execute(
                "INSERT INTO budget_usage(manifest_id) VALUES(?)", (payload["manifest_id"],)
            )
            self._append_event(
                "MANIFEST_REGISTERED", "MANIFEST", payload["manifest_id"],
                "AGENT_FACTORY_SUPERVISOR", {"task_id": payload["task_id"], "role_id": payload["role_id"]},
            )
        return payload["manifest_id"]

    def validate_manifest(self, manifest_id: str) -> KernelDecision:
        row = self._manifest_row(manifest_id)
        if row["state"] != "PROPOSED":
            raise StateTransitionError("only PROPOSED manifests can be validated")
        payload = json.loads(row["payload_json"])
        self._validate_manifest_payload(payload)
        self.transition_manifest(
            manifest_id, "VALIDATED", actor_id="AGENT_FACTORY_KERNEL",
            reason="schema, role, task, permission, budget, expiry, and conflict inputs validated",
        )
        return KernelDecision(True, "VALIDATED", "manifest satisfies deterministic O2 controls")

    def _manifest_row(self, manifest_id: str) -> sqlite3.Row:
        row = self._connection.execute(
            "SELECT * FROM manifests WHERE manifest_id=?", (manifest_id,)
        ).fetchone()
        if row is None:
            raise ContractError("manifest is not registered")
        return row

    def transition_manifest(self, manifest_id: str, new_state: str, *, actor_id: str, reason: str) -> None:
        _require_string(reason, "transition reason")
        row = self._manifest_row(manifest_id)
        current = row["state"]
        transitions = self.lifecycle["transitions"]
        if new_state not in self.lifecycle["states"] or new_state not in transitions.get(current, []):
            raise StateTransitionError(f"transition {current}->{new_state} is not allowed")
        with self._connection:
            updated = self._connection.execute(
                "UPDATE manifests SET state=? WHERE manifest_id=? AND state=?",
                (new_state, manifest_id, current),
            ).rowcount
            if updated != 1:
                raise StateTransitionError("manifest state changed concurrently")
            self._append_event(
                "MANIFEST_STATE_CHANGED", "MANIFEST", manifest_id, actor_id,
                {"from": current, "to": new_state, "reason": reason},
            )

    def activate_manifest(self, manifest_id: str) -> KernelDecision:
        row = self._manifest_row(manifest_id)
        if row["state"] != "VALIDATED":
            raise StateTransitionError("manifest must be VALIDATED before activation")
        if self.kill_switch_state() != "RUNNING":
            raise PermissionDenied("kill switch is not RUNNING")
        if _parse_timestamp(row["expires_at"], "expires_at") <= _utc_now():
            self.transition_manifest(manifest_id, "EXPIRED", actor_id="AGENT_FACTORY_KERNEL", reason="manifest expired")
            raise PermissionDenied("manifest expired")
        unmet = self._connection.execute(
            """
            SELECT d.depends_on_task_id
            FROM dependencies d JOIN tasks t ON t.task_id=d.depends_on_task_id
            WHERE d.task_id=? AND t.status!='COMPLETED'
            """,
            (row["task_id"],),
        ).fetchall()
        if unmet:
            raise PermissionDenied("task dependencies are not complete")
        self.transition_manifest(
            manifest_id, "ACTIVE", actor_id="AGENT_FACTORY_KERNEL",
            reason="all deterministic activation requirements passed",
        )
        with self._connection:
            self._connection.execute(
                "UPDATE tasks SET status='ACTIVE' WHERE task_id=? AND status='REGISTERED'",
                (row["task_id"],),
            )
            self._append_event(
                "TASK_ACTIVATED", "TASK", row["task_id"], "AGENT_FACTORY_KERNEL",
                {"manifest_id": manifest_id},
            )
        return KernelDecision(True, "ACTIVE", "synthetic Kernel state activated; no external capability issued")

    def record_acceptance(
        self,
        task_id: str,
        reviewer_manifest_id: str,
        decision: str,
        *,
        evidence_reference: str,
    ) -> None:
        if decision not in {"PASS", "BLOCKED", "HUMAN_REQUIRED"}:
            raise ContractError("acceptance decision must be PASS, BLOCKED, or HUMAN_REQUIRED")
        _require_string(evidence_reference, "evidence_reference")
        target = self._connection.execute(
            "SELECT * FROM tasks WHERE task_id=?", (task_id,)
        ).fetchone()
        if target is None or target["status"] != "AWAITING_ACCEPTANCE":
            raise StateTransitionError("task is not awaiting independent acceptance")
        reviewer = self._manifest_row(reviewer_manifest_id)
        if reviewer["state"] != "ACTIVE" or reviewer["role_id"] != "INDEPENDENT_ACCEPTANCE_AGENT":
            raise PermissionDenied("an active Independent Acceptance manifest is required")
        reviewer_task = self._connection.execute(
            "SELECT * FROM tasks WHERE task_id=?", (reviewer["task_id"],)
        ).fetchone()
        if reviewer_task["parent_task_id"] != task_id:
            raise ContractError("acceptance task must be a registered child of the reviewed task")
        if reviewer["actor_instance_id"] == target["actor_instance_id"]:
            raise PermissionDenied("implementer cannot review its own task")
        target_status = "COMPLETED" if decision == "PASS" else decision
        with self._connection:
            self._connection.execute(
                "INSERT INTO acceptance_records(task_id, reviewer_manifest_id, reviewer_instance_id, decision, evidence_reference, created_at) VALUES(?, ?, ?, ?, ?, ?)",
                (
                    task_id, reviewer_manifest_id, reviewer["actor_instance_id"], decision,
                    evidence_reference, _utc_now().isoformat(),
                ),
            )
            self._connection.execute(
                "UPDATE tasks SET status=? WHERE task_id=? AND status='AWAITING_ACCEPTANCE'",
                (target_status, task_id),
            )
            self._connection.execute(
                "UPDATE tasks SET status='COMPLETED' WHERE task_id=? AND status='ACTIVE'",
                (reviewer["task_id"],),
            )
            self._connection.execute(
                "UPDATE manifests SET state='COMPLETED' WHERE manifest_id=? AND state='ACTIVE'",
                (reviewer_manifest_id,),
            )
            self._append_event(
                "INDEPENDENT_ACCEPTANCE_RECORDED", "TASK", task_id, reviewer["actor_instance_id"],
                {"decision": decision, "evidence_reference": evidence_reference, "reviewer_manifest_id": reviewer_manifest_id},
            )

    def record_response(self, manifest_id: str, payload: dict[str, Any]) -> str:
        _require_exact_fields(payload, self.RESPONSE_FIELDS, "response")
        if payload.get("schema_version") != 1:
            raise ContractError("unsupported response version")
        for field in ("response_id", "task_id", "role_id", "actor_instance_id", "result_summary", "recommended_next_action"):
            _require_string(payload[field], field)
        allowed_statuses = {"PASS", "BLOCKED", "HUMAN_REQUIRED", "FAILED", "EXPIRED", "CANCELLED"}
        if payload["status"] not in allowed_statuses:
            raise ContractError("unsupported response status")
        if payload["status"] == "HUMAN_REQUIRED" and payload["human_required"] is not True:
            raise ContractError("HUMAN_REQUIRED response must set human_required=true")
        if not isinstance(payload["human_required"], bool):
            raise ContractError("human_required must be boolean")
        for field in ("artifact_references", "changed_paths_or_state", "evidence", "unresolved_risks"):
            _require_string_list(payload[field], field)
        _require_string_list(payload["authority_used"], "authority_used", non_empty=True)
        if not isinstance(payload["tests"], list):
            raise ContractError("tests must be a list")
        for test in payload["tests"]:
            if not isinstance(test, dict):
                raise ContractError("test result must be an object")
            _require_exact_fields(test, {"name", "outcome", "evidence_reference"}, "test result")
            _require_string(test["name"], "test name")
            if test["outcome"] not in {"PASS", "FAIL", "SKIPPED", "NOT_RUN"}:
                raise ContractError("unknown test outcome")
        if payload["status"] == "PASS" and any(test["outcome"] == "FAIL" for test in payload["tests"]):
            raise ContractError("PASS response cannot contain failed test evidence")
        costs = payload["costs"]
        if not isinstance(costs, dict):
            raise ContractError("response costs must be an object")
        _require_exact_fields(costs, {"tokens_used", "tool_calls_used", "cost_usd"}, "response costs")
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0 for value in costs.values()):
            raise ContractError("response costs must be non-negative numbers")
        _parse_timestamp(payload["created_at"], "response.created_at")
        manifest = self._manifest_row(manifest_id)
        usage = self._connection.execute(
            "SELECT tokens_used, tool_calls_used, cost_usd FROM budget_usage WHERE manifest_id=?",
            (manifest_id,),
        ).fetchone()
        if (
            costs["tokens_used"] != usage["tokens_used"]
            or costs["tool_calls_used"] != usage["tool_calls_used"]
            or abs(float(costs["cost_usd"]) - float(usage["cost_usd"])) > 1e-9
        ):
            raise ContractError("response costs do not match durable budget usage")
        task = self._connection.execute(
            "SELECT * FROM tasks WHERE task_id=?", (manifest["task_id"],)
        ).fetchone()
        for field, durable_value in (
            ("task_id", manifest["task_id"]),
            ("role_id", manifest["role_id"]),
            ("actor_instance_id", manifest["actor_instance_id"]),
            ("parent_task_id", task["parent_task_id"]),
        ):
            if payload[field] != durable_value:
                raise ContractError(f"response {field} does not match durable lineage")
        allowed_manifest_states = {"ACTIVE", "BLOCKED"}
        if manifest["state"] not in allowed_manifest_states:
            raise StateTransitionError("manifest cannot produce a terminal response from its current state")
        manifest_target = {
            "PASS": "COMPLETED",
            "BLOCKED": "BLOCKED",
            "HUMAN_REQUIRED": "HUMAN_REQUIRED",
            "FAILED": "FAILED",
            "EXPIRED": "EXPIRED",
            "CANCELLED": "CANCELLED",
        }[payload["status"]]
        if manifest_target != manifest["state"] and manifest_target not in self.lifecycle["transitions"].get(manifest["state"], []):
            raise StateTransitionError(f"response cannot transition manifest to {manifest_target}")
        task_target = "AWAITING_ACCEPTANCE" if payload["status"] == "PASS" else payload["status"]
        with self._connection:
            try:
                self._connection.execute(
                    "INSERT INTO responses(response_id, task_id, manifest_id, status, payload_json, created_at) VALUES(?, ?, ?, ?, ?, ?)",
                    (payload["response_id"], payload["task_id"], manifest_id, payload["status"], _canonical(payload), payload["created_at"]),
                )
            except sqlite3.IntegrityError as exc:
                raise ContractError("response identity already exists") from exc
            self._connection.execute(
                "UPDATE manifests SET state=? WHERE manifest_id=? AND state=?",
                (manifest_target, manifest_id, manifest["state"]),
            )
            self._connection.execute(
                "UPDATE tasks SET status=? WHERE task_id=?",
                (task_target, payload["task_id"]),
            )
            self._append_event(
                "RESPONSE_RECORDED", "RESPONSE", payload["response_id"], payload["actor_instance_id"],
                {"task_id": payload["task_id"], "manifest_id": manifest_id, "status": payload["status"]},
            )
        return payload["response_id"]

    def permission_decision(
        self,
        manifest_id: str,
        capability: str,
        *,
        case_id: str | None = None,
        tax_year: int | None = None,
        run_id: str | None = None,
    ) -> KernelDecision:
        row = self._manifest_row(manifest_id)
        if row["state"] != "ACTIVE" or self.kill_switch_state() != "RUNNING":
            return KernelDecision(False, "DENY", "manifest is not active or kill switch is not running")
        if capability not in self.capabilities:
            return KernelDecision(False, "DENY", "unknown capability")
        capability_contract = self.capabilities[capability]
        if capability_contract.get("maximum_tier") == "A6" or capability_contract.get("no_standing_agent_permission"):
            return KernelDecision(False, "HUMAN_REQUIRED", "A6 cannot be granted as Agent permission")
        payload = json.loads(row["payload_json"])
        if capability not in payload["requested_capabilities"]:
            return KernelDecision(False, "DENY", "capability is not in the validated manifest")
        if capability_contract.get("case_run_required"):
            context = payload["scope"]["case_context"]
            supplied = {"case_id": case_id, "tax_year": tax_year, "run_id": run_id}
            if context is None or context != supplied:
                return KernelDecision(False, "DENY", "case/run scope mismatch")
        return KernelDecision(True, "ALLOW", "capability matches active manifest and scope")

    def consume_budget(
        self,
        manifest_id: str,
        *,
        tokens: int = 0,
        tool_calls: int = 0,
        cost_usd: float = 0,
        child_tasks: int = 0,
    ) -> KernelDecision:
        values = (tokens, tool_calls, cost_usd, child_tasks)
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0 for value in values):
            raise ContractError("budget consumption values must be non-negative numbers")
        row = self._manifest_row(manifest_id)
        if row["state"] != "ACTIVE":
            raise PermissionDenied("budget may be consumed only by an active manifest")
        payload = json.loads(row["payload_json"])
        usage = self._connection.execute(
            "SELECT * FROM budget_usage WHERE manifest_id=?", (manifest_id,)
        ).fetchone()
        new_usage = {
            "tokens_used": usage["tokens_used"] + int(tokens),
            "tool_calls_used": usage["tool_calls_used"] + int(tool_calls),
            "cost_usd": usage["cost_usd"] + float(cost_usd),
            "child_tasks_created": usage["child_tasks_created"] + int(child_tasks),
        }
        limits = payload["budget"]
        exceeded = (
            new_usage["tokens_used"] > limits["token_limit"]
            or new_usage["tool_calls_used"] > limits["tool_call_limit"]
            or new_usage["cost_usd"] > limits["cost_limit_usd"]
            or new_usage["child_tasks_created"] > self.execution_policy["hard_limits"]["max_child_tasks"]
        )
        with self._connection:
            if exceeded:
                self._connection.execute(
                    "UPDATE manifests SET state='BLOCKED' WHERE manifest_id=? AND state='ACTIVE'",
                    (manifest_id,),
                )
                self._append_event(
                    "BUDGET_EXHAUSTED", "MANIFEST", manifest_id, "BUDGET_ENFORCER",
                    {"attempted_usage": new_usage},
                )
                return KernelDecision(False, "BLOCKED", "budget limit would be exceeded")
            self._connection.execute(
                """
                UPDATE budget_usage
                SET tokens_used=?, tool_calls_used=?, cost_usd=?, child_tasks_created=?
                WHERE manifest_id=?
                """,
                (*new_usage.values(), manifest_id),
            )
            self._append_event(
                "BUDGET_CONSUMED", "MANIFEST", manifest_id, "BUDGET_ENFORCER", new_usage,
            )
        return KernelDecision(True, "ALLOW", "budget consumption recorded")

    def authorize_retry(self, manifest_id: str, failure_class: str, attempt_id: str) -> KernelDecision:
        _require_string(attempt_id, "attempt_id")
        row = self._manifest_row(manifest_id)
        if row["state"] != "FAILED":
            return KernelDecision(False, "DENY", "retry requires a terminal FAILED attempt")
        policy = self.execution_policy["retry_policy"]
        if failure_class not in policy["retryable_failures"]:
            outcome = "HUMAN_REQUIRED" if failure_class in policy["non_retryable_failures"] else "DENY"
            return KernelDecision(False, outcome, "failure class is not automatically retryable")
        if self.kill_switch_state() != "RUNNING":
            return KernelDecision(False, "BLOCKED", "kill switch is not RUNNING")
        payload = json.loads(row["payload_json"])
        if self._connection.execute(
            "SELECT 1 FROM retry_attempts WHERE attempt_id=?", (attempt_id,)
        ).fetchone() is not None:
            raise ContractError("retry attempt identity already exists")
        count = self._connection.execute(
            "SELECT COUNT(*) AS count FROM retry_attempts WHERE manifest_id=?", (manifest_id,)
        ).fetchone()["count"]
        if count >= payload["max_retries"]:
            return KernelDecision(False, "BLOCKED", "retry limit exhausted")
        with self._connection:
            try:
                self._connection.execute(
                    "INSERT INTO retry_attempts(attempt_id, manifest_id, ordinal, failure_class, created_at) VALUES(?, ?, ?, ?, ?)",
                    (attempt_id, manifest_id, count + 1, failure_class, _utc_now().isoformat()),
                )
            except sqlite3.IntegrityError as exc:
                raise ContractError("retry attempt identity already exists") from exc
            self._connection.execute(
                "UPDATE tasks SET retry_count=retry_count+1 WHERE task_id=?", (row["task_id"],)
            )
            self._append_event(
                "RETRY_AUTHORIZED", "MANIFEST", manifest_id, "RETRY_ENFORCER",
                {"attempt_id": attempt_id, "ordinal": count + 1, "failure_class": failure_class},
            )
        return KernelDecision(True, "ALLOW", "new retry attempt authorized within policy")

    def kill_switch_state(self) -> str:
        row = self._connection.execute(
            "SELECT state FROM kill_switch WHERE singleton=1"
        ).fetchone()
        if row is None or row["state"] not in self.execution_policy["kill_switch"]["states"]:
            raise IntegrityError("kill switch state is missing or unknown")
        return str(row["state"])

    def set_kill_switch(self, new_state: str, *, actor_id: str, authority_reference: str) -> None:
        if new_state not in self.execution_policy["kill_switch"]["states"]:
            raise ContractError("unknown kill switch state")
        _require_string(authority_reference, "authority_reference")
        current = self.kill_switch_state()
        if new_state == "RUNNING" and actor_id != "HUMAN_PROJECT_OWNER":
            raise PermissionDenied("only Human authority may set RUNNING")
        if new_state == "PAUSED" and actor_id not in {"HUMAN_PROJECT_OWNER", "MASTER_PROJECT_ORCHESTRATOR"}:
            raise PermissionDenied("actor may not pause dispatch")
        if new_state == "HALTED" and actor_id not in {"HUMAN_PROJECT_OWNER", "MASTER_PROJECT_ORCHESTRATOR"} | CONTROL_ROLES:
            raise PermissionDenied("actor may not halt")
        with self._connection:
            self._connection.execute(
                "UPDATE kill_switch SET state=?, updated_at=?, authority_reference=? WHERE singleton=1",
                (new_state, _utc_now().isoformat(), authority_reference),
            )
            revoked: list[str] = []
            if new_state == "HALTED":
                active = self._connection.execute(
                    "SELECT manifest_id, state FROM manifests WHERE state IN ('ACTIVE', 'BLOCKED')"
                ).fetchall()
                for manifest in active:
                    self._connection.execute(
                        "UPDATE manifests SET state='REVOKED' WHERE manifest_id=?",
                        (manifest["manifest_id"],),
                    )
                    revoked.append(manifest["manifest_id"])
                    self._append_event(
                        "MANIFEST_STATE_CHANGED", "MANIFEST", manifest["manifest_id"], actor_id,
                        {"from": manifest["state"], "to": "REVOKED", "reason": "global kill switch halted"},
                    )
            self._append_event(
                "KILL_SWITCH_CHANGED", "KILL_SWITCH", "GLOBAL", actor_id,
                {"from": current, "to": new_state, "authority_reference": authority_reference, "revoked_manifests": revoked},
            )

    def bind_agent_bridge_request(
        self,
        bridge_payload: dict[str, Any],
        task_payload: dict[str, Any],
        *,
        depends_on: Iterable[str] = (),
    ) -> KernelDecision:
        from scripts.agent_bridge_validate import validate_request

        bridge_result = validate_request(bridge_payload)
        if not bridge_result.valid or bridge_result.outcome != "PASSIVE_VALID":
            return KernelDecision(False, bridge_result.outcome, bridge_result.reason)
        exact_pairs = {
            "task_id": "task_id",
            "repository": "repository",
            "ref": "ref",
            "task": "objective",
        }
        for bridge_field, task_field in exact_pairs.items():
            if bridge_payload[bridge_field] != task_payload.get(task_field):
                raise ContractError(f"Agent Bridge {bridge_field} does not match task contract")
        if bridge_payload["acceptance"] != task_payload.get("acceptance_criteria"):
            raise ContractError("Agent Bridge acceptance does not match task contract")
        if not set(bridge_payload["forbidden_actions"]) <= set(task_payload.get("forbidden_actions", [])):
            raise ContractError("task contract weakens Agent Bridge forbidden actions")
        task_id = self.register_task(
            task_payload, gate_triggers=(), depends_on=depends_on, actor_id="AGENT_BRIDGE_BINDING"
        )
        with self._connection:
            self._connection.execute(
                "INSERT INTO bridge_bindings(task_id, bridge_task_id, base_commit, allowed_scope_json, risk_class) VALUES(?, ?, ?, ?, ?)",
                (
                    task_id, bridge_payload["task_id"], bridge_payload["base_commit"],
                    _canonical(bridge_payload["allowed_scope"]), bridge_payload["risk_class"],
                ),
            )
            self._append_event(
                "AGENT_BRIDGE_BOUND", "TASK", task_id, "AGENT_BRIDGE_BINDING",
                {"base_commit": bridge_payload["base_commit"], "risk_class": bridge_payload["risk_class"]},
            )
        return KernelDecision(True, "REGISTERED", "Agent Bridge request bound to registered Kernel task")

    def create_checkpoint(self, checkpoint_id: str) -> str:
        _require_string(checkpoint_id, "checkpoint_id")
        self.verify_audit_chain()
        last_event = self._connection.execute(
            "SELECT COALESCE(MAX(event_id), 0) AS event_id FROM audit_events"
        ).fetchone()["event_id"]
        snapshot = self._state_snapshot(last_event)
        snapshot_hash = _digest(snapshot)
        with self._connection:
            try:
                self._connection.execute(
                    "INSERT INTO checkpoints(checkpoint_id, created_at, last_event_id, contract_set_id, snapshot_json, snapshot_hash) VALUES(?, ?, ?, ?, ?, ?)",
                    (
                        checkpoint_id, _utc_now().isoformat(), last_event, CONTRACT_SET_ID,
                        _canonical(snapshot), snapshot_hash,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise ContractError("checkpoint identity already exists") from exc
            self._append_event(
                "CHECKPOINT_CREATED", "CHECKPOINT", checkpoint_id, "CHECKPOINT_CONTROLLER",
                {"last_event_id": last_event, "snapshot_hash": snapshot_hash},
            )
        return snapshot_hash

    def _state_snapshot(self, last_event_id: int) -> dict[str, Any]:
        def rows(query: str) -> list[dict[str, Any]]:
            return [dict(row) for row in self._connection.execute(query).fetchall()]

        return {
            "contract_set_id": CONTRACT_SET_ID,
            "last_event_id": last_event_id,
            "kill_switch": rows("SELECT state, updated_at, authority_reference FROM kill_switch ORDER BY singleton"),
            "tasks": rows("SELECT task_id, parent_task_id, role_id, actor_instance_id, status, payload_json, retry_count FROM tasks ORDER BY task_id"),
            "dependencies": rows("SELECT task_id, depends_on_task_id FROM dependencies ORDER BY task_id, depends_on_task_id"),
            "task_human_gates": rows("SELECT * FROM task_human_gates ORDER BY task_id, trigger"),
            "manifests": rows("SELECT manifest_id, actor_instance_id, task_id, role_id, state, payload_json FROM manifests ORDER BY manifest_id"),
            "budget_usage": rows("SELECT * FROM budget_usage ORDER BY manifest_id"),
            "retry_attempts": rows("SELECT * FROM retry_attempts ORDER BY attempt_id"),
            "responses": rows("SELECT * FROM responses ORDER BY response_id"),
            "acceptance_records": rows("SELECT * FROM acceptance_records ORDER BY acceptance_id"),
            "bridge_bindings": rows("SELECT * FROM bridge_bindings ORDER BY task_id"),
        }

    def recover_latest_checkpoint(self) -> dict[str, Any]:
        self.verify_audit_chain()
        row = self._connection.execute(
            "SELECT * FROM checkpoints ORDER BY created_at DESC, checkpoint_id DESC LIMIT 1"
        ).fetchone()
        if row is None:
            raise IntegrityError("no checkpoint is available")
        if row["contract_set_id"] != CONTRACT_SET_ID:
            raise IntegrityError("checkpoint contract set mismatch")
        snapshot = json.loads(row["snapshot_json"])
        if row["snapshot_hash"] != _digest(snapshot):
            raise IntegrityError("checkpoint snapshot integrity failed")
        return {
            "checkpoint_id": row["checkpoint_id"],
            "created_at": row["created_at"],
            "snapshot_hash": row["snapshot_hash"],
            "snapshot": snapshot,
        }

    @staticmethod
    def inspect_read_only(database_path: Path | str) -> dict[str, Any]:
        path = Path(database_path).resolve()
        connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            schema = connection.execute(
                "SELECT version FROM kernel_schema WHERE component='orchestrator'"
            ).fetchone()
            if schema is None or schema["version"] != KERNEL_SCHEMA_VERSION:
                raise IntegrityError("unsupported or missing orchestrator schema")
            kill = connection.execute("SELECT state FROM kill_switch WHERE singleton=1").fetchone()
            counts = {
                table: connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]
                for table in ("tasks", "dependencies", "task_human_gates", "manifests", "responses", "acceptance_records", "retry_attempts", "audit_events", "checkpoints")
            }
            checkpoint = connection.execute(
                "SELECT checkpoint_id, snapshot_hash FROM checkpoints ORDER BY created_at DESC, checkpoint_id DESC LIMIT 1"
            ).fetchone()
            previous_hash: str | None = None
            for row in connection.execute("SELECT * FROM audit_events ORDER BY event_id").fetchall():
                payload = json.loads(row["payload_json"])
                event_body = {
                    "event_type": row["event_type"],
                    "entity_type": row["entity_type"],
                    "entity_id": row["entity_id"],
                    "occurred_at": row["occurred_at"],
                    "actor_id": row["actor_id"],
                    "payload": payload,
                    "previous_hash": previous_hash,
                }
                if row["previous_hash"] != previous_hash or row["event_hash"] != _digest(event_body):
                    raise IntegrityError(f"audit chain failed at event {row['event_id']}")
                previous_hash = row["event_hash"]
            return {
                "schema_version": schema["version"],
                "kill_switch": kill["state"] if kill else "UNKNOWN",
                "counts": counts,
                "latest_checkpoint": dict(checkpoint) if checkpoint else None,
                "audit_integrity": "PASS",
            }
        finally:
            connection.close()
