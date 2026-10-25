"""Recoverable composition of durable case intent and create-only storage.

SQLite and the external provider are deliberately not presented as one
transaction.  The wrapped creator must provide idempotent exact-scope replay;
the existing GoogleDriveStorageScopeCreator does so through its private journal.
"""

from __future__ import annotations

import hashlib
import json
from typing import Callable, Protocol

from agent_lab.case_persistence import SQLiteCasePersistence, StorageProvisioningIntent
from agent_lab.case_registry import StorageScopeReference, TaxPeriod
from agent_lab.google_drive_provisioning import ProvisioningError


class IdempotentStorageCreator(Protocol):
    def create_case_scope(self, tax_period: TaxPeriod, case_id: str) -> StorageScopeReference: ...


class StorageReconciliationRequired(RuntimeError):
    pass


class DurableStorageProvisioningAdapter:
    """Persist intent before provider I/O and reconcile exact retries."""

    def __init__(
        self, persistence: SQLiteCasePersistence, creator: IdempotentStorageCreator,
        *, after_provider: Callable[[StorageScopeReference], None] | None = None,
    ) -> None:
        self._persistence = persistence
        self._creator = creator
        self._after_provider = after_provider

    @staticmethod
    def operation_id(*, request_id: str, owner_id: str, case_id: str, tax_year: int) -> str:
        if any(not value.strip() for value in (request_id, owner_id, case_id)):
            raise ValueError("complete provisioning identity is required")
        canonical = json.dumps(
            {"case_id": case_id, "owner_id": owner_id, "request_id": request_id, "tax_year": tax_year},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
        return "STORAGE-PROVISION:sha256:" + hashlib.sha256(canonical).hexdigest()

    def provision_case_scope(
        self, *, owner_id: str, tax_period: TaxPeriod, case_id: str, request_id: str,
    ) -> StorageScopeReference:
        operation_id = self.operation_id(
            request_id=request_id, owner_id=owner_id, case_id=case_id,
            tax_year=tax_period.year,
        )
        intent = self._persistence.prepare_storage_provisioning(
            operation_id=operation_id, request_id=request_id, owner_id=owner_id,
            case_id=case_id, tax_year=tax_period.year,
        )
        if intent.status == "COMPLETE":
            return self._scope(intent)
        if intent.status == "RECONCILIATION_REQUIRED":
            raise StorageReconciliationRequired("storage outcome is uncertain; explicit reconciliation required")

        self._persistence.transition_storage_provisioning(
            operation_id=operation_id,
            expected_statuses=frozenset({"INTENT", "IN_PROGRESS", "RETRYABLE_FAILURE"}),
            status="IN_PROGRESS",
        )
        try:
            scope = self._creator.create_case_scope(tax_period, case_id)
            if self._after_provider is not None:
                self._after_provider(scope)
        except ProvisioningError as exc:
            uncertain = "uncertain" in str(exc).casefold() or "requires inspection" in str(exc).casefold()
            self._persistence.transition_storage_provisioning(
                operation_id=operation_id, expected_statuses=frozenset({"IN_PROGRESS"}),
                status="RECONCILIATION_REQUIRED" if uncertain else "RETRYABLE_FAILURE",
                failure_code="PROVIDER_OUTCOME_UNCERTAIN" if uncertain else "PROVIDER_RETRYABLE_FAILURE",
            )
            if uncertain:
                raise StorageReconciliationRequired(
                    "storage outcome is uncertain; explicit reconciliation required"
                ) from None
            raise
        except Exception:
            self._persistence.transition_storage_provisioning(
                operation_id=operation_id, expected_statuses=frozenset({"IN_PROGRESS"}),
                status="RETRYABLE_FAILURE", failure_code="PROVIDER_FAILURE",
            )
            raise

        completed = self._persistence.transition_storage_provisioning(
            operation_id=operation_id, expected_statuses=frozenset({"IN_PROGRESS"}),
            status="COMPLETE", storage_scope=scope,
        )
        return self._scope(completed)

    @staticmethod
    def _scope(intent: StorageProvisioningIntent) -> StorageScopeReference:
        if intent.storage_provider is None or intent.storage_root_id is None:
            raise StorageReconciliationRequired("completed provisioning has no storage reference")
        return StorageScopeReference(intent.storage_provider, intent.storage_root_id)
