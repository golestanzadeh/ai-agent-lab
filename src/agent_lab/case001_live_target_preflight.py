"""Read-only validation of an explicit CASE-001 migration target scope."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent_lab.artifact_identity import ArtifactIdentity

from agent_lab.case001_migration_manifest import Case001MigrationManifest
from agent_lab.case001_migration_preflight import (
    Case001MigrationPreflight,
    MigrationPreflightError,
    MigrationPreflightResult,
)


class LiveTargetPreflightError(RuntimeError):
    """Base error for fail-closed live target validation."""


@dataclass(frozen=True, slots=True)
class LiveTargetScopeResult:
    target_object_id: str
    target_name: str
    target_mime_type: str
    target_is_folder: bool
    target_is_empty: bool
    child_count: int
    structural_preflight: MigrationPreflightResult
    manifest_identity: ArtifactIdentity | None = None


class GoogleDriveLiveTargetScopePreflight:
    """Validate an explicit Drive target folder without storage mutation."""

    FOLDER_MIME = "application/vnd.google-apps.folder"

    def __init__(self, *, drive_service: Any) -> None:
        self._drive = drive_service

    def run(self, manifest: Case001MigrationManifest, *, target_object_id: str) -> LiveTargetScopeResult:
        target_object_id = target_object_id.strip()
        if not target_object_id:
            raise LiveTargetPreflightError("target_object_id is required")

        metadata = self._get_metadata(target_object_id)
        if metadata.get("trashed", False):
            raise LiveTargetPreflightError("target folder is trashed")
        if str(metadata.get("mimeType", "")) != self.FOLDER_MIME:
            raise LiveTargetPreflightError("target object is not a folder")

        children = self._list_children(target_object_id)
        target_is_empty = len(children) == 0
        try:
            structural = Case001MigrationPreflight().run(
                manifest,
                target_scope_is_actual=True,
                target_is_empty=target_is_empty,
            )
        except MigrationPreflightError as exc:
            raise LiveTargetPreflightError(str(exc)) from exc

        return LiveTargetScopeResult(
            target_object_id=target_object_id,
            target_name=str(metadata.get("name", "")),
            target_mime_type=str(metadata.get("mimeType", "")),
            target_is_folder=True,
            target_is_empty=target_is_empty,
            child_count=len(children),
            structural_preflight=structural,
            manifest_identity=manifest.artifact_identity,
        )

    def _get_metadata(self, object_id: str) -> dict[str, Any]:
        try:
            return self._drive.files().get(
                fileId=object_id,
                fields="id,name,mimeType,parents,trashed",
            ).execute()
        except Exception as exc:
            raise LiveTargetPreflightError("target object is unavailable") from exc

    def _list_children(self, parent_id: str) -> tuple[dict[str, Any], ...]:
        page_token: str | None = None
        results: list[dict[str, Any]] = []
        while True:
            try:
                response = self._drive.files().list(
                    q=f"'{parent_id}' in parents and trashed = false",
                    spaces="drive",
                    fields="nextPageToken,files(id,name,mimeType,parents,trashed)",
                    pageToken=page_token,
                    orderBy="name",
                ).execute()
            except Exception as exc:
                raise LiveTargetPreflightError("cannot inspect target children") from exc
            results.extend(response.get("files", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                return tuple(results)
