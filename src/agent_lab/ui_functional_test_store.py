"""Isolated, local-only functional UI test store.

NOT the authoritative Kernel case registry or a production persistence provider.
Only explicitly TEST-prefixed cases and metadata are accepted. No private PDFs.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from threading import RLock

from agent_lab.case_registry import (
    AssessmentMode,
    CaseRecord,
    CaseRegistry,
    CaseType,
    LifecycleStatus,
    OwnerType,
    StorageScopeReference,
    TaxPeriod,
)
from agent_lab.case_state import CaseState, CaseStateStore
from agent_lab.ui_dashboard import DashboardCase
from agent_lab.ui_synthetic_document_parser import CONTENT_TYPE, MAX_CONTENT_BYTES


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class SyntheticDocumentMetadata:
    case_id: str
    label: str
    digest: str
    reference: str
    content_type: str | None = None
    content: bytes | None = None


class FunctionalTestStore:
    def __init__(self, path: str | Path):
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._db = sqlite3.connect(self.path, check_same_thread=False)
        self._db.execute("PRAGMA foreign_keys=ON")
        with self._db:
            self._db.executescript("""
                CREATE TABLE IF NOT EXISTS test_case(
                    case_id TEXT PRIMARY KEY, tax_year INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'CREATED',
                    CHECK(case_id LIKE 'TEST-%'));
                CREATE TABLE IF NOT EXISTS test_document(
                    case_id TEXT NOT NULL REFERENCES test_case(case_id),
                    digest TEXT NOT NULL, label TEXT NOT NULL,
                    content_type TEXT, content BLOB,
                    PRIMARY KEY(case_id,digest));
                CREATE TABLE IF NOT EXISTS test_issue(
                    case_id TEXT NOT NULL REFERENCES test_case(case_id),
                    issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL, answer TEXT,
                    state TEXT NOT NULL DEFAULT 'OPEN');
                CREATE TABLE IF NOT EXISTS test_audit(
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id TEXT NOT NULL, event TEXT NOT NULL,
                    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            """)
            columns = {
                row[1] for row in self._db.execute("PRAGMA table_info(test_document)")
            }
            if "content_type" not in columns:
                self._db.execute("ALTER TABLE test_document ADD COLUMN content_type TEXT")
            if "content" not in columns:
                self._db.execute("ALTER TABLE test_document ADD COLUMN content BLOB")
        self._reload_backend()

    def _reload_backend(self) -> None:
        """Rebuild the canonical in-memory models from the isolated test snapshot."""
        registry = CaseRegistry()
        state_store = CaseStateStore(registry)
        fixed_time = datetime(2000, 1, 1, tzinfo=timezone.utc)
        for case_id, tax_year, status in self._db.execute(
            "SELECT case_id,tax_year,status FROM test_case ORDER BY case_id"
        ):
            lifecycle = LifecycleStatus(status)
            record = CaseRecord(
                case_id=case_id,
                owner_type=OwnerType.PERSON,
                owner_id=f"TEST-OWNER-{case_id}",
                tax_period=TaxPeriod("CALENDAR_YEAR", tax_year),
                case_type=CaseType.INDIVIDUAL,
                assessment_mode=AssessmentMode.UNKNOWN_PENDING_VERIFICATION,
                lifecycle_status=lifecycle,
                storage_scope_reference=StorageScopeReference(
                    "functional-test", f"test://{case_id}"
                ),
                schema_version=1,
                created_at=fixed_time,
                updated_at=fixed_time,
            )
            registry.register(record, request_id=f"TEST-CREATE-{case_id}")
            state_store.initialize_case(case_id)
        registry.validate()
        state_store.validate()
        self._case_registry = registry
        self._case_state_store = state_store

    def close(self):
        self._db.close()

    def cases(self) -> tuple[DashboardCase, ...]:
        with self._lock:
            self._case_registry.validate()
            self._case_state_store.validate()
            return tuple(
                DashboardCase(
                    record.case_id,
                    record.tax_period.year,
                    record.lifecycle_status.value,
                )
                for record in sorted(
                    self._case_registry.all_records(),
                    key=lambda item: (-item.tax_period.year, item.case_id),
                )
            )

    def case_state(self, case_id: str) -> CaseState:
        with self._lock:
            self._check_case(case_id)
            return self._case_state_store.get_state(case_id)

    def _check_case(self, case_id: str):
        if not case_id.startswith("TEST-") or self._case_registry.get(case_id) is None:
            raise ValueError("unknown or unauthorized test case")

    def create_case(self, case_id: str, tax_year: int):
        if not case_id.startswith("TEST-") or len(case_id) > 64 or not all(
            ch.isascii() and (ch.isalnum() or ch in "-_") for ch in case_id
        ) or not 2000 <= tax_year <= 2100:
            raise ValueError("invalid isolated test case")
        with self._lock, self._db:
            self._db.execute("INSERT INTO test_case(case_id,tax_year) VALUES(?,?)", (case_id,tax_year))
            self._audit(case_id,"CASE_CREATED")
        with self._lock:
            self._reload_backend()

    def _audit(self, case_id: str, event: str):
        self._db.execute("INSERT INTO test_audit(case_id,event) VALUES(?,?)",(case_id,event))

    def add_document(
        self, case_id: str, label: str, data: bytes,
        content_type: str = CONTENT_TYPE,
    ) -> bool:
        if (
            not data or len(data) > MAX_CONTENT_BYTES or content_type != CONTENT_TYPE
            or not label.strip() or len(label) > 100
        ):
            raise ValueError("invalid test document")
        digest=hashlib.sha256(data).hexdigest()
        with self._lock, self._db:
            self._check_case(case_id)
            cur=self._db.execute(
                "INSERT OR IGNORE INTO test_document(case_id,digest,label,content_type,content) VALUES(?,?,?,?,?)",
                (case_id, digest, label, content_type, data),
            )
            if cur.rowcount:
                self._audit(case_id,"DOCUMENT_HASH_REGISTERED")
            return bool(cur.rowcount)

    def resolve_document(self, case_id: str, digest: str) -> SyntheticDocumentMetadata:
        if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            raise ValueError("malformed synthetic document digest")
        with self._lock:
            self._check_case(case_id)
            rows = self._db.execute(
                "SELECT label,digest,content_type,content FROM test_document WHERE case_id=? AND digest=?",
                (case_id, digest),
            ).fetchall()
            if len(rows) != 1:
                raise ValueError("document is not owned by the exact test case")
            label, stored_digest, content_type, content = rows[0]
            if content is not None and hashlib.sha256(content).hexdigest() != stored_digest:
                raise ValueError("stored synthetic document content does not match its digest")
            return SyntheticDocumentMetadata(
                case_id=case_id,
                label=label,
                digest=stored_digest,
                reference=f"test-document://{case_id}/sha256:{stored_digest}",
                content_type=content_type,
                content=content,
            )

    def resolve_document_content(self, case_id: str, digest: str) -> SyntheticDocumentMetadata:
        document = self.resolve_document(case_id, digest)
        if document.content_type != CONTENT_TYPE or document.content is None:
            raise ValueError("synthetic document content is unavailable or unsupported")
        if not document.content or len(document.content) > MAX_CONTENT_BYTES:
            raise ValueError("stored synthetic document size is invalid")
        return document

    def add_issue(self, case_id: str, question: str):
        if not question.strip() or len(question)>500:
            raise ValueError("invalid question")
        with self._lock, self._db:
            self._check_case(case_id)
            self._db.execute("INSERT INTO test_issue(case_id,question) VALUES(?,?)",(case_id,question))
            self._audit(case_id,"ISSUE_CREATED")

    def answer_issue(self, case_id: str, issue_id: int, answer: str):
        if not answer.strip() or len(answer)>2000:
            raise ValueError("invalid answer")
        with self._lock, self._db:
            self._check_case(case_id)
            cur=self._db.execute("UPDATE test_issue SET answer=?,state='ANSWERED' WHERE case_id=? AND issue_id=? AND state='OPEN'",(answer,case_id,issue_id))
            if not cur.rowcount:
                raise ValueError("issue not found or already answered")
            self._audit(case_id,"ISSUE_ANSWERED")

    def detail(self, case_id: str) -> dict:
        with self._lock:
            self._check_case(case_id)
            return {
                "documents": tuple(self._db.execute("SELECT label,digest FROM test_document WHERE case_id=? ORDER BY label",(case_id,))),
                "issues": tuple(self._db.execute("SELECT issue_id,question,answer,state FROM test_issue WHERE case_id=? ORDER BY issue_id",(case_id,))),
                "activity": tuple(self._db.execute("SELECT event,recorded_at FROM test_audit WHERE case_id=? ORDER BY event_id DESC",(case_id,))),
            }
