"""Local Google Drive OAuth credential loading.

Keeps OAuth client configuration and the locally generated authorized-user
 token separate. Secrets and token files must remain outside the repository.
"""

from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = Path.home() / "ai-tax-agent" / "credentials.json"
TOKEN_FILE = Path.home() / "ai-tax-agent" / "token.json"


def get_drive_credentials() -> Credentials:
    """Load or obtain local OAuth credentials for authorized Drive access."""
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

