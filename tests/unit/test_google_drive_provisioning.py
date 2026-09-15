import json
from types import SimpleNamespace

import pytest

from agent_lab.case_creation_workflow import InMemoryAuditSink
from agent_lab.case_registry import TaxPeriod
from agent_lab.google_drive_provisioning import GoogleDriveStorageScopeCreator as Creator, ProvisioningError


class FakeDrive:
    def __init__(self):
        self.objects = {"root": {"id": "root", "mimeType": Creator.MIME, "trashed": False,
                                 "capabilities": {"canAddChildren": True}}}
        self.calls = []
        self.fail = False
        self.conflict = False

    def files(self):
        return self

    def get(self, **kwargs):
        self.calls.append(("get", kwargs))
        return SimpleNamespace(execute=lambda: self.objects[kwargs["fileId"]])

    def list(self, **kwargs):
        self.calls.append(("list", kwargs))
        assert "in parents and name =" in kwargs["q"]
        return SimpleNamespace(execute=lambda: {"files": [{"id": "conflict"}] if self.conflict else []})

    def create(self, **kwargs):
        self.calls.append(("create", kwargs))
        def execute():
            if self.fail:
                raise RuntimeError("sensitive provider diagnostic")
            result = dict(kwargs["body"], id=f"folder-{len(self.objects)}", trashed=False,
                          capabilities={"canAddChildren": True})
            self.objects[result["id"]] = result
            return result
        return SimpleNamespace(execute=execute)


@pytest.fixture
def env(tmp_path):
    drive, audit = FakeDrive(), InMemoryAuditSink()
    creator = Creator(drive_service=drive, system_root_id="root", journal_path=tmp_path/"refs.json", audit=audit)
    return creator, drive, audit


def test_standard_tree_and_restart_replay(env):
    creator, drive, audit = env
    period = TaxPeriod("CALENDAR_YEAR", 2024)
    first = creator.create_case_scope(period, "CASE-001")
    assert len(drive.objects) == 11
    assert [c[1]["body"]["name"] for c in drive.calls if c[0] == "create"] == [
        "Tax_Years", "2024", "Cases", "CASE-001", *Creator.REQUIRED_SUBFOLDERS]
    for folder in Creator.REQUIRED_SUBFOLDERS:
        assert any(o.get("name") == folder and o["parents"] == [first.root_id] for o in drive.objects.values())
    restarted = Creator(drive_service=drive, system_root_id="root", journal_path=creator.path, audit=audit)
    assert restarted.create_case_scope(period, "CASE-001") == first
    assert restarted.documents_scope(period, "CASE-001").root_id != first.root_id
    assert len([c for c in drive.calls if c[0] == "create"]) == 10
    assert audit.events[-1].outcome == "COMPLETE"
    assert {c[0] for c in drive.calls} == {"get", "list", "create"}


def test_uncertain_creation_never_retries(env):
    creator, drive, _ = env
    drive.fail = True
    with pytest.raises(ProvisioningError, match="private journal"):
        creator.create_case_scope(TaxPeriod("CALENDAR_YEAR", 2024), "CASE-001")
    assert json.loads(creator.path.read_text())["pending"]
    before = len(drive.calls)
    with pytest.raises(ProvisioningError, match="uncertain"):
        creator.create_case_scope(TaxPeriod("CALENDAR_YEAR", 2024), "CASE-001")
    assert len(drive.calls) == before


def test_unrecorded_existing_folder_fails_closed(env):
    creator, drive, _ = env
    drive.conflict = True
    with pytest.raises(ProvisioningError, match="unrecorded"):
        creator.create_case_scope(TaxPeriod("CALENDAR_YEAR", 2024), "CASE-001")
    assert not any(c[0] == "create" for c in drive.calls)


@pytest.mark.parametrize("case", ["", "OTHER", "CASE-../secret", "CASE-'query"])
def test_invalid_case_no_drive_access(env, case):
    creator, drive, _ = env
    with pytest.raises(ProvisioningError):
        creator.create_case_scope(TaxPeriod("CALENDAR_YEAR", 2024), case)
    assert not drive.calls


def test_year_mismatch_no_drive_access(env):
    creator, drive, _ = env
    creator.create_case_scope(TaxPeriod("CALENDAR_YEAR", 2024), "CASE-001")
    before = len(drive.calls)
    with pytest.raises(ProvisioningError, match="another year"):
        creator.create_case_scope(TaxPeriod("CALENDAR_YEAR", 2025), "CASE-001")
    assert len(drive.calls) == before


@pytest.mark.parametrize("field,value", [("trashed", True), ("parents", ["unrelated"]), ("name", "wrong")])
def test_stored_folder_scope_tampering_rejected(env, field, value):
    creator, drive, _ = env
    creator.create_case_scope(TaxPeriod("CALENDAR_YEAR", 2024), "CASE-001")
    drive.objects["folder-1"][field] = value
    with pytest.raises(ProvisioningError, match="placement"):
        creator.create_case_scope(TaxPeriod("CALENDAR_YEAR", 2024), "CASE-001")


def test_lock_and_root_mismatch_fail_closed(env):
    creator, drive, _ = env
    lock = creator.path.with_suffix(".json.lock")
    lock.touch()
    with pytest.raises(ProvisioningError, match="locked"):
        creator.create_case_scope(TaxPeriod("CALENDAR_YEAR", 2024), "CASE-001")
    assert not drive.calls
    lock.unlink()
    creator.create_case_scope(TaxPeriod("CALENDAR_YEAR", 2024), "CASE-001")
    creator.root = "other-root"
    with pytest.raises(ProvisioningError, match="scope mismatch"):
        creator.create_case_scope(TaxPeriod("CALENDAR_YEAR", 2024), "CASE-001")


def test_missing_creation_permission_no_create(env):
    creator, drive, _ = env
    drive.objects["root"]["capabilities"]["canAddChildren"] = False
    with pytest.raises(ProvisioningError, match="permit"):
        creator.create_case_scope(TaxPeriod("CALENDAR_YEAR", 2024), "CASE-001")
    assert not any(c[0] == "create" for c in drive.calls)


def test_other_case_reuses_only_shared_parents(env):
    creator, drive, _ = env
    period = TaxPeriod("CALENDAR_YEAR", 2024)
    first = creator.create_case_scope(period, "CASE-001")
    before = len(drive.calls)
    second = creator.create_case_scope(period, "CASE-002")
    assert first != second
    calls = drive.calls[before:]
    assert not any(c[0] == "get" and c[1]["fileId"] == first.root_id for c in calls)
    assert len([c for c in calls if c[0] == "create"]) == 7


def test_confirmed_partial_folders_resume_without_duplicates(env):
    creator, drive, _ = env
    original_get = drive.get
    def fail_after_confirmed_folder(**kwargs):
        if kwargs["fileId"] == "folder-1":
            raise RuntimeError("temporary read failure")
        return original_get(**kwargs)
    drive.get = fail_after_confirmed_folder
    with pytest.raises(ProvisioningError):
        creator.create_case_scope(TaxPeriod("CALENDAR_YEAR", 2024), "CASE-001")
    assert len(drive.objects) == 2
    assert json.loads(creator.path.read_text())["pending"] is None
    drive.get = original_get
    creator.create_case_scope(TaxPeriod("CALENDAR_YEAR", 2024), "CASE-001")
    assert len(drive.objects) == 11
