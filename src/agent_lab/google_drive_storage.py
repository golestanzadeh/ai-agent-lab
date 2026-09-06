"""Metadata-only Google Drive adapter with deterministic case containment.

The adapter never performs a Drive-wide search. A case_id is resolved through
CaseScopedDriveResolver to obtain the exact registered Drive root. Explicit
object reads then verify the object's parent chain terminates at that root.
"""

from __future__ import annotations

from typing import Any

from agent_lab.case_scoped_drive import CaseScopedDriveResolver, OutOfScopeError
from agent_lab.storage import StorageAdapterError, StorageObjectMetadata, StorageObjectNotFoundError


class GoogleDriveStorageError(StorageAdapterError):
    """Base error for Google Drive adapter failures."""


class GoogleDriveScopeError(GoogleDriveStorageError):
    pass


class GoogleDriveMetadataAdapter:
    """Case-scoped metadata adapter over an injected Google Drive service."""

    PROVIDER = "google_drive"
    FOLDER_MIME = "application/vnd.google-apps.folder"

    def __init__(self, *, drive_service: Any, resolver: CaseScopedDriveResolver, max_ancestry_depth: int = 100) -> None:
        if max_ancestry_depth < 1:
            raise ValueError("max_ancestry_depth must be >= 1")
        self._drive = drive_service
        self._resolver = resolver
        self._max_ancestry_depth = max_ancestry_depth

    def list_children(self, case_id: str) -> tuple[StorageObjectMetadata, ...]:
        scope = self._resolver.resolve(case_id).storage_scope
        if scope.provider != self.PROVIDER:
            raise GoogleDriveScopeError("case storage provider is not Google Drive")

        page_token: str | None = None
        results: list[StorageObjectMetadata] = []
        while True:
            request = self._drive.files().list(
                q=f"'{scope.root_id}' in parents and trashed = false",
                spaces="drive",
                fields="nextPageToken,files(id,name,mimeType,parents,trashed)",
                pageToken=page_token,
                orderBy="name",
            )
            response = request.execute()
            for item in response.get("files", []):
                metadata = self._normalize(item)
                self._assert_contained(scope.root_id, metadata.object_id)
                results.append(metadata)
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return tuple(results)

    def get_metadata(self, case_id: str, object_id: str) -> StorageObjectMetadata:
        scope = self._resolver.resolve(case_id).storage_scope
        if scope.provider != self.PROVIDER:
            raise GoogleDriveScopeError("case storage provider is not Google Drive")
        if not object_id or not object_id.strip():
            raise StorageObjectNotFoundError("object_id is required")

        try:
            item = self._drive.files().get(
                fileId=object_id,
                fields="id,name,mimeType,parents,trashed",
            ).execute()
        except Exception as exc:  # provider-specific errors are intentionally normalized
            raise StorageObjectNotFoundError(f"Google Drive object unavailable: {object_id}") from exc

        metadata = self._normalize(item)
        if metadata.object_id != object_id or item.get("trashed", False):
            raise StorageObjectNotFoundError(f"object is unavailable: {object_id}")
        self._assert_contained(scope.root_id, object_id)
        return metadata

    def _assert_contained(self, root_id: str, object_id: str) -> None:
        if object_id == root_id:
            return

        current_id = object_id
        visited: set[str] = set()
        for _ in range(self._max_ancestry_depth):
            if current_id in visited:
                raise GoogleDriveScopeError("cyclic or malformed Drive ancestry")
            visited.add(current_id)
            try:
                item = self._drive.files().get(
                    fileId=current_id,
                    fields="id,parents,trashed",
                ).execute()
            except Exception as exc:
                raise OutOfScopeError(f"cannot verify Drive object ancestry: {object_id}") from exc

            if item.get("trashed", False):
                raise OutOfScopeError(f"trashed object is outside active case scope: {object_id}")
            parents = tuple(item.get("parents", ()))
            if root_id in parents:
                return
            if not parents:
                raise OutOfScopeError(f"Drive object is not a descendant of case root: {object_id}")
            if len(parents) != 1:
                raise OutOfScopeError(f"ambiguous Drive ancestry for object: {object_id}")
            current_id = parents[0]

        raise OutOfScopeError(f"Drive ancestry exceeds configured safety depth: {object_id}")

    @staticmethod
    def _normalize(item: dict[str, Any]) -> StorageObjectMetadata:
        object_id = str(item.get("id", "")).strip()
        if not object_id:
            raise GoogleDriveStorageError("Drive response omitted object id")
        return StorageObjectMetadata(
            object_id=object_id,
            name=str(item.get("name", "")),
            mime_type=str(item.get("mimeType", "")),
            parent_ids=tuple(str(parent) for parent in item.get("parents", ())),
            is_folder=str(item.get("mimeType", "")) == GoogleDriveMetadataAdapter.FOLDER_MIME,
        )
