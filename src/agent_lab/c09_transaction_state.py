"""Synthetic-only durable C09 transaction integration over the real Kernel.

Transport and witness providers are injected.  This module performs no network,
IPC, credential, protected-data, backup, or restore operation.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .c09_witness_protocol import PROTOCOL, ZERO, WitnessError, WitnessRecord, canonical_bytes, digest
from .identity_continuity_authority import IdentityContinuityAuthority, IdentityContinuityContext
from .orchestrator_kernel import OrchestratorKernel, PermissionDenied


class C09TransactionError(RuntimeError):
    """A fail-closed transaction or recovery error."""


class InjectedCrash(C09TransactionError):
    """Synthetic process termination boundary used only by tests."""


class WitnessClient(Protocol):
    def append_or_resolve(self, record: WitnessRecord) -> str: ...
    def verify_exact(self, record: WitnessRecord, generation: str) -> None: ...
    def read_complete_chain(self, deployment_id: str) -> tuple[tuple[str, bytes], ...]: ...


@dataclass(frozen=True, slots=True)
class TransactionResult:
    transaction_id: str
    state: str
    identity_head: str
    receipt_digest: str
    witness_generation: str
    acknowledged: bool


class DurableC09TransactionState:
    """Durable staged receipts; Kernel remains the sole coordinator."""

    _STATES = {"PREPARED", "PENDING", "IDENTITY_COMMITTED", "WITNESS_STAGED", "WITNESSED", "COMMITTED", "ACKNOWLEDGED"}

    def __init__(self, path: str | Path, kernel: OrchestratorKernel,
                 context: IdentityContinuityContext, witness: WitnessClient, mac_key: bytes) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.kernel = kernel
        self.context = context
        self.authority = IdentityContinuityAuthority(kernel, context)
        self.witness = witness
        self.mac_key = mac_key
        if not mac_key:
            raise C09TransactionError("synthetic witness key unavailable")
        self.db = sqlite3.connect(self.path, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS identity_state(
              deployment_id TEXT PRIMARY KEY, epoch INTEGER NOT NULL, head TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS c09_transaction(
              transaction_id TEXT PRIMARY KEY, operation_id TEXT NOT NULL UNIQUE,
              capability TEXT NOT NULL, payload_digest TEXT NOT NULL,
              expected_epoch INTEGER NOT NULL, expected_head TEXT NOT NULL,
              next_head TEXT NOT NULL, state TEXT NOT NULL,
              receipt_json TEXT, receipt_digest TEXT,
              witness_bytes BLOB, witness_generation TEXT,
              acknowledged INTEGER NOT NULL DEFAULT 0,
              CHECK(state IN ('PREPARED','PENDING','IDENTITY_COMMITTED','WITNESS_STAGED','WITNESSED','COMMITTED','ACKNOWLEDGED')));
            CREATE UNIQUE INDEX IF NOT EXISTS c09_one_successor
              ON c09_transaction(expected_epoch, expected_head)
              WHERE state IN ('IDENTITY_COMMITTED','WITNESS_STAGED','WITNESSED','COMMITTED','ACKNOWLEDGED');
        """)
        self._verify_durable_receipts()
        self._verify_durable_witnesses()

    def close(self) -> None:
        self.db.close()

    def initialize(self, head: str = ZERO) -> None:
        try:
            self.db.execute("BEGIN IMMEDIATE")
            changed = self.db.execute(
                "INSERT OR IGNORE INTO identity_state VALUES(?,?,?)",
                (self.context.deployment_id, 0, head),
            ).rowcount
            self.db.execute("COMMIT")
        except Exception:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise
        if changed != 1:
            raise C09TransactionError("identity state already initialized")
        self.authority.initialize(head)

    @staticmethod
    def _next_head(current: str, transaction_id: str, payload_digest: str) -> str:
        return digest(canonical_bytes({"current": current, "payload": payload_digest, "transaction": transaction_id}))

    def begin(self, *, transaction_id: str, operation_id: str, capability: str,
              payload: dict, stop_after: str | None = None) -> TransactionResult:
        if capability in {"identity_backup", "identity_restore"}:
            raise PermissionDenied("capability is defined but has no operational grant")
        decision = self.kernel.permission_decision(
            self.context.manifest_id, capability, case_id=self.context.case_id,
            tax_year=self.context.tax_year, run_id=self.context.run_id,
        )
        if not decision.allowed:
            raise PermissionDenied("Kernel denied C09 transaction capability")
        payload_digest = digest(canonical_bytes(payload))
        existing = self.db.execute(
            "SELECT * FROM c09_transaction WHERE transaction_id=? OR operation_id=?",
            (transaction_id, operation_id),
        ).fetchone()
        if existing is not None:
            if (existing["transaction_id"], existing["operation_id"], existing["capability"], existing["payload_digest"]) != (
                transaction_id, operation_id, capability, payload_digest
            ):
                raise C09TransactionError("transaction replay or conflicting identity")
            return self.recover(transaction_id, stop_after=stop_after)
        state = self.db.execute(
            "SELECT epoch,head FROM identity_state WHERE deployment_id=?", (self.context.deployment_id,)
        ).fetchone()
        if state is None:
            raise C09TransactionError("identity state unavailable")
        next_head = self._next_head(state["head"], transaction_id, payload_digest)
        with self.db:
            self.db.execute(
                "INSERT INTO c09_transaction(transaction_id,operation_id,capability,payload_digest,expected_epoch,expected_head,next_head,state) VALUES(?,?,?,?,?,?,?,'PREPARED')",
                (transaction_id, operation_id, capability, payload_digest, state["epoch"], state["head"], next_head),
            )
        self._crash("PREPARED", stop_after)
        return self.recover(transaction_id, stop_after=stop_after)

    def recover(self, transaction_id: str, *, stop_after: str | None = None) -> TransactionResult:
        row = self._row(transaction_id)
        if row["state"] == "PREPARED":
            self.authority.reserve(
                row["expected_epoch"], row["expected_head"], row["next_head"],
                reservation_id=row["transaction_id"], request_digest=row["payload_digest"],
            )
            with self.db:
                changed = self.db.execute(
                    "UPDATE c09_transaction SET state='PENDING' WHERE transaction_id=? AND state='PREPARED'",
                    (transaction_id,),
                ).rowcount
                if changed != 1:
                    raise C09TransactionError("conflicting reservation transition")
            self._crash("PENDING", stop_after)
            row = self._row(transaction_id)
        if row["state"] == "PENDING":
            self._verify_pending(row)
            receipt = self._receipt(row)
            receipt_json = canonical_bytes(receipt).decode("utf-8")
            receipt_digest = digest(receipt_json.encode("utf-8"))
            try:
                self.db.execute("BEGIN IMMEDIATE")
                changed = self.db.execute(
                    "UPDATE identity_state SET epoch=?,head=? WHERE deployment_id=? AND epoch=? AND head=?",
                    (row["expected_epoch"] + 1, row["next_head"], self.context.deployment_id,
                     row["expected_epoch"], row["expected_head"]),
                ).rowcount
                if changed != 1:
                    raise C09TransactionError("identity compare-and-swap conflict")
                self.db.execute(
                    "UPDATE c09_transaction SET state='IDENTITY_COMMITTED',receipt_json=?,receipt_digest=? WHERE transaction_id=? AND state='PENDING'",
                    (receipt_json, receipt_digest, transaction_id),
                )
                self.db.execute("COMMIT")
            except Exception:
                if self.db.in_transaction:
                    self.db.execute("ROLLBACK")
                raise
            self._crash("IDENTITY_COMMITTED", stop_after)
            row = self._row(transaction_id)
        if row["state"] == "IDENTITY_COMMITTED":
            self._verify_pending(row)
            record = self._record(row)
            with self.db:
                changed = self.db.execute(
                    "UPDATE c09_transaction SET state='WITNESS_STAGED',witness_bytes=? WHERE transaction_id=? AND state='IDENTITY_COMMITTED'",
                    (record.to_bytes(), transaction_id),
                ).rowcount
                if changed != 1:
                    raise C09TransactionError("conflicting witness staging transition")
            self._crash("WITNESS_STAGED", stop_after)
            row = self._row(transaction_id)
        if row["state"] == "WITNESS_STAGED":
            self._verify_pending(row)
            record = WitnessRecord.from_bytes(row["witness_bytes"], self.mac_key)
            generation = self.witness.append_or_resolve(record)
            self.witness.verify_exact(record, generation)
            with self.db:
                changed = self.db.execute(
                    "UPDATE c09_transaction SET state='WITNESSED',witness_generation=? WHERE transaction_id=? AND state='WITNESS_STAGED'",
                    (generation, transaction_id),
                ).rowcount
                if changed != 1:
                    raise C09TransactionError("conflicting witness transition")
            self._crash("WITNESSED", stop_after)
            row = self._row(transaction_id)
        if row["state"] == "WITNESSED":
            self._verify_pending(row)
            record = WitnessRecord.from_bytes(row["witness_bytes"], self.mac_key)
            self.witness.verify_exact(record, row["witness_generation"])
            self.authority.finalize(
                row["expected_epoch"], row["next_head"], reservation_id=row["transaction_id"],
                request_digest=row["payload_digest"],
            )
            with self.db:
                self.db.execute(
                    "UPDATE c09_transaction SET state='COMMITTED' WHERE transaction_id=? AND state='WITNESSED'",
                    (transaction_id,),
                )
            self._crash("COMMITTED", stop_after)
        return self.result(transaction_id)

    def acknowledge(self, transaction_id: str) -> TransactionResult:
        row = self._row(transaction_id)
        if row["state"] not in {"COMMITTED", "ACKNOWLEDGED"}:
            raise C09TransactionError("unverified transaction cannot be acknowledged")
        self._verify_durable_witnesses()
        self.authority.verify(row["expected_epoch"] + 1, row["next_head"])
        with self.db:
            self.db.execute(
                "UPDATE c09_transaction SET state='ACKNOWLEDGED',acknowledged=1 WHERE transaction_id=? AND state='COMMITTED'",
                (transaction_id,),
            )
        return self.result(transaction_id)

    def result(self, transaction_id: str) -> TransactionResult:
        row = self._row(transaction_id)
        return TransactionResult(transaction_id, row["state"], row["next_head"],
                                 row["receipt_digest"] or "", row["witness_generation"] or "",
                                 bool(row["acknowledged"]))

    def _row(self, transaction_id: str) -> sqlite3.Row:
        row = self.db.execute("SELECT * FROM c09_transaction WHERE transaction_id=?", (transaction_id,)).fetchone()
        if row is None or row["state"] not in self._STATES:
            raise C09TransactionError("transaction unavailable")
        return row

    def _record(self, row: sqlite3.Row) -> WitnessRecord:
        prior = self.db.execute(
            "SELECT witness_bytes FROM c09_transaction WHERE state IN ('WITNESSED','COMMITTED','ACKNOWLEDGED') ORDER BY expected_epoch DESC LIMIT 1"
        ).fetchone()
        previous = ZERO if prior is None else digest(prior["witness_bytes"])
        return WitnessRecord(
            PROTOCOL, self.context.deployment_id, row["expected_epoch"] + 1,
            row["expected_epoch"] + 1, previous,
            row["next_head"], row["next_head"], 0, row["operation_id"],
        ).signed(self.mac_key)

    def _verify_pending(self, row: sqlite3.Row) -> None:
        self.authority.verify_pending(
            row["expected_epoch"], row["expected_head"], row["next_head"],
            reservation_id=row["transaction_id"], request_digest=row["payload_digest"],
        )

    @staticmethod
    def _receipt(row: sqlite3.Row) -> dict:
        return {
            "contract": "ai-tax-agent.c09-staged-receipt/1",
            "transaction_id": row["transaction_id"], "operation_id": row["operation_id"],
            "payload_digest": row["payload_digest"], "expected_epoch": row["expected_epoch"],
            "expected_head": row["expected_head"], "identity_head": row["next_head"],
        }

    def _verify_durable_receipts(self) -> None:
        rows = self.db.execute(
            "SELECT * FROM c09_transaction WHERE state IN "
            "('IDENTITY_COMMITTED','WITNESS_STAGED','WITNESSED','COMMITTED','ACKNOWLEDGED') "
            "ORDER BY expected_epoch"
        ).fetchall()
        for row in rows:
            derived_head = self._next_head(
                row["expected_head"], row["transaction_id"], row["payload_digest"]
            )
            if row["next_head"] != derived_head:
                raise C09TransactionError("durable transaction head derivation is invalid")
            expected_json = canonical_bytes(self._receipt(row)).decode("utf-8")
            expected_digest = digest(expected_json.encode("utf-8"))
            if row["receipt_json"] != expected_json or row["receipt_digest"] != expected_digest:
                raise C09TransactionError("durable staged receipt is missing or altered")

    def _verify_durable_witnesses(self) -> None:
        rows = self.db.execute(
            "SELECT state,witness_bytes,witness_generation,operation_id,next_head FROM c09_transaction "
            "WHERE state IN ('WITNESS_STAGED','WITNESSED','COMMITTED','ACKNOWLEDGED') ORDER BY expected_epoch"
        ).fetchall()
        external = self.witness.read_complete_chain(self.context.deployment_id)
        committed_count = sum(row["state"] != "WITNESS_STAGED" for row in rows)
        if len(external) < committed_count or len(external) > len(rows):
            raise C09TransactionError("external witness head disagrees with durable local state")
        if len(external) != len(rows) and not (
            len(rows) == committed_count + 1 and rows[-1]["state"] == "WITNESS_STAGED"
            and len(external) == committed_count
        ):
            raise C09TransactionError("external witness enumeration is incomplete")
        previous = ZERO
        for index, (generation, payload) in enumerate(external):
            row = rows[index]
            if row["witness_bytes"] is None:
                raise C09TransactionError("durable witness evidence is incomplete")
            if payload != row["witness_bytes"]:
                raise C09TransactionError("external witness chain conflicts with durable local state")
            if row["witness_generation"] is not None and generation != row["witness_generation"]:
                raise C09TransactionError("external witness generation conflicts with durable local state")
            record = WitnessRecord.from_bytes(payload, self.mac_key)
            if record.deployment_id != self.context.deployment_id or record.epoch != index + 1 or record.sequence != index + 1:
                raise C09TransactionError("external witness sequence or scope is invalid")
            if (
                record.record_type != "COMMIT" or record.operation_id != row["operation_id"]
                or record.kernel_head != row["next_head"] or record.identity_head != row["next_head"]
                or record.backup_generation != 0 or record.owner_authorization_digest is not None
            ):
                raise C09TransactionError("external witness semantics conflict with durable transaction")
            if record.previous_record != previous:
                raise C09TransactionError("durable witness chain is truncated or reordered")
            self.witness.verify_exact(record, generation)
            previous = digest(payload)

    @staticmethod
    def _crash(boundary: str, requested: str | None) -> None:
        if requested == boundary:
            raise InjectedCrash(f"synthetic crash after {boundary}")
