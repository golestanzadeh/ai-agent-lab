"""Canonical SQLite persistence for case metadata, state and UI scope.

Document bytes and identity/fact payloads deliberately do not belong here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json
from pathlib import Path
import sqlite3
from threading import RLock

from agent_lab.case_registry import (
    AssessmentMode, CaseRecord, CaseRegistry, CaseType, LifecycleStatus,
    OwnerType, StorageScopeReference, TaxPeriod,
)
from agent_lab.case_state import CaseState, RunRecord, RunStatus, validate_run_transition


SCHEMA_VERSION = 3


class CasePersistenceError(RuntimeError):
    pass


class CaseRevisionConflict(CasePersistenceError):
    pass


@dataclass(frozen=True, slots=True)
class VersionedCaseState:
    state: CaseState
    revision: int
    idempotent: bool = False


@dataclass(frozen=True, slots=True)
class VersionedRun:
    run: RunRecord
    tax_year: int
    revision: int
    idempotent: bool = False


@dataclass(frozen=True, slots=True)
class StorageProvisioningIntent:
    operation_id: str
    request_id: str
    owner_id: str
    case_id: str
    tax_year: int
    status: str
    attempt_count: int
    storage_provider: str | None
    storage_root_id: str | None
    failure_code: str | None
    revision: int


@dataclass(frozen=True, slots=True)
class DurableCaseRuntime:
    registry: CaseRegistry
    states: tuple[CaseState, ...]
    allowed_case_ids: frozenset[str]
    runs: tuple[VersionedRun, ...] = ()

    def state(self, case_id: str) -> CaseState:
        if case_id not in self.allowed_case_ids:
            raise PermissionError("case is outside the authorized runtime scope")
        for state in self.states:
            if state.case_id == case_id:
                return state
        raise CasePersistenceError("authorized case state is unavailable")

    def case_runs(self, case_id: str) -> tuple[VersionedRun, ...]:
        if case_id not in self.allowed_case_ids:
            raise PermissionError("case is outside the authorized runtime scope")
        return tuple(run for run in self.runs if run.run.case_id == case_id)


class SQLiteCasePersistence:
    """One deployment-wide SQLite authority for case metadata and state."""

    def __init__(self, path: str | Path, *, integrity_key: bytes) -> None:
        if not isinstance(integrity_key, bytes) or len(integrity_key) < 32:
            raise ValueError("a protected integrity key of at least 32 bytes is required")
        self.path = Path(path).resolve()
        lowered = self.path.as_posix().casefold()
        if any(marker in lowered for marker in ("/onedrive/", "/google drive/", "/dropbox/")):
            raise ValueError("live SQLite database cannot be placed in a synced folder")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._anchor_path = self.path.with_suffix(self.path.suffix + ".audit-anchor")
        self._key = integrity_key
        self._lock = RLock()
        self._db = sqlite3.connect(self.path, check_same_thread=False)
        try:
            self._initialize_connection()
        except BaseException:
            self._db.close()
            raise

    def _initialize_connection(self) -> None:
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.execute("PRAGMA busy_timeout=5000")
        version = self._db.execute("PRAGMA user_version").fetchone()[0]
        if version == 0:
            tables = self._db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            if tables:
                raise CasePersistenceError("unversioned database is not accepted")
            if self._anchor_path.exists():
                raise CasePersistenceError("database is missing while protected anchor exists")
            self._create_schema()
            self._write_anchor()
        elif version == 1:
            self._verify_all()
            self._verify_anchor(schema_version=1)
            self._migrate_v1_to_v2()
            version = 2
        if version == 2:
            self._verify_all()
            self._verify_anchor(schema_version=2)
            self._migrate_v2_to_v3()
        elif version not in {0, 1, SCHEMA_VERSION}:
            raise CasePersistenceError("unsupported case persistence schema")
        self._verify_all()
        self._verify_anchor()

    def close(self) -> None:
        self._db.close()

    def _create_schema(self) -> None:
        with self._db:
            self._db.executescript("""
                CREATE TABLE case_record(
                    case_id TEXT PRIMARY KEY, owner_type TEXT NOT NULL,
                    owner_id TEXT NOT NULL, tax_period_type TEXT NOT NULL,
                    tax_year INTEGER NOT NULL, case_type TEXT NOT NULL,
                    assessment_mode TEXT NOT NULL, lifecycle_status TEXT NOT NULL,
                    storage_provider TEXT NOT NULL, storage_root_id TEXT NOT NULL UNIQUE,
                    schema_version INTEGER NOT NULL, created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL, last_run_id TEXT, digest TEXT NOT NULL,
                    CHECK(tax_year BETWEEN 1900 AND 9999));
                CREATE INDEX case_owner_year ON case_record(owner_id,tax_year,case_id);
                CREATE TABLE case_state(
                    case_id TEXT PRIMARY KEY REFERENCES case_record(case_id),
                    payload TEXT NOT NULL, revision INTEGER NOT NULL,
                    digest TEXT NOT NULL CHECK(revision >= 1));
                CREATE TABLE ui_case_authorization(
                    owner_id TEXT NOT NULL, case_id TEXT NOT NULL REFERENCES case_record(case_id),
                    granted_at TEXT NOT NULL, digest TEXT NOT NULL,
                    PRIMARY KEY(owner_id,case_id));
                CREATE TABLE case_audit(
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL,
                    case_id TEXT NOT NULL, payload_digest TEXT NOT NULL,
                    previous_digest TEXT NOT NULL, event_digest TEXT NOT NULL);
                CREATE TABLE durable_run(
                    run_id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES case_record(case_id),
                    tax_year INTEGER NOT NULL, request_id TEXT,
                    status TEXT NOT NULL, schema_version INTEGER NOT NULL,
                    revision INTEGER NOT NULL, created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL, digest TEXT NOT NULL,
                    UNIQUE(case_id,request_id), CHECK(revision >= 1));
                CREATE INDEX run_case_year ON durable_run(case_id,tax_year,run_id);
                CREATE TABLE mutation_request(
                    request_id TEXT PRIMARY KEY, operation TEXT NOT NULL,
                    case_id TEXT NOT NULL REFERENCES case_record(case_id),
                    request_json TEXT NOT NULL, request_digest TEXT NOT NULL, result_json TEXT NOT NULL,
                    result_digest TEXT NOT NULL);
                CREATE TABLE storage_provisioning(
                    operation_id TEXT PRIMARY KEY, request_id TEXT NOT NULL UNIQUE,
                    owner_id TEXT NOT NULL, case_id TEXT NOT NULL UNIQUE,
                    tax_year INTEGER NOT NULL, status TEXT NOT NULL,
                    attempt_count INTEGER NOT NULL, storage_provider TEXT,
                    storage_root_id TEXT, failure_code TEXT, revision INTEGER NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL, digest TEXT NOT NULL,
                    CHECK(attempt_count >= 0), CHECK(revision >= 1));
                PRAGMA user_version=3;
            """)

    def _migrate_v1_to_v2(self) -> None:
        try:
            self._db.execute("BEGIN IMMEDIATE")
            self._db.execute("ALTER TABLE case_state ADD COLUMN revision INTEGER NOT NULL DEFAULT 1")
            self._db.execute("""CREATE TABLE durable_run(
                    run_id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES case_record(case_id),
                    tax_year INTEGER NOT NULL, request_id TEXT,
                    status TEXT NOT NULL, schema_version INTEGER NOT NULL,
                    revision INTEGER NOT NULL, created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL, digest TEXT NOT NULL,
                    UNIQUE(case_id,request_id), CHECK(revision >= 1))""")
            self._db.execute("CREATE INDEX run_case_year ON durable_run(case_id,tax_year,run_id)")
            self._db.execute("""CREATE TABLE mutation_request(
                    request_id TEXT PRIMARY KEY, operation TEXT NOT NULL,
                    case_id TEXT NOT NULL REFERENCES case_record(case_id),
                    request_json TEXT NOT NULL, request_digest TEXT NOT NULL, result_json TEXT NOT NULL,
                    result_digest TEXT NOT NULL)""")
            self._db.execute("PRAGMA user_version=2")
            self._db.commit()
            self._write_anchor(schema_version=2)
        except Exception:
            self._db.rollback()
            raise

    def _migrate_v2_to_v3(self) -> None:
        try:
            self._db.execute("BEGIN IMMEDIATE")
            self._db.execute("""CREATE TABLE storage_provisioning(
                operation_id TEXT PRIMARY KEY, request_id TEXT NOT NULL UNIQUE,
                owner_id TEXT NOT NULL, case_id TEXT NOT NULL UNIQUE,
                tax_year INTEGER NOT NULL, status TEXT NOT NULL,
                attempt_count INTEGER NOT NULL, storage_provider TEXT,
                storage_root_id TEXT, failure_code TEXT, revision INTEGER NOT NULL,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL, digest TEXT NOT NULL,
                CHECK(attempt_count >= 0), CHECK(revision >= 1))""")
            self._db.execute("PRAGMA user_version=3")
            self._db.commit(); self._write_anchor()
        except Exception:
            self._db.rollback(); raise

    @staticmethod
    def _canonical(value: dict) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def _mac(self, value: dict | str) -> str:
        raw = value if isinstance(value, str) else self._canonical(value)
        return hmac.new(self._key, raw.encode(), hashlib.sha256).hexdigest()

    @staticmethod
    def _case_payload(record: CaseRecord) -> dict:
        return {
            "case_id": record.case_id, "owner_type": record.owner_type.value,
            "owner_id": record.owner_id, "tax_period_type": record.tax_period.type,
            "tax_year": record.tax_period.year, "case_type": record.case_type.value,
            "assessment_mode": record.assessment_mode.value,
            "lifecycle_status": record.lifecycle_status.value,
            "storage_provider": record.storage_scope_reference.provider,
            "storage_root_id": record.storage_scope_reference.root_id,
            "schema_version": record.schema_version,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
            "last_run_id": record.last_run_id,
        }

    @staticmethod
    def _state_payload(state: CaseState) -> dict:
        payload = asdict(state)
        payload["created_at"] = state.created_at.isoformat()
        payload["updated_at"] = state.updated_at.isoformat()
        return payload

    def register_case(self, record: CaseRecord, state: CaseState, *, ui_owner_id: str) -> None:
        if state.case_id != record.case_id or ui_owner_id != record.owner_id:
            raise CasePersistenceError("case, state and authorization scope must match")
        case_payload = self._case_payload(record)
        state_payload = self._state_payload(state)
        authorization = {
            "owner_id": ui_owner_id, "case_id": record.case_id,
            "granted_at": record.created_at.isoformat(),
        }
        with self._lock:
            self._verify_all()
            provisioning = self._db.execute(
                "SELECT * FROM storage_provisioning WHERE case_id=?", (record.case_id,)
            ).fetchone()
            if provisioning is not None:
                intent = self._intent(provisioning)
                if (
                    intent.status != "COMPLETE"
                    or intent.owner_id != record.owner_id
                    or intent.tax_year != record.tax_period.year
                    or intent.storage_provider != record.storage_scope_reference.provider
                    or intent.storage_root_id != record.storage_scope_reference.root_id
                ):
                    raise CasePersistenceError("completed provisioning does not match case registration")
            existing = self._db.execute(
                "SELECT digest FROM case_record WHERE case_id=?", (record.case_id,)
            ).fetchone()
            if existing is not None:
                existing_state = self._db.execute(
                    "SELECT digest FROM case_state WHERE case_id=?", (record.case_id,)
                ).fetchone()
                existing_auth = self._db.execute(
                    "SELECT digest FROM ui_case_authorization WHERE owner_id=? AND case_id=?",
                    (ui_owner_id, record.case_id),
                ).fetchone()
                if (
                    not hmac.compare_digest(existing["digest"], self._mac(case_payload))
                    or existing_state is None
                    or not hmac.compare_digest(existing_state["digest"], self._mac(self._canonical(state_payload)))
                    or existing_auth is None
                    or not hmac.compare_digest(existing_auth["digest"], self._mac(authorization))
                ):
                    raise CasePersistenceError("case identity already exists with different content")
                return
            try:
                self._db.execute("BEGIN IMMEDIATE")
                self._db.execute(
                    "INSERT INTO case_record VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    tuple(case_payload.values()) + (self._mac(case_payload),),
                )
                state_json = self._canonical(state_payload)
                self._db.execute(
                    "INSERT INTO case_state(case_id,payload,revision,digest) VALUES(?,?,?,?)",
                    (record.case_id, state_json, 1, self._mac(state_json)),
                )
                self._db.execute(
                    "INSERT INTO ui_case_authorization VALUES(?,?,?,?)",
                    (*authorization.values(), self._mac(authorization)),
                )
                self._audit("CASE_REGISTERED", record.case_id, self._mac(case_payload))
                self._db.commit()
                self._write_anchor()
            except Exception:
                self._db.rollback()
                raise

    def load_runtime(self, *, owner_id: str, allowed_case_ids: frozenset[str]) -> DurableCaseRuntime:
        if not owner_id.strip() or not allowed_case_ids:
            raise ValueError("owner_id and a non-empty allowlist are required")
        with self._lock:
            self._verify_all()
            placeholders = ",".join("?" for _ in allowed_case_ids)
            rows = self._db.execute(
                f"SELECT c.*,s.payload,s.digest AS state_digest,a.granted_at,a.digest AS auth_digest "
                f"FROM case_record c JOIN case_state s USING(case_id) "
                f"JOIN ui_case_authorization a ON a.case_id=c.case_id AND a.owner_id=c.owner_id "
                f"WHERE c.owner_id=? AND c.case_id IN ({placeholders}) ORDER BY c.case_id",
                (owner_id, *sorted(allowed_case_ids)),
            ).fetchall()
            if {row["case_id"] for row in rows} != set(allowed_case_ids):
                raise CasePersistenceError("authorized case scope is incomplete or mismatched")
            registry = CaseRegistry()
            states = []
            for row in rows:
                record = self._record(row)
                registry.register(record)
                states.append(self._state(row["payload"]))
            registry.validate()
            run_rows = self._db.execute(
                f"SELECT r.* FROM durable_run r JOIN case_record c USING(case_id) "
                f"WHERE c.owner_id=? AND r.case_id IN ({placeholders}) ORDER BY r.run_id",
                (owner_id, *sorted(allowed_case_ids)),
            ).fetchall()
            runs = tuple(self._versioned_run(row) for row in run_rows)
            return DurableCaseRuntime(registry, tuple(states), allowed_case_ids, runs)

    def get_state(self, *, owner_id: str, case_id: str, tax_year: int) -> VersionedCaseState:
        with self._lock:
            self._verify_all(); self._verify_anchor()
            self._authorize(owner_id, case_id, tax_year)
            row = self._db.execute("SELECT * FROM case_state WHERE case_id=?", (case_id,)).fetchone()
            return VersionedCaseState(self._state(row["payload"]), row["revision"])

    def prepare_storage_provisioning(
        self, *, operation_id: str, request_id: str, owner_id: str,
        case_id: str, tax_year: int,
    ) -> StorageProvisioningIntent:
        values = (operation_id, request_id, owner_id, case_id)
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError("complete provisioning identity is required")
        if isinstance(tax_year, bool) or not isinstance(tax_year, int):
            raise ValueError("tax_year must be an integer")
        with self._lock:
            self._verify_all(); self._verify_anchor()
            existing = self._db.execute(
                "SELECT * FROM storage_provisioning WHERE operation_id=? OR request_id=? OR case_id=?",
                (operation_id, request_id, case_id),
            ).fetchall()
            if existing:
                if len(existing) != 1:
                    raise CasePersistenceError("conflicting provisioning identities")
                intent = self._intent(existing[0])
                if (intent.operation_id, intent.request_id, intent.owner_id, intent.case_id, intent.tax_year) != (
                    operation_id, request_id, owner_id, case_id, tax_year,
                ):
                    raise CasePersistenceError("provisioning identity already has different scope")
                return intent
            case = self._db.execute("SELECT owner_id,tax_year FROM case_record WHERE case_id=?", (case_id,)).fetchone()
            if case is not None and (case["owner_id"] != owner_id or case["tax_year"] != tax_year):
                raise PermissionError("provisioning scope conflicts with registered case")
            now = datetime.now(timezone.utc).isoformat()
            payload = self._provisioning_payload(
                operation_id, request_id, owner_id, case_id, tax_year, "INTENT", 0,
                None, None, None, 1, now, now,
            )
            try:
                self._db.execute("BEGIN IMMEDIATE")
                self._db.execute("INSERT INTO storage_provisioning VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                 tuple(payload.values()) + (self._mac(payload),))
                self._audit("STORAGE_PROVISIONING_INTENT", case_id, self._mac(payload))
                self._db.commit(); self._write_anchor()
            except Exception:
                self._db.rollback(); raise
            row = self._db.execute("SELECT * FROM storage_provisioning WHERE operation_id=?", (operation_id,)).fetchone()
            return self._intent(row)

    def transition_storage_provisioning(
        self, *, operation_id: str, expected_statuses: frozenset[str], status: str,
        storage_scope: StorageScopeReference | None = None, failure_code: str | None = None,
    ) -> StorageProvisioningIntent:
        allowed = {"IN_PROGRESS", "COMPLETE", "RETRYABLE_FAILURE", "RECONCILIATION_REQUIRED"}
        if status not in allowed or not expected_statuses:
            raise ValueError("invalid provisioning transition")
        with self._lock:
            self._verify_all(); self._verify_anchor()
            try:
                self._db.execute("BEGIN IMMEDIATE")
                row = self._db.execute("SELECT * FROM storage_provisioning WHERE operation_id=?", (operation_id,)).fetchone()
                if row is None:
                    raise CasePersistenceError("unknown provisioning operation")
                current = self._intent(row)
                if current.status == "COMPLETE" and status == "COMPLETE":
                    if storage_scope is None or (current.storage_provider, current.storage_root_id) != (
                        storage_scope.provider, storage_scope.root_id,
                    ):
                        raise CasePersistenceError("completed storage scope does not match")
                    self._db.rollback(); return current
                if current.status not in expected_statuses:
                    raise CaseRevisionConflict("provisioning status conflict")
                if status == "COMPLETE" and storage_scope is None:
                    raise ValueError("completed provisioning requires storage scope")
                if status != "COMPLETE" and storage_scope is not None:
                    raise ValueError("storage scope is only valid for completion")
                now = datetime.now(timezone.utc).isoformat(); revision = current.revision + 1
                attempts = current.attempt_count + (1 if status == "IN_PROGRESS" else 0)
                payload = self._provisioning_payload(
                    current.operation_id, current.request_id, current.owner_id, current.case_id,
                    current.tax_year, status, attempts,
                    storage_scope.provider if storage_scope else current.storage_provider,
                    storage_scope.root_id if storage_scope else current.storage_root_id,
                    failure_code, revision, row["created_at"], now,
                )
                self._db.execute("""UPDATE storage_provisioning SET status=?,attempt_count=?,
                    storage_provider=?,storage_root_id=?,failure_code=?,revision=?,updated_at=?,digest=?
                    WHERE operation_id=?""", (
                    status, attempts, payload["storage_provider"], payload["storage_root_id"],
                    failure_code, revision, now, self._mac(payload), operation_id,
                ))
                self._audit(f"STORAGE_PROVISIONING_{status}", current.case_id, self._mac(payload))
                self._db.commit(); self._write_anchor()
                return StorageProvisioningIntent(
                    operation_id, current.request_id, current.owner_id, current.case_id,
                    current.tax_year, status, attempts, payload["storage_provider"],
                    payload["storage_root_id"], failure_code, revision,
                )
            except Exception:
                self._db.rollback(); raise

    def get_storage_provisioning(self, *, operation_id: str) -> StorageProvisioningIntent:
        with self._lock:
            self._verify_all(); self._verify_anchor()
            row = self._db.execute("SELECT * FROM storage_provisioning WHERE operation_id=?", (operation_id,)).fetchone()
            if row is None:
                raise CasePersistenceError("unknown provisioning operation")
            return self._intent(row)

    def mutate_state(
        self, *, owner_id: str, case_id: str, tax_year: int, request_id: str,
        expected_revision: int, lifecycle_status: str | None = None,
        last_run_id: str | None = None, **refs: str | None,
    ) -> VersionedCaseState:
        allowed = {"parties_ref", "documents_ref", "evidence_ref", "facts_ref", "assumptions_ref",
                   "rules_ref", "calculations_ref", "optimization_ref", "challenges_ref",
                   "approvals_ref", "outputs_ref"}
        if set(refs) - allowed or not request_id.strip() or expected_revision < 1:
            raise ValueError("invalid state mutation request")
        request = {"owner_id": owner_id, "case_id": case_id, "tax_year": tax_year,
                   "expected_revision": expected_revision, "lifecycle_status": lifecycle_status,
                   "last_run_id": last_run_id, "refs": refs}
        with self._lock:
            cached = self._idempotent_result(request_id, "MUTATE_STATE", case_id, request)
            if cached is not None:
                return VersionedCaseState(self._state(cached["payload"]), cached["revision"], True)
            self._verify_all(); self._verify_anchor()
            try:
                self._db.execute("BEGIN IMMEDIATE")
                self._authorize(owner_id, case_id, tax_year)
                row = self._db.execute("SELECT * FROM case_state WHERE case_id=?", (case_id,)).fetchone()
                if row["revision"] != expected_revision:
                    raise CaseRevisionConflict("case state revision conflict")
                state = self._state(row["payload"])
                if last_run_id is not None:
                    run = self._db.execute("SELECT case_id,tax_year FROM durable_run WHERE run_id=?", (last_run_id,)).fetchone()
                    if run is None or run["case_id"] != case_id or run["tax_year"] != tax_year:
                        raise CasePersistenceError("last_run_id is outside the authorized case scope")
                values = asdict(state) | refs
                values["lifecycle_status"] = lifecycle_status or state.lifecycle_status
                values["last_run_id"] = last_run_id if last_run_id is not None else state.last_run_id
                values["updated_at"] = datetime.now(timezone.utc)
                updated = CaseState(**values)
                payload = self._canonical(self._state_payload(updated)); revision = expected_revision + 1
                self._db.execute("UPDATE case_state SET payload=?,revision=?,digest=? WHERE case_id=?",
                                 (payload, revision, self._mac(payload), case_id))
                result = {"payload": payload, "revision": revision}
                self._record_request(request_id, "MUTATE_STATE", case_id, request, result)
                self._audit("CASE_STATE_MUTATED", case_id, self._mac(result))
                self._db.commit(); self._write_anchor()
                return VersionedCaseState(updated, revision)
            except Exception:
                self._db.rollback(); raise

    def create_run(
        self, *, owner_id: str, case_id: str, tax_year: int, run_id: str,
        request_id: str, expected_state_revision: int,
    ) -> VersionedRun:
        if not run_id.strip() or not request_id.strip() or expected_state_revision < 1:
            raise ValueError("invalid run creation request")
        request = {"owner_id": owner_id, "case_id": case_id, "tax_year": tax_year,
                   "run_id": run_id, "expected_state_revision": expected_state_revision}
        with self._lock:
            cached = self._idempotent_result(request_id, "CREATE_RUN", case_id, request)
            if cached is not None:
                return self._versioned_run_result(cached, idempotent=True)
            self._verify_all(); self._verify_anchor()
            try:
                self._db.execute("BEGIN IMMEDIATE"); self._authorize(owner_id, case_id, tax_year)
                state_row = self._db.execute("SELECT * FROM case_state WHERE case_id=?", (case_id,)).fetchone()
                if state_row["revision"] != expected_state_revision:
                    raise CaseRevisionConflict("case state revision conflict")
                now = datetime.now(timezone.utc)
                run = RunRecord(run_id, case_id, request_id, RunStatus.CREATED, 1, now, now)
                payload = self._run_payload(run, tax_year, 1)
                self._db.execute("INSERT INTO durable_run VALUES(?,?,?,?,?,?,?,?,?,?)", tuple(payload.values()) + (self._mac(payload),))
                state = self._state(state_row["payload"])
                updated = CaseState(**(asdict(state) | {"last_run_id": run_id, "updated_at": now}))
                state_payload = self._canonical(self._state_payload(updated))
                self._db.execute("UPDATE case_state SET payload=?,revision=?,digest=? WHERE case_id=?",
                                 (state_payload, expected_state_revision + 1, self._mac(state_payload), case_id))
                result = {"run": payload}
                self._record_request(request_id, "CREATE_RUN", case_id, request, result)
                self._audit("RUN_CREATED", case_id, self._mac(payload))
                self._db.commit(); self._write_anchor()
                return VersionedRun(run, tax_year, 1)
            except sqlite3.IntegrityError as exc:
                self._db.rollback(); raise CasePersistenceError("run identity already exists") from exc
            except Exception:
                self._db.rollback(); raise

    def transition_run(
        self, *, owner_id: str, case_id: str, tax_year: int, run_id: str,
        request_id: str, expected_revision: int, status: RunStatus,
    ) -> VersionedRun:
        request = {"owner_id": owner_id, "case_id": case_id, "tax_year": tax_year,
                   "run_id": run_id, "expected_revision": expected_revision, "status": status.value}
        with self._lock:
            cached = self._idempotent_result(request_id, "TRANSITION_RUN", case_id, request)
            if cached is not None:
                return self._versioned_run_result(cached, idempotent=True)
            self._verify_all(); self._verify_anchor()
            try:
                self._db.execute("BEGIN IMMEDIATE"); self._authorize(owner_id, case_id, tax_year)
                row = self._db.execute("SELECT * FROM durable_run WHERE run_id=?", (run_id,)).fetchone()
                if row is None or row["case_id"] != case_id or row["tax_year"] != tax_year:
                    raise CasePersistenceError("run is outside the authorized case scope")
                if row["revision"] != expected_revision:
                    raise CaseRevisionConflict("run revision conflict")
                run = self._run(row); validate_run_transition(run.status, status)
                updated = RunRecord(run.run_id, run.case_id, run.request_id, status, run.schema_version,
                                    run.created_at, datetime.now(timezone.utc))
                revision = expected_revision + 1; payload = self._run_payload(updated, tax_year, revision)
                self._db.execute("UPDATE durable_run SET status=?,revision=?,updated_at=?,digest=? WHERE run_id=?",
                                 (status.value, revision, updated.updated_at.isoformat(), self._mac(payload), run_id))
                result = {"run": payload}
                self._record_request(request_id, "TRANSITION_RUN", case_id, request, result)
                self._audit("RUN_TRANSITIONED", case_id, self._mac(payload))
                self._db.commit(); self._write_anchor()
                return VersionedRun(updated, tax_year, revision)
            except Exception:
                self._db.rollback(); raise

    def _record(self, row: sqlite3.Row) -> CaseRecord:
        return CaseRecord(
            case_id=row["case_id"], owner_type=OwnerType(row["owner_type"]),
            owner_id=row["owner_id"],
            tax_period=TaxPeriod(row["tax_period_type"], row["tax_year"]),
            case_type=CaseType(row["case_type"]),
            assessment_mode=AssessmentMode(row["assessment_mode"]),
            lifecycle_status=LifecycleStatus(row["lifecycle_status"]),
            storage_scope_reference=StorageScopeReference(row["storage_provider"], row["storage_root_id"]),
            schema_version=row["schema_version"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            last_run_id=row["last_run_id"],
        )

    @staticmethod
    def _state(payload: str) -> CaseState:
        value = json.loads(payload)
        value["created_at"] = datetime.fromisoformat(value["created_at"])
        value["updated_at"] = datetime.fromisoformat(value["updated_at"])
        return CaseState(**value)

    @staticmethod
    def _run(row: sqlite3.Row) -> RunRecord:
        return RunRecord(
            row["run_id"], row["case_id"], row["request_id"], RunStatus(row["status"]),
            row["schema_version"], datetime.fromisoformat(row["created_at"]),
            datetime.fromisoformat(row["updated_at"]),
        )

    def _versioned_run(self, row: sqlite3.Row) -> VersionedRun:
        return VersionedRun(self._run(row), row["tax_year"], row["revision"])

    @staticmethod
    def _versioned_run_result(result: dict, *, idempotent: bool) -> VersionedRun:
        payload = result.get("run")
        if not isinstance(payload, dict):
            raise CasePersistenceError("idempotency run result is malformed")
        try:
            run = RunRecord(
                payload["run_id"], payload["case_id"], payload["request_id"],
                RunStatus(payload["status"]), payload["schema_version"],
                datetime.fromisoformat(payload["created_at"]),
                datetime.fromisoformat(payload["updated_at"]),
            )
            return VersionedRun(run, payload["tax_year"], payload["revision"], idempotent)
        except (KeyError, TypeError, ValueError) as exc:
            raise CasePersistenceError("idempotency run result is malformed") from exc

    @staticmethod
    def _run_payload(run: RunRecord, tax_year: int, revision: int) -> dict:
        return {
            "run_id": run.run_id, "case_id": run.case_id, "tax_year": tax_year,
            "request_id": run.request_id, "status": run.status.value,
            "schema_version": run.schema_version, "revision": revision,
            "created_at": run.created_at.isoformat(), "updated_at": run.updated_at.isoformat(),
        }

    def _authorize(self, owner_id: str, case_id: str, tax_year: int) -> None:
        if not owner_id.strip() or not case_id.strip() or isinstance(tax_year, bool):
            raise ValueError("complete owner/case/year scope is required")
        row = self._db.execute(
            "SELECT 1 FROM case_record c JOIN ui_case_authorization a USING(case_id) "
            "WHERE c.case_id=? AND c.owner_id=? AND c.tax_year=? AND a.owner_id=c.owner_id",
            (case_id, owner_id, tax_year),
        ).fetchone()
        if row is None:
            raise PermissionError("owner/case/year scope is not authorized")

    def _idempotent_result(
        self, request_id: str, operation: str, case_id: str, request: dict,
    ) -> dict | None:
        if not request_id.strip():
            raise ValueError("request_id is required")
        row = self._db.execute("SELECT * FROM mutation_request WHERE request_id=?", (request_id,)).fetchone()
        if row is None:
            return None
        request_json = self._canonical(request)
        request_digest = self._mac({"operation": operation, "case_id": case_id, "request_json": request_json})
        if (row["operation"] != operation or row["case_id"] != case_id
                or row["request_json"] != request_json
                or not hmac.compare_digest(row["request_digest"], request_digest)):
            raise CasePersistenceError("request_id was already used for different content")
        if not hmac.compare_digest(row["result_digest"], self._mac(row["result_json"])):
            raise CasePersistenceError("idempotency result integrity failure")
        return json.loads(row["result_json"])

    def _record_request(
        self, request_id: str, operation: str, case_id: str, request: dict, result: dict,
    ) -> None:
        result_json = self._canonical(result)
        request_json = self._canonical(request)
        self._db.execute(
            "INSERT INTO mutation_request VALUES(?,?,?,?,?,?,?)",
            (request_id, operation, case_id, request_json,
             self._mac({"operation": operation, "case_id": case_id, "request_json": request_json}),
             result_json, self._mac(result_json)),
        )

    @staticmethod
    def _provisioning_payload(
        operation_id: str, request_id: str, owner_id: str, case_id: str, tax_year: int,
        status: str, attempt_count: int, storage_provider: str | None,
        storage_root_id: str | None, failure_code: str | None, revision: int,
        created_at: str, updated_at: str,
    ) -> dict:
        return {
            "operation_id": operation_id, "request_id": request_id, "owner_id": owner_id,
            "case_id": case_id, "tax_year": tax_year, "status": status,
            "attempt_count": attempt_count, "storage_provider": storage_provider,
            "storage_root_id": storage_root_id, "failure_code": failure_code,
            "revision": revision, "created_at": created_at, "updated_at": updated_at,
        }

    @staticmethod
    def _intent(row: sqlite3.Row) -> StorageProvisioningIntent:
        return StorageProvisioningIntent(
            row["operation_id"], row["request_id"], row["owner_id"], row["case_id"],
            row["tax_year"], row["status"], row["attempt_count"], row["storage_provider"],
            row["storage_root_id"], row["failure_code"], row["revision"],
        )

    def _audit(self, action: str, case_id: str, payload_digest: str) -> None:
        previous = self._db.execute(
            "SELECT event_digest FROM case_audit ORDER BY event_id DESC LIMIT 1"
        ).fetchone()
        previous_digest = previous[0] if previous else "0" * 64
        event = {
            "action": action, "case_id": case_id,
            "payload_digest": payload_digest, "previous_digest": previous_digest,
        }
        self._db.execute(
            "INSERT INTO case_audit(action,case_id,payload_digest,previous_digest,event_digest) VALUES(?,?,?,?,?)",
            (*event.values(), self._mac(event)),
        )

    def _verify_all(self) -> None:
        with self._lock:
            counts = {
                table: self._db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                for table in ("case_record", "case_state", "ui_case_authorization")
            }
            if len(set(counts.values())) != 1:
                raise CasePersistenceError("case persistence completeness failure")
            mismatch = self._db.execute("""
                SELECT count(*) FROM case_record c
                LEFT JOIN case_state s ON s.case_id=c.case_id
                LEFT JOIN ui_case_authorization a ON a.case_id=c.case_id
                WHERE s.case_id IS NULL OR a.case_id IS NULL OR a.owner_id<>c.owner_id
            """).fetchone()[0]
            if mismatch:
                raise CasePersistenceError("case persistence scope failure")
            case_ids = {
                row[0] for row in self._db.execute("SELECT case_id FROM case_record")
            }
            registered_ids = [
                row[0] for row in self._db.execute(
                    "SELECT case_id FROM case_audit WHERE action='CASE_REGISTERED'"
                )
            ]
            if len(registered_ids) != len(set(registered_ids)) or set(registered_ids) != case_ids:
                raise CasePersistenceError("case audit completeness failure")
            previous = "0" * 64
            for row in self._db.execute("SELECT * FROM case_audit ORDER BY event_id"):
                event = {key: row[key] for key in ("action", "case_id", "payload_digest", "previous_digest")}
                if row["previous_digest"] != previous or not hmac.compare_digest(row["event_digest"], self._mac(event)):
                    raise CasePersistenceError("case audit integrity failure")
                previous = row["event_digest"]
            for row in self._db.execute("SELECT * FROM case_record"):
                record = self._record(row)
                if not hmac.compare_digest(row["digest"], self._mac(self._case_payload(record))):
                    raise CasePersistenceError("case record integrity failure")
            for row in self._db.execute("SELECT * FROM case_state"):
                state = self._state(row["payload"])
                if state.case_id != row["case_id"]:
                    raise CasePersistenceError("case state scope failure")
                if not hmac.compare_digest(row["digest"], self._mac(row["payload"])):
                    raise CasePersistenceError("case state integrity failure")
            for row in self._db.execute("SELECT * FROM ui_case_authorization"):
                authorization = {key: row[key] for key in ("owner_id", "case_id", "granted_at")}
                if not hmac.compare_digest(row["digest"], self._mac(authorization)):
                    raise CasePersistenceError("case authorization integrity failure")

            version = self._db.execute("PRAGMA user_version").fetchone()[0]
            if version >= 2:
                for row in self._db.execute("SELECT r.*,c.owner_id,c.tax_year AS case_tax_year FROM durable_run r JOIN case_record c USING(case_id)"):
                    run = self._run(row)
                    if row["tax_year"] != row["case_tax_year"]:
                        raise CasePersistenceError("run case/year scope failure")
                    if not hmac.compare_digest(row["digest"], self._mac(self._run_payload(run, row["tax_year"], row["revision"]))):
                        raise CasePersistenceError("run integrity failure")
                for row in self._db.execute("SELECT * FROM mutation_request"):
                    expected_request = self._mac({
                        "operation": row["operation"], "case_id": row["case_id"],
                        "request_json": row["request_json"],
                    })
                    if (not hmac.compare_digest(row["request_digest"], expected_request)
                            or not hmac.compare_digest(row["result_digest"], self._mac(row["result_json"]))):
                        raise CasePersistenceError("idempotency result integrity failure")
                    if self._db.execute("SELECT 1 FROM case_record WHERE case_id=?", (row["case_id"],)).fetchone() is None:
                        raise CasePersistenceError("idempotency case scope failure")
                for row in self._db.execute("SELECT s.payload FROM case_state s"):
                    state = self._state(row["payload"])
                    if state.last_run_id is not None:
                        run = self._db.execute("SELECT case_id FROM durable_run WHERE run_id=?", (state.last_run_id,)).fetchone()
                        # Creation workflow run identities predate durable execution runs.
                        if run is not None and run["case_id"] != state.case_id:
                            raise CasePersistenceError("case state run scope failure")
            if version >= 3:
                allowed_statuses = {
                    "INTENT", "IN_PROGRESS", "COMPLETE", "RETRYABLE_FAILURE",
                    "RECONCILIATION_REQUIRED",
                }
                for row in self._db.execute("SELECT * FROM storage_provisioning"):
                    payload = self._provisioning_payload(*(
                        row[key] for key in (
                            "operation_id", "request_id", "owner_id", "case_id", "tax_year",
                            "status", "attempt_count", "storage_provider", "storage_root_id",
                            "failure_code", "revision", "created_at", "updated_at",
                        )
                    ))
                    if row["status"] not in allowed_statuses or not hmac.compare_digest(row["digest"], self._mac(payload)):
                        raise CasePersistenceError("storage provisioning integrity failure")
                    case = self._db.execute("SELECT owner_id,tax_year,storage_provider,storage_root_id FROM case_record WHERE case_id=?", (row["case_id"],)).fetchone()
                    if case is not None and (
                        row["status"] != "COMPLETE" or case["owner_id"] != row["owner_id"]
                        or case["tax_year"] != row["tax_year"]
                        or case["storage_provider"] != row["storage_provider"]
                        or case["storage_root_id"] != row["storage_root_id"]
                    ):
                        raise CasePersistenceError("storage provisioning case association failure")

    def _anchor_payload(self, *, schema_version: int | None = None) -> dict:
        event = self._db.execute(
            "SELECT event_id,event_digest FROM case_audit ORDER BY event_id DESC LIMIT 1"
        ).fetchone()
        effective_version = schema_version or SCHEMA_VERSION
        payload = {
            "schema_version": effective_version,
            "event_count": self._db.execute("SELECT count(*) FROM case_audit").fetchone()[0],
            "head_event_id": event["event_id"] if event else 0,
            "head_digest": event["event_digest"] if event else "0" * 64,
            "case_count": self._db.execute("SELECT count(*) FROM case_record").fetchone()[0],
            "key_verifier": self._mac("ai-tax-agent.case-persistence/key-verifier/1"),
        }
        if effective_version >= 3:
            payload["provisioning_count"] = self._db.execute(
                "SELECT count(*) FROM storage_provisioning"
            ).fetchone()[0]
        return payload

    def _write_anchor(self, *, schema_version: int | None = None) -> None:
        import os
        payload = self._anchor_payload(schema_version=schema_version)
        document = payload | {"anchor_mac": self._mac(payload)}
        temporary = self._anchor_path.with_suffix(self._anchor_path.suffix + ".writing")
        with temporary.open("x", encoding="utf-8") as stream:
            stream.write(self._canonical(document))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, self._anchor_path)

    def _verify_anchor(self, *, schema_version: int | None = None) -> None:
        try:
            document = json.loads(self._anchor_path.read_text(encoding="utf-8"))
            required = {
                "schema_version", "event_count", "head_event_id", "head_digest",
                "case_count", "key_verifier", "anchor_mac",
            }
            if (schema_version or SCHEMA_VERSION) >= 3:
                required.add("provisioning_count")
            if not isinstance(document, dict) or set(document) != required:
                raise ValueError
            payload = {key: document[key] for key in document if key != "anchor_mac"}
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            raise CasePersistenceError("case audit anchor unavailable or malformed") from exc
        if (
            not hmac.compare_digest(str(document["anchor_mac"]), self._mac(payload))
            or not hmac.compare_digest(
                str(document["key_verifier"]),
                self._mac("ai-tax-agent.case-persistence/key-verifier/1"),
            )
            or payload != self._anchor_payload(schema_version=schema_version)
        ):
            raise CasePersistenceError("case audit anchor integrity failure")
