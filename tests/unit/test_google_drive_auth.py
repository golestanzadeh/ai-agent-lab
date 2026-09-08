from agent_lab.google_drive_auth import SCOPES


def test_drive_oauth_scopes_support_metadata_read_and_agent_managed_files():
    assert set(SCOPES) == {
        "https://www.googleapis.com/auth/drive.metadata.readonly",
        "https://www.googleapis.com/auth/drive.file",
    }
