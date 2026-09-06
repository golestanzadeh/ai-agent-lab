"""Minimal Google Drive API smoke test.

This test authenticates with the local OAuth desktop credential and lists only
metadata for the AI-Tax-Agent folder. It does not read, modify, upload, or
process any tax documents.
"""

from __future__ import annotations

from googleapiclient.discovery import build

from agent_lab.google_drive_auth import get_drive_credentials

TARGET_FOLDER_NAME = "AI-Tax-Agent"


def find_target_folder(service):
    """Return metadata for the target folder, if it exists."""
    query = (
        "name = 'AI-Tax-Agent' "
        "and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    )
    response = (
        service.files()
        .list(
            q=query,
            spaces="drive",
            fields="files(id,name,mimeType)",
            pageSize=10,
        )
        .execute()
    )
    return response.get("files", [])


def main() -> None:
    credentials = get_drive_credentials()
    service = build("drive", "v3", credentials=credentials)
    folders = find_target_folder(service)

    if not folders:
        print("Google Drive smoke test: AUTH OK; AI-Tax-Agent folder NOT FOUND")
        return

    print("Google Drive smoke test: PASS")
    for folder in folders:
        print(f"Folder: {folder['name']} | ID: {folder['id']}")


if __name__ == "__main__":
    main()
