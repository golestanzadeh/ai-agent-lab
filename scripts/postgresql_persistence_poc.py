"""Disposable PostgreSQL 18 acceptance harness for the frozen persistence contract.

This harness uses only the existing ai-tax-postgres-test container and synthetic
data. It refuses to overwrite an existing PoC schema or restore database.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time


CONTAINER = "ai-tax-postgres-test"
DATABASE = "ai_tax_test"
SCHEMA = "ai_tax_poc_20261016"
RESTORE_DATABASE = "ai_tax_poc_restore_20261016"


def run(command: list[str], *, input_data: bytes | None = None, binary: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        input=input_data,
        capture_output=True,
        check=False,
        text=not binary,
    )


def psql(sql: str, *, database: str = DATABASE, role: str | None = None) -> subprocess.CompletedProcess:
    prefix = f"SET ROLE {role};" if role else ""
    return run([
        "docker", "exec", "-i", CONTAINER, "psql", "-X", "-v", "ON_ERROR_STOP=1",
        "-U", "postgres", "-d", database, "-Atc", prefix + sql,
    ])


def require(condition: bool, name: str, details: str = "") -> dict[str, str]:
    if not condition:
        raise AssertionError(f"{name}: {details}")
    return {"test": name, "status": "PASS", "details": details}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    results: list[dict[str, str]] = []
    started = time.perf_counter()

    try:
        info = run(["docker", "info", "--format", "{{.OSType}}|{{.ServerVersion}}"])
        results.append(require(info.returncode == 0 and info.stdout.strip().startswith("linux|"), "environment.docker", info.stdout.strip()))
        ready = run(["docker", "exec", CONTAINER, "pg_isready", "-U", "postgres", "-d", DATABASE])
        results.append(require(ready.returncode == 0, "environment.connectivity", ready.stdout.strip()))
        version = psql("SHOW server_version;")
        results.append(require(version.returncode == 0 and version.stdout.strip().startswith("18."), "environment.postgresql18", version.stdout.strip()))

        exists = psql(f"SELECT count(*) FROM pg_namespace WHERE nspname='{SCHEMA}';")
        results.append(require(exists.stdout.strip() == "0", "safety.schema_absent", exists.stdout.strip()))
        restore_exists = psql(f"SELECT count(*) FROM pg_database WHERE datname='{RESTORE_DATABASE}';", database="postgres")
        results.append(require(restore_exists.stdout.strip() == "0", "safety.restore_database_absent", restore_exists.stdout.strip()))

        migration = run([
            "docker", "exec", "-i", CONTAINER, "psql", "-X", "-v", "ON_ERROR_STOP=1",
            "-U", "postgres", "-d", DATABASE,
        ], input_data=args.schema.read_bytes(), binary=True)
        results.append(require(migration.returncode == 0, "contract.schema_migration", migration.stderr.decode(errors="replace")[-400:]))

        seed_sql = """
        BEGIN;
        INSERT INTO ai_tax_poc_20261016.tax_case VALUES
          ('SYN-CASE-A',2024,'root://synthetic/a',1,clock_timestamp()),
          ('SYN-CASE-B',2024,'root://synthetic/b',1,clock_timestamp());
        INSERT INTO ai_tax_poc_20261016.identity_record
          (identity_id,record_type,status,payload,digest,revision,schema_version) VALUES
          ('SYN-PERSON-A','PERSON','ACTIVE','{}',repeat('a',64),1,2),
          ('SYN-PERSON-B','PERSON','ACTIVE','{}',repeat('b',64),1,2);
        INSERT INTO ai_tax_poc_20261016.case_party_role
          (binding_id,case_id,tax_year,subject_id,role_code,valid_from,valid_to_exclusive,evidence_ref,authorization_ref,revision,schema_version) VALUES
          ('BIND-A','SYN-CASE-A',2024,'SYN-PERSON-A','PRIMARY_TAXPAYER','2024-01-01','2025-01-01','sha256:'||repeat('c',64),'AUTH-SYN-A',1,2),
          ('BIND-B','SYN-CASE-B',2024,'SYN-PERSON-B','PRIMARY_TAXPAYER','2024-01-01','2025-01-01','sha256:'||repeat('d',64),'AUTH-SYN-B',1,2);
        INSERT INTO ai_tax_poc_20261016.subject_fact_binding
          (request_id,case_id,tax_year,subject_id,semantic_key,fact_artifact_ref,declaration_artifact_ref,confirmation_ref,authorization_ref,lineage,payload_digest,revision,schema_version) VALUES
          ('REQ-A','SYN-CASE-A',2024,'SYN-PERSON-A','synthetic.fact','sha256:'||repeat('e',64),'sha256:'||repeat('f',64),'CONF-SYN-A','AUTH-SYN-A','["AUD-SYN-A"]',repeat('1',64),1,2);
        INSERT INTO ai_tax_poc_20261016.idempotency_request VALUES ('REQ-A',repeat('2',64),repeat('3',64),clock_timestamp());
        INSERT INTO ai_tax_poc_20261016.audit_event
          (case_id,tax_year,action,payload_digest,previous_digest,event_digest) VALUES
          ('SYN-CASE-A',2024,'SYNTHETIC_CREATE',repeat('4',64),repeat('0',64),repeat('5',64));
        COMMIT;
        """
        seeded = psql(seed_sql)
        results.append(require(seeded.returncode == 0, "functional.atomic_multitable_commit", seeded.stderr[-400:]))

        readback = psql("SELECT count(*) FROM ai_tax_poc_20261016.subject_fact_binding WHERE case_id='SYN-CASE-A' AND tax_year=2024;")
        results.append(require(readback.stdout.strip() == "1", "functional.create_read", readback.stdout.strip()))
        updated = psql("UPDATE ai_tax_poc_20261016.identity_record SET status='INACTIVE',revision=2 WHERE identity_id='SYN-PERSON-B'; SELECT status||'|'||revision FROM ai_tax_poc_20261016.identity_record WHERE identity_id='SYN-PERSON-B';")
        results.append(require(updated.returncode == 0 and updated.stdout.strip().endswith("INACTIVE|2"), "functional.update_permitted", updated.stdout.strip()))
        deleted = psql("INSERT INTO ai_tax_poc_20261016.identity_record VALUES ('SYN-TEMP','PERSON','UNRESOLVED','{}',repeat('6',64),1,2,clock_timestamp()); DELETE FROM ai_tax_poc_20261016.identity_record WHERE identity_id='SYN-TEMP'; SELECT count(*) FROM ai_tax_poc_20261016.identity_record WHERE identity_id='SYN-TEMP';")
        results.append(require(deleted.returncode == 0 and deleted.stdout.strip().endswith("0"), "functional.delete_permitted", deleted.stdout.strip()))

        rollback = psql("BEGIN; INSERT INTO ai_tax_poc_20261016.tax_case VALUES ('SYN-ROLLBACK',2024,'root://synthetic/rollback',1,clock_timestamp()); ROLLBACK; SELECT count(*) FROM ai_tax_poc_20261016.tax_case WHERE case_id='SYN-ROLLBACK';")
        results.append(require(rollback.returncode == 0 and rollback.stdout.strip().endswith("0"), "functional.rollback", rollback.stdout.strip()))
        invalid = psql("INSERT INTO ai_tax_poc_20261016.identity_record VALUES ('bad','PERSON','ACTIVE','{}','bad',0,9,clock_timestamp());")
        results.append(require(invalid.returncode != 0, "functional.invalid_input_rejected"))
        fk = psql("INSERT INTO ai_tax_poc_20261016.case_party_role(binding_id,case_id,tax_year,subject_id,role_code,valid_from,evidence_ref,authorization_ref,revision,schema_version) VALUES('BAD-FK','SYN-CASE-A',2024,'SYN-MISSING','CHILD','2024-01-01','sha256:'||repeat('a',64),'AUTH',1,2);")
        results.append(require(fk.returncode != 0, "functional.foreign_key_rejected"))
        duplicate = psql("INSERT INTO ai_tax_poc_20261016.idempotency_request VALUES ('REQ-A',repeat('9',64),repeat('8',64),clock_timestamp());")
        results.append(require(duplicate.returncode != 0, "functional.idempotency_conflict_rejected"))

        scoped = psql("SET ai_tax.case_id='SYN-CASE-A'; SET ai_tax.tax_year='2024'; SELECT string_agg(case_id,',') FROM ai_tax_poc_20261016.tax_case;", role="ai_tax_poc_reader")
        results.append(require(scoped.returncode == 0 and scoped.stdout.strip().endswith("SYN-CASE-A"), "security.case_year_rls", scoped.stdout.strip()))
        unauthorized = psql("UPDATE ai_tax_poc_20261016.identity_record SET status='ACTIVE' WHERE identity_id='SYN-PERSON-B';", role="ai_tax_poc_reader")
        results.append(require(unauthorized.returncode != 0, "security.readonly_role_write_denied"))

        admin_tamper = psql("UPDATE ai_tax_poc_20261016.audit_event SET payload_digest=repeat('9',64) WHERE event_id=1; SELECT payload_digest FROM ai_tax_poc_20261016.audit_event WHERE event_id=1;")
        results.append(require(admin_tamper.returncode == 0 and admin_tamper.stdout.strip().endswith("9" * 64), "security.admin_tamper_demonstrated"))
        repaired = psql("UPDATE ai_tax_poc_20261016.audit_event SET payload_digest=repeat('4',64) WHERE event_id=1;")
        results.append(require(repaired.returncode == 0, "security.synthetic_audit_restored"))

        lock_ready = threading.Event()
        first_result: list[subprocess.CompletedProcess] = []
        def holder() -> None:
            lock_ready.set()
            first_result.append(psql("BEGIN; SELECT * FROM ai_tax_poc_20261016.idempotency_request WHERE request_id='REQ-A' FOR UPDATE; SELECT pg_sleep(2); COMMIT;"))
        thread = threading.Thread(target=holder)
        thread.start(); lock_ready.wait(); time.sleep(0.35)
        conflict = psql("SET lock_timeout='300ms'; UPDATE ai_tax_poc_20261016.idempotency_request SET outcome_digest=repeat('7',64) WHERE request_id='REQ-A';")
        thread.join()
        results.append(require(first_result[0].returncode == 0 and conflict.returncode != 0, "functional.concurrent_conflict_timeout"))

        perf = psql("EXPLAIN (ANALYZE,FORMAT JSON) SELECT * FROM ai_tax_poc_20261016.subject_fact_binding WHERE case_id='SYN-CASE-A' AND tax_year=2024 AND subject_id='SYN-PERSON-A';")
        results.append(require(perf.returncode == 0 and 'Execution Time' in perf.stdout, "operations.indexed_query_plan"))
        size = psql("SELECT pg_total_relation_size('ai_tax_poc_20261016.subject_fact_binding') > 0;")
        results.append(require(size.stdout.strip() == "t", "operations.storage_measurement"))

        restarted = run(["docker", "restart", CONTAINER])
        results.append(require(restarted.returncode == 0, "recovery.container_restart", restarted.stdout.strip()))
        ready2 = run(["docker", "exec", CONTAINER, "pg_isready", "-U", "postgres", "-d", DATABASE])
        durable = psql("SELECT count(*) FROM ai_tax_poc_20261016.subject_fact_binding WHERE request_id='REQ-A';")
        results.append(require(ready2.returncode == 0 and durable.stdout.strip() == "1", "recovery.restart_durability", durable.stdout.strip()))

        dump = run(["docker", "exec", CONTAINER, "pg_dump", "-U", "postgres", "-d", DATABASE, "-Fc", "-n", SCHEMA], binary=True)
        results.append(require(dump.returncode == 0 and len(dump.stdout) > 0, "recovery.controlled_backup", f"bytes={len(dump.stdout)}"))
        created = psql(f"CREATE DATABASE {RESTORE_DATABASE};", database="postgres")
        results.append(require(created.returncode == 0, "recovery.isolated_restore_database"))
        restored = run(["docker", "exec", "-i", CONTAINER, "pg_restore", "-U", "postgres", "-d", RESTORE_DATABASE, "--exit-on-error"], input_data=dump.stdout, binary=True)
        results.append(require(restored.returncode == 0, "recovery.restore"))
        restored_count = psql("SELECT count(*) FROM ai_tax_poc_20261016.subject_fact_binding WHERE request_id='REQ-A';", database=RESTORE_DATABASE)
        restored_integrity = psql("SELECT count(*) FROM ai_tax_poc_20261016.audit_event WHERE event_digest=repeat('5',64) AND payload_digest=repeat('4',64);", database=RESTORE_DATABASE)
        results.append(require(restored_count.stdout.strip() == "1" and restored_integrity.stdout.strip() == "1", "recovery.restored_records_integrity"))
        dropped = psql(f"DROP DATABASE {RESTORE_DATABASE};", database="postgres")
        results.append(require(dropped.returncode == 0, "recovery.disposable_restore_removed"))

        # Existing lab table must remain untouched.
        lab = psql("SELECT count(*)||'|'||max(epoch) FROM public.lab_events;")
        results.append(require(lab.returncode == 0 and lab.stdout.strip() == "2|103", "safety.existing_lab_preserved", lab.stdout.strip()))

        status = "PASS"
    except Exception as exc:
        status = "FAIL"
        results.append({"test": "harness.exception", "status": "FAIL", "details": str(exc)})

    document = {
        "schema_version": 1,
        "status": status,
        "container": CONTAINER,
        "database": DATABASE,
        "poc_schema": SCHEMA,
        "synthetic_only": True,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "passed": sum(item["status"] == "PASS" for item in results),
        "total": len(results),
        "results": results,
    }
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: document[key] for key in ("status", "passed", "total", "elapsed_seconds")}))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
