"""OI-0002 SQLite persistence adapter for existing identity and case-party authorities.

Private local database only. Does not create a competing case registry or authorize
real CASE-001 identity registration.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import hashlib
import json
import sqlite3
from pathlib import Path

from agent_lab.case_registry import CaseRegistry, OwnerType
from agent_lab.person_entity_registry import (
    EntityRecord, PersonEntityRegistry, PersonRecord, RecordType, RegistryStatus,
)

SCHEMA_VERSION = 1
PARTY_ROLES = frozenset({
    "PRIMARY_TAXPAYER", "SPOUSE_OR_PARTNER", "CHILD",
    "OTHER_DEPENDENT_OR_RELEVANT_PERSON", "DOCUMENT_ISSUER",
    "EMPLOYER", "INSURER", "DONATION_RECIPIENT",
    "SERVICE_PROVIDER", "TAX_AUTHORITY_CONTACT",
})


def _canonical(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: dict) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class CasePartyRole:
    binding_id: str
    case_id: str
    subject_type: str
    subject_id: str
    role: str
    valid_from: date
    valid_to_exclusive: date | None
    evidence_ref: str
    authorization_ref: str


class IdentityPersistence:
    """Transactional protected SQLite adapter; caller supplies existing registries."""

    def __init__(self, path: str | Path, *, cases: CaseRegistry, authorize=None) -> None:
        self._cases = cases
        self._authorize = authorize
        self._db = sqlite3.connect(str(path))
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.execute("PRAGMA busy_timeout=5000")
        existing_version = self._db.execute('PRAGMA user_version').fetchone()[0]
        if existing_version == 0:
            existing_tables = self._db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            if existing_tables:
                self._db.close()
                raise ValueError('unversioned existing database requires reviewed migration')
        if existing_version not in (0, SCHEMA_VERSION):
            self._db.close()
            raise ValueError('unsupported database schema version')
        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS identity_record (
                identity_id TEXT PRIMARY KEY,
                record_type TEXT NOT NULL CHECK(record_type IN ('PERSON','ENTITY')),
                payload TEXT NOT NULL,
                digest TEXT NOT NULL,
                schema_version INTEGER NOT NULL CHECK(schema_version = 1)
            );
            CREATE TABLE IF NOT EXISTS case_party_role (
                binding_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                subject_type TEXT NOT NULL CHECK(subject_type IN ('PERSON','ENTITY')),
                subject_id TEXT NOT NULL REFERENCES identity_record(identity_id),
                role TEXT NOT NULL,
                valid_from TEXT NOT NULL,
                valid_to_exclusive TEXT,
                evidence_ref TEXT NOT NULL,
                authorization_ref TEXT NOT NULL,
                digest TEXT NOT NULL,
                schema_version INTEGER NOT NULL CHECK(schema_version = 1)
            );
            CREATE INDEX IF NOT EXISTS idx_case_party_scope
                ON case_party_role(case_id, subject_id, role);
            CREATE TABLE IF NOT EXISTS identity_audit (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                case_id TEXT,
                subject_id TEXT NOT NULL,
                payload_digest TEXT NOT NULL,
                recorded_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS subject_fact_binding (
                request_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                tax_year INTEGER NOT NULL,
                subject_id TEXT NOT NULL REFERENCES identity_record(identity_id),
                artifact_ref TEXT NOT NULL,
                authorization_ref TEXT NOT NULL,
                digest TEXT NOT NULL
            );
        """)
        self._db.execute('PRAGMA user_version=1')

    def _audit(self, action: str, case_id: str | None, subject_id: str, digest: str) -> None:
        from datetime import timezone
        self._db.execute(
            'INSERT INTO identity_audit(action,case_id,subject_id,payload_digest,recorded_at) VALUES (?,?,?,?,?)',
            (action, case_id, subject_id, digest, datetime.now(timezone.utc).isoformat()),
        )

    def _integrity_failure(self, case_id: str | None, subject_id: str, reason: str) -> None:
        with self._db:
            self._audit('INTEGRITY_FAILURE', case_id, subject_id, _digest({'reason': reason}))
        raise ValueError(reason)

    def _security_failure(self, action: str, case_id: str, reason: str) -> None:
        with self._db:
            self._audit('SECURITY_' + action, case_id, 'REDACTED', _digest({'reason': reason}))
        raise PermissionError(reason)

    def _check_access(self, action: str, case_id: str, authorization_ref: str) -> None:
        case = self._cases.get(case_id)
        if case is None or not authorization_ref or self._authorize is None:
            self._security_failure('DENIED', case_id, 'case authorization unavailable')
        try:
            allowed = self._authorize(action, case_id, case.storage_scope_reference.root_id, authorization_ref) is True
        except Exception:
            allowed = False
        if not allowed:
            self._security_failure('DENIED', case_id, 'case authorization denied')

    def close(self) -> None:
        self._db.close()

    def save_identity(self, record: PersonRecord | EntityRecord) -> None:
        identity_id = record.person_id if isinstance(record, PersonRecord) else record.entity_id
        payload = {
            "identity_id": identity_id, "record_type": record.record_type.value,
            "status": record.status.value, "name": record.preferred_display_name,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
            "lookup_attributes": list(map(list, record.lookup_attributes)),
            "record_schema_version": record.schema_version,
        }
        encoded = _canonical(payload)
        with self._db:
            old = self._db.execute(
                "SELECT payload FROM identity_record WHERE identity_id=?", (identity_id,)
            ).fetchone()
            if old is not None:
                if old["payload"] == encoded:
                    return
                raise ValueError("identity already exists with different content")
            self._db.execute(
                "INSERT INTO identity_record VALUES (?,?,?,?,?)",
                (identity_id, record.record_type.value, encoded, _digest(payload), SCHEMA_VERSION),
            )
            self._audit('IDENTITY_REGISTER', None, identity_id, _digest(payload))

    def load_identity(self, identity_id: str) -> PersonRecord | EntityRecord | None:
        row = self._db.execute(
            "SELECT * FROM identity_record WHERE identity_id=?", (identity_id,)
        ).fetchone()
        if row is None:
            return None
        if row["schema_version"] != SCHEMA_VERSION:
            self._integrity_failure(None, identity_id, 'unsupported identity schema')
        payload = json.loads(row["payload"])
        if _digest(payload) != row["digest"] or payload["identity_id"] != identity_id or payload["record_type"] != row["record_type"]:
            self._integrity_failure(None, identity_id, 'identity integrity failure')
        record_class = PersonRecord if row["record_type"] == RecordType.PERSON.value else EntityRecord
        return record_class(
            **{("person_id" if record_class is PersonRecord else "entity_id"): identity_id},
            status=RegistryStatus(payload["status"]),
            preferred_display_name=payload["name"],
            created_at=datetime.fromisoformat(payload["created_at"]),
            updated_at=datetime.fromisoformat(payload["updated_at"]),
            schema_version=payload["record_schema_version"],
            lookup_attributes=tuple(tuple(item) for item in payload["lookup_attributes"]),
        )

    def restore_identity(self, identity_id: str, registry: PersonEntityRegistry) -> None:
        record = self.load_identity(identity_id)
        if record is None:
            raise KeyError("unknown identity")
        if isinstance(record, PersonRecord):
            registry.register_person(record)
        else:
            registry.register_entity(record)

    def bind_party(self, binding: CasePartyRole) -> None:
        self._check_access('bind_party', binding.case_id, binding.authorization_ref)
        case = self._cases.get(binding.case_id)
        if case is None:
            raise KeyError("unknown case")
        if binding.subject_type not in ('PERSON', 'ENTITY'):
            raise ValueError('unsupported subject type')
        if binding.role not in PARTY_ROLES:
            raise ValueError("unsupported party role")
        if not binding.binding_id or not binding.evidence_ref or not binding.authorization_ref:
            raise ValueError("binding id, evidence and authorization are required")
        if binding.valid_to_exclusive is not None and binding.valid_from >= binding.valid_to_exclusive:
            raise ValueError("invalid effective interval")
        subject = self.load_identity(binding.subject_id)
        if subject is None or subject.record_type.value != binding.subject_type:
            raise ValueError("unknown or mismatched subject")
        if subject.status is not RegistryStatus.ACTIVE:
            raise PermissionError("inactive or unresolved subject")
        if binding.role == "PRIMARY_TAXPAYER" and (
            case.owner_id != binding.subject_id or case.owner_type.value != binding.subject_type
        ):
            raise PermissionError("primary taxpayer must be exact registered case owner")
        payload = {
            "binding_id": binding.binding_id, "case_id": binding.case_id,
            "subject_type": binding.subject_type, "subject_id": binding.subject_id,
            "role": binding.role, "valid_from": binding.valid_from.isoformat(),
            "valid_to_exclusive": binding.valid_to_exclusive.isoformat() if binding.valid_to_exclusive else None,
            "evidence_ref": binding.evidence_ref, "authorization_ref": binding.authorization_ref,
        }
        with self._db:
            old = self._db.execute("SELECT * FROM case_party_role WHERE binding_id=?", (binding.binding_id,)).fetchone()
            if old:
                if old["digest"] == _digest(payload) and old["schema_version"] == SCHEMA_VERSION:
                    return
                raise ValueError("binding id reused with different payload")
            for other in self._db.execute(
                "SELECT * FROM case_party_role WHERE case_id=? AND subject_id=? AND role=?",
                (binding.case_id, binding.subject_id, binding.role),
            ):
                if (binding.valid_to_exclusive is None or date.fromisoformat(other["valid_from"]) < binding.valid_to_exclusive) and (
                    other["valid_to_exclusive"] is None or binding.valid_from < date.fromisoformat(other["valid_to_exclusive"])
                ):
                    raise ValueError("overlapping role binding")
            self._db.execute(
                "INSERT INTO case_party_role VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (binding.binding_id, binding.case_id, binding.subject_type, binding.subject_id,
                 binding.role, payload["valid_from"], payload["valid_to_exclusive"],
                 binding.evidence_ref, binding.authorization_ref, _digest(payload), SCHEMA_VERSION),
            )
            self._audit('CASE_PARTY_BIND', binding.case_id, binding.subject_id, _digest(payload))

    def list_parties(self, case_id: str, *, on_date: date, authorization_ref: str) -> tuple[CasePartyRole, ...]:
        self._check_access('read_party', case_id, authorization_ref)
        if self._cases.get(case_id) is None:
            raise KeyError("unknown case")
        result = []
        for row in self._db.execute(
            "SELECT * FROM case_party_role WHERE case_id=? ORDER BY binding_id", (case_id,)
        ):
            payload = {key: row[key] for key in (
                "binding_id", "case_id", "subject_type", "subject_id", "role",
                "valid_from", "valid_to_exclusive", "evidence_ref", "authorization_ref"
            )}
            if row["schema_version"] != SCHEMA_VERSION or _digest(payload) != row["digest"]:
                self._integrity_failure(case_id, row['subject_id'], 'party binding integrity failure')
            if self.load_identity(row["subject_id"]) is None:
                self._integrity_failure(case_id, row['subject_id'], 'missing subject identity')
            start = date.fromisoformat(row["valid_from"])
            end = date.fromisoformat(row["valid_to_exclusive"]) if row["valid_to_exclusive"] else None
            if start <= on_date and (end is None or on_date < end):
                result.append(CasePartyRole(
                    row["binding_id"], case_id, row["subject_type"], row["subject_id"],
                    row["role"], start, end, row["evidence_ref"], row["authorization_ref"]
                ))
        return tuple(result)


    def read_case_identity(self, *, case_id: str, subject_id: str,
                           on_date: date, authorization_ref: str) -> PersonRecord | EntityRecord:
        parties = self.list_parties(case_id, on_date=on_date, authorization_ref=authorization_ref)
        if not any(p.subject_id == subject_id for p in parties):
            self._security_failure('DENIED', case_id, 'subject not associated with case')
        record = self.load_identity(subject_id)
        if record is None:
            self._integrity_failure(case_id, subject_id, 'missing case subject')
        return record

    def bind_fact_reference(self, *, request_id: str, case_id: str, tax_year: int,
                            subject_id: str, fact, authorization_ref: str) -> str:
        """Persist a subject-scoped reference to an unchanged immutable v1 fact."""
        from agent_lab.human_declared_fact import HumanDeclaredFact
        if not isinstance(fact, HumanDeclaredFact):
            raise TypeError("HumanDeclaredFact required")
        fact.assert_consumable(case_id=case_id, tax_year=tax_year)
        case = self._cases.get(case_id)
        if case is None or case.tax_period.year != tax_year:
            raise PermissionError("case/year mismatch")
        self._check_access('bind_fact', case_id, authorization_ref)
        if not request_id or not authorization_ref or authorization_ref != fact.authorization_reference:
            raise PermissionError("matching authorization required")
        if not any(p.subject_id == subject_id for p in self.list_parties(case_id, on_date=date(tax_year, 7, 1), authorization_ref=authorization_ref)):
            raise PermissionError("subject not associated with case at reference date")
        ref = fact.artifact_identity.reference
        payload = dict(request_id=request_id, case_id=case_id, tax_year=tax_year,
                       subject_id=subject_id, artifact_ref=ref, authorization_ref=authorization_ref)
        with self._db:
            old = self._db.execute("SELECT * FROM subject_fact_binding WHERE request_id=?", (request_id,)).fetchone()
            if old:
                if old["digest"] != _digest(payload):
                    raise ValueError("request ID conflict")
                return ref
            self._db.execute("INSERT INTO subject_fact_binding VALUES (?,?,?,?,?,?,?)",
                             (request_id, case_id, tax_year, subject_id, ref, authorization_ref, _digest(payload)))
            self._audit('SUBJECT_FACT_BIND', case_id, subject_id, _digest(payload))
        return ref

    def read_fact_references(self, *, case_id: str, tax_year: int,
                             subject_id: str, authorization_ref: str) -> tuple[str, ...]:
        case = self._cases.get(case_id)
        if case is None or case.tax_period.year != tax_year or not authorization_ref:
            raise PermissionError("invalid scope")
        if not any(p.subject_id == subject_id for p in self.list_parties(case_id, on_date=date(tax_year, 7, 1), authorization_ref=authorization_ref)):
            raise PermissionError("subject not associated with case")
        refs = []
        for row in self._db.execute(
            "SELECT * FROM subject_fact_binding WHERE case_id=? AND tax_year=? AND subject_id=?",
            (case_id, tax_year, subject_id),
        ):
            payload = dict(request_id=row["request_id"], case_id=row["case_id"],
                           tax_year=row["tax_year"], subject_id=row["subject_id"],
                           artifact_ref=row["artifact_ref"], authorization_ref=row["authorization_ref"])
            if row["digest"] != _digest(payload):
                self._integrity_failure(case_id, subject_id, 'fact reference integrity failure')
            if row["authorization_ref"] != authorization_ref:
                raise PermissionError("authorization mismatch")
            refs.append(row["artifact_ref"])
        return tuple(sorted(refs))
