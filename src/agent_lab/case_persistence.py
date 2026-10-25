"""Canonical SQLite persistence for case metadata, state and UI scope.

Document bytes and identity/fact payloads deliberately do not belong here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
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
from agent_lab.case_state import CaseState


SCHEMA_VERSION = 1


class CasePersistenceError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class DurableCaseRuntime:
    registry: CaseRegistry
    states: tuple[CaseState, ...]
    allowed_case_ids: frozenset[str]

    def state(self, case_id: str) -> CaseState:
        if case_id not in self.allowed_case_ids:
            raise PermissionError("case is outside the authorized runtime scope")
        for state in self.states:
            if state.case_id == case_id:
                return state
        raise CasePersistenceError("authorized case state is unavailable")


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
        self._key = integrity_key
        self._lock = RLock()
        self._db = sqlite3.connect(self.path, check_same_thread=False)
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
                self._db.close()
                raise CasePersistenceError("unversioned database is not accepted")
            self._create_schema()
        elif version != SCHEMA_VERSION:
            self._db.close()
            raise CasePersistenceError("unsupported case persistence schema")
        self._verify_all()

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
                    payload TEXT NOT NULL, digest TEXT NOT NULL);
                CREATE TABLE ui_case_authorization(
                    owner_id TEXT NOT NULL, case_id TEXT NOT NULL REFERENCES case_record(case_id),
                    granted_at TEXT NOT NULL, digest TEXT NOT NULL,
                    PRIMARY KEY(owner_id,case_id));
                CREATE TABLE case_audit(
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL,
                    case_id TEXT NOT NULL, payload_digest TEXT NOT NULL,
                    previous_digest TEXT NOT NULL, event_digest TEXT NOT NULL);
                PRAGMA user_version=1;
            """)

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
                    "INSERT INTO case_state VALUES(?,?,?)",
                    (record.case_id, state_json, self._mac(state_json)),
                )
                self._db.execute(
                    "INSERT INTO ui_case_authorization VALUES(?,?,?,?)",
                    (*authorization.values(), self._mac(authorization)),
                )
                self._audit("CASE_REGISTERED", record.case_id, self._mac(case_payload))
                self._db.commit()
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
            return DurableCaseRuntime(registry, tuple(states), allowed_case_ids)

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
