from agent_lab.google_drive_auth import SCOPES


def test_drive_oauth_scope_supports_authorized_case_migration_and_document_processing():
    # Full Drive scope was explicitly human-authorized on 2026-09-12 after
    # drive.file failed closed for pre-existing CASE-001 documents.
    assert set(SCOPES) == {"https://www.googleapis.com/auth/drive"}
