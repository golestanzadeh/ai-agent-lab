from copy import deepcopy

import pytest

from agent_lab.ipc_envelope import (
    CONTRACT,
    EnvelopeValidationError,
    decode_and_validate_frame,
    validate_envelope,
)
from agent_lab.ipc_wire_primitives import canonical_sha256, encode_frame


def envelope(**overrides):
    value = {
        "contract": CONTRACT,
        "message_type": "PREPARE_MUTATION",
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
        "capability": "identity_create",
        "domain_operation": "REGISTER_IDENTITY",
        "expected_epoch": "0",
        "expected_head": "sha256:" + "0" * 64,
        "authorization_references": ["AUTH-1", "AUTH-2"],
        "expires_at": "2026-10-14T20:00:00.000000Z",
        "payload": {},
    }
    value.update(overrides)
    body = dict(value)
    del body["request_digest"]
    value["request_digest"] = canonical_sha256(body)
    return value


def test_exact_canonical_envelope_validates_from_object_and_frame():
    value = envelope()
    result = validate_envelope(value)
    assert result.transaction_id == value["transaction_id"]
    assert result.domain_operation == "REGISTER_IDENTITY"
    assert decode_and_validate_frame(encode_frame(value)) == result


@pytest.mark.parametrize("field", sorted(set(envelope()) - {"request_digest"}))
def test_every_required_field_is_required(field):
    value = envelope()
    del value[field]
    with pytest.raises(EnvelopeValidationError, match="field set mismatch"):
        validate_envelope(value)


def test_request_digest_is_required():
    value = envelope()
    del value["request_digest"]
    with pytest.raises(EnvelopeValidationError, match="field set mismatch"):
        validate_envelope(value)


def test_unexpected_field_is_rejected():
    value = envelope(unapproved=True)
    with pytest.raises(EnvelopeValidationError, match="unexpected"):
        validate_envelope(value)


@pytest.mark.parametrize("contract", ["oi0002.kernel-identity-ipc/1.0", "oi0002.kernel-identity-ipc-dev/2.0", ""])
def test_unknown_or_operational_contract_versions_are_rejected(contract):
    with pytest.raises(EnvelopeValidationError, match="unsupported contract"):
        validate_envelope(envelope(contract=contract))


@pytest.mark.parametrize("message_type", ["PREPARE_BACKUP", "COMMIT_RESTORE", "PING", ""])
def test_operational_or_unknown_message_types_are_rejected(message_type):
    with pytest.raises(EnvelopeValidationError, match="message type"):
        validate_envelope(envelope(message_type=message_type))


@pytest.mark.parametrize(
    ("message_type", "operation", "capability"),
    [
        ("READ_IDENTITY_STATE", "READ_CASE_IDENTITY", "identity_read"),
        ("READ_IDENTITY_STATE", "LIST_PARTIES", "identity_read"),
        ("READ_IDENTITY_STATE", "READ_FACTS", "identity_read"),
        ("COMMIT_MUTATION", "UPDATE_IDENTITY_STATUS", "identity_status_transition"),
        ("GET_TRANSACTION", "BIND_PARTY", "case_party_bind"),
        ("ABORT_PREPARED", "BIND_FACT", "subject_fact_bind"),
    ],
)
def test_closed_supported_message_operation_capability_combinations(message_type, operation, capability):
    assert validate_envelope(envelope(message_type=message_type, domain_operation=operation, capability=capability))


@pytest.mark.parametrize(
    "changes",
    [
        {"scope_kind": "DEPLOYMENT_STORE", "case_id": "*", "tax_year": "*"},
        {"capability": "identity_read"},
        {"domain_operation": "RESTORE_IDENTITY_STORE"},
        {"message_type": "READ_IDENTITY_STATE", "domain_operation": "REGISTER_IDENTITY"},
        {"message_type": "PREPARE_MUTATION", "domain_operation": "READ_FACTS", "capability": "identity_read"},
        {"payload": {"identity_id": "SECRET"}},
        {"authorization_references": ["AUTH-2", "AUTH-1"]},
        {"authorization_references": ["AUTH-1", "AUTH-1"]},
        {"expected_epoch": "01"},
        {"tax_year": "25"},
    ],
)
def test_operational_scope_authority_payload_and_malformed_values_fail_closed(changes):
    with pytest.raises(EnvelopeValidationError):
        validate_envelope(envelope(**changes))


def test_digest_binds_every_field_and_substitution_is_rejected():
    value = envelope()
    substituted = deepcopy(value)
    substituted["task_id"] = "TASK-OTHER"
    with pytest.raises(EnvelopeValidationError, match="digest mismatch"):
        validate_envelope(substituted)


@pytest.mark.parametrize(
    "changes",
    [
        {"transaction_id": "tx:v1:123e4567-e89b-12d3-a456-426614174000"},
        {"expected_head": "SHA256:" + "0" * 64},
        {"expires_at": "2026-10-14T20:00:00Z"},
        {"expires_at": "2026-02-30T20:00:00.000000Z"},
        {"case_id": ""},
    ],
)
def test_malformed_identifiers_digest_and_timestamp_are_rejected(changes):
    with pytest.raises(EnvelopeValidationError):
        validate_envelope(envelope(**changes))


def test_noncanonical_frame_is_rejected_before_schema_validation():
    payload = b'{"contract":"' + CONTRACT.encode() + b'", "message_type":"PING"}'
    frame = len(payload).to_bytes(4, "little") + payload
    with pytest.raises(EnvelopeValidationError, match="wire frame rejected"):
        decode_and_validate_frame(frame)


def test_validator_exposes_no_dispatch_or_operational_surface():
    import agent_lab.ipc_envelope as module

    forbidden = {"dispatch", "connect", "listen", "send", "commit", "restore", "mutate", "authorize"}
    assert forbidden.isdisjoint(set(module.__dict__))
