"""Owner-scoped, read-only inventory for document-bearing backup readiness."""
from __future__ import annotations

from hashlib import sha256


def verify_case_backup_source(host, case_id: str, tax_year: int) -> dict:
    with host._lock:
        snapshot = host.list_case_documents(case_id, tax_year)
        with host.persistence._lock:
            host.persistence._verify_all()
            host.persistence._verify_anchor()
            host.persistence._authorize(host.owner_id, case_id, tax_year)
            columns={r['name'] for r in host.persistence._db.execute('PRAGMA table_info(case_document_index)')}
            if 'registry_state' in columns and host.persistence._db.execute(
                "SELECT 1 FROM case_document_index WHERE case_id=? AND (registry_state<>'PENDING' OR source_status<>'ACTIVE') LIMIT 1",(case_id,)
            ).fetchone():
                raise ValueError('Lifecycle or unresolved documents require extended backup support')
            row = host.persistence._db.execute(
                "SELECT lifecycle_status,storage_root_id FROM case_record WHERE case_id=? AND owner_id=? AND tax_year=?",
                (case_id, host.owner_id, tax_year),
            ).fetchone()
            if row is None or row["lifecycle_status"] != "CREATED":
                raise ValueError("Case finality or ownership blocks backup")
            if host.persistence._db.execute(
                "SELECT 1 FROM durable_run WHERE case_id=?", (case_id,)
            ).fetchone():
                raise ValueError("Durable runs require separate lineage backup")
            if host.persistence._db.execute(
                "SELECT 1 FROM mutation_request WHERE case_id=?", (case_id,)
            ).fetchone():
                raise ValueError("Mutation dependencies require separate review")
            case_root = row["storage_root_id"]
        files = []
        seen_names = set()
        for entry in snapshot["files"]:
            if entry["name"] in seen_names:
                raise ValueError("Duplicate filenames block unambiguous backup")
            seen_names.add(entry["name"])
            metadata, content = host.get_case_document(case_id, tax_year, entry["id"])
            if metadata["name"] != entry["name"] or len(content) != int(entry["size"]):
                raise ValueError("Drive bytes mismatch metadata")
            files.append({
                "id": entry["id"], "name": entry["name"],
                "size": len(content), "sha256": sha256(content).hexdigest()
            })
        return {
            "case_id": case_id, "tax_year": tax_year,
            "storage_root_id": case_root, "documents": files,
            "source_verified": True, "backup_created": False,
            "deletion_enabled": False
        }
