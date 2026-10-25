from datetime import datetime, timezone
import hashlib
import hmac
import json
import sqlite3

import pytest

from agent_lab.case_persistence import (
    CasePersistenceError, CaseRevisionConflict, SQLiteCasePersistence,
)
from agent_lab.case_registry import (
    AssessmentMode, CaseRecord, CaseType, LifecycleStatus, OwnerType,
    StorageScopeReference, TaxPeriod,
)
from agent_lab.case_state import CaseState, RunStatus
from agent_lab.durable_kernel_run import DurableKernelRunLifecycle


KEY = b"case-persistence-f03-key-32-bytes-minimum"


def registered(store, case_id="CASE-2025-0001", owner="PERSON-A", year=2025):
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    record = CaseRecord(
        case_id, OwnerType.PERSON, owner, TaxPeriod("CALENDAR_YEAR", year),
        CaseType.INDIVIDUAL, AssessmentMode.UNKNOWN_PENDING_VERIFICATION,
        LifecycleStatus.CREATED, StorageScopeReference("local", f"ROOT-{case_id}"),
        1, now, now,
    )
    state = CaseState(case_id, 1, "READY", now, now)
    store.register_case(record, state, ui_owner_id=owner)


def test_state_and_run_lifecycle_is_versioned_idempotent_and_restart_safe(tmp_path):
    path = tmp_path / "case.sqlite3"
    store = SQLiteCasePersistence(path, integrity_key=KEY); registered(store)
    changed = store.mutate_state(
        owner_id="PERSON-A", case_id="CASE-2025-0001", tax_year=2025,
        request_id="STATE-1", expected_revision=1, documents_ref="DOCSET-1",
    )
    assert changed.revision == 2 and changed.state.documents_ref == "DOCSET-1"
    repeated = store.mutate_state(
        owner_id="PERSON-A", case_id="CASE-2025-0001", tax_year=2025,
        request_id="STATE-1", expected_revision=1, documents_ref="DOCSET-1",
    )
    assert repeated.idempotent and repeated.revision == 2
    run = store.create_run(
        owner_id="PERSON-A", case_id="CASE-2025-0001", tax_year=2025,
        run_id="RUN-1", request_id="RUN-REQUEST-1", expected_state_revision=2,
    )
    assert run.run.status is RunStatus.CREATED and run.revision == 1
    running = store.transition_run(
        owner_id="PERSON-A", case_id="CASE-2025-0001", tax_year=2025,
        run_id="RUN-1", request_id="RUN-TRANSITION-1", expected_revision=1,
        status=RunStatus.RUNNING,
    )
    assert running.revision == 2
    created_replay = store.create_run(
        owner_id="PERSON-A", case_id="CASE-2025-0001", tax_year=2025,
        run_id="RUN-1", request_id="RUN-REQUEST-1", expected_state_revision=2,
    )
    transition_replay = store.transition_run(
        owner_id="PERSON-A", case_id="CASE-2025-0001", tax_year=2025,
        run_id="RUN-1", request_id="RUN-TRANSITION-1", expected_revision=1,
        status=RunStatus.RUNNING,
    )
    assert created_replay.idempotent and created_replay.run.status is RunStatus.CREATED
    assert created_replay.revision == 1
    assert transition_replay.idempotent and transition_replay.run.status is RunStatus.RUNNING
    assert transition_replay.revision == 2
    store.close()
    reopened = SQLiteCasePersistence(path, integrity_key=KEY)
    runtime = reopened.load_runtime(owner_id="PERSON-A", allowed_case_ids=frozenset({"CASE-2025-0001"}))
    assert runtime.state("CASE-2025-0001").last_run_id == "RUN-1"
    assert runtime.case_runs("CASE-2025-0001")[0].run.status is RunStatus.RUNNING
    reopened.close()


def test_conflicts_changed_replay_and_invalid_transition_fail_without_partial_state(tmp_path):
    store = SQLiteCasePersistence(tmp_path / "case.sqlite3", integrity_key=KEY); registered(store)
    store.mutate_state(owner_id="PERSON-A", case_id="CASE-2025-0001", tax_year=2025,
                       request_id="M1", expected_revision=1, facts_ref="FACTS-1")
    with pytest.raises(CaseRevisionConflict):
        store.mutate_state(owner_id="PERSON-A", case_id="CASE-2025-0001", tax_year=2025,
                           request_id="M2", expected_revision=1, facts_ref="FACTS-2")
    with pytest.raises(CasePersistenceError, match="different content"):
        store.mutate_state(owner_id="PERSON-A", case_id="CASE-2025-0001", tax_year=2025,
                           request_id="M1", expected_revision=1, facts_ref="CHANGED")
    store.create_run(owner_id="PERSON-A", case_id="CASE-2025-0001", tax_year=2025,
                     run_id="RUN-1", request_id="R1", expected_state_revision=2)
    with pytest.raises(ValueError, match="invalid run transition"):
        store.transition_run(owner_id="PERSON-A", case_id="CASE-2025-0001", tax_year=2025,
                             run_id="RUN-1", request_id="T1", expected_revision=1,
                             status=RunStatus.SUCCEEDED)
    assert store.load_runtime(owner_id="PERSON-A", allowed_case_ids=frozenset({"CASE-2025-0001"})).case_runs("CASE-2025-0001")[0].run.status is RunStatus.CREATED
    store.close()


