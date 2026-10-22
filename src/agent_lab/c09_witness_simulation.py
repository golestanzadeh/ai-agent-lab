"""Isolated, non-operational C09 witness protocol simulator.

No production Kernel/Identity path imports this module.  It models canonical
records, conditional create, retention/version attacks, and crash recovery for
local proof-of-correctness tests only.  It has no network or credential code.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, replace
from typing import Any

from .c09_witness_protocol import (
    PROTOCOL,
    ZERO,
    WitnessError,
    WitnessRecord,
    canonical_bytes,
    digest,
)


@dataclass(frozen=True, slots=True)
class StoredVersion:
    payload: WitnessRecord | None
    delete_marker: bool = False


class SimulatedImmutableObjectStore:
    """Provider-neutral model; versions/delete markers remain observable."""

    def __init__(self) -> None:
        self._objects: dict[str, list[StoredVersion]] = {}
        self.available = True

    def conditional_create(self, record: WitnessRecord) -> None:
        if not self.available:
            raise WitnessError("witness unavailable")
        versions = self._objects.setdefault(record.object_key, [])
        if versions and not versions[-1].delete_marker:
            raise WitnessError("conditional create conflict")
        versions.append(StoredVersion(record))

    def inject_version(self, key: str, record: WitnessRecord) -> None:
        self._objects.setdefault(key, []).append(StoredVersion(record))

    def inject_delete_marker(self, key: str) -> None:
        self._objects.setdefault(key, []).append(StoredVersion(None, True))

    def versions(self, key: str) -> tuple[StoredVersion, ...]:
        if not self.available:
            raise WitnessError("witness unavailable")
        return tuple(self._objects.get(key, ()))

    def records(self, deployment_id: str) -> list[WitnessRecord]:
        if not self.available:
            raise WitnessError("witness unavailable")
        prefix = f"witness/v1/{deployment_id}/"
        result: list[WitnessRecord] = []
        for key, versions in self._objects.items():
            if not key.startswith(prefix):
                continue
            if len(versions) != 1 or versions[0].delete_marker or versions[0].payload is None:
                raise WitnessError("object version or delete-marker ambiguity")
            result.append(versions[0].payload)
        return sorted(result, key=lambda item: (item.epoch, item.sequence))


@dataclass(slots=True)
class LocalState:
    epoch: int = 1
    sequence: int = 0
    kernel_head: str = ZERO
    identity_head: str = ZERO
    backup_generation: int = 0
    pending: dict[str, Any] | None = None
    finalized: bool = True

    def clone(self) -> "LocalState":
        return LocalState(self.epoch, self.sequence, self.kernel_head, self.identity_head, self.backup_generation, dict(self.pending) if self.pending else None, self.finalized)


class WitnessProtocolHarness:
    """Deterministic crash/recovery model; never used by operational code."""

    def __init__(self, *, key: bytes = b"synthetic-witness-key", owner_key: bytes = b"synthetic-owner-restore-key", deployment_id: str = "DEPLOYMENT-SYNTHETIC") -> None:
        if key == owner_key:
            raise WitnessError("Owner and witness authentication keys must differ")
        self.key = key
        self.owner_key = owner_key
        self.deployment_id = deployment_id
        self.store = SimulatedImmutableObjectStore()
        self.state = LocalState()
        self.used_operations: set[str] = set()
        self.used_restore_authorizations: set[str] = set()

    def _next_record(self, operation_id: str) -> WitnessRecord:
        prior = self.store.records(self.deployment_id)
        previous = prior[-1].commitment if prior else ZERO
        pending = self.state.pending
        if pending is None:
            raise WitnessError("missing pending transaction")
        return WitnessRecord(
            PROTOCOL,
            self.deployment_id,
            self.state.epoch,
            self.state.sequence + 1,
            previous,
            pending["kernel_head"],
            pending["identity_head"],
            self.state.backup_generation,
            operation_id,
        ).signed(self.key)

    def execute(self, operation_id: str, *, crash_at: str | None = None) -> str:
        if operation_id in self.used_operations or self.state.pending is not None:
            raise WitnessError("duplicate, replay, or unresolved pending transaction")
        next_sequence = self.state.sequence + 1
        self.state.pending = {
            "operation_id": operation_id,
            "kernel_head": digest(f"kernel:{self.state.epoch}:{next_sequence}:{operation_id}".encode()),
            "identity_head": digest(f"identity:{self.state.epoch}:{next_sequence}:{operation_id}".encode()),
        }
        self.state.finalized = False
        if crash_at == "before_identity":
            return "PENDING"
        self.state.identity_head = self.state.pending["identity_head"]
        if crash_at == "after_identity":
            return "IDENTITY_COMMITTED_NOT_FINAL"
        record = self._next_record(operation_id)
        self.store.conditional_create(record)
        if crash_at == "after_witness":
            return "WITNESSED_NOT_FINAL"
        self._finalize(record)
        return "FINALIZED"

    def _finalize(self, record: WitnessRecord) -> None:
        record.verify(self.key)
        if self.state.pending is None or self.state.pending["operation_id"] != record.operation_id:
            raise WitnessError("witness does not match pending transaction")
        if (self.state.identity_head != record.identity_head
                or self.state.pending["identity_head"] != record.identity_head
                or self.state.pending["kernel_head"] != record.kernel_head):
            raise WitnessError("Identity or staged heads do not match witness")
        self.state.sequence = record.sequence
        self.state.kernel_head = record.kernel_head
        self.state.identity_head = record.identity_head
        self.state.pending = None
        self.state.finalized = True
        self.used_operations.add(record.operation_id)

    def recover(self) -> str:
        records = self.verify_witness_chain()
        latest = records[-1] if records else None
        pending = self.state.pending
        if pending is not None:
            matching = next((item for item in records if item.operation_id == pending["operation_id"]), None)
            if matching is not None:
                self._finalize(matching)
                return "FINALIZED_FROM_WITNESS"
            if self.state.identity_head == pending["identity_head"]:
                # Only reconcile when the local finalized base exactly matches
                # the externally authenticated head; never replay Identity.
                base_ok = (
                    (latest is None and self.state.epoch == 1 and self.state.sequence == 0
                     and self.state.kernel_head == ZERO)
                    or (latest is not None and
                        (self.state.epoch, self.state.sequence, self.state.kernel_head)
                        == (latest.epoch, latest.sequence, latest.kernel_head))
                )
                if not base_ok:
                    raise WitnessError("unverifiable Identity-ahead base")
                try:
                    record = self._next_record(pending["operation_id"])
                    self.store.conditional_create(record)
                    self._finalize(record)
                    return "RECONCILED_IDENTITY_AHEAD"
                except WitnessError:
                    return "FAIL_CLOSED_IDENTITY_AHEAD"
            self.state.pending = None
            self.state.finalized = True
            return "ABORTED_BEFORE_IDENTITY"
        if latest is None:
            if self.state.sequence != 0 or self.state.kernel_head != ZERO or self.state.identity_head != ZERO:
                raise WitnessError("local state ahead of empty witness")
            return "CONSISTENT_EMPTY"
        if (self.state.epoch, self.state.sequence, self.state.kernel_head, self.state.identity_head) != (
            latest.epoch,
            latest.sequence,
            latest.kernel_head,
            latest.identity_head,
        ):
            raise WitnessError("local state is stale or inconsistent with witness")
        return "CONSISTENT"

    def verify_witness_chain(self) -> list[WitnessRecord]:
        records = self.store.records(self.deployment_id)
        previous = ZERO
        expected_epoch, expected_sequence = 1, 1
        for record in records:
            record.verify(self.key)
            ordinary = record.epoch == expected_epoch and record.sequence == expected_sequence
            restore = (
                record.record_type == "RESTORE"
                and record.epoch == expected_epoch + 1
                and record.sequence == 1
                and record.owner_authorization_digest is not None
            )
            if not ordinary and not restore:
                raise WitnessError("witness sequence gap, high sequence, or epoch fork")
            if record.previous_record != previous:
                raise WitnessError("witness chain fork")
            previous = record.commitment
            if restore:
                expected_epoch, expected_sequence = record.epoch, 2
            else:
                expected_sequence += 1
        return records

    def authorized_restore(self, authorization: dict[str, Any]) -> None:
        required = {"authorization_id", "source_commitment", "target_epoch", "target_sequence", "target_kernel_head", "target_identity_head", "target_backup_generation", "expires", "owner_mac"}
        if set(authorization) != required:
            raise WitnessError("restore authorization shape mismatch")
        authorization_id = authorization["authorization_id"]
        if authorization_id in self.used_restore_authorizations or authorization["expires"] != "VALID":
            raise WitnessError("restore authorization reused or expired")
        unsigned = {key: authorization[key] for key in sorted(required - {"owner_mac"})}
        expected = "hmac-sha256:" + hmac.new(self.owner_key, b"AI-TAX-AGENT\x00C09-RESTORE\x00" + canonical_bytes(unsigned), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, authorization["owner_mac"]):
            raise WitnessError("restore authorization authentication mismatch")
        records = self.verify_witness_chain()
        if not records or records[-1].commitment != authorization["source_commitment"]:
            raise WitnessError("restore source does not match current witness")
        if authorization["target_epoch"] != self.state.epoch + 1 or authorization["target_sequence"] != 1:
            raise WitnessError("restore target epoch mismatch")
        self.used_restore_authorizations.add(authorization_id)

        record = WitnessRecord(
            PROTOCOL,
            self.deployment_id,
            authorization["target_epoch"],
            1,
            authorization["source_commitment"],
            authorization["target_kernel_head"],
            authorization["target_identity_head"],
            authorization["target_backup_generation"],
            f"RESTORE:{authorization_id}",
            "RESTORE",
            digest(canonical_bytes(unsigned)),
        ).signed(self.key)
        self.store.conditional_create(record)
        self.state = LocalState(
            epoch=record.epoch,
            sequence=record.sequence,
            kernel_head=record.kernel_head,
            identity_head=record.identity_head,
            backup_generation=record.backup_generation,
            finalized=True,
        )

    def sign_restore(self, authorization_id: str, *, source_commitment: str, target_epoch: int, expires: str = "VALID") -> dict[str, Any]:
        value = {
            "authorization_id": authorization_id,
            "expires": expires,
            "source_commitment": source_commitment,
            "target_backup_generation": self.state.backup_generation + 1,
            "target_epoch": target_epoch,
            "target_identity_head": digest(f"restore-identity:{target_epoch}".encode()),
            "target_kernel_head": digest(f"restore-kernel:{target_epoch}".encode()),
            "target_sequence": 1,
        }
        value["owner_mac"] = "hmac-sha256:" + hmac.new(self.owner_key, b"AI-TAX-AGENT\x00C09-RESTORE\x00" + canonical_bytes(value), hashlib.sha256).hexdigest()
        return value
