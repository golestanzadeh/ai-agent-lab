"""Canonical C09 witness record contract shared by adapters and test models."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from dataclasses import dataclass, replace
from typing import Any


PROTOCOL = "ai-tax-agent.c09-witness/1"
ZERO = "sha256:" + "0" * 64
_DOMAIN = b"AI-TAX-AGENT\x00C09-WITNESS\x00"
_FIELDS = {
    "backup_generation",
    "deployment_id",
    "epoch",
    "identity_head",
    "kernel_head",
    "mac",
    "operation_id",
    "owner_authorization_digest",
    "previous_record",
    "protocol",
    "record_type",
    "sequence",
}


class WitnessError(RuntimeError):
    """Fail-closed witness protocol error."""


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise WitnessError("duplicate witness field")
        result[key] = value
    return result


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
        if not isinstance(key, bytes) or not key:
            raise WitnessError("witness authentication key unavailable")
        tag = hmac.new(key, _DOMAIN + canonical_bytes(self.unsigned()), hashlib.sha256).hexdigest()
        return replace(self, mac="hmac-sha256:" + tag)

    def verify(self, key: bytes) -> None:
        if self.protocol != PROTOCOL or type(self.epoch) is not int or type(self.sequence) is not int:
            raise WitnessError("invalid witness contract")
        if self.epoch < 1 or self.sequence < 1:
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
            if not isinstance(value, str) or sha256.fullmatch(value) is None:
                raise WitnessError("invalid record commitment")
        if self.owner_authorization_digest is not None and (
            not isinstance(self.owner_authorization_digest, str)
            or sha256.fullmatch(self.owner_authorization_digest) is None
        ):
            raise WitnessError("invalid Owner authorization commitment")
        if type(self.backup_generation) is not int or self.backup_generation < 0:
            raise WitnessError("invalid backup generation")
        expected = self.signed(key).mac
        if not isinstance(self.mac, str) or not hmac.compare_digest(expected, self.mac):
            raise WitnessError("invalid witness authentication")
        if len(self.to_bytes()) > 4096:
            raise WitnessError("witness record too large")

    def to_bytes(self) -> bytes:
        return canonical_bytes({**self.unsigned(), "mac": self.mac})

    @classmethod
    def from_bytes(cls, payload: bytes, key: bytes) -> "WitnessRecord":
        if not isinstance(payload, bytes) or len(payload) > 4096:
            raise WitnessError("invalid witness encoding")
        try:
            text = payload.decode("utf-8", errors="strict")
            value = json.loads(
                text,
                object_pairs_hook=_reject_duplicate_pairs,
                parse_constant=lambda _value: (_ for _ in ()).throw(
                    WitnessError("invalid witness number")
                ),
            )
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise WitnessError("invalid witness encoding") from exc
        if not isinstance(value, dict) or set(value) != _FIELDS:
            raise WitnessError("witness schema mismatch")
        if canonical_bytes(value) != payload:
            raise WitnessError("non-canonical witness encoding")
        try:
            record = cls(**value)
        except TypeError as exc:
            raise WitnessError("witness schema mismatch") from exc
        record.verify(key)
        return record

    @property
    def commitment(self) -> str:
        return digest(self.to_bytes())

    @property
    def object_key(self) -> str:
        return (
            f"witness/v1/{self.deployment_id}/epoch-{self.epoch:020d}/"
            f"sequence-{self.sequence:020d}.json"
        )


def verify_chain(
    records: list[WitnessRecord], key: bytes, *, deployment_id: str
) -> tuple[WitnessRecord, ...]:
    """Verify one complete ordered deployment history; never sorts attacker input."""
    previous = ZERO
    expected_epoch = 1
    expected_sequence = 1
    seen_operations: set[str] = set()
    verified: list[WitnessRecord] = []
    for record in records:
        record.verify(key)
        if record.deployment_id != deployment_id:
            raise WitnessError("cross-deployment witness record")
        if record.operation_id in seen_operations:
            raise WitnessError("duplicate witness operation")
        ordinary = (
            record.record_type == "COMMIT"
            and record.epoch == expected_epoch
            and record.sequence == expected_sequence
        )
        restore = (
            record.record_type == "RESTORE"
            and record.epoch == expected_epoch + 1
            and record.sequence == 1
            and record.owner_authorization_digest is not None
        )
        if not ordinary and not restore:
            raise WitnessError("witness sequence gap, reorder, or epoch fork")
        if record.previous_record != previous:
            raise WitnessError("witness chain fork")
        verified.append(record)
        seen_operations.add(record.operation_id)
        previous = record.commitment
        if restore:
            expected_epoch = record.epoch
            expected_sequence = 2
        else:
            expected_sequence += 1
    return tuple(verified)
