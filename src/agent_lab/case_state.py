"""Deterministic case-scoped state and execution/run model."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from threading import RLock

from agent_lab.case_registry import CaseRegistry


class RunStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


_TERMINAL = {
    RunStatus.SUCCEEDED,
    RunStatus.FAILED,
    RunStatus.BLOCKED,
    RunStatus.CANCELLED,
}

_ALLOWED_TRANSITIONS: dict[RunStatus, frozenset[RunStatus]] = {
    RunStatus.CREATED: frozenset({RunStatus.RUNNING, RunStatus.CANCELLED}),
    RunStatus.RUNNING: frozenset(_TERMINAL),
    RunStatus.SUCCEEDED: frozenset(),
    RunStatus.FAILED: frozenset(),
    RunStatus.BLOCKED: frozenset(),
    RunStatus.CANCELLED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class CaseState:
    """Structured operational state for exactly one tax case."""

    case_id: str
    schema_version: int
    lifecycle_status: str
    created_at: datetime
    updated_at: datetime
    parties_ref: str | None = None
    documents_ref: str | None = None
    evidence_ref: str | None = None
    facts_ref: str | None = None
    assumptions_ref: str | None = None
    rules_ref: str | None = None
    calculations_ref: str | None = None
    optimization_ref: str | None = None
    challenges_ref: str | None = None
    approvals_ref: str | None = None
    outputs_ref: str | None = None
    last_run_id: str | None = None

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id is required")
        if self.schema_version < 1:
            raise ValueError("schema_version must be >= 1")
        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot precede created_at")


@dataclass(frozen=True, slots=True)
class RunRecord:
    """Identity and lifecycle record for one execution against one case."""

    run_id: str
    case_id: str
    request_id: str | None
    status: RunStatus
    schema_version: int
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        for name, value in (("run_id", self.run_id), ("case_id", self.case_id)):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if self.request_id is not None and not self.request_id.strip():
            raise ValueError("request_id cannot be empty")
        if self.schema_version < 1:
            raise ValueError("schema_version must be >= 1")
        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot precede created_at")


class CaseStateStore:
    """In-memory case-scoped state and run store with fail-closed invariants."""

    def __init__(self, case_registry: CaseRegistry, *, schema_version: int = 1) -> None:
        if schema_version < 1:
            raise ValueError("schema_version must be >= 1")
        self._case_registry = case_registry
        self._schema_version = schema_version
        self._states: dict[str, CaseState] = {}
        self._runs: dict[str, RunRecord] = {}
        self._request_index: dict[str, str] = {}
        self._run_counter = 0
        self._lock = RLock()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def initialize_case(self, case_id: str) -> CaseState:
        with self._lock:
            self._require_case(case_id)
            existing = self._states.get(case_id)
            if existing is not None:
                return existing
            now = self._now()
            state = CaseState(
                case_id=case_id,
                schema_version=self._schema_version,
                lifecycle_status="READY",
                created_at=now,
                updated_at=now,
            )
            self._states[case_id] = state
            return state

    def get_state(self, case_id: str) -> CaseState:
        with self._lock:
            self._require_case(case_id)
            state = self._states.get(case_id)
            if state is None:
                raise KeyError(f"case state not initialized: {case_id}")
            return state

    def update_state(self, case_id: str, *, last_run_id: str | None = None, **refs: str | None) -> CaseState:
        allowed = {
            "parties_ref", "documents_ref", "evidence_ref", "facts_ref",
            "assumptions_ref", "rules_ref", "calculations_ref",
            "optimization_ref", "challenges_ref", "approvals_ref", "outputs_ref",
        }
        unknown = set(refs) - allowed
        if unknown:
            raise ValueError(f"unknown state fields: {sorted(unknown)}")
        with self._lock:
            state = self.get_state(case_id)
            if last_run_id is not None:
                self._require_run_for_case(last_run_id, case_id)
            updated = replace(
                state,
                **refs,
                last_run_id=last_run_id if last_run_id is not None else state.last_run_id,
                updated_at=self._now(),
            )
            self._states[case_id] = updated
            return updated

    def create_run(self, case_id: str, *, request_id: str | None = None) -> RunRecord:
        with self._lock:
            self._require_case(case_id)
            self.initialize_case(case_id)
            if request_id is not None:
                if not request_id.strip():
                    raise ValueError("request_id cannot be empty")
                existing_run_id = self._request_index.get(request_id)
                if existing_run_id is not None:
                    existing = self._runs[existing_run_id]
                    if existing.case_id != case_id:
                        raise ValueError("request_id already belongs to another case")
                    return existing

            self._run_counter += 1
            run_id = f"RUN-{self._run_counter:08d}"
            now = self._now()
            run = RunRecord(
                run_id=run_id,
                case_id=case_id,
                request_id=request_id,
                status=RunStatus.CREATED,
                schema_version=self._schema_version,
                created_at=now,
                updated_at=now,
            )
            self._runs[run_id] = run
            if request_id is not None:
                self._request_index[request_id] = run_id
            self._states[case_id] = replace(
                self._states[case_id], last_run_id=run_id, updated_at=now
            )
            return run

    def get_run(self, case_id: str, run_id: str) -> RunRecord:
        with self._lock:
            self._require_case(case_id)
            run = self._runs.get(run_id)
            if run is None:
                raise KeyError(f"unknown run_id: {run_id}")
            if run.case_id != case_id:
                raise PermissionError("run belongs to another case")
            return run

    def transition_run(self, case_id: str, run_id: str, status: RunStatus) -> RunRecord:
        with self._lock:
            run = self.get_run(case_id, run_id)
            if status not in _ALLOWED_TRANSITIONS[run.status]:
                raise ValueError(
                    f"invalid run transition: {run.status.value} -> {status.value}"
                )
            updated = replace(run, status=status, updated_at=self._now())
            self._runs[run_id] = updated
            return updated

    def list_runs(self, case_id: str) -> tuple[RunRecord, ...]:
        with self._lock:
            self._require_case(case_id)
            return tuple(
                sorted(
                    (run for run in self._runs.values() if run.case_id == case_id),
                    key=lambda run: run.run_id,
                )
            )

    def validate(self) -> None:
        with self._lock:
            for run in self._runs.values():
                self._require_case(run.case_id)
                if run.request_id is not None and self._request_index.get(run.request_id) != run.run_id:
                    raise ValueError(f"request index mismatch: {run.run_id}")
            for case_id, state in self._states.items():
                self._require_case(case_id)
                if state.last_run_id is not None:
                    self._require_run_for_case(state.last_run_id, case_id)

    def _require_case(self, case_id: str) -> None:
        if not case_id or not case_id.strip():
            raise ValueError("case_id is required")
        if self._case_registry.get(case_id) is None:
            raise KeyError(f"unknown case_id: {case_id}")

    def _require_run_for_case(self, run_id: str, case_id: str) -> RunRecord:
        run = self._runs.get(run_id)
        if run is None:
            raise KeyError(f"unknown run_id: {run_id}")
        if run.case_id != case_id:
            raise PermissionError("run belongs to another case")
        return run
