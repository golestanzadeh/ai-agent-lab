"""Durable synthetic identity evidence authorities and protected resolver.

Only metadata and keyed integrity values are persisted. Protected bytes are
obtained from an injected, case-scoped verifier and are never stored here.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable


class IdentityEvidenceError(RuntimeError): pass


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class EvidenceScope:
    case_id: str; tax_year: int; subject_id: str; semantic_key: str
    actor_id: str; run_id: str; task_id: str; manifest_id: str
    valid_from: date; valid_to_exclusive: date


@dataclass(frozen=True, slots=True)
class ProtectedEvidence:
    event_id: str; kind: str; scope: EvidenceScope; provider: str; object_id: str
    document_revision: str; content_digest: str; parent_event_id: str | None
    expires_at: datetime | None; revoked_at: datetime | None; consumed_at: datetime | None


class DurableIdentityEvidenceAuthority:
    ALLOWED = ("OWNER_DECLARATION", "OWNER_CONFIRMATION", "IDENTITY_AUTHORIZATION")

    def __init__(self, db_path: str | Path, *, integrity_key: bytes) -> None:
        if len(integrity_key) < 32: raise IdentityEvidenceError("protected integrity key required")
        path=Path(db_path).resolve()
        if not path.exists(): raise IdentityEvidenceError("preprovisioned synthetic identity database required")
        self._key=bytes(integrity_key); self._db=sqlite3.connect(f"file:{path.as_posix()}?mode=rw",uri=True)
        self._db.row_factory=sqlite3.Row; self._db.execute("PRAGMA foreign_keys=ON"); self._db.execute("PRAGMA journal_mode=WAL"); self._db.execute("PRAGMA busy_timeout=5000")
        with self._db:
            self._db.executescript("""
            CREATE TABLE IF NOT EXISTS identity_evidence_v2(
              event_id TEXT PRIMARY KEY,kind TEXT NOT NULL,case_id TEXT NOT NULL,tax_year INTEGER NOT NULL,
              subject_id TEXT NOT NULL,semantic_key TEXT NOT NULL,actor_id TEXT NOT NULL,run_id TEXT NOT NULL,
              task_id TEXT NOT NULL,manifest_id TEXT NOT NULL,valid_from TEXT NOT NULL,valid_to_exclusive TEXT NOT NULL,
              provider TEXT NOT NULL,object_id TEXT NOT NULL,document_revision TEXT NOT NULL,content_digest TEXT NOT NULL,
              parent_event_id TEXT,created_at TEXT NOT NULL,expires_at TEXT,revoked_at TEXT,consumed_at TEXT,row_mac TEXT NOT NULL,
              FOREIGN KEY(parent_event_id) REFERENCES identity_evidence_v2(event_id));
            CREATE TABLE IF NOT EXISTS identity_evidence_audit_v2(
              sequence INTEGER PRIMARY KEY,event_id TEXT NOT NULL,action TEXT NOT NULL,payload TEXT NOT NULL,
              previous_mac TEXT NOT NULL,event_mac TEXT NOT NULL,occurred_at TEXT NOT NULL);
            """)
        self.verify_integrity()

    def _mac(self, value: object) -> str:
        return hmac.new(self._key,_canonical(value).encode(),hashlib.sha256).hexdigest()

    @staticmethod
    def _scope_dict(scope: EvidenceScope) -> dict[str,object]:
        return {"case_id":scope.case_id,"tax_year":scope.tax_year,"subject_id":scope.subject_id,
                "semantic_key":scope.semantic_key,"actor_id":scope.actor_id,"run_id":scope.run_id,
                "task_id":scope.task_id,"manifest_id":scope.manifest_id,"valid_from":scope.valid_from.isoformat(),
                "valid_to_exclusive":scope.valid_to_exclusive.isoformat()}

    def append(self, *, event_id: str, kind: str, scope: EvidenceScope, provider: str,
               object_id: str, document_revision: str, content_digest: str,
               parent_event_id: str | None = None, expires_at: datetime | None = None) -> str:
        strings=(event_id,scope.case_id,scope.subject_id,scope.semantic_key,scope.actor_id,scope.run_id,
                 scope.task_id,scope.manifest_id,provider,object_id,document_revision)
        if kind not in self.ALLOWED or not all(isinstance(v,str) and v.strip() for v in strings): raise IdentityEvidenceError("complete evidence metadata required")
        if scope.valid_from>=scope.valid_to_exclusive or not 1900<=scope.tax_year<=9999: raise IdentityEvidenceError("invalid evidence scope")
        if not content_digest.startswith("sha256:") or len(content_digest)!=71: raise IdentityEvidenceError("canonical SHA-256 required")
        try: bytes.fromhex(content_digest[7:])
        except ValueError as exc: raise IdentityEvidenceError("canonical SHA-256 required") from exc
        if expires_at is not None and expires_at.tzinfo is None: raise IdentityEvidenceError("expiry must be timezone-aware")
        parent=None if parent_event_id is None else self._row(parent_event_id)
        expected=None if kind=="OWNER_DECLARATION" else self.ALLOWED[self.ALLOWED.index(kind)-1]
        if (expected is None) != (parent is None): raise IdentityEvidenceError("invalid evidence parent")
        if parent is not None:
            same=(parent["kind"]==expected and parent["case_id"]==scope.case_id and parent["tax_year"]==scope.tax_year
                  and parent["subject_id"]==scope.subject_id and parent["semantic_key"]==scope.semantic_key
                  and parent["document_revision"]==document_revision and parent["content_digest"]==content_digest)
            if not same or parent["revoked_at"] is not None: raise IdentityEvidenceError("missing, revoked or mismatched parent")
        created=datetime.now(timezone.utc).isoformat(); payload={"event_id":event_id,"kind":kind,**self._scope_dict(scope),
            "provider":provider,"object_id":object_id,"document_revision":document_revision,"content_digest":content_digest,
            "parent_event_id":parent_event_id,"created_at":created,"expires_at":expires_at.isoformat() if expires_at else None,
            "revoked_at":None,"consumed_at":None}
        try:
            with self._db:
                self._db.execute("INSERT INTO identity_evidence_v2 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    tuple(payload[k] for k in ("event_id","kind","case_id","tax_year","subject_id","semantic_key","actor_id","run_id","task_id","manifest_id","valid_from","valid_to_exclusive","provider","object_id","document_revision","content_digest","parent_event_id","created_at","expires_at","revoked_at","consumed_at"))+(self._mac(payload),))
                self._audit(event_id,"APPEND",{"kind":kind})
        except sqlite3.IntegrityError as exc: raise IdentityEvidenceError("duplicate or invalid evidence") from exc
        return event_id

    def revoke(self,event_id:str,*,actor_id:str) -> None:
        row=self._row(event_id)
        if row["revoked_at"] is not None: return
        when=datetime.now(timezone.utc).isoformat(); payload=self._payload(row); payload["revoked_at"]=when
        with self._db:
            self._db.execute("UPDATE identity_evidence_v2 SET revoked_at=?,row_mac=? WHERE event_id=?",(when,self._mac(payload),event_id)); self._audit(event_id,"REVOKE",{"actor_id":actor_id})

    def consume_authorization(self,event_id:str) -> None:
        row=self._row(event_id); self._assert_usable(row,authorization=True)
        when=datetime.now(timezone.utc).isoformat(); payload=self._payload(row); payload["consumed_at"]=when
        with self._db:
            changed=self._db.execute("UPDATE identity_evidence_v2 SET consumed_at=?,row_mac=? WHERE event_id=? AND consumed_at IS NULL",(when,self._mac(payload),event_id)).rowcount
            if changed!=1: raise IdentityEvidenceError("authorization already consumed")
            self._audit(event_id,"CONSUME",{})

    def resolve(self,event_id:str,*,content_loader:Callable[[str,str,str,str],bytes],expected_scope:EvidenceScope) -> ProtectedEvidence:
        row=self._row(event_id); self._assert_usable(row,authorization=row["kind"]=="IDENTITY_AUTHORIZATION")
        for key,value in self._scope_dict(expected_scope).items():
            observed=row[key] if key not in {"valid_from","valid_to_exclusive"} else row[key]
            expected=value
            if observed!=expected: raise IdentityEvidenceError("evidence scope mismatch")
        content=content_loader(row["case_id"],row["provider"],row["object_id"],row["document_revision"])
        digest="sha256:"+hashlib.sha256(content).hexdigest()
        if not hmac.compare_digest(digest,row["content_digest"]): raise IdentityEvidenceError("protected content digest mismatch")
        if row["parent_event_id"]: self.resolve(row["parent_event_id"],content_loader=content_loader,expected_scope=expected_scope)
        return self._record(row)

    def _assert_usable(self,row:sqlite3.Row,*,authorization:bool) -> None:
        if row["revoked_at"] is not None or (authorization and row["consumed_at"] is not None): raise IdentityEvidenceError("evidence revoked or consumed")
        if row["expires_at"] and datetime.fromisoformat(row["expires_at"])<=datetime.now(timezone.utc): raise IdentityEvidenceError("evidence expired")
        if not hmac.compare_digest(row["row_mac"],self._mac(self._payload(row))): raise IdentityEvidenceError("evidence integrity failure")

    def _row(self,event_id:str) -> sqlite3.Row:
        row=self._db.execute("SELECT * FROM identity_evidence_v2 WHERE event_id=?",(event_id,)).fetchone()
        if row is None: raise IdentityEvidenceError("evidence unavailable")
        return row

    @staticmethod
    def _payload(row:sqlite3.Row) -> dict[str,object]: return {k:row[k] for k in row.keys() if k!="row_mac"}

    def _record(self,row:sqlite3.Row) -> ProtectedEvidence:
        s=EvidenceScope(row["case_id"],row["tax_year"],row["subject_id"],row["semantic_key"],row["actor_id"],row["run_id"],row["task_id"],row["manifest_id"],date.fromisoformat(row["valid_from"]),date.fromisoformat(row["valid_to_exclusive"]))
        parse=lambda v: datetime.fromisoformat(v) if v else None
        return ProtectedEvidence(row["event_id"],row["kind"],s,row["provider"],row["object_id"],row["document_revision"],row["content_digest"],row["parent_event_id"],parse(row["expires_at"]),parse(row["revoked_at"]),parse(row["consumed_at"]))

    def _audit(self,event_id:str,action:str,details:dict[str,object]) -> None:
        last=self._db.execute("SELECT sequence,event_mac FROM identity_evidence_audit_v2 ORDER BY sequence DESC LIMIT 1").fetchone(); seq=1 if last is None else last["sequence"]+1; prev="0"*64 if last is None else last["event_mac"]; occurred=datetime.now(timezone.utc).isoformat(); payload=_canonical(details); mac=self._mac({"sequence":seq,"event_id":event_id,"action":action,"payload":payload,"previous_mac":prev,"occurred_at":occurred}); self._db.execute("INSERT INTO identity_evidence_audit_v2 VALUES(?,?,?,?,?,?,?)",(seq,event_id,action,payload,prev,mac,occurred))

    def verify_integrity(self) -> None:
        for row in self._db.execute("SELECT * FROM identity_evidence_v2"):
            if not hmac.compare_digest(row["row_mac"],self._mac(self._payload(row))): raise IdentityEvidenceError("evidence integrity failure")
        prev="0"*64
        for row in self._db.execute("SELECT * FROM identity_evidence_audit_v2 ORDER BY sequence"):
            expected=self._mac({"sequence":row["sequence"],"event_id":row["event_id"],"action":row["action"],"payload":row["payload"],"previous_mac":row["previous_mac"],"occurred_at":row["occurred_at"]})
            if row["previous_mac"]!=prev or not hmac.compare_digest(row["event_mac"],expected): raise IdentityEvidenceError("identity audit integrity failure")
            prev=row["event_mac"]

    def close(self) -> None:
        self.verify_integrity(); self._db.close()
