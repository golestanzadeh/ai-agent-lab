"""Durable, case-scoped state for the local synthetic Milestone A journey."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


class WorkflowStoreError(RuntimeError): pass
class WorkflowScopeError(WorkflowStoreError): pass
class WorkflowIntegrityError(WorkflowStoreError): pass
class WorkflowTransitionError(WorkflowStoreError): pass


class WorkflowStage(str, Enum):
    CREATE_CASE="CREATE_CASE"; INTAKE="INTAKE"; PROCESS="PROCESS"; SPECIALIST_REVIEW="SPECIALIST_REVIEW"
    CHIEF_REVIEW="CHIEF_REVIEW"; CALCULATION="CALCULATION"; FORM_PREVIEW="FORM_PREVIEW"
    APPROVAL_STAGE_1="APPROVAL_STAGE_1"; APPROVAL_STAGE_2="APPROVAL_STAGE_2"
    SYNTHETIC_SUBMISSION="SYNTHETIC_SUBMISSION"; RECEIPT="RECEIPT"; RECOVERY="RECOVERY"


ORDER = tuple(WorkflowStage)


@dataclass(frozen=True, slots=True)
class WorkflowSnapshot:
    case_id: str; tax_year: int; run_id: str; stage: WorkflowStage; sequence: int; artifact_identity: str; transition_hash: str


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class SyntheticWorkflowStore:
    SCHEMA_VERSION = 1

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(self.path)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys=ON")
        with self._db:
            self._db.execute("CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
            self._db.execute("CREATE TABLE IF NOT EXISTS workflows(run_id TEXT PRIMARY KEY,case_id TEXT NOT NULL,tax_year INTEGER NOT NULL,stage TEXT NOT NULL,sequence INTEGER NOT NULL,artifact_identity TEXT NOT NULL,transition_hash TEXT NOT NULL,UNIQUE(case_id,tax_year,run_id))")
            self._db.execute("CREATE TABLE IF NOT EXISTS transitions(transition_id TEXT PRIMARY KEY,run_id TEXT NOT NULL REFERENCES workflows(run_id),ordinal INTEGER NOT NULL,payload_json TEXT NOT NULL,event_hash TEXT NOT NULL,UNIQUE(run_id,ordinal))")
            self._db.execute("CREATE TABLE IF NOT EXISTS action_attempts(transition_id TEXT PRIMARY KEY,run_id TEXT NOT NULL REFERENCES workflows(run_id),request_json TEXT NOT NULL,request_hash TEXT NOT NULL,outcome TEXT NOT NULL CHECK(outcome IN ('PENDING','ACCEPTED','REJECTED')))")
            row=self._db.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
            if row is None: self._db.execute("INSERT INTO metadata VALUES('schema_version',?)",(str(self.SCHEMA_VERSION),))
            elif row["value"] != str(self.SCHEMA_VERSION): raise WorkflowIntegrityError("unsupported workflow schema version")
        self.verify_integrity()

    def close(self) -> None: self._db.close()
    def __enter__(self): return self
    def __exit__(self, *_): self.close()

    @staticmethod
    def _scope(case_id: str, tax_year: int, run_id: str) -> None:
        if not case_id.startswith("SYNTHETIC-") or not run_id.startswith("RUN-SYNTHETIC-") or not isinstance(tax_year,int) or isinstance(tax_year,bool):
            raise WorkflowScopeError("exact synthetic case_id, tax_year, and run_id are required")

    def create(self, case_id: str, tax_year: int, run_id: str, artifact_identity: str, transition_id: str) -> WorkflowSnapshot:
        self._scope(case_id,tax_year,run_id)
        existing=self._db.execute("SELECT * FROM workflows WHERE run_id=?",(run_id,)).fetchone()
        if existing:
            snap=self._snapshot(existing)
            initial=self._db.execute("SELECT transition_id,payload_json,event_hash FROM transitions WHERE run_id=? AND ordinal=1",(run_id,)).fetchone()
            if (snap.case_id,snap.tax_year)!=(case_id,tax_year) or initial is None: raise WorkflowScopeError("run_id belongs to another exact scope")
            if initial["transition_id"] != transition_id: raise WorkflowTransitionError("initial transition identity was already used differently")
            initial_payload=json.loads(initial["payload_json"])
            if initial_payload["artifact_identity"] != artifact_identity: raise WorkflowTransitionError("initial transition payload changed")
            return WorkflowSnapshot(case_id,tax_year,run_id,WorkflowStage.CREATE_CASE,1,artifact_identity,initial["event_hash"])
        return self._write(case_id,tax_year,run_id,None,WorkflowStage.CREATE_CASE,artifact_identity,transition_id)

    def advance(self, case_id: str, tax_year: int, run_id: str, expected: WorkflowStage, target: WorkflowStage, artifact_identity: str, transition_id: str) -> WorkflowSnapshot:
        self._scope(case_id,tax_year,run_id)
        row=self._db.execute("SELECT * FROM workflows WHERE run_id=?",(run_id,)).fetchone()
        if row is None: raise WorkflowScopeError("workflow run is not registered")
        current=self._snapshot(row)
        if (current.case_id,current.tax_year)!=(case_id,tax_year): raise WorkflowScopeError("workflow scope mismatch")
        prior=self._db.execute("SELECT payload_json,event_hash FROM transitions WHERE transition_id=?",(transition_id,)).fetchone()
        if prior:
            payload=json.loads(prior["payload_json"])
            if payload["case_id"]==case_id and payload["tax_year"]==tax_year and payload["run_id"]==run_id and payload["target"]==target.value and payload["artifact_identity"]==artifact_identity:
                return WorkflowSnapshot(case_id,tax_year,run_id,target,payload["ordinal"],artifact_identity,prior["event_hash"])
            raise WorkflowTransitionError("transition identity was already used differently")
        if current.stage is not expected or ORDER.index(target)!=ORDER.index(expected)+1: raise WorkflowTransitionError("stale or out-of-order transition")
        return self._write(case_id,tax_year,run_id,current,target,artifact_identity,transition_id)

    def get(self, case_id: str, tax_year: int, run_id: str) -> WorkflowSnapshot:
        self._scope(case_id,tax_year,run_id)
        row=self._db.execute("SELECT * FROM workflows WHERE run_id=?",(run_id,)).fetchone()
        if row is None or (row["case_id"],row["tax_year"])!=(case_id,tax_year): raise WorkflowScopeError("workflow scope not found")
        return self._snapshot(row)

    def reserve_action_attempt(self, run_id: str, transition_id: str, request_payload: dict[str, object]) -> str:
        request_json=_canonical(request_payload); request_hash="sha256:"+hashlib.sha256(request_json.encode()).hexdigest()
        prior=self._db.execute("SELECT request_hash,outcome FROM action_attempts WHERE transition_id=?",(transition_id,)).fetchone()
        if prior:
            if prior["request_hash"]!=request_hash: raise WorkflowTransitionError("action attempt identity was already used differently")
            return prior["outcome"]
        with self._db:
            self._db.execute("INSERT INTO action_attempts VALUES(?,?,?,?,?)",(transition_id,run_id,request_json,request_hash,"PENDING"))
        return "PENDING"

    def finalize_action_attempt(self, transition_id: str, outcome: str) -> None:
        if outcome not in {"ACCEPTED","REJECTED"}: raise ValueError("invalid action attempt outcome")
        with self._db:
            changed=self._db.execute("UPDATE action_attempts SET outcome=? WHERE transition_id=? AND outcome='PENDING'",(outcome,transition_id)).rowcount
        if changed != 1: raise WorkflowTransitionError("action attempt is already final")

    def action_attempt(self, transition_id: str) -> dict[str, object]:
        row=self._db.execute("SELECT request_json,outcome FROM action_attempts WHERE transition_id=?",(transition_id,)).fetchone()
        if row is None: raise WorkflowTransitionError("action attempt not found")
        return {"request":json.loads(row["request_json"]),"outcome":row["outcome"]}

    def _write(self, case_id, tax_year, run_id, current, target, artifact_identity, transition_id):
        if not artifact_identity.startswith("sha256:") or len(artifact_identity)!=71 or not transition_id.strip(): raise WorkflowTransitionError("valid artifact and transition identities are required")
        ordinal=1 if current is None else current.sequence+1
        previous="GENESIS" if current is None else current.transition_hash
        payload={"case_id":case_id,"tax_year":tax_year,"run_id":run_id,"ordinal":ordinal,"target":target.value,"artifact_identity":artifact_identity,"previous_hash":previous}
        digest="sha256:"+hashlib.sha256(_canonical(payload).encode()).hexdigest()
        with self._db:
            if current is None: self._db.execute("INSERT INTO workflows VALUES(?,?,?,?,?,?,?)",(run_id,case_id,tax_year,target.value,ordinal,artifact_identity,digest))
            else:
                changed=self._db.execute("UPDATE workflows SET stage=?,sequence=?,artifact_identity=?,transition_hash=? WHERE run_id=? AND transition_hash=?",(target.value,ordinal,artifact_identity,digest,run_id,current.transition_hash)).rowcount
                if changed != 1: raise WorkflowTransitionError("workflow changed concurrently")
            self._db.execute("INSERT INTO transitions VALUES(?,?,?,?,?)",(transition_id,run_id,ordinal,_canonical(payload),digest))
        return self.get(case_id,tax_year,run_id)

    def verify_integrity(self) -> None:
        previous: dict[str,str] = {}
        for row in self._db.execute("SELECT * FROM transitions ORDER BY run_id,ordinal"):
            payload=json.loads(row["payload_json"]); digest="sha256:"+hashlib.sha256(_canonical(payload).encode()).hexdigest()
            expected_previous=previous.get(row["run_id"],"GENESIS")
            if digest!=row["event_hash"] or payload["ordinal"]!=row["ordinal"] or payload.get("previous_hash")!=expected_previous: raise WorkflowIntegrityError("workflow transition journal integrity failed")
            previous[row["run_id"]]=row["event_hash"]
        for row in self._db.execute("SELECT * FROM workflows"):
            last=self._db.execute("SELECT event_hash,payload_json,ordinal FROM transitions WHERE run_id=? ORDER BY ordinal DESC LIMIT 1",(row["run_id"],)).fetchone()
            payload=json.loads(last["payload_json"]) if last else {}
            if last is None or last["event_hash"]!=row["transition_hash"] or last["ordinal"]!=row["sequence"] or payload.get("target")!=row["stage"] or payload.get("artifact_identity")!=row["artifact_identity"]: raise WorkflowIntegrityError("workflow head integrity failed")
        for row in self._db.execute("SELECT request_json,request_hash FROM action_attempts"):
            digest="sha256:"+hashlib.sha256(row["request_json"].encode()).hexdigest()
            if digest!=row["request_hash"]: raise WorkflowIntegrityError("action attempt integrity failed")

    @staticmethod
    def _snapshot(row):
        return WorkflowSnapshot(row["case_id"],row["tax_year"],row["run_id"],WorkflowStage(row["stage"]),row["sequence"],row["artifact_identity"],row["transition_hash"])
