"""Kernel-authorized, tamper-evident identity and case-party persistence."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import sqlite3
from typing import Callable

from agent_lab.case_registry import CaseRegistry
from agent_lab.human_declared_fact import (
    FactConfirmationState, FactProvenanceKind, FactValidationStatus,
    HumanDeclaredFact, HumanFactValidationResult,
)
from agent_lab.person_entity_registry import (
    EntityRecord, PersonEntityRegistry, PersonRecord, RecordType, RegistryStatus,
)

SCHEMA_VERSION = 2
SHA_REFERENCE = re.compile(r"^sha256:[0-9a-f]{64}$")
PARTY_ROLES = frozenset({
    "PRIMARY_TAXPAYER", "SPOUSE_OR_PARTNER", "CHILD",
    "OTHER_DEPENDENT_OR_RELEVANT_PERSON", "DOCUMENT_ISSUER", "EMPLOYER",
    "INSURER", "DONATION_RECIPIENT", "SERVICE_PROVIDER", "TAX_AUTHORITY_CONTACT",
})
EXCLUSIVE_ROLES = frozenset({"PRIMARY_TAXPAYER", "SPOUSE_OR_PARTNER"})


def _canonical(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _legacy_digest(value: dict) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


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


@dataclass(frozen=True, slots=True)
class SubjectFactEnvelope:
    request_id: str
    case_id: str
    tax_year: int
    subject_type: str
    subject_id: str
    semantic_key: str
    fact_artifact_ref: str
    declaration_artifact_ref: str
    confirmation_ref: str
    authorization_ref: str
    valid_from: date
    valid_to_exclusive: date
    audit_lineage: tuple[str, ...]
    revision: int = 1


class IdentityPersistence:
    """One protected SQLite authority composed with the existing Case Registry."""

    def __init__(
        self, path: str | Path, *, cases: CaseRegistry,
        authorize: Callable[[str, str, str, str], bool] | None = None,
        evidence_resolver: Callable[[str, str, str, int, str, date, date], None],
        integrity_key: bytes,
        fault_injector: Callable[[str], None] | None = None,
    ) -> None:
        if not isinstance(integrity_key, bytes) or len(integrity_key) < 32:
            raise ValueError("a protected integrity key of at least 32 bytes is required")
        self._path = Path(path).resolve()
        lowered = self._path.as_posix().casefold()
        if any(marker in lowered for marker in ("/onedrive/", "/google drive/", "/dropbox/")):
            raise ValueError("live SQLite database cannot be placed in a synced folder")
        self._anchor_path = self._path.with_suffix(self._path.suffix + ".audit-anchor")
        self._cases = cases
        self._authorize = authorize
        if evidence_resolver is None:
            raise ValueError("a protected evidence resolver is required")
        self._resolve_evidence = evidence_resolver
        self._key = integrity_key
        self._fault = fault_injector
        self._db = sqlite3.connect(str(self._path))
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
                raise ValueError("unversioned existing database requires reviewed migration")
            self._create_schema()
        elif version == 1:
            self._migrate_v1()
        elif version != SCHEMA_VERSION:
            self._db.close()
            raise ValueError("unsupported database schema version")
        self._verify_audit_continuity(create_empty=True)
        self._verify_data_integrity()

    def _mac(self, value: dict | str) -> str:
        raw = value if isinstance(value, str) else _canonical(value)
        return hmac.new(self._key, raw.encode(), hashlib.sha256).hexdigest()

    def _create_schema(self) -> None:
        with self._db:
            self._db.executescript("""
                CREATE TABLE identity_record(
                    identity_id TEXT PRIMARY KEY, record_type TEXT NOT NULL CHECK(record_type IN ('PERSON','ENTITY')),
                    payload TEXT NOT NULL, digest TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>=1),
                    schema_version INTEGER NOT NULL CHECK(schema_version=2));
                CREATE TABLE identity_history(
                    identity_id TEXT NOT NULL, revision INTEGER NOT NULL, payload TEXT NOT NULL,
                    digest TEXT NOT NULL, PRIMARY KEY(identity_id,revision));
                CREATE TABLE case_party_role(
                    binding_id TEXT PRIMARY KEY, case_id TEXT NOT NULL,
                    subject_type TEXT NOT NULL CHECK(subject_type IN ('PERSON','ENTITY')),
                    subject_id TEXT NOT NULL REFERENCES identity_record(identity_id), role TEXT NOT NULL,
                    valid_from TEXT NOT NULL, valid_to_exclusive TEXT, evidence_ref TEXT NOT NULL,
                    authorization_ref TEXT NOT NULL, digest TEXT NOT NULL,
                    revision INTEGER NOT NULL CHECK(revision>=1), schema_version INTEGER NOT NULL CHECK(schema_version=2));
                CREATE INDEX idx_case_party_scope ON case_party_role(case_id,role,valid_from,valid_to_exclusive);
                CREATE TABLE subject_fact_binding(
                    request_id TEXT PRIMARY KEY, case_id TEXT NOT NULL, tax_year INTEGER NOT NULL,
                    subject_type TEXT NOT NULL CHECK(subject_type IN ('PERSON','ENTITY')),
                    subject_id TEXT NOT NULL REFERENCES identity_record(identity_id), semantic_key TEXT NOT NULL,
                    fact_payload TEXT NOT NULL, fact_artifact_ref TEXT NOT NULL,
                    declaration_artifact_ref TEXT NOT NULL, confirmation_ref TEXT NOT NULL,
                    authorization_ref TEXT NOT NULL, valid_from TEXT NOT NULL, valid_to_exclusive TEXT NOT NULL,
                    audit_lineage TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>=1),
                    digest TEXT NOT NULL, schema_version INTEGER NOT NULL CHECK(schema_version=2));
                CREATE INDEX idx_subject_fact_scope ON subject_fact_binding(case_id,tax_year,subject_id);
                CREATE TABLE identity_audit(
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT, event_payload TEXT NOT NULL,
                    previous_mac TEXT NOT NULL, event_mac TEXT NOT NULL, recorded_at TEXT NOT NULL);
                PRAGMA user_version=2;
            """)

    def _migrate_v1(self) -> None:
        fact_count = self._db.execute("SELECT count(*) FROM subject_fact_binding").fetchone()[0]
        if fact_count:
            self._db.close()
            raise ValueError("v1 fact bindings require reviewed lineage migration")
        identities = list(self._db.execute("SELECT * FROM identity_record"))
        roles = list(self._db.execute("SELECT * FROM case_party_role"))
        audits = list(self._db.execute("SELECT * FROM identity_audit ORDER BY event_id"))
        for row in identities:
            payload = json.loads(row["payload"])
            if _legacy_digest(payload) != row["digest"]:
                self._db.close(); raise ValueError("v1 identity integrity failure")
        for row in roles:
            payload = {key: row[key] for key in (
                "binding_id", "case_id", "subject_type", "subject_id", "role", "valid_from",
                "valid_to_exclusive", "evidence_ref", "authorization_ref")}
            if _legacy_digest(payload) != row["digest"]:
                self._db.close(); raise ValueError("v1 role integrity failure")
        with self._db:
            self._db.executescript("DROP TABLE subject_fact_binding; DROP TABLE identity_audit; DROP TABLE case_party_role; DROP TABLE identity_record;")
        self._create_schema()
        with self._db:
            for row in identities:
                payload = json.loads(row["payload"]); digest = self._mac(payload)
                self._db.execute("INSERT INTO identity_record VALUES(?,?,?,?,?,2)", (row["identity_id"],row["record_type"],row["payload"],digest,1))
                self._db.execute("INSERT INTO identity_history VALUES(?,?,?,?)", (row["identity_id"],1,row["payload"],digest))
            for row in roles:
                payload = {key: row[key] for key in ("binding_id","case_id","subject_type","subject_id","role","valid_from","valid_to_exclusive","evidence_ref","authorization_ref")}
                self._db.execute("INSERT INTO case_party_role VALUES(?,?,?,?,?,?,?,?,?,?,?,2)", (*payload.values(),self._mac(payload),1))
            for row in audits:
                self._append_audit("LEGACY_V1_EVENT", row["case_id"], row["subject_id"], {"action":row["action"],"legacy_digest":row["payload_digest"]})
        self._sync_anchor()

    def _anchor_payload(self, count: int, head: str) -> dict:
        return {"schema_version":1,"event_count":count,"head_mac":head}

    def _write_anchor(self, count: int, head: str) -> None:
        payload = self._anchor_payload(count, head)
        document = {**payload, "anchor_mac": self._mac(payload)}
        temp = self._anchor_path.with_suffix(self._anchor_path.suffix + ".tmp")
        temp.write_text(_canonical(document), encoding="utf-8")
        os.replace(temp, self._anchor_path)

    def _audit_head(self) -> tuple[int, str]:
        rows = self._db.execute("SELECT * FROM identity_audit ORDER BY event_id").fetchall()
        previous = "0" * 64
        expected_id = 1
        for row in rows:
            if row["event_id"] != expected_id or row["previous_mac"] != previous:
                raise ValueError("audit continuity failure")
            content = {"event_id":row["event_id"],"event_payload":row["event_payload"],"previous_mac":previous,"recorded_at":row["recorded_at"]}
            if not hmac.compare_digest(self._mac(content), row["event_mac"]):
                raise ValueError("audit integrity failure")
            previous = row["event_mac"]; expected_id += 1
        return len(rows), previous

    def _verify_audit_continuity(self, *, create_empty: bool = False) -> None:
        count, head = self._audit_head()
        if not self._anchor_path.exists():
            if create_empty and count == 0:
                self._write_anchor(0, head); return
            raise ValueError("audit anchor missing")
        document = json.loads(self._anchor_path.read_text(encoding="utf-8"))
        payload = {key:document[key] for key in ("schema_version","event_count","head_mac")}
        if not hmac.compare_digest(self._mac(payload), document.get("anchor_mac", "")):
            raise ValueError("audit anchor integrity failure")
        if payload != self._anchor_payload(count, head):
            raise ValueError("audit anchor continuity failure")

    def _sync_anchor(self) -> None:
        count, head = self._audit_head()
        self._write_anchor(count, head)

    def _verify_data_integrity(self) -> None:
        for row in self._db.execute("SELECT * FROM identity_record"):
            payload = json.loads(row["payload"])
            if row["schema_version"] != 2 or payload.get("identity_id") != row["identity_id"] or not hmac.compare_digest(self._mac(payload), row["digest"]):
                raise ValueError("identity integrity failure")
        for row in self._db.execute("SELECT * FROM identity_history"):
            payload=json.loads(row["payload"])
            if payload.get("identity_id") != row["identity_id"] or not hmac.compare_digest(self._mac(payload),row["digest"]):
                raise ValueError("identity history integrity failure")
        for row in self._db.execute("SELECT * FROM case_party_role"):
            payload = {key:row[key] for key in ("binding_id","case_id","subject_type","subject_id","role","valid_from","valid_to_exclusive","evidence_ref","authorization_ref")}
            if row["schema_version"] != 2 or not hmac.compare_digest(self._mac(payload), row["digest"]):
                raise ValueError("party binding integrity failure")
        for row in self._db.execute("SELECT * FROM subject_fact_binding"):
            fact_payload=json.loads(row["fact_payload"]); lineage=tuple(json.loads(row["audit_lineage"])["items"])
            env=SubjectFactEnvelope(row["request_id"],row["case_id"],row["tax_year"],row["subject_type"],row["subject_id"],row["semantic_key"],row["fact_artifact_ref"],row["declaration_artifact_ref"],row["confirmation_ref"],row["authorization_ref"],date.fromisoformat(row["valid_from"]),date.fromisoformat(row["valid_to_exclusive"]),lineage,row["revision"])
            payload={**asdict(env),"valid_from":env.valid_from.isoformat(),"valid_to_exclusive":env.valid_to_exclusive.isoformat(),"audit_lineage":list(lineage),"fact_payload":fact_payload}
            if row["schema_version"] != 2 or not hmac.compare_digest(self._mac(payload), row["digest"]):
                raise ValueError("fact lineage integrity failure")

    def _append_audit(self, action: str, case_id: str | None, subject_id: str, details: dict) -> None:
        last = self._db.execute("SELECT event_id,event_mac FROM identity_audit ORDER BY event_id DESC LIMIT 1").fetchone()
        event_id = 1 if last is None else last["event_id"] + 1
        previous = "0" * 64 if last is None else last["event_mac"]
        recorded = datetime.now(timezone.utc).isoformat()
        payload = _canonical({"action":action,"case_id":case_id,"subject_id":subject_id,"details_digest":self._mac(details)})
        content = {"event_id":event_id,"event_payload":payload,"previous_mac":previous,"recorded_at":recorded}
        self._db.execute("INSERT INTO identity_audit VALUES(?,?,?,?,?)", (event_id,payload,previous,self._mac(content),recorded))

    def _commit(self, stage: str, operation: Callable[[], None]) -> None:
        self._verify_audit_continuity()
        with self._db:
            operation()
            if self._fault:
                self._fault(stage + ":BEFORE_COMMIT")
        if self._fault:
            self._fault(stage + ":AFTER_COMMIT")
        self._sync_anchor()

    def _failure(self, action: str, case_id: str | None, reason: str, *, permission: bool) -> None:
        def op(): self._append_audit(action, case_id, "REDACTED", {"reason":reason})
        self._commit(action, op)
        raise (PermissionError if permission else ValueError)(reason)

    def _check_access(self, action: str, case_id: str, authorization_ref: str) -> None:
        case = self._cases.get(case_id)
        if case is None or not authorization_ref or self._authorize is None:
            self._failure("SECURITY_DENIED", case_id, "case authorization unavailable", permission=True)
        try:
            allowed = self._authorize(action, case_id, case.storage_scope_reference.root_id, authorization_ref) is True
        except Exception:
            allowed = False
        if not allowed:
            self._failure("SECURITY_DENIED", case_id, "case authorization denied", permission=True)

    @staticmethod
    def _identity_payload(record: PersonRecord | EntityRecord) -> dict:
        identity_id = record.person_id if isinstance(record, PersonRecord) else record.entity_id
        return {"identity_id":identity_id,"record_type":record.record_type.value,"status":record.status.value,
                "name":record.preferred_display_name,"created_at":record.created_at.isoformat(),
                "updated_at":record.updated_at.isoformat(),"lookup_attributes":list(map(list,record.lookup_attributes)),
                "record_schema_version":record.schema_version}

    def _load_identity(self, identity_id: str, *, require_active: bool = False):
        row = self._db.execute("SELECT * FROM identity_record WHERE identity_id=?", (identity_id,)).fetchone()
        if row is None: return None
        payload = json.loads(row["payload"])
        if row["schema_version"] != SCHEMA_VERSION or not hmac.compare_digest(self._mac(payload), row["digest"]):
            self._failure("INTEGRITY_FAILURE", None, "identity integrity failure", permission=False)
        cls = PersonRecord if row["record_type"] == RecordType.PERSON.value else EntityRecord
        record = cls(**{("person_id" if cls is PersonRecord else "entity_id"):identity_id},
            status=RegistryStatus(payload["status"]),preferred_display_name=payload["name"],
            created_at=datetime.fromisoformat(payload["created_at"]),updated_at=datetime.fromisoformat(payload["updated_at"]),
            schema_version=payload["record_schema_version"],lookup_attributes=tuple(tuple(x) for x in payload["lookup_attributes"]))
        if require_active and record.status is not RegistryStatus.ACTIVE:
            self._failure("LIFECYCLE_DENIED", None, "identity is not active", permission=True)
        return record

    def register_identity(self, *, case_id: str, record: PersonRecord | EntityRecord, authorization_ref: str) -> None:
        self._check_access("register_identity", case_id, authorization_ref)
        payload = self._identity_payload(record); identity_id = payload["identity_id"]
        def op():
            old = self._db.execute("SELECT payload FROM identity_record WHERE identity_id=?",(identity_id,)).fetchone()
            if old:
                if old["payload"] == _canonical(payload): return
                raise ValueError("identity already exists with different content")
            digest=self._mac(payload)
            self._db.execute("INSERT INTO identity_record VALUES(?,?,?,?,?,2)",(identity_id,payload["record_type"],_canonical(payload),digest,1))
            self._db.execute("INSERT INTO identity_history VALUES(?,?,?,?)",(identity_id,1,_canonical(payload),digest))
            self._append_audit("IDENTITY_REGISTER",case_id,identity_id,{"digest":digest})
        self._commit("IDENTITY_REGISTER",op)

    def update_identity_status(self, *, case_id: str, identity_id: str, status: RegistryStatus, authorization_ref: str) -> None:
        self._check_access("update_identity",case_id,authorization_ref)
        case=self._cases.get(case_id)
        associated=self._db.execute("SELECT 1 FROM case_party_role WHERE case_id=? AND subject_id=? LIMIT 1",(case_id,identity_id)).fetchone()
        if case.owner_id != identity_id and associated is None:
            self._failure("SECURITY_DENIED",case_id,"identity is not associated with case",permission=True)
        record=self._load_identity(identity_id)
        if record is None: raise KeyError("unknown identity")
        payload=self._identity_payload(record); payload["status"]=status.value; payload["updated_at"]=datetime.now(timezone.utc).isoformat()
        def op():
            row=self._db.execute("SELECT revision FROM identity_record WHERE identity_id=?",(identity_id,)).fetchone(); revision=row["revision"]+1; digest=self._mac(payload)
            self._db.execute("UPDATE identity_record SET payload=?,digest=?,revision=? WHERE identity_id=?",(_canonical(payload),digest,revision,identity_id))
            self._db.execute("INSERT INTO identity_history VALUES(?,?,?,?)",(identity_id,revision,_canonical(payload),digest))
            self._append_audit("IDENTITY_STATUS",case_id,identity_id,{"status":status.value,"revision":revision})
        self._commit("IDENTITY_STATUS",op)

    def bind_party(self, binding: CasePartyRole) -> None:
        self._check_access("bind_party",binding.case_id,binding.authorization_ref)
        case=self._cases.get(binding.case_id)
        if binding.subject_type not in ("PERSON","ENTITY") or binding.role not in PARTY_ROLES: self._failure("VALIDATION_DENIED",binding.case_id,"unsupported subject type or role",permission=False)
        if not binding.binding_id or not SHA_REFERENCE.fullmatch(binding.evidence_ref) or not SHA_REFERENCE.fullmatch(binding.authorization_ref): self._failure("VALIDATION_DENIED",binding.case_id,"canonical binding, evidence and authorization are required",permission=False)
        if binding.valid_to_exclusive is not None and binding.valid_from >= binding.valid_to_exclusive: self._failure("VALIDATION_DENIED",binding.case_id,"invalid effective interval",permission=False)
        evidence_end=binding.valid_to_exclusive or date(self._cases.get(binding.case_id).tax_period.year+1,1,1)
        try:
            self._resolve_evidence("ROLE_EVIDENCE",binding.evidence_ref,binding.case_id,self._cases.get(binding.case_id).tax_period.year,binding.subject_id,binding.valid_from,evidence_end)
            self._resolve_evidence("IDENTITY_AUTHORIZATION",binding.authorization_ref,binding.case_id,self._cases.get(binding.case_id).tax_period.year,binding.subject_id,binding.valid_from,evidence_end)
        except Exception: self._failure("EVIDENCE_DENIED",binding.case_id,"role evidence is unavailable or mismatched",permission=True)
        subject=self._load_identity(binding.subject_id,require_active=True)
        if subject is None or subject.record_type.value != binding.subject_type: self._failure("VALIDATION_DENIED",binding.case_id,"unknown or mismatched subject",permission=False)
        if binding.role=="PRIMARY_TAXPAYER" and (case.owner_id!=binding.subject_id or case.owner_type.value!=binding.subject_type): self._failure("SECURITY_DENIED",binding.case_id,"primary taxpayer must be exact registered case owner",permission=True)
        payload={"binding_id":binding.binding_id,"case_id":binding.case_id,"subject_type":binding.subject_type,"subject_id":binding.subject_id,"role":binding.role,"valid_from":binding.valid_from.isoformat(),"valid_to_exclusive":binding.valid_to_exclusive.isoformat() if binding.valid_to_exclusive else None,"evidence_ref":binding.evidence_ref,"authorization_ref":binding.authorization_ref}
        old=self._db.execute("SELECT * FROM case_party_role WHERE binding_id=?",(binding.binding_id,)).fetchone()
        if old:
            if hmac.compare_digest(old["digest"],self._mac(payload)): return
            self._failure("VALIDATION_DENIED",binding.case_id,"binding id reused with different payload",permission=False)
        query="SELECT * FROM case_party_role WHERE case_id=? AND role=?" if binding.role in EXCLUSIVE_ROLES else "SELECT * FROM case_party_role WHERE case_id=? AND role=? AND subject_id=?"
        args=(binding.case_id,binding.role) if binding.role in EXCLUSIVE_ROLES else (binding.case_id,binding.role,binding.subject_id)
        for other in self._db.execute(query,args):
            if (binding.valid_to_exclusive is None or date.fromisoformat(other["valid_from"])<binding.valid_to_exclusive) and (other["valid_to_exclusive"] is None or binding.valid_from<date.fromisoformat(other["valid_to_exclusive"])): self._failure("VALIDATION_DENIED",binding.case_id,"overlapping role binding",permission=False)
        def op():
            digest=self._mac(payload)
            self._db.execute("INSERT INTO case_party_role VALUES(?,?,?,?,?,?,?,?,?,?,?,2)",(*payload.values(),digest,1))
            self._append_audit("CASE_PARTY_BIND",binding.case_id,binding.subject_id,{"digest":digest})
        self._commit("CASE_PARTY_BIND",op)

    def list_parties(self, case_id: str, *, on_date: date, authorization_ref: str) -> tuple[CasePartyRole,...]:
        self._check_access("read_party",case_id,authorization_ref); result=[]
        for row in self._db.execute("SELECT * FROM case_party_role WHERE case_id=? ORDER BY binding_id",(case_id,)):
            payload={key:row[key] for key in ("binding_id","case_id","subject_type","subject_id","role","valid_from","valid_to_exclusive","evidence_ref","authorization_ref")}
            if row["schema_version"]!=2 or not hmac.compare_digest(self._mac(payload),row["digest"]): self._failure("INTEGRITY_FAILURE",case_id,"party binding integrity failure",permission=False)
            self._load_identity(row["subject_id"],require_active=True)
            start=date.fromisoformat(row["valid_from"]); end=date.fromisoformat(row["valid_to_exclusive"]) if row["valid_to_exclusive"] else None
            evidence_end=end or date(self._cases.get(case_id).tax_period.year+1,1,1)
            try:
                self._resolve_evidence("ROLE_EVIDENCE",row["evidence_ref"],case_id,self._cases.get(case_id).tax_period.year,row["subject_id"],start,evidence_end)
                self._resolve_evidence("IDENTITY_AUTHORIZATION",row["authorization_ref"],case_id,self._cases.get(case_id).tax_period.year,row["subject_id"],start,evidence_end)
            except Exception: raise PermissionError("role evidence is unavailable or mismatched")
            if start<=on_date and (end is None or on_date<end): result.append(CasePartyRole(row["binding_id"],case_id,row["subject_type"],row["subject_id"],row["role"],start,end,row["evidence_ref"],row["authorization_ref"]))
        return tuple(result)

    def read_case_identity(self, *, case_id: str, subject_id: str, on_date: date, authorization_ref: str):
        if not any(p.subject_id==subject_id for p in self.list_parties(case_id,on_date=on_date,authorization_ref=authorization_ref)): self._failure("SECURITY_DENIED",case_id,"subject not associated with case",permission=True)
        return self._load_identity(subject_id,require_active=True)

    def restore_case_identity(self, *, case_id: str, subject_id: str, on_date: date, authorization_ref: str, registry: PersonEntityRegistry) -> None:
        record=self.read_case_identity(case_id=case_id,subject_id=subject_id,on_date=on_date,authorization_ref=authorization_ref)
        registry.register_person(record) if isinstance(record,PersonRecord) else registry.register_entity(record)

    @staticmethod
    def _fact_payload(fact: HumanDeclaredFact) -> dict:
        return {"case_id":fact.case_id,"tax_year":fact.tax_year,"semantic_key":fact.semantic_key,"value":fact.value,
            "declaring_actor_reference":fact.declaring_actor_reference,"confirmation_state":fact.confirmation_state.value,
            "declared_at":fact.declared_at.isoformat(),"validation":{"status":fact.validation.status.value,"checks":list(fact.validation.checks),"errors":list(fact.validation.errors)},
            "authorization_reference":fact.authorization_reference,"audit_references":list(fact.audit_references),"consuming_references":list(fact.consuming_references),"source_type":fact.source_type.value,"version":fact.version}

    @staticmethod
    def _restore_fact(payload: dict) -> HumanDeclaredFact:
        return HumanDeclaredFact(payload["case_id"],payload["tax_year"],payload["semantic_key"],payload["value"],payload["declaring_actor_reference"],FactConfirmationState(payload["confirmation_state"]),datetime.fromisoformat(payload["declared_at"]),HumanFactValidationResult(FactValidationStatus(payload["validation"]["status"]),tuple(payload["validation"]["checks"]),tuple(payload["validation"]["errors"])),payload["authorization_reference"],tuple(payload["audit_references"]),tuple(payload["consuming_references"]),FactProvenanceKind(payload["source_type"]),payload["version"])

    def bind_fact(self, *, request_id: str, case_id: str, tax_year: int, subject_id: str, fact: HumanDeclaredFact,
                  declaration_artifact_ref: str, confirmation_ref: str, valid_from: date,
                  valid_to_exclusive: date, authorization_ref: str) -> SubjectFactEnvelope:
        try: fact.assert_consumable(case_id=case_id,tax_year=tax_year)
        except Exception: self._failure("VALIDATION_DENIED",case_id,"fact is not consumable in scope",permission=False)
        case=self._cases.get(case_id)
        if case is None or case.tax_period.year!=tax_year: self._failure("SECURITY_DENIED",case_id,"case/year mismatch",permission=True)
        self._check_access("bind_fact",case_id,authorization_ref)
        refs=(declaration_artifact_ref,confirmation_ref,authorization_ref,*fact.audit_references)
        if not request_id or any(not SHA_REFERENCE.fullmatch(ref) for ref in refs): self._failure("VALIDATION_DENIED",case_id,"canonical immutable fact lineage is required",permission=False)
        if authorization_ref!=fact.authorization_reference: self._failure("SECURITY_DENIED",case_id,"matching authorization required",permission=True)
        year_start=date(tax_year,1,1); year_end=date(tax_year+1,1,1)
        if not (year_start<=valid_from<valid_to_exclusive<=year_end): self._failure("VALIDATION_DENIED",case_id,"fact validity must be an explicit interval within the tax year",permission=False)
        for kind,ref in (("OWNER_DECLARATION",declaration_artifact_ref),("OWNER_CONFIRMATION",confirmation_ref),("IDENTITY_AUTHORIZATION",authorization_ref),*(("IDENTITY_AUDIT",r) for r in fact.audit_references)):
            try: self._resolve_evidence(kind,ref,case_id,tax_year,subject_id,valid_from,valid_to_exclusive)
            except Exception: self._failure("EVIDENCE_DENIED",case_id,"fact evidence is unavailable or mismatched",permission=True)
        roles=[p for p in self.list_parties(case_id,on_date=valid_from,authorization_ref=authorization_ref) if p.subject_id==subject_id]
        if not any(p.valid_from<=valid_from and (p.valid_to_exclusive is None or p.valid_to_exclusive>=valid_to_exclusive) for p in roles): self._failure("SECURITY_DENIED",case_id,"subject role does not cover fact validity",permission=True)
        record=self._load_identity(subject_id,require_active=True); subject_type=record.record_type.value
        fact_payload=self._fact_payload(fact); ref=fact.artifact_identity.reference
        env=SubjectFactEnvelope(request_id,case_id,tax_year,subject_type,subject_id,fact.semantic_key,ref,declaration_artifact_ref,confirmation_ref,authorization_ref,valid_from,valid_to_exclusive,tuple(fact.audit_references))
        payload={**asdict(env),"valid_from":valid_from.isoformat(),"valid_to_exclusive":valid_to_exclusive.isoformat(),"audit_lineage":list(env.audit_lineage),"fact_payload":fact_payload}
        old=self._db.execute("SELECT digest FROM subject_fact_binding WHERE request_id=?",(request_id,)).fetchone()
        if old:
            if not hmac.compare_digest(old["digest"],self._mac(payload)): self._failure("VALIDATION_DENIED",case_id,"request ID conflict",permission=False)
            return env
        def op():
            digest=self._mac(payload)
            self._db.execute("INSERT INTO subject_fact_binding VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,2)",(request_id,case_id,tax_year,subject_type,subject_id,fact.semantic_key,_canonical(fact_payload),ref,declaration_artifact_ref,confirmation_ref,authorization_ref,valid_from.isoformat(),valid_to_exclusive.isoformat(),_canonical({"items":list(env.audit_lineage)}),1,digest))
            self._append_audit("SUBJECT_FACT_BIND",case_id,subject_id,{"digest":digest})
        self._commit("SUBJECT_FACT_BIND",op); return env

    def read_facts(self, *, case_id: str, tax_year: int, subject_id: str, authorization_ref: str) -> tuple[SubjectFactEnvelope,...]:
        self._check_access("read_fact",case_id,authorization_ref); case=self._cases.get(case_id)
        if case is None or case.tax_period.year!=tax_year: raise PermissionError("invalid scope")
        self._load_identity(subject_id,require_active=True); result=[]
        for row in self._db.execute("SELECT * FROM subject_fact_binding WHERE case_id=? AND tax_year=? AND subject_id=? ORDER BY request_id",(case_id,tax_year,subject_id)):
            fact_payload=json.loads(row["fact_payload"]); lineage=tuple(json.loads(row["audit_lineage"])["items"])
            env=SubjectFactEnvelope(row["request_id"],row["case_id"],row["tax_year"],row["subject_type"],row["subject_id"],row["semantic_key"],row["fact_artifact_ref"],row["declaration_artifact_ref"],row["confirmation_ref"],row["authorization_ref"],date.fromisoformat(row["valid_from"]),date.fromisoformat(row["valid_to_exclusive"]),lineage,row["revision"])
            payload={**asdict(env),"valid_from":env.valid_from.isoformat(),"valid_to_exclusive":env.valid_to_exclusive.isoformat(),"audit_lineage":list(lineage),"fact_payload":fact_payload}
            fact=self._restore_fact(fact_payload)
            if row["schema_version"]!=2 or row["authorization_ref"]!=authorization_ref or fact.artifact_identity.reference!=row["fact_artifact_ref"] or fact.confirmation_state is not FactConfirmationState.CONFIRMED or not hmac.compare_digest(self._mac(payload),row["digest"]): self._failure("INTEGRITY_FAILURE",case_id,"fact lineage integrity failure",permission=False)
            fact.assert_consumable(case_id=case_id,tax_year=tax_year)
            for kind,ref in (("OWNER_DECLARATION",env.declaration_artifact_ref),("OWNER_CONFIRMATION",env.confirmation_ref),("IDENTITY_AUTHORIZATION",env.authorization_ref),*(("IDENTITY_AUDIT",r) for r in env.audit_lineage)):
                try: self._resolve_evidence(kind,ref,case_id,tax_year,subject_id,env.valid_from,env.valid_to_exclusive)
                except Exception: raise PermissionError("fact evidence is unavailable or mismatched")
            roles=[p for p in self.list_parties(case_id,on_date=env.valid_from,authorization_ref=authorization_ref) if p.subject_id==subject_id]
            if not any(p.valid_from<=env.valid_from and (p.valid_to_exclusive is None or p.valid_to_exclusive>=env.valid_to_exclusive) for p in roles): raise PermissionError("subject role no longer covers fact validity")
            result.append(env)
        return tuple(result)

    def backup_to(self, destination: str | Path) -> Path:
        self._verify_audit_continuity(); target=Path(destination).resolve()
        if target.exists(): raise FileExistsError("backup destination already exists")
        with sqlite3.connect(target) as backup: self._db.backup(backup)
        count,head=self._audit_head(); payload=self._anchor_payload(count,head); doc={**payload,"anchor_mac":self._mac(payload)}
        target.with_suffix(target.suffix+".audit-anchor").write_text(_canonical(doc),encoding="utf-8")
        return target

    def close(self) -> None:
        self._verify_audit_continuity(); self._db.close()
