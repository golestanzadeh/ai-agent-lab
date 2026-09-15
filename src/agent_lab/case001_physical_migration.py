"""Controlled CASE-001 physical migration executor.

The executor is provider-port based and contains no Drive credentials or global
search capability. DRY_RUN is the default. LIVE requires explicit enablement
and exact durable approval validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from agent_lab.approval import ApprovalExecutionContext, ApprovalStatus
from agent_lab.case001_migration_manifest import Case001MigrationManifest
from agent_lab.durable_approval import DurableApprovalStore


class PhysicalMigrationError(RuntimeError):
    """Base fail-closed error for controlled physical migration."""


class PhysicalMigrationPreconditionError(PhysicalMigrationError):
    pass


class PhysicalMigrationVerificationError(PhysicalMigrationError):
    pass


class PhysicalMigrationRollbackError(PhysicalMigrationError):
    def __init__(self, message: str, *, object_ids: tuple[str, ...]) -> None:
        super().__init__(message)
        self.object_ids = object_ids


class MigrationMode(str, Enum):
    DRY_RUN = "DRY_RUN"
    LIVE = "LIVE"


@dataclass(frozen=True, slots=True)
class PhysicalMigrationResult:
    mode: MigrationMode
    case_id: str
    document_count: int
    moved_object_ids: tuple[str, ...]
    verified: bool
    approval_consumed: bool


@runtime_checkable
class StorageMutationPort(Protocol):
    def list_children(self, parent_id: str) -> tuple[str, ...]: ...

    def get_parent(self, object_id: str) -> str: ...

    def move(
        self,
        object_id: str,
        new_parent_id: str,
        *,
        expected_old_parent_id: str,
    ) -> None: ...


class Case001PhysicalMigrationExecutor:
    """Deterministically move an accepted CASE-001 manifest between parents."""

    def __init__(self, *, storage: StorageMutationPort) -> None:
        if not isinstance(storage, StorageMutationPort):
            raise TypeError("storage must implement StorageMutationPort")
        self._storage = storage

    def execute(
        self,
        manifest: Case001MigrationManifest,
        *,
        source_parent_id: str,
        target_parent_id: str,
        mode: MigrationMode = MigrationMode.DRY_RUN,
        live_enabled: bool = False,
        approval_store: DurableApprovalStore | None = None,
        approval_id: str | None = None,
        approval_context: ApprovalExecutionContext | None = None,
    ) -> PhysicalMigrationResult:
        self._validate_manifest_and_parameters(
            manifest,
            source_parent_id=source_parent_id,
            target_parent_id=target_parent_id,
        )
        expected_ids = tuple(mapping.source_object_id for mapping in manifest.mappings)

        if mode is MigrationMode.LIVE:
            if live_enabled is not True:
                raise PhysicalMigrationPreconditionError("live execution is not explicitly enabled")
            if approval_store is None or not approval_id or approval_context is None:
                raise PhysicalMigrationPreconditionError(
                    "live execution requires durable approval store, approval_id, and context"
                )
            approval = approval_store.validate(approval_id, approval_context)
            if approval.approval_status is not ApprovalStatus.APPROVED:
                raise PhysicalMigrationPreconditionError("durable approval is not APPROVED")
        elif mode is not MigrationMode.DRY_RUN:
            raise PhysicalMigrationPreconditionError("unknown migration mode")

        self._validate_storage_preconditions(
            expected_ids,
            source_parent_id=source_parent_id,
            target_parent_id=target_parent_id,
        )

        if mode is MigrationMode.DRY_RUN:
            return PhysicalMigrationResult(
                mode=mode,
                case_id=manifest.case_id,
                document_count=len(expected_ids),
                moved_object_ids=(),
                verified=True,
                approval_consumed=False,
            )

        applied: list[str] = []
        try:
            for object_id in expected_ids:
                self._storage.move(
                    object_id,
                    target_parent_id,
                    expected_old_parent_id=source_parent_id,
                )
                applied.append(object_id)

            self._verify_post_state(
                expected_ids,
                source_parent_id=source_parent_id,
                target_parent_id=target_parent_id,
            )

            consumed = approval_store.consume(approval_id, approval_context)
            if consumed.approval_status is not ApprovalStatus.CONSUMED:
                raise PhysicalMigrationVerificationError(
                    "approval consumption did not reach CONSUMED"
                )
        except Exception as exc:
            rollback_failures = self._rollback(
                tuple(applied),
                source_parent_id=source_parent_id,
                target_parent_id=target_parent_id,
            )
            if rollback_failures:
                raise PhysicalMigrationRollbackError(
                    "physical migration failed and rollback was incomplete",
                    object_ids=rollback_failures,
                ) from exc
            raise

        return PhysicalMigrationResult(
            mode=mode,
            case_id=manifest.case_id,
            document_count=len(expected_ids),
            moved_object_ids=expected_ids,
            verified=True,
            approval_consumed=True,
        )

    @staticmethod
    def _validate_manifest_and_parameters(
        manifest: Case001MigrationManifest,
        *,
        source_parent_id: str,
        target_parent_id: str,
    ) -> None:
        if not isinstance(manifest, Case001MigrationManifest):
            raise PhysicalMigrationPreconditionError("invalid CASE-001 manifest")
        if manifest.case_id != "CASE-001" or manifest.tax_period_year != 2024:
            raise PhysicalMigrationPreconditionError("unexpected migration case or tax period")
        if not source_parent_id.strip() or not target_parent_id.strip():
            raise PhysicalMigrationPreconditionError("source and target parent IDs are required")
        if source_parent_id == target_parent_id:
            raise PhysicalMigrationPreconditionError("source and target parents must differ")
        if not manifest.mappings:
            raise PhysicalMigrationPreconditionError("migration manifest is empty")

        object_ids: set[str] = set()
        logical_ids: set[str] = set()
        for mapping in manifest.mappings:
            if mapping.source_provider != manifest.source_provider:
                raise PhysicalMigrationPreconditionError("mapping provider mismatch")
            if mapping.source_scope_ref != manifest.source_scope_ref:
                raise PhysicalMigrationPreconditionError("mapping source scope mismatch")
            if mapping.target_scope_ref != manifest.target_scope_ref:
                raise PhysicalMigrationPreconditionError("mapping target scope mismatch")
            if mapping.source_object_id in object_ids:
                raise PhysicalMigrationPreconditionError("duplicate source object")
            if mapping.logical_document_id in logical_ids:
                raise PhysicalMigrationPreconditionError("duplicate logical document")
            object_ids.add(mapping.source_object_id)
            logical_ids.add(mapping.logical_document_id)

    def _validate_storage_preconditions(
        self,
        expected_ids: tuple[str, ...],
        *,
        source_parent_id: str,
        target_parent_id: str,
    ) -> None:
        target_children = tuple(self._storage.list_children(target_parent_id))
        if target_children:
            raise PhysicalMigrationPreconditionError("target parent is not empty")
        source_children = set(self._storage.list_children(source_parent_id))
        for object_id in expected_ids:
            if object_id not in source_children:
                raise PhysicalMigrationPreconditionError(
                    f"expected source object is absent: {object_id}"
                )
            if self._storage.get_parent(object_id) != source_parent_id:
                raise PhysicalMigrationPreconditionError(
                    f"source object parent mismatch: {object_id}"
                )

    def _verify_post_state(
        self,
        expected_ids: tuple[str, ...],
        *,
        source_parent_id: str,
        target_parent_id: str,
    ) -> None:
        target_children = tuple(self._storage.list_children(target_parent_id))
        if set(target_children) != set(expected_ids) or len(target_children) != len(expected_ids):
            raise PhysicalMigrationVerificationError("target contents do not exactly match manifest")
        source_children = set(self._storage.list_children(source_parent_id))
        for object_id in expected_ids:
            if object_id in source_children:
                raise PhysicalMigrationVerificationError(
                    f"migrated object still appears under source: {object_id}"
                )
            if self._storage.get_parent(object_id) != target_parent_id:
                raise PhysicalMigrationVerificationError(
                    f"migrated object parent mismatch: {object_id}"
                )

    def _rollback(
        self,
        applied: tuple[str, ...],
        *,
        source_parent_id: str,
        target_parent_id: str,
    ) -> tuple[str, ...]:
        failures: list[str] = []
        for object_id in reversed(applied):
            try:
                self._storage.move(
                    object_id,
                    source_parent_id,
                    expected_old_parent_id=target_parent_id,
                )
            except Exception:
                failures.append(object_id)
        return tuple(failures)
