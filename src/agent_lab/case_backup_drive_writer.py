"""Drive API backup writer: independent immutable document snapshots, fail closed."""
from __future__ import annotations

import json
from hashlib import sha256
from io import BytesIO

from googleapiclient.http import MediaIoBaseUpload


FOLDER_MIME = "application/vnd.google-apps.folder"


def _children(drive, parent, name):
    result, token = [], None
    while True:
        page = drive.files().list(
            q=f"'{parent}' in parents and name = '{name}' and trashed = false",
            fields="nextPageToken,files(id,name,mimeType,parents,trashed)",
            pageSize=1000, pageToken=token,
        ).execute()
        result.extend(page.get("files", []))
        token = page.get("nextPageToken")
        if not token:
            return result


def _folder(drive, parent, name):
    existing = _children(drive, parent, name)
    if len(existing) > 1 or (existing and existing[0].get("mimeType") != FOLDER_MIME):
        raise RuntimeError("Ambiguous backup folder")
    if existing:
        return existing[0]["id"]
    created = drive.files().create(
        body={"name": name, "mimeType": FOLDER_MIME, "parents": [parent]},
        fields="id,name,mimeType,parents,trashed",
    ).execute()
    if (created.get("name") != name or created.get("mimeType") != FOLDER_MIME
            or created.get("parents") != [parent] or created.get("trashed") is not False):
        raise RuntimeError("Backup folder creation not verified")
    return created["id"]


def _upload_verified(drive, parent, name, data, mime):
    media = MediaIoBaseUpload(BytesIO(data), mimetype=mime, resumable=False)
    obj = drive.files().create(
        body={"name": name, "parents": [parent]}, media_body=media,
        fields="id,name,size,parents,trashed",
    ).execute()
    if (obj.get("name") != name or obj.get("parents") != [parent]
            or obj.get("trashed") is not False or int(obj.get("size", -1)) != len(data)):
        raise RuntimeError("Backup upload metadata mismatch")
    # Read the remote bytes, not only the provider's upload acknowledgement.
    remote = drive.files().get_media(fileId=obj["id"]).execute()
    if sha256(remote).digest() != sha256(data).digest():
        raise RuntimeError("Backup upload digest mismatch")
    return obj["id"]


def write_document_snapshot(host, request, path):
    """Shared MANUAL/PRE_DELETE writer; does not delete or alter the source."""
    from agent_lab.case_backup_preflight import verify_case_backup_source
    from agent_lab.google_drive_auth import get_drive_credentials
    from googleapiclient.discovery import build
    import os

    with host._lock:
        preflight = verify_case_backup_source(host, request.case_id, request.tax_year)
        if not preflight["source_verified"]:
            raise RuntimeError("Unverified source")
        drive = build("drive", "v3", credentials=get_drive_credentials(), cache_discovery=False)
        root = os.environ["AI_TAX_AGENT_DRIVE_ROOT_ID"]
        root_meta = drive.files().get(fileId=root, fields="id,mimeType,trashed").execute()
        if root_meta.get("mimeType") != FOLDER_MIME or root_meta.get("trashed") is not False:
            raise RuntimeError("Untrusted Drive root")
        base = _folder(drive, root, path[0])
        identity_folder = _folder(drive, base, path[1])
        if _children(drive, identity_folder, path[2]):
            raise RuntimeError("Backup version already exists; no overwrite")
        version = _folder(drive, identity_folder, path[2])
        manifest_files = []
        for entry in preflight["documents"]:
            _, content = host.get_case_document(request.case_id, request.tax_year, entry["id"])
            if sha256(content).hexdigest() != entry["sha256"]:
                raise RuntimeError("Source changed while backing up")
            stored_id = _upload_verified(drive, version, entry["id"], content, "application/octet-stream")
            manifest_files.append({**entry, "backup_drive_id": stored_id})
        manifest = {
            "schema": "case-document-snapshot/1",
            "backup_id": request.backup_id,
            "case_identity": request.case_identity,
            "case_id": request.case_id,
            "tax_year": request.tax_year,
            "trigger": request.trigger.value,
            "source_root_id": preflight["storage_root_id"],
            "documents": manifest_files,
            "scope": "DOCUMENTS_ONLY_NOT_RESTORABLE_CASE",
        }
        blob = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        manifest_id = _upload_verified(drive, version, "manifest.json", blob, "application/json")
        return {
            "backup_id": request.backup_id,
            "path": path,
            "verified": True,
            "scope": "DOCUMENTS_ONLY_NOT_RESTORABLE_CASE",
            "folder_id": version,
            "manifest_id": manifest_id,
            "document_count": len(manifest_files),
            "manifest_sha256": sha256(blob).hexdigest(),
        }
