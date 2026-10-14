"""Closed non-operational IPC envelope validation.

The development contract validates canonical synthetic envelopes only.  It does
not authenticate a peer, authorize or dispatch an operation, carry domain data,
or expose persistence, finality, backup, or restore behavior.
"""

from __future__ import annotations

import hmac
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from agent_lab.ipc_wire_primitives import (
    WireFormatError,
    canonical_sha256,
    decode_frame,
)


CONTRACT = "oi0002.kernel-identity-ipc-dev/1.0"
MESSAGE_TYPES = frozenset(
    {
        "PREPARE_MUTATION",
        "COMMIT_MUTATION",
        "GET_TRANSACTION",
        "ABORT_PREPARED",
        "READ_IDENTITY_STATE",
    }
)
OPERATION_CAPABILITIES = {
    "REGISTER_IDENTITY": "identity_create",
    "UPDATE_IDENTITY_STATUS": "identity_status_transition",
    "BIND_PARTY": "case_party_bind",
    "CORRECT_PARTY_ROLE": "identity_update",
    "BIND_FACT": "subject_fact_bind",
    "READ_CASE_IDENTITY": "identity_read",
    "LIST_PARTIES": "identity_read",
    "READ_FACTS": "identity_read",
}
MUTATION_OPERATIONS = frozenset(
    {"REGISTER_IDENTITY", "UPDATE_IDENTITY_STATUS", "BIND_PARTY", "CORRECT_PARTY_ROLE", "BIND_FACT"}
)
READ_OPERATIONS = frozenset({"READ_CASE_IDENTITY", "LIST_PARTIES", "READ_FACTS"})

_FIELDS = frozenset(
    {
        "contract", "message_type", "transaction_id", "request_digest",
        "deployment_id", "scope_kind", "case_id", "tax_year", "run_id",
        "task_id", "manifest_id", "actor_instance_id", "role_id",
        "capability", "domain_operation", "expected_epoch", "expected_head",
        "authorization_references", "expires_at", "payload",
    }
)
_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,95}\Z")
_TRANSACTION_RE = re.compile(
    r"tx:v1:[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z"
)
_DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
_EPOCH_RE = re.compile(r"0|[1-9][0-9]{0,19}\Z")
_YEAR_RE = re.compile(r"[0-9]{4}\Z")
_TIMESTAMP_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z\Z")


class EnvelopeValidationError(ValueError):
    """The canonical envelope violates the closed development contract."""


@dataclass(frozen=True, slots=True)
class ValidatedEnvelope:
    transaction_id: str
    message_type: str
    case_id: str
    tax_year: str
    domain_operation: str
    capability: str
    request_digest: str


def _require_id(name: str, value: Any) -> str:
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise EnvelopeValidationError(f"{name} is malformed")
    return value


def _validate_timestamp(value: Any) -> None:
    if not isinstance(value, str) or _TIMESTAMP_RE.fullmatch(value) is None:
        raise EnvelopeValidationError("expires_at is malformed")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError as exc:
        raise EnvelopeValidationError("expires_at is not a real UTC timestamp") from exc


def validate_envelope(value: dict[str, Any]) -> ValidatedEnvelope:
    """Validate one already-decoded canonical development envelope."""

    if not isinstance(value, dict):
        raise EnvelopeValidationError("envelope must be an object")
    actual = frozenset(value)
    if actual != _FIELDS:
        missing = sorted(_FIELDS - actual)
        unexpected = sorted(actual - _FIELDS)
        raise EnvelopeValidationError(f"field set mismatch; missing={missing}; unexpected={unexpected}")
    if value["contract"] != CONTRACT:
        raise EnvelopeValidationError("unsupported contract version")
    message_type = value["message_type"]
    if not isinstance(message_type, str) or message_type not in MESSAGE_TYPES:
        raise EnvelopeValidationError("unsupported message type")
    transaction_id = value["transaction_id"]
    if not isinstance(transaction_id, str) or _TRANSACTION_RE.fullmatch(transaction_id) is None:
        raise EnvelopeValidationError("transaction_id must be a lowercase UUIDv4 binding")
    for name in (
        "deployment_id", "case_id", "run_id", "task_id", "manifest_id",
        "actor_instance_id", "role_id",
    ):
        _require_id(name, value[name])
    if value["scope_kind"] != "CASE_YEAR":
        raise EnvelopeValidationError("development contract permits CASE_YEAR scope only")
    year = value["tax_year"]
    if not isinstance(year, str) or _YEAR_RE.fullmatch(year) is None or not 1900 <= int(year) <= 9999:
        raise EnvelopeValidationError("tax_year is malformed")
    operation = value["domain_operation"]
    if not isinstance(operation, str) or operation not in OPERATION_CAPABILITIES:
        raise EnvelopeValidationError("unsupported domain operation")
    capability = value["capability"]
    if capability != OPERATION_CAPABILITIES[operation]:
        raise EnvelopeValidationError("operation/capability mismatch")
    if message_type in {"PREPARE_MUTATION", "COMMIT_MUTATION"} and operation not in MUTATION_OPERATIONS:
        raise EnvelopeValidationError("mutation message requires a mutation operation")
    if message_type == "READ_IDENTITY_STATE" and operation not in READ_OPERATIONS:
        raise EnvelopeValidationError("read message requires a read operation")
    epoch = value["expected_epoch"]
    if not isinstance(epoch, str) or _EPOCH_RE.fullmatch(epoch) is None:
        raise EnvelopeValidationError("expected_epoch is malformed")
    head = value["expected_head"]
    if not isinstance(head, str) or _DIGEST_RE.fullmatch(head) is None:
        raise EnvelopeValidationError("expected_head is malformed")
    references = value["authorization_references"]
    if not isinstance(references, list) or len(references) > 16:
        raise EnvelopeValidationError("authorization_references must be a bounded list")
    if any(not isinstance(item, str) or _ID_RE.fullmatch(item) is None for item in references):
        raise EnvelopeValidationError("authorization reference is malformed")
    if references != sorted(set(references)):
        raise EnvelopeValidationError("authorization references must be sorted and unique")
    _validate_timestamp(value["expires_at"])
    if value["payload"] != {}:
        raise EnvelopeValidationError("development envelope payload must be empty")
    digest = value["request_digest"]
    if not isinstance(digest, str) or _DIGEST_RE.fullmatch(digest) is None:
        raise EnvelopeValidationError("request_digest is malformed")
    body = dict(value)
    del body["request_digest"]
    expected_digest = canonical_sha256(body)
    if not hmac.compare_digest(digest, expected_digest):
        raise EnvelopeValidationError("request_digest mismatch")
    return ValidatedEnvelope(transaction_id, message_type, value["case_id"], year, operation, capability, digest)


def decode_and_validate_frame(frame: bytes) -> ValidatedEnvelope:
    try:
        value = decode_frame(frame)
    except WireFormatError as exc:
        raise EnvelopeValidationError("wire frame rejected") from exc
    return validate_envelope(value)
