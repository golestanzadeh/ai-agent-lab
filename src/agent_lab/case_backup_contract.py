"""One backup contract for manual and pre-delete snapshots.

No network or destructive operation is performed by this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID


class BackupTrigger(str, Enum):
    MANUAL = "MANUAL"
    PRE_DELETE = "PRE_DELETE"


BACKUP_ROOT = "Case_Backups"


def backup_folder(case_identity: str, backup_id: str) -> tuple[str, str, str]:
    """Canonical provider-relative path, outside Tax_Years and Cases."""
    if not case_identity or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in case_identity):
        raise ValueError("Invalid immutable case identity")
    try:
        parsed = UUID(backup_id)
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("Invalid backup identifier") from exc
    if str(parsed) != backup_id or parsed.version != 4:
        raise ValueError("Backup ID must be canonical UUIDv4")
    return (BACKUP_ROOT, case_identity, backup_id)


@dataclass(frozen=True)
class BackupRequest:
    case_identity: str
    case_id: str
    tax_year: int
    backup_id: str
    trigger: BackupTrigger

    def __post_init__(self):
        if not isinstance(self.trigger, BackupTrigger):
            raise ValueError("Unknown backup trigger")
        if not self.case_id or not 1900 <= self.tax_year <= 9999:
            raise ValueError("Invalid case scope")
        backup_folder(self.case_identity, self.backup_id)


def select_restore_snapshot(backups: list[dict], selected_backup_id: str) -> dict:
    """Exact version selection. Never silently substitute the newest backup."""
    matches = [item for item in backups if item.get("backup_id") == selected_backup_id]
    if len(matches) != 1 or matches[0].get("verified") is not True:
        raise ValueError("Selected backup missing, ambiguous or unverified")
    return matches[0]


def create_backup(request: BackupRequest, snapshot_writer):
    """Single entry point for both triggers; writer must commit verified snapshot."""
    path = backup_folder(request.case_identity, request.backup_id)
    receipt = snapshot_writer(request, path)
    if (not isinstance(receipt, dict)
            or receipt.get("backup_id") != request.backup_id
            or receipt.get("verified") is not True
            or tuple(receipt.get("path", ())) != path):
        raise RuntimeError("Snapshot writer did not verify durable backup")
    return receipt
