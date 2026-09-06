"""Provider-neutral, case-scoped storage contract.

Higher-level tax workflow code depends on this contract rather than a
specific storage provider. Every case-data operation is explicitly bound to
one case_id and receives its scope from the case-scoped resolver boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from agent_lab.case_registry import StorageScopeReference
from agent_lab.case_scoped_drive import CaseScopedDriveResolver


@dataclass(frozen=True, slots=True)
class StorageObjectMetadata:
    """Minimal normalized metadata for a case-scoped storage object."""

    object_id: str
    name: str
    mime_type: str
    parent_ids: tuple[str, ...]
    is_folder: bool


class CaseScopedStorageAdapter(Protocol):
    """Only case-scoped storage operations belong in this interface."""

    def list_children(self, case_id: str) -> tuple[StorageObjectMetadata, ...]: ...

    def get_metadata(self, case_id: str, object_id: str) -> StorageObjectMetadata: ...


class StorageAdapterError(RuntimeError):
    """Base error for storage adapter failures."""


class StorageObjectNotFoundError(StorageAdapterError):
    pass


class StorageObjectOutOfScopeError(StorageAdapterError):
    pass


class CaseScopedStorage:
    """Enforce resolver-derived scope before delegating to a provider adapter."""

    def __init__(self, resolver: CaseScopedDriveResolver, provider: CaseScopedStorageAdapter) -> None:
        self._resolver = resolver
        self._provider = provider

    def list_children(self, case_id: str) -> tuple[StorageObjectMetadata, ...]:
        self._resolver.resolve(case_id)
        return self._provider.list_children(case_id)

    def get_metadata(self, case_id: str, object_id: str) -> StorageObjectMetadata:
        self._resolver.resolve(case_id)
        if not object_id or not object_id.strip():
            raise StorageObjectNotFoundError("object_id is required")
        return self._provider.get_metadata(case_id, object_id)


class InMemoryCaseScopedStorageAdapter:
    """Small deterministic provider used for adapter contract tests."""

    def __init__(self, scopes: dict[str, StorageScopeReference]) -> None:
        self._scopes = dict(scopes)
        self._objects: dict[str, dict[str, StorageObjectMetadata]] = {
            case_id: {} for case_id in scopes
        }

    def add_object(self, case_id: str, metadata: StorageObjectMetadata) -> None:
        if case_id not in self._scopes:
            raise KeyError(f"unknown case_id: {case_id}")
        self._objects[case_id][metadata.object_id] = metadata

    def list_children(self, case_id: str) -> tuple[StorageObjectMetadata, ...]:
        if case_id not in self._objects:
            raise StorageObjectNotFoundError(f"unknown case_id: {case_id}")
        return tuple(sorted(self._objects[case_id].values(), key=lambda item: item.object_id))

    def get_metadata(self, case_id: str, object_id: str) -> StorageObjectMetadata:
        objects = self._objects.get(case_id)
        if objects is None:
            raise StorageObjectNotFoundError(f"unknown case_id: {case_id}")
        metadata = objects.get(object_id)
        if metadata is None:
            raise StorageObjectNotFoundError(f"object is not in case scope: {object_id}")
        return metadata
