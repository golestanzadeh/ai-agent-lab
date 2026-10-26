"""Fail-closed, journaled case folders on a verified Google Drive Desktop mount.

This proves filesystem provisioning, NOT remote Google API synchronization.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from agent_lab.case_registry import StorageScopeReference, TaxPeriod
from agent_lab.google_drive_provisioning import ProvisioningError


class DriveDesktopScopeCreator:
    FOLDERS = ("Documents", "Evidence", "Tax_Categories", "Calculations", "Reports", "Audit")

    def __init__(self, *, drive_root: Path, journal_root: Path):
        self.root = drive_root
        self.journals = journal_root
        self._verify_mount()

    def _verify_mount(self):
        if not self.root.is_dir():
            raise ProvisioningError("Google Drive Desktop project root unavailable")
        if not (self.root / "Tax_Years" / "2024").is_dir():
            raise ProvisioningError("expected established Drive project year is missing")
        if not (self.root / "System").is_dir():
            raise ProvisioningError("Google Drive project identity verification failed")

    def create_case_scope(self, tax_period: TaxPeriod, case_id: str) -> StorageScopeReference:
        self._verify_mount()
        if not isinstance(case_id, str) or case_id != f"CASE-{tax_period.year}-" + case_id.rsplit("-", 1)[-1] or not case_id.rsplit("-", 1)[-1].isdigit():
            raise ProvisioningError("invalid case identity")
        self.journals.mkdir(parents=True, exist_ok=True)
        journal = self.journals / (case_id + ".json")
        relative = Path("Tax_Years") / str(tax_period.year) / "Cases" / case_id
        target = self.root / relative
        if journal.exists():
            try:
                state = json.loads(journal.read_text(encoding="utf-8"))
            except Exception:
                raise ProvisioningError("unreadable provisioning journal")
            if state != {"case_id": case_id, "relative": relative.as_posix(), "status": "COMPLETE"}:
                raise ProvisioningError("provisioning journal needs reconciliation")
            if not target.is_dir() or any(not (target / x).is_dir() for x in self.FOLDERS):
                raise ProvisioningError("completed folder tree differs from journal")
            return StorageScopeReference("google_drive_desktop", str(target))
        if target.exists() or (self.root / "Tax_Years" / str(tax_period.year)).exists():
            raise ProvisioningError("unrecorded year or case folder requires reconciliation")
        temp = journal.with_suffix(".writing")
        with temp.open("x", encoding="utf-8") as f:
            json.dump({"case_id": case_id, "relative": relative.as_posix(), "status": "IN_PROGRESS"}, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, journal)
        try:
            target.mkdir(parents=True, exist_ok=False)
            for name in self.FOLDERS:
                (target / name).mkdir(exist_ok=False)
            with temp.open("x", encoding="utf-8") as f:
                json.dump({"case_id": case_id, "relative": relative.as_posix(), "status": "COMPLETE"}, f)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp, journal)
        except Exception:
            raise ProvisioningError("folder creation uncertain; inspect journal and Drive")
        return StorageScopeReference("google_drive_desktop", str(target))
