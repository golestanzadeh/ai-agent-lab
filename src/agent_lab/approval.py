"""Deterministic Human Approval Store and Gate for consequential actions."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from threading import RLock

from agent_lab.audit import ActorType, AuditEventType, AuditStatus, AuditStore


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    CONSUMED = "CONSUMED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class IntendedOperation(str, Enum):
    PHYSICAL_MIGRATION = "PHYSICAL_MIGRATION"


class ApprovalError(RuntimeError):
    """Base error for fail-closed approval operations."""


class InvalidApprovalError(ApprovalError):
    pass


class ApprovalNotFoundError(ApprovalError):
    pass


class ApprovalValidationError(ApprovalError):
    pass


class ApprovalAlreadyConsumedError(ApprovalValidationError):
    pass


@dataclass(frozen=True, slots=True)
class ApprovalExecutionContext:
    """Exact execution identity that an approval is permitted to authorize."""

    case_id: str
    run_id: str
    manifest_identity: str
    manifest_version: str
    manifest_reference: str
    preflight_identity: str
    preflight_reference: str
    preflight_result: str
    intended_operation: IntendedOperation
    actor: str


@dataclass(frozen=True, slots=True)
class MigrationApproval:
    """Immutable approval artifact; lifecycle changes create a new value."""

    approval_id: str
    case_id: str
    run_id: str
    manifest_identity: str
    manifest_version: str
    manifest_reference: str
    preflight_identity: str
    preflight_reference: str
    preflight_result: str
    intended_operation: IntendedOperation
    approver: str
    actor: str
    approval_timestamp: datetime
    authorization_reference: str
    approval_status: ApprovalStatus
    audit_reference: str


class ApprovalGate:
    """Own deterministic authorization and binding validation only."""

    @staticmethod
    def _required(name: str, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise InvalidApprovalError(f"{name} is required")

    @classmethod
    def validate_binding(
        cls, approval: MigrationApproval, context: ApprovalExecutionContext
    ) -> None:
        if not isinstance(approval, MigrationApproval):
            raise ApprovalValidationError("unknown approval artifact")
        if approval.approval_status is ApprovalStatus.CONSUMED:
            raise ApprovalAlreadyConsumedError("APPROVAL_ALREADY_CONSUMED")
        if approval.approval_status is not ApprovalStatus.APPROVED:
            raise ApprovalValidationError("approval is not APPROVED")
        if not isinstance(context, ApprovalExecutionContext):
            raise ApprovalValidationError("invalid execution context")
        required = (
            ("case_id", context.case_id),
            ("run_id", context.run_id),
            ("manifest_identity", context.manifest_identity),
            ("manifest_version", context.manifest_version),
            ("manifest_reference", context.manifest_reference),
            ("preflight_identity", context.preflight_identity),
            ("preflight_reference", context.preflight_reference),
            ("preflight_result", context.preflight_result),
            ("actor", context.actor),
        )
        for name, value in required:
            cls._required(name, value)
        if context.preflight_result != "PASSED":
            raise ApprovalValidationError("preflight result is not successful")
        if not isinstance(context.intended_operation, IntendedOperation):
            raise ApprovalValidationError("unknown intended operation")
        if approval.case_id != context.case_id or approval.run_id != context.run_id:
            raise ApprovalValidationError("case/run binding mismatch")
        if (
            approval.manifest_identity != context.manifest_identity
            or approval.manifest_version != context.manifest_version
            or approval.manifest_reference != context.manifest_reference
        ):
            raise ApprovalValidationError("manifest binding mismatch")
        if (
            approval.preflight_identity != context.preflight_identity
            or approval.preflight_reference != context.preflight_reference
            or approval.preflight_result != context.preflight_result
        ):
            raise ApprovalValidationError("preflight binding mismatch")
        if approval.intended_operation is not context.intended_operation:
            raise ApprovalValidationError("intended operation mismatch")
        if approval.actor != context.actor:
            raise ApprovalValidationError("actor binding mismatch")
        cls._required("approver", approval.approver)
        cls._required("authorization_reference", approval.authorization_reference)
        cls._required("audit_reference", approval.audit_reference)
        if approval.approval_timestamp.tzinfo is None:
            raise ApprovalValidationError("approval timestamp must be timezone-aware")


class ApprovalStore:
    """Own approval lifecycle and process-local atomic consumption."""

    def __init__(self, *, case_registry, case_state, audit_store: AuditStore) -> None:
        self._case_registry = case_registry
        self._case_state = case_state
        self._audit = audit_store
        self._approvals: dict[str, MigrationApproval] = {}
        self._counter = 0
        self._lock = RLock()

    def _require_scope(self, case_id: str, run_id: str) -> None:
        if self._case_registry.get(case_id) is None:
            raise InvalidApprovalError(f"unknown case_id: {case_id}")
        try:
            self._case_state.get_run(case_id, run_id)
        except (KeyError, PermissionError) as exc:
            raise InvalidApprovalError(f"run is outside case scope: {run_id}") from exc

    @staticmethod
    def _validate_timestamp(timestamp: datetime) -> None:
        if timestamp.tzinfo is None:
            raise InvalidApprovalError("timestamp must be timezone-aware")

    def _validate_common(self, **values: object) -> None:
        self._require_scope(values["case_id"], values["run_id"])
        for name in (
            "case_id", "run_id", "manifest_identity", "manifest_version",
            "manifest_reference", "preflight_identity", "preflight_reference",
            "preflight_result", "actor",
        ):
            ApprovalGate._required(name, values[name])
        if values["preflight_result"] != "PASSED":
            raise InvalidApprovalError("preflight result is not successful")
        if not isinstance(values["intended_operation"], IntendedOperation):
            raise InvalidApprovalError("unknown intended operation")

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
                case_id=case_id, run_id=run_id, manifest_identity=manifest_identity,
                manifest_version=manifest_version, manifest_reference=manifest_reference,
                preflight_identity=preflight_identity, preflight_reference=preflight_reference,
                preflight_result=preflight_result, intended_operation=intended_operation,
                actor=actor,
            )
            if (
                not isinstance(requester_actor_type, ActorType)
                or requester_actor_type not in {ActorType.HUMAN, ActorType.AGENT}
            ):
                raise InvalidApprovalError("approval requester must be HUMAN or AGENT")
            ts = timestamp or datetime.now(timezone.utc)
            self._validate_timestamp(ts)
            self._counter += 1
            approval_id = f"APP-{self._counter:08d}"
            approval = MigrationApproval(
                approval_id=approval_id, case_id=case_id, run_id=run_id,
                manifest_identity=manifest_identity, manifest_version=manifest_version,
                manifest_reference=manifest_reference, preflight_identity=preflight_identity,
                preflight_reference=preflight_reference, preflight_result=preflight_result,
                intended_operation=intended_operation, approver="", actor=actor,
                approval_timestamp=ts, authorization_reference="",
                approval_status=ApprovalStatus.PENDING, audit_reference="",
            )

            def commit(event) -> None:
                self._approvals[approval_id] = replace(approval, audit_reference=event.event_id)

            def rollback() -> None:
                self._approvals.pop(approval_id, None)
                self._counter -= 1

            self._audit.atomic_append(
                case_id=case_id, run_id=run_id,
                event_type=AuditEventType.APPROVAL_REQUESTED,
                actor_type=requester_actor_type, actor_id=actor,
                operation="request_approval", status=AuditStatus.INFO,
                approval_ref=approval_id,
                commit=commit, rollback=rollback,
            )
            return self._approvals[approval_id]

    def grant(
        self, approval_id: str, *, approver: str,
        authorization_reference: str, timestamp: datetime | None = None,
    ) -> MigrationApproval:
        with self._lock:
            approval = self.get(approval_id)
            if approval.approval_status is not ApprovalStatus.PENDING:
                raise ApprovalValidationError("only PENDING approval can be granted")
            ApprovalGate._required("approver", approver)
            ApprovalGate._required("authorization_reference", authorization_reference)
            ts = timestamp or datetime.now(timezone.utc)
            self._validate_timestamp(ts)

            def commit(event) -> None:
                self._approvals[approval_id] = replace(
                    approval, approver=approver, approval_timestamp=ts,
                    authorization_reference=authorization_reference,
                    approval_status=ApprovalStatus.APPROVED,
                    audit_reference=event.event_id,
                )

            def rollback() -> None:
                self._approvals[approval_id] = approval

            self._audit.atomic_append(
                case_id=approval.case_id, run_id=approval.run_id,
                event_type=AuditEventType.APPROVAL_GRANTED,
                actor_type=ActorType.HUMAN, actor_id=approver,
                operation="grant_approval", status=AuditStatus.SUCCESS,
                approval_ref=approval_id,
                metadata={"authorization_reference": authorization_reference},
                commit=commit, rollback=rollback,
            )
            return self._approvals[approval_id]

    def reject(self, approval_id: str, *, actor: str) -> MigrationApproval:
        return self._transition(
            approval_id, ApprovalStatus.REJECTED, actor,
            "reject_approval", AuditEventType.APPROVAL_REJECTED,
        )

    def revoke(self, approval_id: str, *, actor: str) -> MigrationApproval:
        return self._transition(
            approval_id, ApprovalStatus.REVOKED, actor,
            "revoke_approval", AuditEventType.APPROVAL_REVOKED,
        )

    def expire(self, approval_id: str, *, actor: str) -> MigrationApproval:
        return self._transition(
            approval_id, ApprovalStatus.EXPIRED, actor,
            "expire_approval", AuditEventType.APPROVAL_EXPIRED,
        )

    def _transition(self, approval_id, status, actor, operation, event_type):
        with self._lock:
            approval = self.get(approval_id)
            if status in {ApprovalStatus.REVOKED, ApprovalStatus.EXPIRED} and approval.approval_status is not ApprovalStatus.APPROVED:
                raise ApprovalValidationError("only APPROVED approval can be revoked or expired")
            if status is ApprovalStatus.REJECTED and approval.approval_status is not ApprovalStatus.PENDING:
                raise ApprovalValidationError("only PENDING approval can be rejected")
            ApprovalGate._required("actor", actor)

            def commit(event) -> None:
                self._approvals[approval_id] = replace(
                    approval, approval_status=status, audit_reference=event.event_id
                )

            def rollback() -> None:
                self._approvals[approval_id] = approval

            self._audit.atomic_append(
                case_id=approval.case_id, run_id=approval.run_id,
                event_type=event_type, actor_type=ActorType.HUMAN,
                actor_id=actor, operation=operation, status=AuditStatus.INFO,
                approval_ref=approval_id, commit=commit, rollback=rollback,
            )
            return self._approvals[approval_id]

    def get(self, approval_id: str) -> MigrationApproval:
        with self._lock:
            approval = self._approvals.get(approval_id)
            if approval is None:
                raise ApprovalNotFoundError(approval_id)
            return approval

    def validate(self, approval_id: str, context: ApprovalExecutionContext) -> MigrationApproval:
        with self._lock:
            approval = self.get(approval_id)
            ApprovalGate.validate_binding(approval, context)
            return approval

    def consume(self, approval_id: str, context: ApprovalExecutionContext) -> MigrationApproval:
        """Consume exactly once inside one process-local atomic boundary."""
        with self._lock:
            approval = self.get(approval_id)
            if approval.approval_status is ApprovalStatus.CONSUMED:
                raise ApprovalAlreadyConsumedError("APPROVAL_ALREADY_CONSUMED")
            ApprovalGate.validate_binding(approval, context)

            def commit(event) -> None:
                self._approvals[approval_id] = replace(
                    approval, approval_status=ApprovalStatus.CONSUMED,
                    audit_reference=event.event_id,
                )

            def rollback() -> None:
                self._approvals[approval_id] = approval

            self._audit.atomic_append(
                case_id=approval.case_id, run_id=approval.run_id,
                event_type=AuditEventType.APPROVAL_CONSUMED,
                actor_type=ActorType.SYSTEM, actor_id=context.actor,
                operation="consume_approval", status=AuditStatus.SUCCESS,
                approval_ref=approval_id,
                metadata={"intended_operation": context.intended_operation.value},
                commit=commit, rollback=rollback,
            )
            return self._approvals[approval_id]
