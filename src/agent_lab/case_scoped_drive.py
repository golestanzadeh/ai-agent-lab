"""Deterministic case-scoped storage resolver.

This module resolves a validated case_id through Case Registry and exposes
only the exact opaque storage scope recorded for that case. It does not scan
Drive, inspect documents, or infer ownership.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agent_lab.case_registry import CaseRegistry, CaseRecord, StorageScopeReference


class ScopeAccessStatus(str, Enum):
    RESOLVED = "RESOLVED"
    NOT_FOUND = "NOT_FOUND"
    INVALID_SCOPE = "INVALID_SCOPE"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


@dataclass(frozen=True, slots=True)
class ResolvedCaseScope:
    case_id: str
    storage_scope: StorageScopeReference


class CaseScopeError(RuntimeError):
    """Base error for fail-closed case-scope resolution."""


class CaseNotFoundError(CaseScopeError):
    pass


class InvalidCaseScopeError(CaseScopeError):
    pass


class OutOfScopeError(CaseScopeError):
    pass


class CaseScopedDriveResolver:
    """Resolve case storage only through the authoritative Case Registry."""

    def __init__(self, case_registry: CaseRegistry) -> None:
        self._case_registry = case_registry

    def resolve(self, case_id: str) -> ResolvedCaseScope:
        if not case_id or not case_id.strip():
            raise CaseNotFoundError("case_id is required")

        record = self._case_registry.get(case_id)
        if record is None:
            raise CaseNotFoundError(f"unknown case_id: {case_id}")

        self._validate_scope(record)
        return ResolvedCaseScope(case_id=record.case_id, storage_scope=record.storage_scope_reference)

    def assert_case_object(self, case_id: str, object_scope: StorageScopeReference) -> None:
        """Reject an object unless its provider/root exactly matches the case scope."""
        resolved = self.resolve(case_id)
        if resolved.storage_scope != object_scope:
            raise OutOfScopeError(
                f"storage object is outside case scope: {case_id}"
            )

    @staticmethod
    def _validate_scope(record: CaseRecord) -> None:
        scope = record.storage_scope_reference
        if not scope.provider.strip() or not scope.root_id.strip():
            raise InvalidCaseScopeError(
                f"invalid storage scope for case: {record.case_id}"
            )
