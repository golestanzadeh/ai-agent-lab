"""Synthetic-only durable identity evidence lifecycle, not production authorized.

Stores metadata and digests only. Content verification requires a separate,
authorized provider; this module never claims to verify protected bytes.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path


class IdentityEvidenceError(RuntimeError):
    pass


class DurableIdentityEvidenceAuthority:
    """Append-only declaration/confirmation/authorization events in SQLite."""

    ALLOWED = frozenset({"OWNER_DECLARATION", "OWNER_CONFIRMATION", "IDENTITY_AUTHORIZATION"})

    def __init__(self, db_path: str | Path) -> None:
        path = Path(db_path).resolve()
        if not path.exists():
            raise IdentityEvidenceError("preprovisioned synthetic identity database required")
        self._db = sqlite3.connect(f"file:{path.as_posix()}?mode=rw", uri=True)
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS identity_evidence_events ("
            "event_id TEXT PRIMARY KEY, kind TEXT NOT NULL, case_id TEXT NOT NULL, "
            "subject_id TEXT NOT NULL, actor_id TEXT NOT NULL, reference_id TEXT NOT NULL, "
            "content_digest TEXT NOT NULL, parent_event_id TEXT, payload_hash TEXT NOT NULL, "
            "FOREIGN KEY(parent_event_id) REFERENCES identity_evidence_events(event_id))"
        )
        self._db.commit()

    def append(
        self, *, event_id: str, kind: str, case_id: str, subject_id: str,
        actor_id: str, reference_id: str, content_digest: str,
        parent_event_id: str | None = None,
    ) -> str:
        values = (event_id, case_id, subject_id, actor_id, reference_id, content_digest)
        if kind not in self.ALLOWED or not all(isinstance(v, str) and v.strip() for v in values):
            raise IdentityEvidenceError("invalid evidence metadata")
        if not content_digest.startswith("sha256:") or len(content_digest) != 71:
            raise IdentityEvidenceError("canonical SHA-256 reference required")
        try:
            bytes.fromhex(content_digest[7:])
        except ValueError as exc:
            raise IdentityEvidenceError("invalid SHA-256 reference") from exc
        if kind == "OWNER_DECLARATION" and parent_event_id is not None:
            raise IdentityEvidenceError("declaration must be a root event")
        if kind != "OWNER_DECLARATION" and not parent_event_id:
            raise IdentityEvidenceError("confirmation/authorization requires parent evidence")
        if parent_event_id:
            parent = self._db.execute(
                "SELECT kind,case_id,subject_id,content_digest FROM identity_evidence_events WHERE event_id=?",
                (parent_event_id,),
            ).fetchone()
            expected_kind = "OWNER_DECLARATION" if kind == "OWNER_CONFIRMATION" else "OWNER_CONFIRMATION"
            if (parent is None or parent[0] != expected_kind or
                parent[1:] != (case_id, subject_id, content_digest)):
                raise IdentityEvidenceError("missing, cross-case or mismatched parent")
        canonical = json.dumps(
            [event_id, kind, *values[1:], parent_event_id],
            ensure_ascii=False, separators=(",", ":"),
        )
        payload_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        try:
            with self._db:
                self._db.execute(
                    "INSERT INTO identity_evidence_events VALUES (?,?,?,?,?,?,?,?,?)",
                    (event_id, kind, case_id, subject_id, actor_id, reference_id,
                     content_digest, parent_event_id, payload_hash),
                )
        except sqlite3.IntegrityError as exc:
            raise IdentityEvidenceError("duplicate or invalid evidence reference") from exc
        return event_id

    def close(self) -> None:
        self._db.close()
