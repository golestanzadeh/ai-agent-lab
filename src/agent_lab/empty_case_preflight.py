"""Fail-closed, read-only preflight for empty-case deletion.

No mutation is performed. A separate audited two-store deletion transaction is
required before a destructive action can be enabled.
"""
from __future__ import annotations

from dataclasses import dataclass


class EmptyCaseBlocked(RuntimeError):
    pass


@dataclass(frozen=True)
class EmptyCaseReadiness:
    case_id: str
    tax_year: int
    sqlite_ready: bool
    drive_ready: bool
    reason: str


def inspect_empty_case(persistence, drive, *, owner_id: str, case_id: str, tax_year: int):
    """Check canonical SQLite first, then verify exact Drive folder descendants."""
    with persistence._lock:
        persistence._verify_all()
        persistence._verify_anchor()
        persistence._authorize(owner_id, case_id, tax_year)
        row = persistence._db.execute(
            "SELECT lifecycle_status,storage_provider,storage_root_id FROM case_record "
            "WHERE case_id=? AND owner_id=? AND tax_year=?",
            (case_id, owner_id, tax_year),
        ).fetchone()
        if row is None or row['lifecycle_status'] != 'CREATED':
            raise EmptyCaseBlocked('Case lifecycle is not eligible for empty-case deletion')
        if row['storage_provider'] != 'google_drive':
            raise EmptyCaseBlocked('Unverified storage provider')
        for table in ('durable_run', 'mutation_request'):
            if persistence._db.execute(f'SELECT 1 FROM {table} WHERE case_id=? LIMIT 1', (case_id,)).fetchone():
                raise EmptyCaseBlocked('SQLite contains case dependencies')
        state = persistence._db.execute('SELECT payload FROM case_state WHERE case_id=?', (case_id,)).fetchone()
        if state is None:
            raise EmptyCaseBlocked('Missing case state')
        import json
        data = json.loads(state['payload'])
        if any(data.get(field) for field in (
            'documents_ref', 'evidence_ref', 'facts_ref', 'calculations_ref',
            'outputs_ref', 'approvals_ref', 'last_run_id')):
            raise EmptyCaseBlocked('SQLite state contains document or execution references')
        intent = persistence._db.execute(
            'SELECT status,storage_root_id FROM storage_provisioning WHERE case_id=? AND owner_id=? AND tax_year=?',
            (case_id, owner_id, tax_year),
        ).fetchone()
        if intent is None or intent['status'] != 'COMPLETE' or intent['storage_root_id'] != row['storage_root_id']:
            raise EmptyCaseBlocked('Storage provisioning mismatch')
        root_id = row['storage_root_id']
    # The exact root and each child must be verified through the Drive API.
    root = drive.files().get(fileId=root_id, fields='id,name,mimeType,parents,trashed').execute()
    if (root.get('id') != root_id or root.get('name') != case_id or root.get('trashed') is not False
            or root.get('mimeType') != 'application/vnd.google-apps.folder'):
        raise EmptyCaseBlocked('Drive case root identity mismatch')
    expected = {'Documents', 'Evidence', 'Tax_Categories', 'Calculations', 'Reports', 'Audit'}
    def children(parent):
        results = []
        token = None
        while True:
            response = drive.files().list(
                q=f"'{parent}' in parents and trashed = false",
                fields='nextPageToken,files(id,name,mimeType,parents,trashed)',
                pageSize=1000, pageToken=token,
            ).execute()
            results.extend(response.get('files', []))
            token = response.get('nextPageToken')
            if not token:
                return results
    folders = children(root_id)
    if len(folders) != len(expected) or {x.get('name') for x in folders} != expected:
        raise EmptyCaseBlocked('Unexpected Drive case contents')
    for folder in folders:
        if (folder.get('mimeType') != 'application/vnd.google-apps.folder'
                or folder.get('parents') != [root_id] or folder.get('trashed') is not False):
            raise EmptyCaseBlocked('Invalid Drive folder ownership')
        if children(folder['id']):
            raise EmptyCaseBlocked('Drive case contains documents or other objects')
    return EmptyCaseReadiness(case_id, tax_year, True, True, 'EMPTY_CASE_VERIFIED')