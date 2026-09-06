"""Minimal Google Drive API smoke test.

This test authenticates with the local OAuth desktop credential and lists only
metadata for the AI-Tax-Agent folder. It does not read, modify, upload, or
process any tax documents.
"""

from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]
CREDENTIALS_FILE = Path.home() / "ai-tax-agent" / "credentials.json"
TOKEN_FILE = Path.home() / "ai-tax-agent" / "token.json"
TARGET_FOLDER_NAME = "AI-Tax-Agent"


def get_credentials() -> Credentials:
    """Load or obtain OAuth credentials without storing secrets in the repo."""
    credentials = None

    if TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    elif not credentials or not credentials.valid:
        if not CREDENTIALS_FILE.exists():
            raise FileNotFoundError(
                f"OAuth credential file not found: {CREDENTIALS_FILE}"
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
        credentials = flow.run_local_server(port=0)

    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
    return credentials


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
    credentials = get_credentials()
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
