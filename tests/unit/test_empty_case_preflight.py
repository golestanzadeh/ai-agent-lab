from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from agent_lab.empty_case_preflight import inspect_empty_case, EmptyCaseBlocked


class FakePersistence:
    def __init__(self, *, blocked=False):
        from threading import RLock
        self._lock = RLock()
        self.blocked = blocked
        self._db = self
    def _verify_all(self): pass
    def _verify_anchor(self): pass
    def _authorize(self, owner, case, year):
        assert (owner, case, year) == ('owner', 'CASE-2026-0001', 2026)
    def execute(self, sql, args):
        if 'FROM case_record' in sql:
            return SimpleNamespace(fetchone=lambda: dict(lifecycle_status='CREATED', storage_provider='google_drive', storage_root_id='root'))
        if 'FROM durable_run' in sql or 'FROM mutation_request' in sql:
            return SimpleNamespace(fetchone=lambda: ('exists',) if self.blocked else None)
        if 'FROM case_state' in sql:
            return SimpleNamespace(fetchone=lambda: dict(payload='{"documents_ref": null}'))
        if 'FROM storage_provisioning' in sql:
            return SimpleNamespace(fetchone=lambda: dict(status='COMPLETE', storage_root_id='root'))
        raise AssertionError(sql)


def fake_drive(*, has_document=False):
    drive = Mock()
    folders = ['Documents', 'Evidence', 'Tax_Categories', 'Calculations', 'Reports', 'Audit']
    drive.files.return_value.get.return_value.execute.return_value = dict(id='root', name='CASE-2026-0001', trashed=False, mimeType='application/vnd.google-apps.folder')
    def listed(**kwargs):
        parent = kwargs['q'].split("'")[1]
        if parent == 'root':
            return SimpleNamespace(execute=lambda: dict(files=[dict(id=n, name=n, mimeType='application/vnd.google-apps.folder', parents=['root'], trashed=False) for n in folders]))
        return SimpleNamespace(execute=lambda: dict(files=[dict(id='document')] if has_document and parent == 'Documents' else []))
    drive.files.return_value.list.side_effect = listed
    return drive


def test_empty_case_readiness_success():
    result = inspect_empty_case(FakePersistence(), fake_drive(), owner_id='owner', case_id='CASE-2026-0001', tax_year=2026)
    assert result.sqlite_ready and result.drive_ready


def test_sqlite_dependency_prevents_drive_access():
    drive = fake_drive()
    with pytest.raises(EmptyCaseBlocked, match='SQLite'):
        inspect_empty_case(FakePersistence(blocked=True), drive, owner_id='owner', case_id='CASE-2026-0001', tax_year=2026)
    drive.files.assert_not_called()


def test_drive_document_blocks_deletion():
    with pytest.raises(EmptyCaseBlocked, match='Drive case contains'):
        inspect_empty_case(FakePersistence(), fake_drive(has_document=True), owner_id='owner', case_id='CASE-2026-0001', tax_year=2026)