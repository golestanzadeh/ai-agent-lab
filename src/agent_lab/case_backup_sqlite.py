"""Verified, owner-scoped SQLite case snapshot; never modifies canonical rows."""
from __future__ import annotations

import json
from hashlib import sha256

TABLES = ("case_record", "case_state", "ui_case_authorization", "storage_provisioning", "durable_run", "mutation_request", "case_document_index")


def export_case_state(persistence, owner_id: str, case_id: str, tax_year: int) -> tuple[bytes, str]:
    with persistence._lock:
        persistence._verify_all()
        persistence._verify_anchor()
        persistence._authorize(owner_id, case_id, tax_year)
        row = persistence._db.execute(
            "SELECT storage_root_id FROM case_record WHERE case_id=? AND owner_id=? AND tax_year=?",
            (case_id, owner_id, tax_year),
        ).fetchone()
        if row is None:
            raise ValueError("Case identity mismatch")
        snapshot = {"schema": "case-sqlite-snapshot/1", "case_id": case_id,
                    "tax_year": tax_year, "owner_id": owner_id,
                    "storage_root_id": row["storage_root_id"], "tables": {}}
        for table in TABLES:
            exists = persistence._db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone()
            if not exists:
                if table == "case_document_index":
                    snapshot["tables"][table] = []
                    continue
                raise RuntimeError("Missing canonical case table")
            rows = persistence._db.execute(
                f"SELECT * FROM {table} WHERE case_id=?", (case_id,)
            ).fetchall()
            snapshot["tables"][table] = [
                {key: item[key] for key in item.keys()} for item in rows
            ]
        if any(len(snapshot["tables"][table]) != 1 for table in TABLES[:4]):
            raise RuntimeError("Incomplete case persistence snapshot")
        blob = json.dumps(snapshot, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return blob, sha256(blob).hexdigest()
