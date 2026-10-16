"""Stateless response correlation for the non-operational IPC profile.

No response validated here is authoritative.  This module performs no I/O,
authentication, authorization, dispatch, persistence, mutation, or finality.
"""

from __future__ import annotations

import hmac
import re
from dataclasses import dataclass
from typing import Any

from agent_lab.ipc_envelope import CONTRACT, EnvelopeValidationError, ValidatedEnvelope
from agent_lab.ipc_wire_primitives import WireFormatError, canonical_sha256, decode_frame


RESPONSE_FIELDS = frozenset(
    {
        "contract", "message_type", "transaction_id", "request_digest",
        "outcome", "response_digest", "identity_epoch", "identity_head",
        "denial_code",
    }
)
OUTCOMES_BY_MESSAGE = {
    "PREPARE_MUTATION": frozenset({"PREPARED", "DENIED"}),
    "COMMIT_MUTATION": frozenset({"COMMITTED_FINAL", "NOT_FINALIZABLE", "DENIED"}),
    "GET_TRANSACTION": frozenset({"PREPARED", "COMMITTED_FINAL", "ABORTED", "NOT_FINALIZABLE", "DENIED"}),
    "ABORT_PREPARED": frozenset({"ABORTED", "DENIED"}),
    "READ_IDENTITY_STATE": frozenset({"READ_OK", "DENIED"}),
}
DENIAL_CODES = frozenset(
    {
        "AUTHORIZATION_DENIED",
        "SCOPE_DENIED",
        "TRANSACTION_CONFLICT",
        "REQUEST_INVALID",
        "CONTINUITY_CONFLICT",
        "EXPIRED",
        "UNSUPPORTED",
        "TEMPORARY_FAILURE",
    }
)
_DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
_EPOCH_RE = re.compile(r"0|[1-9][0-9]{0,19}\Z")


class ResponseValidationError(ValueError):
    """A response is malformed, ambiguous, or not correlated to its request."""


@dataclass(frozen=True, slots=True)
class CorrelatedResponse:
    transaction_id: str
    request_digest: str
    message_type: str
    outcome: str
    identity_epoch: str
    identity_head: str
    denial_code: str
    response_digest: str


def validate_response(value: dict[str, Any], request: ValidatedEnvelope) -> CorrelatedResponse:
    if not isinstance(value, dict):
        raise ResponseValidationError("response must be an object")
    if not isinstance(request, ValidatedEnvelope):
        raise ResponseValidationError("request must be a validated envelope")
    actual = frozenset(value)
    if actual != RESPONSE_FIELDS:
        missing = sorted(RESPONSE_FIELDS - actual)
        unexpected = sorted(actual - RESPONSE_FIELDS)
        raise ResponseValidationError(f"field set mismatch; missing={missing}; unexpected={unexpected}")
    if value["contract"] != CONTRACT:
        raise ResponseValidationError("unsupported response contract")
    if value["message_type"] != request.message_type:
        raise ResponseValidationError("message type correlation mismatch")
    if value["transaction_id"] != request.transaction_id:
        raise ResponseValidationError("transaction correlation mismatch")
    if value["request_digest"] != request.request_digest:
        raise ResponseValidationError("request digest correlation mismatch")
    outcome = value["outcome"]
    if not isinstance(outcome, str) or outcome not in OUTCOMES_BY_MESSAGE[request.message_type]:
        raise ResponseValidationError("unsupported outcome for request message")
    denial_code = value["denial_code"]
    if outcome == "DENIED":
        if not isinstance(denial_code, str) or denial_code not in DENIAL_CODES:
            raise ResponseValidationError("DENIED requires a closed denial code")
        if value["identity_epoch"] != "" or value["identity_head"] != "":
            raise ResponseValidationError("denial must not disclose continuity state")
    else:
        if denial_code != "":
            raise ResponseValidationError("successful outcome must not carry a denial code")
        epoch = value["identity_epoch"]
        head = value["identity_head"]
        if not isinstance(epoch, str) or _EPOCH_RE.fullmatch(epoch) is None:
            raise ResponseValidationError("identity_epoch is malformed")
        if not isinstance(head, str) or _DIGEST_RE.fullmatch(head) is None:
            raise ResponseValidationError("identity_head is malformed")
    response_digest = value["response_digest"]
    if not isinstance(response_digest, str) or _DIGEST_RE.fullmatch(response_digest) is None:
        raise ResponseValidationError("response_digest is malformed")
    body = dict(value)
    del body["response_digest"]
    expected = canonical_sha256(body)
    if not hmac.compare_digest(response_digest, expected):
        raise ResponseValidationError("response_digest mismatch")
    return CorrelatedResponse(
        request.transaction_id,
        request.request_digest,
        request.message_type,
        outcome,
        value["identity_epoch"],
        value["identity_head"],
        denial_code,
        response_digest,
    )


def decode_and_correlate_response(frame: bytes, request: ValidatedEnvelope) -> CorrelatedResponse:
    try:
        value = decode_frame(frame)
    except WireFormatError as exc:
        raise ResponseValidationError("wire frame rejected") from exc
    try:
        return validate_response(value, request)
    except EnvelopeValidationError as exc:  # defensive boundary for future envelope evolution
        raise ResponseValidationError("request envelope rejected") from exc
