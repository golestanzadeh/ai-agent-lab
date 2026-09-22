"""SQLite-backed durable/reloadable D-017 approval authority.

The durable store preserves the existing approval domain values and binding gate
while persisting each lifecycle transition and its approval audit event in one
SQLite transaction. It performs no Drive mutation.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Mapping

from agent_lab.approval import (
    ApprovalAlreadyConsumedError,
    ApprovalExecutionContext,
    ApprovalGate,
    ApprovalNotFoundError,
    ApprovalStatus,
    ApprovalValidationError,
    IntendedOperation,
    InvalidApprovalError,
    MigrationApproval,
)
from agent_lab.audit import ActorType, AuditEvent, AuditEventType, AuditStatus


DURABLE_APPROVAL_SCHEMA_VERSION = 1


class DurableApprovalError(InvalidApprovalError):
    """Base fail-closed error for durable approval persistence."""


class DurableApprovalIntegrityError(DurableApprovalError):
    pass


class DurableApprovalSchemaError(DurableApprovalError):
    pass


def _utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        raise InvalidApprovalError("timestamp must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise DurableApprovalIntegrityError("durable timestamp must be canonical UTC")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise DurableApprovalIntegrityError("invalid durable timestamp") from exc
    if parsed.tzinfo is None:
        raise DurableApprovalIntegrityError("durable timestamp must be timezone-aware")
    return parsed


def _digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _approval_payload(approval: MigrationApproval) -> dict[str, object]:
    return {
        "schema_version": DURABLE_APPROVAL_SCHEMA_VERSION,
        "approval_id": approval.approval_id,
        "case_id": approval.case_id,
        "run_id": approval.run_id,
        "manifest_identity": approval.manifest_identity,
        "manifest_version": approval.manifest_version,
        "manifest_reference": approval.manifest_reference,
        "preflight_identity": approval.preflight_identity,
        "preflight_reference": approval.preflight_reference,
        "preflight_result": approval.preflight_result,
        "intended_operation": approval.intended_operation.value,
        "approver": approval.approver,
        "actor": approval.actor,
        "approval_timestamp": _utc_iso(approval.approval_timestamp),
        "authorization_reference": approval.authorization_reference,
        "approval_status": approval.approval_status.value,
        "audit_reference": approval.audit_reference,
    }


def _audit_payload(event: AuditEvent) -> dict[str, object]:
    return {
        "schema_version": event.schema_version,
        "event_id": event.event_id,
        "case_id": event.case_id,
        "run_id": event.run_id,
        "event_type": event.event_type.value,
        "occurred_at": _utc_iso(event.occurred_at),
        "actor_type": event.actor_type.value,
        "actor_id": event.actor_id,
        "operation": event.operation,
        "status": event.status.value,
        "input_refs": list(event.input_refs),
        "decision_ref": event.decision_ref,
        "evidence_refs": list(event.evidence_refs),
        "output_refs": list(event.output_refs),
        "error_code": event.error_code,
        "approval_ref": event.approval_ref,
        "metadata": dict(event.metadata),
    }


class DurableApprovalStore:
    """Durable approval lifecycle authority backed by one SQLite database."""

    def __init__(self, db_path: str | Path, *, case_registry, case_state) -> None:
        self._path = str(db_path)
        self._case_registry = case_registry
        self._case_state = case_state
        self._lock = RLock()
        self._connection = sqlite3.connect(
            self._path,
            timeout=10.0,
            isolation_level=None,
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA busy_timeout = 10000")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._initialize_schema()

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def __enter__(self) -> "DurableApprovalStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _initialize_schema(self) -> None:
        with self._lock:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS durable_schema (
                    component TEXT PRIMARY KEY,
                    version INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS durable_counters (
                    kind TEXT PRIMARY KEY,
                    value INTEGER NOT NULL CHECK(value >= 0)
                );
                CREATE TABLE IF NOT EXISTS durable_approvals (
                    approval_id TEXT PRIMARY KEY,
                    schema_version INTEGER NOT NULL,
                    case_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    manifest_identity TEXT NOT NULL,
                    manifest_version TEXT NOT NULL,
                    manifest_reference TEXT NOT NULL,
                    preflight_identity TEXT NOT NULL,
                    preflight_reference TEXT NOT NULL,
                    preflight_result TEXT NOT NULL,
                    intended_operation TEXT NOT NULL,
                    approver TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    approval_timestamp TEXT NOT NULL,
                    authorization_reference TEXT NOT NULL,
                    approval_status TEXT NOT NULL,
                    audit_reference TEXT NOT NULL,
                    integrity_digest TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS durable_approval_audit (
                    event_id TEXT PRIMARY KEY,
                    schema_version INTEGER NOT NULL,
                    case_id TEXT NOT NULL,
                    run_id TEXT,
                    event_type TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    actor_type TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_refs TEXT NOT NULL,
                    decision_ref TEXT,
                    evidence_refs TEXT NOT NULL,
                    output_refs TEXT NOT NULL,
                    error_code TEXT,
                    approval_ref TEXT,
                    metadata TEXT NOT NULL,
                    integrity_digest TEXT NOT NULL
                );
                """
            )
            row = self._connection.execute(
                "SELECT version FROM durable_schema WHERE component = 'approval'"
            ).fetchone()
            if row is None:
                self._connection.execute(
                    "INSERT INTO durable_schema(component, version) VALUES('approval', ?)",
                    (DURABLE_APPROVAL_SCHEMA_VERSION,),
                )
            elif row["version"] != DURABLE_APPROVAL_SCHEMA_VERSION:
                raise DurableApprovalSchemaError(
                    f"unsupported durable approval schema version: {row['version']}"
                )
            self._connection.execute(
                "INSERT OR IGNORE INTO durable_counters(kind, value) VALUES('approval', 0)"
            )
            self._connection.execute(
                "INSERT OR IGNORE INTO durable_counters(kind, value) VALUES('audit', 0)"
            )

    def _require_schema(self) -> None:
        row = self._connection.execute(
            "SELECT version FROM durable_schema WHERE component = 'approval'"
        ).fetchone()
        if row is None or row["version"] != DURABLE_APPROVAL_SCHEMA_VERSION:
            raise DurableApprovalSchemaError("durable approval schema is missing or unsupported")

    def _require_scope(self, case_id: str, run_id: str) -> None:
        if self._case_registry.get(case_id) is None:
            raise InvalidApprovalError(f"unknown case_id: {case_id}")
        try:
            run = self._case_state.get_run(case_id, run_id)
        except (KeyError, PermissionError) as exc:
            raise InvalidApprovalError(f"run is outside case scope: {run_id}") from exc
        if run.case_id != case_id:
            raise InvalidApprovalError(f"run is outside case scope: {run_id}")

    def _validate_common(self, **values: object) -> None:
        self._require_scope(str(values["case_id"]), str(values["run_id"]))
        for name in (
            "case_id",
            "run_id",
            "manifest_identity",
            "manifest_version",
            "manifest_reference",
            "preflight_identity",
            "preflight_reference",
            "preflight_result",
            "actor",
        ):
            ApprovalGate._required(name, values[name])
        if values["preflight_result"] != "PASSED":
            raise InvalidApprovalError("preflight result is not successful")
        if not isinstance(values["intended_operation"], IntendedOperation):
            raise InvalidApprovalError("unknown intended operation")

    def _next_id(self, kind: str, prefix: str) -> str:
        row = self._connection.execute(
            "SELECT value FROM durable_counters WHERE kind = ?", (kind,)
        ).fetchone()
        if row is None:
            raise DurableApprovalSchemaError(f"missing durable counter: {kind}")
        value = int(row["value"]) + 1
        self._connection.execute(
            "UPDATE durable_counters SET value = ? WHERE kind = ?", (value, kind)
        )
        return f"{prefix}-{value:08d}"

    def _event(
        self,
        *,
        event_id: str,
        case_id: str,
        run_id: str,
        event_type: AuditEventType,
        actor_type: ActorType,
        actor_id: str,
        operation: str,
        status: AuditStatus,
        approval_ref: str,
        metadata: Mapping[str, str] | None = None,
    ) -> AuditEvent:
        ApprovalGate._required("actor_id", actor_id)
        ApprovalGate._required("operation", operation)
        return AuditEvent(
            event_id=event_id,
            case_id=case_id,
            run_id=run_id,
            event_type=event_type,
            occurred_at=datetime.now(timezone.utc),
            actor_type=actor_type,
            actor_id=actor_id,
            operation=operation,
            status=status,
            approval_ref=approval_ref,
            metadata=dict(metadata or {}),
        )

    def _write_event(self, event: AuditEvent) -> None:
        payload = _audit_payload(event)
        self._connection.execute(
            """
            INSERT INTO durable_approval_audit(
                event_id, schema_version, case_id, run_id, event_type, occurred_at,
                actor_type, actor_id, operation, status, input_refs, decision_ref,
                evidence_refs, output_refs, error_code, approval_ref, metadata,
                integrity_digest
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id,
                event.schema_version,
                event.case_id,
                event.run_id,
                event.event_type.value,
                _utc_iso(event.occurred_at),
                event.actor_type.value,
                event.actor_id,
                event.operation,
                event.status.value,
                json.dumps(list(event.input_refs), separators=(",", ":")),
                event.decision_ref,
                json.dumps(list(event.evidence_refs), separators=(",", ":")),
                json.dumps(list(event.output_refs), separators=(",", ":")),
                event.error_code,
                event.approval_ref,
                json.dumps(dict(event.metadata), sort_keys=True, separators=(",", ":")),
                _digest(payload),
            ),
        )

    def _write_approval(self, approval: MigrationApproval) -> None:
        payload = _approval_payload(approval)
        values = (
            approval.approval_id,
            DURABLE_APPROVAL_SCHEMA_VERSION,
            approval.case_id,
            approval.run_id,
            approval.manifest_identity,
            approval.manifest_version,
            approval.manifest_reference,
            approval.preflight_identity,
            approval.preflight_reference,
            approval.preflight_result,
            approval.intended_operation.value,
            approval.approver,
            approval.actor,
            _utc_iso(approval.approval_timestamp),
            approval.authorization_reference,
            approval.approval_status.value,
            approval.audit_reference,
            _digest(payload),
        )
        self._connection.execute(
            """
            INSERT INTO durable_approvals(
                approval_id, schema_version, case_id, run_id, manifest_identity,
                manifest_version, manifest_reference, preflight_identity,
                preflight_reference, preflight_result, intended_operation, approver,
                actor, approval_timestamp, authorization_reference, approval_status,
                audit_reference, integrity_digest
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(approval_id) DO UPDATE SET
                schema_version=excluded.schema_version,
                case_id=excluded.case_id,
                run_id=excluded.run_id,
                manifest_identity=excluded.manifest_identity,
                manifest_version=excluded.manifest_version,
                manifest_reference=excluded.manifest_reference,
                preflight_identity=excluded.preflight_identity,
                preflight_reference=excluded.preflight_reference,
                preflight_result=excluded.preflight_result,
                intended_operation=excluded.intended_operation,
                approver=excluded.approver,
                actor=excluded.actor,
                approval_timestamp=excluded.approval_timestamp,
                authorization_reference=excluded.authorization_reference,
                approval_status=excluded.approval_status,
                audit_reference=excluded.audit_reference,
                integrity_digest=excluded.integrity_digest
            """,
            values,
        )

    def _decode_approval(self, row: sqlite3.Row) -> MigrationApproval:
        if row["schema_version"] != DURABLE_APPROVAL_SCHEMA_VERSION:
            raise DurableApprovalSchemaError(
                f"unsupported approval record schema version: {row['schema_version']}"
            )
        try:
            approval = MigrationApproval(
                approval_id=row["approval_id"],
                case_id=row["case_id"],
                run_id=row["run_id"],
                manifest_identity=row["manifest_identity"],
                manifest_version=row["manifest_version"],
                manifest_reference=row["manifest_reference"],
                preflight_identity=row["preflight_identity"],
                preflight_reference=row["preflight_reference"],
                preflight_result=row["preflight_result"],
                intended_operation=IntendedOperation(row["intended_operation"]),
                approver=row["approver"],
                actor=row["actor"],
                approval_timestamp=_parse_utc(row["approval_timestamp"]),
                authorization_reference=row["authorization_reference"],
                approval_status=ApprovalStatus(row["approval_status"]),
                audit_reference=row["audit_reference"],
            )
        except (ValueError, TypeError) as exc:
            raise DurableApprovalIntegrityError("malformed durable approval record") from exc
        for name in (
            "approval_id",
            "case_id",
            "run_id",
            "manifest_identity",
            "manifest_version",
            "manifest_reference",
            "preflight_identity",
            "preflight_reference",
            "preflight_result",
            "actor",
            "audit_reference",
        ):
            ApprovalGate._required(name, getattr(approval, name))
        expected = _digest(_approval_payload(approval))
        if row["integrity_digest"] != expected:
            raise DurableApprovalIntegrityError("durable approval integrity mismatch")
        return approval

    def _decode_event(self, row: sqlite3.Row) -> AuditEvent:
        if row["schema_version"] != 1:
            raise DurableApprovalSchemaError("unsupported durable audit event schema version")
        try:
            event = AuditEvent(
                event_id=row["event_id"],
                case_id=row["case_id"],
                run_id=row["run_id"],
                event_type=AuditEventType(row["event_type"]),
                occurred_at=_parse_utc(row["occurred_at"]),
                actor_type=ActorType(row["actor_type"]),
                actor_id=row["actor_id"],
                operation=row["operation"],
                status=AuditStatus(row["status"]),
                input_refs=tuple(json.loads(row["input_refs"])),
                decision_ref=row["decision_ref"],
                evidence_refs=tuple(json.loads(row["evidence_refs"])),
                output_refs=tuple(json.loads(row["output_refs"])),
                error_code=row["error_code"],
                approval_ref=row["approval_ref"],
                metadata=dict(json.loads(row["metadata"])),
                schema_version=row["schema_version"],
            )
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            raise DurableApprovalIntegrityError("malformed durable audit event") from exc
        if row["integrity_digest"] != _digest(_audit_payload(event)):
            raise DurableApprovalIntegrityError("durable audit integrity mismatch")
        return event

    def _transaction(self):
        self._require_schema()
        self._connection.execute("BEGIN IMMEDIATE")

    def create_pending(
        self,
        *,
        case_id: str,
        run_id: str,
        manifest_identity: str,
        manifest_version: str,
        manifest_reference: str,
        preflight_identity: str,
        preflight_reference: str,
        preflight_result: str,
        intended_operation: IntendedOperation,
        actor: str,
        requester_actor_type: ActorType = ActorType.HUMAN,
        timestamp: datetime | None = None,
    ) -> MigrationApproval:
        with self._lock:
            self._validate_common(
                case_id=case_id,
                run_id=run_id,
                manifest_identity=manifest_identity,
                manifest_version=manifest_version,
                manifest_reference=manifest_reference,
                preflight_identity=preflight_identity,
                preflight_reference=preflight_reference,
                preflight_result=preflight_result,
                intended_operation=intended_operation,
                actor=actor,
            )
            if requester_actor_type not in {ActorType.HUMAN, ActorType.AGENT}:
                raise InvalidApprovalError("approval requester must be HUMAN or AGENT")
            ts = timestamp or datetime.now(timezone.utc)
            _utc_iso(ts)
            try:
                self._transaction()
                approval_id = self._next_id("approval", "APP")
                event_id = self._next_id("audit", "AUDIT")
                event = self._event(
                    event_id=event_id,
                    case_id=case_id,
                    run_id=run_id,
                    event_type=AuditEventType.APPROVAL_REQUESTED,
                    actor_type=requester_actor_type,
                    actor_id=actor,
                    operation="request_approval",
                    status=AuditStatus.INFO,
                    approval_ref=approval_id,
                )
                approval = MigrationApproval(
                    approval_id=approval_id,
                    case_id=case_id,
                    run_id=run_id,
                    manifest_identity=manifest_identity,
                    manifest_version=manifest_version,
                    manifest_reference=manifest_reference,
                    preflight_identity=preflight_identity,
                    preflight_reference=preflight_reference,
                    preflight_result=preflight_result,
                    intended_operation=intended_operation,
                    approver="",
                    actor=actor,
                    approval_timestamp=ts,
                    authorization_reference="",
                    approval_status=ApprovalStatus.PENDING,
                    audit_reference=event_id,
                )
                self._write_approval(approval)
                self._write_event(event)
                self._connection.execute("COMMIT")
                return approval
            except Exception:
                if self._connection.in_transaction:
                    self._connection.execute("ROLLBACK")
                raise

    def get(self, approval_id: str) -> MigrationApproval:
        with self._lock:
            self._require_schema()
            row = self._connection.execute(
                "SELECT * FROM durable_approvals WHERE approval_id = ?", (approval_id,)
            ).fetchone()
            if row is None:
                raise ApprovalNotFoundError(approval_id)
            approval = self._decode_approval(row)
            self._require_scope(approval.case_id, approval.run_id)
            return approval

    def validate(self, approval_id: str, context: ApprovalExecutionContext) -> MigrationApproval:
        with self._lock:
            approval = self.get(approval_id)
            ApprovalGate.validate_binding(approval, context)
            return approval

    def grant(
        self,
        approval_id: str,
        *,
        approver: str,
        authorization_reference: str,
        timestamp: datetime | None = None,
    ) -> MigrationApproval:
        ApprovalGate._required("approver", approver)
        ApprovalGate._required("authorization_reference", authorization_reference)
        ts = timestamp or datetime.now(timezone.utc)
        _utc_iso(ts)
        return self._transition_with_event(
            approval_id,
            expected=ApprovalStatus.PENDING,
            target=ApprovalStatus.APPROVED,
            event_type=AuditEventType.APPROVAL_GRANTED,
            actor_type=ActorType.HUMAN,
            actor_id=approver,
            operation="grant_approval",
            audit_status=AuditStatus.SUCCESS,
            approval_changes={
                "approver": approver,
                "authorization_reference": authorization_reference,
                "approval_timestamp": ts,
            },
            metadata={"authorization_reference": authorization_reference},
        )

    def reject(self, approval_id: str, *, actor: str) -> MigrationApproval:
        return self._transition_with_event(
            approval_id,
            expected=ApprovalStatus.PENDING,
            target=ApprovalStatus.REJECTED,
            event_type=AuditEventType.APPROVAL_REJECTED,
            actor_type=ActorType.HUMAN,
            actor_id=actor,
            operation="reject_approval",
            audit_status=AuditStatus.INFO,
        )

    def revoke(self, approval_id: str, *, actor: str) -> MigrationApproval:
        return self._transition_with_event(
            approval_id,
            expected=ApprovalStatus.APPROVED,
            target=ApprovalStatus.REVOKED,
            event_type=AuditEventType.APPROVAL_REVOKED,
            actor_type=ActorType.HUMAN,
            actor_id=actor,
            operation="revoke_approval",
            audit_status=AuditStatus.INFO,
        )

    def expire(self, approval_id: str, *, actor: str) -> MigrationApproval:
        return self._transition_with_event(
            approval_id,
            expected=ApprovalStatus.APPROVED,
            target=ApprovalStatus.EXPIRED,
            event_type=AuditEventType.APPROVAL_EXPIRED,
            actor_type=ActorType.HUMAN,
            actor_id=actor,
            operation="expire_approval",
            audit_status=AuditStatus.INFO,
        )

    def _transition_with_event(
        self,
        approval_id: str,
        *,
        expected: ApprovalStatus,
        target: ApprovalStatus,
        event_type: AuditEventType,
        actor_type: ActorType,
        actor_id: str,
        operation: str,
        audit_status: AuditStatus,
        approval_changes: Mapping[str, object] | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> MigrationApproval:
        ApprovalGate._required("actor", actor_id)
        with self._lock:
            try:
                self._transaction()
                row = self._connection.execute(
                    "SELECT * FROM durable_approvals WHERE approval_id = ?", (approval_id,)
                ).fetchone()
                if row is None:
                    raise ApprovalNotFoundError(approval_id)
                current = self._decode_approval(row)
                self._require_scope(current.case_id, current.run_id)
                if current.approval_status is not expected:
                    raise ApprovalValidationError(
                        f"only {expected.value} approval can transition to {target.value}"
                    )
                event_id = self._next_id("audit", "AUDIT")
                event = self._event(
                    event_id=event_id,
                    case_id=current.case_id,
                    run_id=current.run_id,
                    event_type=event_type,
                    actor_type=actor_type,
                    actor_id=actor_id,
                    operation=operation,
                    status=audit_status,
                    approval_ref=approval_id,
                    metadata=metadata,
                )
                updated = replace(
                    current,
                    **dict(approval_changes or {}),
                    approval_status=target,
                    audit_reference=event_id,
                )
                self._write_approval(updated)
                self._write_event(event)
                self._connection.execute("COMMIT")
                return updated
            except Exception:
                if self._connection.in_transaction:
                    self._connection.execute("ROLLBACK")
                raise

    def consume(self, approval_id: str, context: ApprovalExecutionContext) -> MigrationApproval:
        """Atomically consume exactly once across process restart/concurrent stores."""
        with self._lock:
            try:
                self._transaction()
                row = self._connection.execute(
                    "SELECT * FROM durable_approvals WHERE approval_id = ?", (approval_id,)
                ).fetchone()
                if row is None:
                    raise ApprovalNotFoundError(approval_id)
                current = self._decode_approval(row)
                self._require_scope(current.case_id, current.run_id)
                if current.approval_status is ApprovalStatus.CONSUMED:
                    raise ApprovalAlreadyConsumedError("APPROVAL_ALREADY_CONSUMED")
                ApprovalGate.validate_binding(current, context)
                event_id = self._next_id("audit", "AUDIT")
                event = self._event(
                    event_id=event_id,
                    case_id=current.case_id,
                    run_id=current.run_id,
                    event_type=AuditEventType.APPROVAL_CONSUMED,
                    actor_type=ActorType.SYSTEM,
                    actor_id=context.actor,
                    operation="consume_approval",
                    status=AuditStatus.SUCCESS,
                    approval_ref=approval_id,
                    metadata={"intended_operation": context.intended_operation.value},
                )
                updated = replace(
                    current,
                    approval_status=ApprovalStatus.CONSUMED,
                    audit_reference=event_id,
                )
                self._write_approval(updated)
                self._write_event(event)
                self._connection.execute("COMMIT")
                return updated
            except Exception:
                if self._connection.in_transaction:
                    self._connection.execute("ROLLBACK")
                raise

    def list_audit_events(self, case_id: str, run_id: str | None = None) -> tuple[AuditEvent, ...]:
        with self._lock:
            self._require_schema()
            if self._case_registry.get(case_id) is None:
                raise InvalidApprovalError(f"unknown case_id: {case_id}")
            if run_id is not None:
                self._require_scope(case_id, run_id)
            if run_id is None:
                rows = self._connection.execute(
                    "SELECT * FROM durable_approval_audit WHERE case_id = ? ORDER BY event_id",
                    (case_id,),
                ).fetchall()
            else:
                rows = self._connection.execute(
                    "SELECT * FROM durable_approval_audit WHERE case_id = ? AND run_id = ? ORDER BY event_id",
                    (case_id, run_id),
                ).fetchall()
            return tuple(self._decode_event(row) for row in rows)
