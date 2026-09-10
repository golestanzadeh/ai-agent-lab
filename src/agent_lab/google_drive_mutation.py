"""Guarded Google Drive mutation adapter for explicit object-parent moves only.

This adapter intentionally exposes no name search and no Drive-wide discovery.
It operates only on object IDs supplied by the caller and verifies single-parent
state before and after each mutation.
"""

from __future__ import annotations

from typing import Any


class GoogleDriveMutationError(RuntimeError):
    """Base fail-closed error for guarded Drive mutation operations."""


class GoogleDriveMutationScopeError(GoogleDriveMutationError):
    pass


class GoogleDriveMutationAdapter:
    """Narrow mutation port used by the controlled migration executor."""

    def __init__(self, *, drive_service: Any) -> None:
        self._drive = drive_service

    def list_children(self, parent_id: str) -> tuple[str, ...]:
        parent_id = self._required("parent_id", parent_id)
        page_token: str | None = None
        object_ids: list[str] = []
        while True:
            try:
                response = self._drive.files().list(
                    q=f"'{parent_id}' in parents and trashed = false",
                    spaces="drive",
                    fields="nextPageToken,files(id,parents,trashed)",
                    pageToken=page_token,
                    orderBy="name",
                ).execute()
            except Exception as exc:
                raise GoogleDriveMutationError("cannot list explicit parent children") from exc
            for item in response.get("files", []):
                object_id = self._required("object_id", str(item.get("id", "")))
                if item.get("trashed", False):
                    raise GoogleDriveMutationScopeError("listed child is unexpectedly trashed")
                parents = tuple(str(parent) for parent in item.get("parents", ()))
                if parents != (parent_id,):
                    raise GoogleDriveMutationScopeError("listed child has ambiguous or mismatched parent")
                object_ids.append(object_id)
            page_token = response.get("nextPageToken")
            if not page_token:
                return tuple(object_ids)

    def get_parent(self, object_id: str) -> str:
        object_id = self._required("object_id", object_id)
        item = self._get(object_id)
        parents = tuple(str(parent) for parent in item.get("parents", ()))
        if len(parents) != 1:
            raise GoogleDriveMutationScopeError("Drive object must have exactly one parent")
        return self._required("parent_id", parents[0])

    def move(
        self,
        object_id: str,
        new_parent_id: str,
        *,
        expected_old_parent_id: str,
    ) -> None:
        object_id = self._required("object_id", object_id)
        new_parent_id = self._required("new_parent_id", new_parent_id)
        expected_old_parent_id = self._required(
            "expected_old_parent_id", expected_old_parent_id
        )
        if new_parent_id == expected_old_parent_id:
            raise GoogleDriveMutationScopeError("new and old parent must differ")

        actual_parent = self.get_parent(object_id)
        if actual_parent != expected_old_parent_id:
            raise GoogleDriveMutationScopeError("guarded old parent mismatch")

        try:
            response = self._drive.files().update(
                fileId=object_id,
                addParents=new_parent_id,
                removeParents=expected_old_parent_id,
                fields="id,parents,trashed",
            ).execute()
        except Exception as exc:
            raise GoogleDriveMutationError("guarded Drive parent move failed") from exc

        if str(response.get("id", "")) != object_id:
            raise GoogleDriveMutationError("Drive move response object mismatch")
        if response.get("trashed", False):
            raise GoogleDriveMutationError("Drive move returned trashed object")
        parents = tuple(str(parent) for parent in response.get("parents", ()))
        if parents != (new_parent_id,):
            raise GoogleDriveMutationError("Drive move response parent mismatch")

        verified_parent = self.get_parent(object_id)
        if verified_parent != new_parent_id:
            raise GoogleDriveMutationError("Drive move post-verification failed")

    def _get(self, object_id: str) -> dict[str, Any]:
        try:
            item = self._drive.files().get(
                fileId=object_id,
                fields="id,parents,trashed",
            ).execute()
        except Exception as exc:
            raise GoogleDriveMutationError("Drive object unavailable") from exc
        if str(item.get("id", "")) != object_id or item.get("trashed", False):
            raise GoogleDriveMutationError("Drive object identity/state mismatch")
        return item

    @staticmethod
    def _required(name: str, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise GoogleDriveMutationScopeError(f"{name} is required")
        return value.strip()
