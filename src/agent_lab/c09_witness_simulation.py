"""Isolated, non-operational C09 witness protocol simulator.

No production Kernel/Identity path imports this module.  It models canonical
records, conditional create, retention/version attacks, and crash recovery for
local proof-of-correctness tests only.  It has no network or credential code.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from dataclasses import dataclass, replace
from typing import Any


PROTOCOL = "ai-tax-agent.c09-witness/1"
ZERO = "sha256:" + "0" * 64


class WitnessError(RuntimeError):
    """Fail-closed protocol or simulated storage error."""


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


@dataclass(frozen=True, slots=True)
class WitnessRecord:
    protocol: str
    deployment_id: str
    epoch: int
    sequence: int
    previous_record: str
    kernel_head: str
    identity_head: str
    backup_generation: int
    operation_id: str
    record_type: str = "COMMIT"
    owner_authorization_digest: str | None = None
    mac: str = ""

    def unsigned(self) -> dict[str, Any]:
        return {
            "backup_generation": self.backup_generation,
            "deployment_id": self.deployment_id,
            "epoch": self.epoch,
            "identity_head": self.identity_head,
            "kernel_head": self.kernel_head,
            "operation_id": self.operation_id,
            "owner_authorization_digest": self.owner_authorization_digest,
            "previous_record": self.previous_record,
            "protocol": self.protocol,
            "record_type": self.record_type,
            "sequence": self.sequence,
        }

    def signed(self, key: bytes) -> "WitnessRecord":
        tag = hmac.new(key, b"AI-TAX-AGENT\x00C09-WITNESS\x00" + canonical_bytes(self.unsigned()), hashlib.sha256).hexdigest()
        return replace(self, mac="hmac-sha256:" + tag)

    def verify(self, key: bytes) -> None:
        if self.protocol != PROTOCOL or self.epoch < 1 or self.sequence < 1:
            raise WitnessError("invalid witness contract")
        if not re.fullmatch(r"[A-Z][A-Z0-9-]{2,63}", self.deployment_id):
            raise WitnessError("invalid deployment identity")
        if not re.fullmatch(r"[A-Z][A-Z0-9:-]{2,127}", self.operation_id):
            raise WitnessError("invalid operation identity")
        if self.record_type not in {"COMMIT", "RESTORE"}:
            raise WitnessError("invalid record type")
        if (self.record_type == "RESTORE") != (self.owner_authorization_digest is not None):
            raise WitnessError("restore authorization binding mismatch")
        sha256 = re.compile(r"sha256:[0-9a-f]{64}")
        for value in (self.previous_record, self.kernel_head, self.identity_head):
            if sha256.fullmatch(value) is None:
                raise WitnessError("invalid record commitment")
        if self.owner_authorization_digest is not None and sha256.fullmatch(self.owner_authorization_digest) is None:
            raise WitnessError("invalid Owner authorization commitment")
        if self.backup_generation < 0:
            raise WitnessError("invalid backup generation")
        expected = self.signed(key).mac
        if not hmac.compare_digest(expected, self.mac):
            raise WitnessError("invalid witness authentication")
        if len(canonical_bytes({**self.unsigned(), "mac": self.mac})) > 4096:
            raise WitnessError("witness record too large")

    @property
    def commitment(self) -> str:
        return digest(canonical_bytes({**self.unsigned(), "mac": self.mac}))

    @property
    def object_key(self) -> str:
        return f"witness/v1/{self.deployment_id}/epoch-{self.epoch:020d}/sequence-{self.sequence:020d}.json"


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

    def __init__(self, *, key: bytes = b"synthetic-witness-key", deployment_id: str = "DEPLOYMENT-SYNTHETIC") -> None:
        self.key = key
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
        expected = "hmac-sha256:" + hmac.new(self.key, b"AI-TAX-AGENT\x00C09-RESTORE\x00" + canonical_bytes(unsigned), hashlib.sha256).hexdigest()
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
        value["owner_mac"] = "hmac-sha256:" + hmac.new(self.key, b"AI-TAX-AGENT\x00C09-RESTORE\x00" + canonical_bytes(value), hashlib.sha256).hexdigest()
        return value
