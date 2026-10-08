"""Synthetic-only Kernel-custodied identity epoch authority (not deployed).

The control-plane database MUST be outside the identity database/anchor recovery
set and separately ACL-protected before any operational use. No key or taxpayer
content is stored here. Not wired into production.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path


class IdentityContinuityError(RuntimeError):
    """Fail-closed identity continuity or rollback detection."""


class IdentityContinuityAuthority:
    """Kernel-owned monotonic head for synthetic recovery/rollback tests."""

    def __init__(self, kernel_db: str | Path, identity_db: str | Path) -> None:
        kernel = Path(kernel_db).resolve()
        identity = Path(identity_db).resolve()
        if kernel == identity or kernel.parent == identity.parent:
            raise IdentityContinuityError("continuity authority requires a separate custody root")
        if not kernel.exists():
            raise IdentityContinuityError("preprovisioned Kernel control-plane database required")
        self._db = sqlite3.connect(f"file:{kernel.as_posix()}?mode=rw", uri=True)
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS identity_continuity_head ("
            "scope TEXT PRIMARY KEY, epoch INTEGER NOT NULL CHECK(epoch >= 0), "
            "head TEXT NOT NULL, pending_head TEXT)"
        )
        self._db.commit()

    def initialize(self, scope: str, head: str) -> None:
        self._validate(scope, head)
        with self._db:
            self._db.execute(
                "INSERT OR IGNORE INTO identity_continuity_head(scope,epoch,head,pending_head) "
                "VALUES (?,0,?,NULL)", (scope, head)
            )
        self.verify(scope, 0, head)

    def reserve(self, scope: str, epoch: int, current_head: str, next_head: str) -> None:
        self._validate(scope, current_head)
        self._validate(scope, next_head)
        if current_head == next_head:
            raise IdentityContinuityError("next head must differ")
        with self._db:
            cursor = self._db.execute(
                "UPDATE identity_continuity_head SET pending_head=? "
                "WHERE scope=? AND epoch=? AND head=? AND pending_head IS NULL",
                (next_head, scope, epoch, current_head)
            )
            if cursor.rowcount != 1:
                raise IdentityContinuityError("stale epoch/head or pending reservation")

    def finalize(self, scope: str, epoch: int, next_head: str) -> None:
        self._validate(scope, next_head)
        with self._db:
            cursor = self._db.execute(
                "UPDATE identity_continuity_head SET epoch=epoch+1,head=pending_head,pending_head=NULL "
                "WHERE scope=? AND epoch=? AND pending_head=?",
                (scope, epoch, next_head)
            )
            if cursor.rowcount != 1:
                raise IdentityContinuityError("missing or conflicting reservation")

    def verify(self, scope: str, epoch: int, head: str) -> None:
        self._validate(scope, head)
        row = self._db.execute(
            "SELECT epoch,head,pending_head FROM identity_continuity_head WHERE scope=?",
            (scope,)
        ).fetchone()
        if row is None or row[2] is not None or row[0] != epoch or row[1] != head:
            raise IdentityContinuityError("rollback, pending write or unknown head")

    @staticmethod
    def _validate(scope: str, head: str) -> None:
        if not isinstance(scope, str) or not scope.strip():
            raise IdentityContinuityError("scope required")
        if not isinstance(head, str) or not head.strip():
            raise IdentityContinuityError("head required")

    def close(self) -> None:
        self._db.close()
