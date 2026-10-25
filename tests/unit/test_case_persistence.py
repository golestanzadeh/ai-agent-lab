from datetime import datetime, timezone
import sqlite3

import pytest

from agent_lab.case_persistence import CasePersistenceError, SQLiteCasePersistence
from agent_lab.case_registry import (
    AssessmentMode, CaseRecord, CaseType, LifecycleStatus, OwnerType,
    StorageScopeReference, TaxPeriod,
)
from agent_lab.case_state import CaseState


KEY = b"case-persistence-test-key-32-bytes-minimum"


def _case(case_id: str, owner: str, year: int) -> tuple[CaseRecord, CaseState]:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    record = CaseRecord(
        case_id, OwnerType.PERSON, owner, TaxPeriod("CALENDAR_YEAR", year),
        CaseType.INDIVIDUAL, AssessmentMode.UNKNOWN_PENDING_VERIFICATION,
        LifecycleStatus.CREATED, StorageScopeReference("google_drive", f"ROOT-{case_id}"),
        1, now, now,
    )
    state = CaseState(case_id, 1, "READY", now, now)
    return record, state


def test_multiple_cases_same_year_and_multiple_years_survive_restart(tmp_path):
    path = tmp_path / "case.sqlite3"
    store = SQLiteCasePersistence(path, integrity_key=KEY)
    for values in (
        ("CASE-2024-0001", "PERSON-A", 2024),
        ("CASE-2024-0002", "PERSON-A", 2024),
        ("CASE-2027-0001", "PERSON-A", 2027),
    ):
        store.register_case(*_case(*values), ui_owner_id="PERSON-A")
    store.close()

    reopened = SQLiteCasePersistence(path, integrity_key=KEY)
    allowed = frozenset({"CASE-2024-0001", "CASE-2024-0002", "CASE-2027-0001"})
    runtime = reopened.load_runtime(owner_id="PERSON-A", allowed_case_ids=allowed)
    assert tuple(record.case_id for record in runtime.registry.all_records()) == tuple(sorted(allowed))
    assert runtime.state("CASE-2027-0001").lifecycle_status == "READY"
    reopened.close()


def test_owner_and_allowlist_scope_fail_closed(tmp_path):
    store = SQLiteCasePersistence(tmp_path / "case.sqlite3", integrity_key=KEY)
    record, state = _case("CASE-2025-0001", "PERSON-A", 2025)
    store.register_case(record, state, ui_owner_id="PERSON-A")
    with pytest.raises(CasePersistenceError, match="incomplete"):
        store.load_runtime(owner_id="PERSON-B", allowed_case_ids=frozenset({record.case_id}))
    with pytest.raises(CasePersistenceError, match="incomplete"):
        store.load_runtime(owner_id="PERSON-A", allowed_case_ids=frozenset({"CASE-MISSING"}))
    store.close()


def test_registration_is_atomic_idempotent_and_rejects_changed_identity(tmp_path):
    store = SQLiteCasePersistence(tmp_path / "case.sqlite3", integrity_key=KEY)
    record, state = _case("CASE-2025-0001", "PERSON-A", 2025)
    store.register_case(record, state, ui_owner_id="PERSON-A")
    store.register_case(record, state, ui_owner_id="PERSON-A")
    changed, changed_state = _case("CASE-2025-0001", "PERSON-A", 2026)
    with pytest.raises(CasePersistenceError, match="different content"):
        store.register_case(changed, changed_state, ui_owner_id="PERSON-A")
    changed_state = CaseState(
        state.case_id, state.schema_version, "BLOCKED", state.created_at, state.updated_at
    )
    with pytest.raises(CasePersistenceError, match="different content"):
        store.register_case(record, changed_state, ui_owner_id="PERSON-A")
    with pytest.raises(CasePersistenceError, match="scope must match"):
        store.register_case(record, state, ui_owner_id="PERSON-B")
    store.close()


def test_tampered_case_state_authorization_and_audit_fail_reopen(tmp_path):
    for table, statement in (
        ("case_record", "UPDATE case_record SET tax_year=2026"),
        ("case_state", "UPDATE case_state SET payload=replace(payload,'READY','BLOCKED')"),
        ("ui_case_authorization", "UPDATE ui_case_authorization SET owner_id='PERSON-B'"),
        ("case_audit", "UPDATE case_audit SET payload_digest=?"),
    ):
        path = tmp_path / f"{table}.sqlite3"
        store = SQLiteCasePersistence(path, integrity_key=KEY)
        record, state = _case("CASE-2025-0001", "PERSON-A", 2025)
        store.register_case(record, state, ui_owner_id="PERSON-A")
        store.close()
        db = sqlite3.connect(path)
        if "?" in statement:
            db.execute(statement, ("f" * 64,))
        else:
            db.execute(statement)
        db.commit(); db.close()
        with pytest.raises(CasePersistenceError, match="integrity failure|scope failure"):
            SQLiteCasePersistence(path, integrity_key=KEY)


