"""Isolated, local-only functional UI test store.

NOT the authoritative Kernel case registry or a production persistence provider.
Only explicitly TEST-prefixed cases and metadata are accepted. No private PDFs.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import sqlite3
from threading import RLock

from agent_lab.ui_dashboard import DashboardCase


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

    def close(self):
        self._db.close()

    def cases(self) -> tuple[DashboardCase, ...]:
        with self._lock:
            return tuple(DashboardCase(*row) for row in self._db.execute(
                "SELECT case_id,tax_year,status FROM test_case ORDER BY tax_year DESC,case_id"))

    def _check_case(self, case_id: str):
        if not case_id.startswith("TEST-") or not self._db.execute(
            "SELECT 1 FROM test_case WHERE case_id=?", (case_id,)).fetchone():
            raise ValueError("unknown or unauthorized test case")

    def create_case(self, case_id: str, tax_year: int):
        if not case_id.startswith("TEST-") or len(case_id) > 64 or not all(
            ch.isascii() and (ch.isalnum() or ch in "-_") for ch in case_id
        ) or not 2000 <= tax_year <= 2100:
            raise ValueError("invalid isolated test case")
        with self._lock, self._db:
            self._db.execute("INSERT INTO test_case(case_id,tax_year) VALUES(?,?)", (case_id,tax_year))
            self._audit(case_id,"CASE_CREATED")

    def _audit(self, case_id: str, event: str):
        self._db.execute("INSERT INTO test_audit(case_id,event) VALUES(?,?)",(case_id,event))

    def add_document(self, case_id: str, label: str, data: bytes) -> bool:
        if not data or len(data)>2_000_000 or not label.strip() or len(label)>100:
            raise ValueError("invalid test document")
        digest=hashlib.sha256(data).hexdigest()
        with self._lock, self._db:
            self._check_case(case_id)
            cur=self._db.execute("INSERT OR IGNORE INTO test_document VALUES(?,?,?)",(case_id,digest,label))
            if cur.rowcount:
                self._audit(case_id,"DOCUMENT_HASH_REGISTERED")
            return bool(cur.rowcount)

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
