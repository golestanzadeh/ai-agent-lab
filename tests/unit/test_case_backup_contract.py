from uuid import uuid4

import pytest

from agent_lab.case_backup_contract import (
    BackupRequest, BackupTrigger, backup_folder, create_backup,
    select_restore_snapshot,
)


def test_both_triggers_share_exact_writer_and_path():
    backup_id = str(uuid4())
    receipts = []
    def writer(req, path):
        receipts.append((req.trigger, path))
        return {"backup_id": req.backup_id, "verified": True, "path": path}
    for trigger in (BackupTrigger.MANUAL, BackupTrigger.PRE_DELETE):
        request = BackupRequest("identity-001", "CASE-2025-0001", 2025, backup_id, trigger)
        create_backup(request, writer)
    assert len(receipts) == 2
    assert receipts[0][1] == receipts[1][1] == ("Case_Backups", "identity-001", backup_id)


def test_restore_can_select_older_version_with_more_documents():
    older, newer = str(uuid4()), str(uuid4())
    versions = [
        {"backup_id": older, "verified": True, "documents": ["a", "b", "c"]},
        {"backup_id": newer, "verified": True, "documents": ["a"]},
    ]
    assert select_restore_snapshot(versions, older)["documents"] == ["a", "b", "c"]
    assert select_restore_snapshot(versions, newer)["documents"] == ["a"]


@pytest.mark.parametrize("selected", ["unknown", None])
def test_unknown_restore_never_falls_back(selected):
    with pytest.raises(ValueError):
        select_restore_snapshot([{"backup_id": str(uuid4()), "verified": True}], selected)


def test_unverified_snapshot_cannot_be_restored():
    with pytest.raises(ValueError):
        select_restore_snapshot([{"backup_id": "x", "verified": False}], "x")


def test_unverified_writer_cannot_claim_success():
    req = BackupRequest("identity-001", "CASE-2025-0001", 2025, str(uuid4()), BackupTrigger.MANUAL)
    with pytest.raises(RuntimeError):
        create_backup(req, lambda request, path: {"backup_id": request.backup_id, "verified": False, "path": path})


@pytest.mark.parametrize("identity", ["../case", "a/b", "", "a\\b"])
def test_unsafe_identity_rejected(identity):
    with pytest.raises(ValueError):
        backup_folder(identity, str(uuid4()))