def test_rejects_wrong_key_synced_path_and_unversioned_database(tmp_path):
    path = tmp_path / "case.sqlite3"
    store = SQLiteCasePersistence(path, integrity_key=KEY)
    store.register_case(*_case("CASE-2025-0001", "PERSON-A", 2025), ui_owner_id="PERSON-A")
    store.close()
    with pytest.raises(CasePersistenceError):
        SQLiteCasePersistence(path, integrity_key=b"another-protected-integrity-key-value")
    empty = tmp_path / "empty.sqlite3"
    SQLiteCasePersistence(empty, integrity_key=KEY).close()
    with pytest.raises(CasePersistenceError, match="anchor integrity"):
        SQLiteCasePersistence(empty, integrity_key=b"another-protected-integrity-key-value")
    with pytest.raises(ValueError, match="synced"):
        SQLiteCasePersistence(tmp_path / "OneDrive" / "case.sqlite3", integrity_key=KEY)
    unknown = tmp_path / "unknown.sqlite3"
    db = sqlite3.connect(unknown); db.execute("CREATE TABLE unknown(value TEXT)"); db.commit(); db.close()
    with pytest.raises(CasePersistenceError, match="unversioned"):
        SQLiteCasePersistence(unknown, integrity_key=KEY)


def test_deleted_or_cross_owner_scope_rows_fail_reopen(tmp_path):
    for name, statement in (
        ("missing-state", "DELETE FROM case_state"),
        ("cross-owner", "UPDATE ui_case_authorization SET owner_id='PERSON-B'"),
        ("missing-audit", "DELETE FROM case_audit"),
    ):
        path = tmp_path / f"{name}.sqlite3"
        store = SQLiteCasePersistence(path, integrity_key=KEY)
        store.register_case(*_case("CASE-2025-0001", "PERSON-A", 2025), ui_owner_id="PERSON-A")
        store.close()
        db = sqlite3.connect(path); db.execute(statement); db.commit(); db.close()
        with pytest.raises(CasePersistenceError, match="completeness|scope|integrity"):
            SQLiteCasePersistence(path, integrity_key=KEY)


def test_anchor_rejects_coordinated_rows_deletion_and_valid_prefix_rollback(tmp_path):
    path = tmp_path / "case.sqlite3"
    store = SQLiteCasePersistence(path, integrity_key=KEY)
    store.register_case(*_case("CASE-2024-0001", "PERSON-A", 2024), ui_owner_id="PERSON-A")
    backup = tmp_path / "prefix.sqlite3"
    source = sqlite3.connect(path); target = sqlite3.connect(backup); source.backup(target)
    source.close(); target.close()
    store.register_case(*_case("CASE-2025-0001", "PERSON-A", 2025), ui_owner_id="PERSON-A")
    store.close()

    path.write_bytes(backup.read_bytes())
    with pytest.raises(CasePersistenceError, match="anchor integrity"):
        SQLiteCasePersistence(path, integrity_key=KEY)

    db = sqlite3.connect(path)
    db.execute("PRAGMA foreign_keys=OFF")
    for table in ("case_state", "ui_case_authorization", "case_audit", "case_record"):
        db.execute(f"DELETE FROM {table}")
    db.commit(); db.close()
    with pytest.raises(CasePersistenceError, match="anchor integrity"):
        SQLiteCasePersistence(path, integrity_key=KEY)


def test_failed_open_releases_windows_database_handle(tmp_path):
    path = tmp_path / "case.sqlite3"
    store = SQLiteCasePersistence(path, integrity_key=KEY)
    store.register_case(*_case("CASE-2025-0001", "PERSON-A", 2025), ui_owner_id="PERSON-A")
    store.close()
    with pytest.raises(CasePersistenceError):
        SQLiteCasePersistence(path, integrity_key=b"another-protected-integrity-key-value")
    renamed = tmp_path / "recoverable.sqlite3"
    path.rename(renamed)
    renamed.unlink()