def test_owner_case_year_run_isolation_and_duplicate_run_rejected(tmp_path):
    store = SQLiteCasePersistence(tmp_path / "case.sqlite3", integrity_key=KEY)
    registered(store, "CASE-2025-A", "PERSON-A", 2025); registered(store, "CASE-2025-B", "PERSON-A", 2025)
    for owner, case, year in (("PERSON-B", "CASE-2025-A", 2025), ("PERSON-A", "CASE-2025-A", 2024)):
        with pytest.raises(PermissionError):
            store.create_run(owner_id=owner, case_id=case, tax_year=year, run_id="RUN-X",
                             request_id=f"REQ-{owner}-{year}", expected_state_revision=1)
    store.create_run(owner_id="PERSON-A", case_id="CASE-2025-A", tax_year=2025,
                     run_id="RUN-X", request_id="REQ-X", expected_state_revision=1)
    with pytest.raises(CasePersistenceError, match="run identity"):
        store.create_run(owner_id="PERSON-A", case_id="CASE-2025-B", tax_year=2025,
                         run_id="RUN-X", request_id="REQ-Y", expected_state_revision=1)
    store.close()


def test_kernel_adapter_requires_exact_registered_context(tmp_path):
    class Kernel:
        def registered_case_context(self, task_id):
            assert task_id == "TASK-1"
            return {"case_id": "CASE-2025-0001", "tax_year": 2025, "run_id": "RUN-1"}
    store = SQLiteCasePersistence(tmp_path / "case.sqlite3", integrity_key=KEY); registered(store)
    adapter = DurableKernelRunLifecycle(Kernel(), store)
    run = adapter.create_for_registered_task(
        task_id="TASK-1", owner_id="PERSON-A", case_id="CASE-2025-0001", tax_year=2025,
        run_id="RUN-1", request_id="KERNEL-RUN-1", expected_state_revision=1,
    )
    assert run.run.run_id == "RUN-1"
    with pytest.raises(PermissionError, match="do not match"):
        adapter.transition_for_registered_task(
            task_id="TASK-1", owner_id="PERSON-A", case_id="CASE-2025-0001", tax_year=2024,
            run_id="RUN-1", request_id="BAD", expected_revision=1, status=RunStatus.RUNNING,
        )
    store.close()


def test_empty_v1_database_migrates_atomically_to_v2(tmp_path):
    path = tmp_path / "v1.sqlite3"
    db = sqlite3.connect(path)
    db.executescript("""
      CREATE TABLE case_record(case_id TEXT PRIMARY KEY,owner_type TEXT NOT NULL,owner_id TEXT NOT NULL,tax_period_type TEXT NOT NULL,tax_year INTEGER NOT NULL,case_type TEXT NOT NULL,assessment_mode TEXT NOT NULL,lifecycle_status TEXT NOT NULL,storage_provider TEXT NOT NULL,storage_root_id TEXT NOT NULL UNIQUE,schema_version INTEGER NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,last_run_id TEXT,digest TEXT NOT NULL);
      CREATE TABLE case_state(case_id TEXT PRIMARY KEY REFERENCES case_record(case_id),payload TEXT NOT NULL,digest TEXT NOT NULL);
      CREATE TABLE ui_case_authorization(owner_id TEXT NOT NULL,case_id TEXT NOT NULL REFERENCES case_record(case_id),granted_at TEXT NOT NULL,digest TEXT NOT NULL,PRIMARY KEY(owner_id,case_id));
      CREATE TABLE case_audit(event_id INTEGER PRIMARY KEY AUTOINCREMENT,action TEXT NOT NULL,case_id TEXT NOT NULL,payload_digest TEXT NOT NULL,previous_digest TEXT NOT NULL,event_digest TEXT NOT NULL);
      PRAGMA user_version=1;
    """); db.close()
    canonical = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    mac = lambda value: hmac.new(KEY, (value if isinstance(value, str) else canonical(value)).encode(), hashlib.sha256).hexdigest()
    payload = {"schema_version": 1, "event_count": 0, "head_event_id": 0,
               "head_digest": "0" * 64, "case_count": 0,
               "key_verifier": mac("ai-tax-agent.case-persistence/key-verifier/1")}
    path.with_suffix(".sqlite3.audit-anchor").write_text(canonical(payload | {"anchor_mac": mac(payload)}), encoding="utf-8")
    store = SQLiteCasePersistence(path, integrity_key=KEY)
    assert store._db.execute("PRAGMA user_version").fetchone()[0] == 2
    assert store._db.execute("SELECT revision FROM case_state").fetchall() == []
    store.close()


@pytest.mark.parametrize("statement", [
    "UPDATE durable_run SET status='SUCCEEDED'",
    "UPDATE mutation_request SET request_json='{}'",
    "DELETE FROM case_audit WHERE action='RUN_CREATED'",
])
def test_run_request_and_audit_tampering_fail_closed_after_restart(tmp_path, statement):
    path = tmp_path / (hashlib.sha256(statement.encode()).hexdigest() + ".sqlite3")
    store = SQLiteCasePersistence(path, integrity_key=KEY); registered(store)
    store.create_run(owner_id="PERSON-A", case_id="CASE-2025-0001", tax_year=2025,
                     run_id="RUN-1", request_id="REQ-1", expected_state_revision=1)
    store.close()
    db = sqlite3.connect(path); db.execute(statement); db.commit(); db.close()
    with pytest.raises((CasePersistenceError, ValueError)):
        SQLiteCasePersistence(path, integrity_key=KEY)
