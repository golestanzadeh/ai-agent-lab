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

    def read_protected_revision(self, case_id, reference, *, now, max_bytes=1024*1024):
        """Read only an exact binary revision under the registered case root.

        This verifies bytes and containment. It does not authenticate the
        reference authority or grant source/custody acceptance.
        """
        import io
        from googleapiclient.http import MediaIoBaseDownload
        from agent_lab.identity_protected_revision import ProtectedReference,MaterializedRevision,verify_protected_revision
        if not isinstance(reference,ProtectedReference) or type(max_bytes) is not int or not 0<max_bytes<=1024*1024:
            raise GoogleDriveScopeError("typed bounded protected reference required")
        scope=self._resolver.resolve(case_id).storage_scope
        revision=reference.revision
        if (reference.scope.case_id!=case_id or revision.provider!=self.PROVIDER or scope.provider!=self.PROVIDER
                or revision.root_id!=scope.root_id or revision.object_id==scope.root_id
                or revision.revision_id.casefold() in {"head","latest",""}
                or reference.revoked_at is not None or reference.expires_at<=now):
            raise GoogleDriveScopeError("protected source scope/lease unavailable")
        before=self._assert_contained(scope.root_id,revision.object_id,capture_versions=True)
        metadata=self._drive.revisions().get(fileId=revision.object_id,revisionId=revision.revision_id,
            fields="id,mimeType,size").execute(num_retries=0)
        size=metadata.get("size")
        mime=metadata.get("mimeType")
        if (metadata.get("id")!=revision.revision_id or not isinstance(size,str) or not size.isascii() or not size.isdecimal()
                or str(int(size))!=size or not 0<int(size)<=max_bytes or not isinstance(mime,str)
                or mime.startswith("application/vnd.google-apps.")):
            raise GoogleDriveScopeError("exact bounded binary revision unavailable")
        class BoundedBuffer(io.BytesIO):
            def write(self, data):
                if self.tell()+len(data)>max_bytes:
                    raise GoogleDriveScopeError("protected revision exceeds bound")
                return super().write(data)
        stream=BoundedBuffer()
        request=self._drive.revisions().get_media(fileId=revision.object_id,revisionId=revision.revision_id)
        download=MediaIoBaseDownload(stream,request,chunksize=min(65536,max_bytes))
        done=False
        for _ in range((int(size)+min(65536,max_bytes)-1)//min(65536,max_bytes)+1):
            previous=stream.tell()
            _,done=download.next_chunk(num_retries=0)
            if download._uri!=request.uri or stream.tell()<=previous or stream.tell()>int(size):
                raise GoogleDriveScopeError("protected media progress/source mismatch")
            if done:
                break
        if not done:
            raise GoogleDriveScopeError("protected media did not complete within bound")
        raw=stream.getvalue()
        if len(raw)!=int(size) or before!=self._assert_contained(scope.root_id,revision.object_id,capture_versions=True):
            raise GoogleDriveScopeError("protected revision length or containment changed")
        observed=MaterializedRevision(revision,raw)
        verify_protected_revision(reference,observed,committed_provider=scope.provider,committed_root=scope.root_id,
            expected_scope=reference.scope,now=now,max_bytes=max_bytes)
        return observed

    def _assert_contained(self, root_id: str, object_id: str, *, capture_versions=False):
        if object_id == root_id:
            return

        current_id = object_id
        visited: set[str] = set()
        versions=[]
        for _ in range(self._max_ancestry_depth):
            if current_id in visited:
                raise GoogleDriveScopeError("cyclic or malformed Drive ancestry")
            visited.add(current_id)
            try:
                item = self._drive.files().get(
                    fileId=current_id,
                    fields="id,parents,trashed,version" if capture_versions else "id,parents,trashed",
                ).execute()
            except Exception as exc:
                raise OutOfScopeError(f"cannot verify Drive object ancestry: {object_id}") from exc

            if item.get("trashed", False):
                raise OutOfScopeError(f"trashed object is outside active case scope: {object_id}")
            parents = tuple(item.get("parents", ()))
            if capture_versions:
                version=item.get("version")
                if (item.get("id")!=current_id or len(parents)!=1 or not isinstance(version,str)
                        or not version.isascii() or not version.isdecimal() or str(int(version))!=version):
                    raise GoogleDriveScopeError("stable exact ancestry identity required")
                versions.append((current_id,parents[0],version))
            if root_id in parents:
                return tuple(versions) if capture_versions else None
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
