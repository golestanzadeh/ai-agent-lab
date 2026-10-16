from copy import deepcopy

import pytest

from agent_lab.ipc_envelope import CONTRACT, validate_envelope
from agent_lab.ipc_response import (
    DENIAL_CODES,
    OUTCOMES_BY_MESSAGE,
    RESPONSE_FIELDS,
    ResponseValidationError,
    decode_and_correlate_response,
    validate_response,
)
from agent_lab.ipc_wire_primitives import canonical_sha256, encode_frame


def request(message_type="PREPARE_MUTATION"):
    operation = "READ_FACTS" if message_type == "READ_IDENTITY_STATE" else "REGISTER_IDENTITY"
    capability = "identity_read" if message_type == "READ_IDENTITY_STATE" else "identity_create"
    value = {
        "contract": CONTRACT,
        "message_type": message_type,
        "transaction_id": "tx:v1:123e4567-e89b-42d3-a456-426614174000",
        "request_digest": "sha256:" + "0" * 64,
        "deployment_id": "DEPLOYMENT-SYNTHETIC",
        "scope_kind": "CASE_YEAR",
        "case_id": "CASE-SYNTHETIC",
        "tax_year": "2025",
        "run_id": "RUN-SYNTHETIC",
        "task_id": "TASK-SYNTHETIC",
        "manifest_id": "MANIFEST-SYNTHETIC",
        "actor_instance_id": "ACTOR-SYNTHETIC",
        "role_id": "IDENTITY_ADMINISTRATION_AGENT",
        "capability": capability,
        "domain_operation": operation,
        "expected_epoch": "0",
        "expected_head": "sha256:" + "0" * 64,
        "authorization_references": [],
        "expires_at": "2026-10-16T20:00:00.000000Z",
        "payload": {},
    }
    body = dict(value)
    del body["request_digest"]
    value["request_digest"] = canonical_sha256(body)
    return validate_envelope(value)


def response(req, outcome, denial_code=""):
    denied = outcome == "DENIED"
    value = {
        "contract": CONTRACT,
        "message_type": req.message_type,
        "transaction_id": req.transaction_id,
        "request_digest": req.request_digest,
        "outcome": outcome,
        "response_digest": "sha256:" + "0" * 64,
        "identity_epoch": "" if denied else "1",
        "identity_head": "" if denied else "sha256:" + "1" * 64,
        "denial_code": denial_code,
    }
    body = dict(value)
    del body["response_digest"]
    value["response_digest"] = canonical_sha256(body)
    return value


@pytest.mark.parametrize(
    ("message_type", "outcome"),
    [(message_type, outcome) for message_type, outcomes in OUTCOMES_BY_MESSAGE.items() for outcome in outcomes if outcome != "DENIED"],
)
def test_every_allowed_success_relationship_correlates(message_type, outcome):
    req = request(message_type)
    value = response(req, outcome)
    result = validate_response(value, req)
    assert result.outcome == outcome
    assert decode_and_correlate_response(encode_frame(value), req) == result


@pytest.mark.parametrize("message_type", sorted(OUTCOMES_BY_MESSAGE))
@pytest.mark.parametrize("denial_code", sorted(DENIAL_CODES))
def test_every_closed_denial_code_is_accepted_without_continuity_disclosure(message_type, denial_code):
    req = request(message_type)
    result = validate_response(response(req, "DENIED", denial_code), req)
    assert result.denial_code == denial_code
    assert result.identity_epoch == result.identity_head == ""


@pytest.mark.parametrize(
    ("message_type", "outcome"),
    [
        (message_type, outcome)
        for message_type, allowed in OUTCOMES_BY_MESSAGE.items()
        for outcome in {"PREPARED", "COMMITTED_FINAL", "ABORTED", "NOT_FINALIZABLE", "READ_OK"} - allowed
    ],
)
def test_every_unapproved_message_outcome_relationship_is_rejected(message_type, outcome):
    req = request(message_type)
    with pytest.raises(ResponseValidationError, match="unsupported outcome"):
        validate_response(response(req, outcome), req)


@pytest.mark.parametrize("field", sorted(RESPONSE_FIELDS))
def test_every_response_field_is_required(field):
    req = request()
    value = response(req, "PREPARED")
    del value[field]
    with pytest.raises(ResponseValidationError, match="field set mismatch"):
        validate_response(value, req)


def test_unexpected_and_free_form_fields_are_rejected():
    req = request()
    value = response(req, "PREPARED")
    value["message"] = "sensitive details"
    with pytest.raises(ResponseValidationError, match="unexpected"):
        validate_response(value, req)


@pytest.mark.parametrize(
    ("field", "replacement", "match"),
    [
        ("contract", "oi0002.kernel-identity-ipc/1.0", "contract"),
        ("message_type", "COMMIT_MUTATION", "message type"),
        ("transaction_id", "tx:v1:123e4567-e89b-42d3-a456-426614174001", "transaction"),
        ("request_digest", "sha256:" + "2" * 64, "request digest"),
        ("outcome", "UNKNOWN", "outcome"),
    ],
)
def test_version_and_request_correlation_substitutions_are_rejected(field, replacement, match):
    req = request()
    value = response(req, "PREPARED")
    value[field] = replacement
    with pytest.raises(ResponseValidationError, match=match):
        validate_response(value, req)


@pytest.mark.parametrize("code", ["", "DATABASE_ERROR", "user@example.test", "x" * 200])
def test_denied_response_rejects_missing_unknown_or_sensitive_free_form_codes(code):
    req = request()
    with pytest.raises(ResponseValidationError, match="closed denial code"):
        validate_response(response(req, "DENIED", code), req)


def test_success_cannot_carry_denial_code_and_denial_cannot_disclose_continuity():
    req = request()
    with pytest.raises(ResponseValidationError, match="must not carry"):
        validate_response(response(req, "PREPARED", "EXPIRED"), req)
    denied = response(req, "DENIED", "EXPIRED")
    denied["identity_epoch"] = "1"
    with pytest.raises(ResponseValidationError, match="must not disclose"):
        validate_response(denied, req)


@pytest.mark.parametrize("field", ["identity_epoch", "identity_head", "response_digest"])
def test_malformed_continuity_and_response_digest_are_rejected(field):
    req = request()
    value = response(req, "PREPARED")
    value[field] = "malformed"
    with pytest.raises(ResponseValidationError):
        validate_response(value, req)


def test_response_digest_binds_complete_correlated_response():
    req = request()
    value = response(req, "PREPARED")
    substituted = deepcopy(value)
    substituted["identity_epoch"] = "2"
    with pytest.raises(ResponseValidationError, match="response_digest mismatch"):
        validate_response(substituted, req)


def test_noncanonical_or_ambiguous_frame_is_rejected_before_correlation():
    req = request()
    payload = b'{"contract":"' + CONTRACT.encode() + b'", "outcome":"DENIED"}'
    with pytest.raises(ResponseValidationError, match="wire frame rejected"):
        decode_and_correlate_response(len(payload).to_bytes(4, "little") + payload, req)


def test_validator_is_stateless_and_has_no_operational_surface():
    import agent_lab.ipc_response as module

    forbidden = {"dispatch", "connect", "listen", "send", "commit", "restore", "mutate", "authorize", "store"}
    assert forbidden.isdisjoint(set(module.__dict__))
