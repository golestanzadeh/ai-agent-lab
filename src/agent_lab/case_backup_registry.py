"""Fail-closed backup reservation registry, using canonical SQLite connection.

This module is an integration component, not a permission to delete a case.
The registry is created only when explicitly initialized by the caller.
"""
from __future__ import annotations

import hmac
import json


def initialize_registry(persistence):
    with persistence._lock:
        persistence._verify_all()
        persistence._verify_anchor()
        persistence._db.execute("""CREATE TABLE IF NOT EXISTS case_backup_registry(
            backup_id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL,
            tax_year INTEGER NOT NULL,
            owner_id TEXT NOT NULL,
            identity TEXT NOT NULL,
            folder_id TEXT NOT NULL UNIQUE,
            manifest_digest TEXT NOT NULL,
            receipt_json TEXT NOT NULL,
            receipt_mac TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('VERIFIED', 'RETIRED'))
        )""")
        persistence._db.execute(
            "CREATE INDEX IF NOT EXISTS case_backup_reservation ON case_backup_registry(case_id,owner_id,state)"
        )
        persistence._db.commit()


def register_verified_backup(persistence, *, owner_id, case_id, tax_year, identity, receipt):
    with persistence._lock:
        persistence._verify_all()
        persistence._verify_anchor()
        persistence._authorize(owner_id, case_id, tax_year)
        if (receipt.get("verified") is not True
                or receipt.get("scope") != "FULL_SNAPSHOT_RESTORE_NOT_YET_IMPLEMENTED"
                or not receipt.get("folder_id") or not receipt.get("manifest_sha256")):
            raise ValueError("Only verified complete snapshot receipts can be registered")
        record = {
            "backup_id": receipt["backup_id"], "case_id": case_id,
            "tax_year": tax_year, "owner_id": owner_id, "identity": identity,
            "folder_id": receipt["folder_id"],
            "manifest_digest": receipt["manifest_sha256"],
            "receipt": receipt,
        }
        encoded = json.dumps(record, sort_keys=True, separators=(",", ":"))
        mac = persistence._mac(encoded)
        persistence._db.execute(
            """INSERT INTO case_backup_registry
            (backup_id,case_id,tax_year,owner_id,identity,folder_id,manifest_digest,receipt_json,receipt_mac,state)
            VALUES(?,?,?,?,?,?,?,?,?,'VERIFIED')""",
            (receipt["backup_id"], case_id, tax_year, owner_id, identity,
             receipt["folder_id"], receipt["manifest_sha256"], encoded, mac),
        )
        persistence._db.commit()


def list_reserved_backups(persistence, *, owner_id, case_id):
    with persistence._lock:
        persistence._verify_all()
        persistence._verify_anchor()
        rows = persistence._db.execute(
            "SELECT * FROM case_backup_registry WHERE owner_id=? AND case_id=? ORDER BY backup_id",
            (owner_id, case_id),
        ).fetchall()
        result = []
        for row in rows:
            if not hmac.compare_digest(row["receipt_mac"], persistence._mac(row["receipt_json"])):
                raise RuntimeError("Backup registry integrity failure")
            payload = json.loads(row["receipt_json"])
            if (payload["backup_id"] != row["backup_id"]
                    or payload["folder_id"] != row["folder_id"]
                    or payload["manifest_digest"] != row["manifest_digest"]
                    or payload["case_id"] != case_id or payload["owner_id"] != owner_id):
                raise RuntimeError("Backup registry identity mismatch")
            if row["state"] == "VERIFIED":
                result.append(payload)
        return result


def number_is_reserved(persistence, *, owner_id, case_id):
    return bool(list_reserved_backups(persistence, owner_id=owner_id, case_id=case_id))
