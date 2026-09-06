"""Deterministic, case-scoped append-only audit event recorder."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from typing import Mapping

from agent_lab.case_registry import CaseRegistry
from agent_lab.case_state import CaseStateStore


class AuditEventType(str, Enum):
    RUN_CREATED = "RUN_CREATED"
    RUN_STARTED = "RUN_STARTED"
    RUN_COMPLETED = "RUN_COMPLETED"
    RUN_FAILED = "RUN_FAILED"
    RUN_BLOCKED = "RUN_BLOCKED"
    RUN_CANCELLED = "RUN_CANCELLED"
    TOOL_CALLED = "TOOL_CALLED"
    TOOL_COMPLETED = "TOOL_COMPLETED"
    TOOL_FAILED = "TOOL_FAILED"
    DECISION_RECORDED = "DECISION_RECORDED"
    EVIDENCE_LINKED = "EVIDENCE_LINKED"
    APPROVAL_REQUESTED = "APPROVAL_REQUESTED"
    APPROVAL_GRANTED = "APPROVAL_GRANTED"
    APPROVAL_REJECTED = "APPROVAL_REJECTED"
    STATE_CHANGED = "STATE_CHANGED"
    OUTPUT_CREATED = "OUTPUT_CREATED"
    ERROR_RECORDED = "ERROR_RECORDED"


class ActorType(str, Enum):
    HUMAN = "human"
    AGENT = "agent"
    SYSTEM = "system"
    TOOL = "tool"


class AuditStatus(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    FAILURE = "failure"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: str
    case_id: str
    run_id: str | None
    event_type: AuditEventType
    occurred_at: datetime
    actor_type: ActorType
    actor_id: str
    operation: str
    status: AuditStatus
    input_refs: tuple[str, ...] = ()
    decision_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()
    output_refs: tuple[str, ...] = ()
    error_code: str | None = None
    approval_ref: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)
    schema_version: int = 1


class AuditError(RuntimeError):
    """Base error for fail-closed audit operations."""


class InvalidAuditEventError(AuditError):
    pass


class AuditEventNotFoundError(AuditError):
    pass


class AuditStore:
    """In-memory append-only audit store for the foundational runtime."""

    def __init__(self, case_registry: CaseRegistry, case_state: CaseStateStore) -> None:
        self._case_registry = case_registry
        self._case_state = case_state
        self._events: dict[str, AuditEvent] = {}
        self._sequence = 0
        self._lock = RLock()

    def append(
        self,
        *,
        case_id: str,
        run_id: str | None,
        event_type: AuditEventType,
        actor_type: ActorType,
        actor_id: str,
        operation: str,
        status: AuditStatus = AuditStatus.INFO,
        input_refs: tuple[str, ...] = (),
        decision_ref: str | None = None,
        evidence_refs: tuple[str, ...] = (),
        output_refs: tuple[str, ...] = (),
        error_code: str | None = None,
        approval_ref: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> AuditEvent:
        with self._lock:
            self._validate(case_id, run_id, actor_id, operation)
            self._sequence += 1
            event = AuditEvent(
                event_id=f"AUDIT-{self._sequence:08d}",
                case_id=case_id,
                run_id=run_id,
                event_type=event_type,
                occurred_at=datetime.now(timezone.utc),
                actor_type=actor_type,
                actor_id=actor_id,
                operation=operation,
                status=status,
                input_refs=tuple(input_refs),
                decision_ref=decision_ref,
                evidence_refs=tuple(evidence_refs),
                output_refs=tuple(output_refs),
                error_code=error_code,
                approval_ref=approval_ref,
                metadata=dict(metadata or {}),
            )
            self._events[event.event_id] = event
            return event

    def get(self, case_id: str, event_id: str) -> AuditEvent:
        with self._lock:
            self._require_case(case_id)
            event = self._events.get(event_id)
            if event is None or event.case_id != case_id:
                raise AuditEventNotFoundError(event_id)
            return event

    def list_events(self, case_id: str, run_id: str | None = None) -> tuple[AuditEvent, ...]:
        with self._lock:
            self._require_case(case_id)
            if run_id is not None:
                self._require_run(case_id, run_id)
            events = [event for event in self._events.values() if event.case_id == case_id]
            if run_id is not None:
                events = [event for event in events if event.run_id == run_id]
            return tuple(events)

    def validate(self) -> None:
        with self._lock:
            for event in self._events.values():
                self._validate(event.case_id, event.run_id, event.actor_id, event.operation)

    def _validate(self, case_id: str, run_id: str | None, actor_id: str, operation: str) -> None:
        self._require_case(case_id)
        if not actor_id.strip() or not operation.strip():
            raise InvalidAuditEventError("actor_id and operation are required")
        if run_id is not None:
            self._require_run(case_id, run_id)

    def _require_case(self, case_id: str) -> None:
        if not case_id or not case_id.strip() or self._case_registry.get(case_id) is None:
            raise InvalidAuditEventError(f"unknown case_id: {case_id}")

    def _require_run(self, case_id: str, run_id: str) -> None:
        try:
            run = self._case_state.get_run(case_id, run_id)
        except (KeyError, PermissionError) as exc:
            raise InvalidAuditEventError(f"run is outside case scope: {run_id}") from exc
        if run.case_id != case_id:
            raise InvalidAuditEventError(f"run is outside case scope: {run_id}")
