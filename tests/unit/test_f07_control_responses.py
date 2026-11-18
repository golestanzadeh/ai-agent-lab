from copy import deepcopy

import pytest

from agent_lab.ipc_operational_read import validate_response
from agent_lab.ipc_wire_primitives import canonical_sha256, decode_frame, encode_frame


def sha(number):
    return f"sha256:{number:064x}"


def exchange(message, outcome):
    scope = dict(deployment_id="TEST", transaction_id="tx:v1:00000000-0000-4000-8000-000000000001",
                 scope_kind="CASE_YEAR", case_id="TEST-CASE", tax_year="2025", run_id="RUN",
                 task_id="TASK", manifest_id="MANIFEST", actor_instance_id="ACTOR",
                 role_id="ROLE", capability="identity_create", domain_operation="REGISTER_IDENTITY")
    receipts = dict(staged_receipt_digest="", witness_preimage_digest="", signed_record_digest="")
    if outcome in ("IDENTITY_COMMITTED", "COMMITTED_FINAL"):
        receipts.update(staged_receipt_digest=sha(1), witness_preimage_digest=sha(2))
    finalization = None
    if outcome == "COMMITTED_FINAL":
        receipts["signed_record_digest"] = sha(3)
        finalization = dict(receipts, witness_object_key="witness/test.json", witness_generation="123",
                            custodian_verification_digest=sha(4), custodian_nonce="a" * 64)
    payload = deepcopy(finalization) if message == "FINALIZE_MUTATION" else {"original_request_digest": sha(5)}
    request = dict(scope, payload=payload, contract="oi0002.kernel-identity-c09/1.1",
                   message_type=message, request_digest=sha(6))
    snapshot = dict(receipts, outcome=outcome, identity_epoch="1", identity_head=sha(7),
                    identity_audit_count="3", identity_audit_head=sha(8))
    response = dict(snapshot, contract=request["contract"], message_type=message,
                    transaction_id=scope["transaction_id"], request_digest=sha(6), denial_code="", result="")
    checkpoint = dict(scope=scope, prepare_digest=sha(5), snapshot=snapshot, finalize_payload=finalization)
    return request, response, checkpoint


def validate(request, response, checkpoint):
    response = dict(response, response_digest=canonical_sha256(response))
    validate_response(decode_frame(encode_frame(response)), request, transaction_checkpoint=checkpoint)


@pytest.mark.parametrize(("message", "outcome"), [
    ("GET_TRANSACTION", "PREPARED"), ("GET_TRANSACTION", "IDENTITY_COMMITTED"),
    ("GET_TRANSACTION", "COMMITTED_FINAL"), ("GET_TRANSACTION", "ABORTED"),
    ("FINALIZE_MUTATION", "COMMITTED_FINAL"), ("ABORT_PREPARED", "ABORTED"),
])
def test_control_round_trip_requires_verified_checkpoint(message, outcome):
    request, response, checkpoint = exchange(message, outcome)
    validate(request, response, checkpoint)
    with pytest.raises(ValueError):
        validate(request, response, None)
    request["request_digest"] = sha(42)
    with pytest.raises(ValueError, match="response correlation"):
        validate(request, response, checkpoint)
    response["request_digest"] = sha(42)
    validate(request, response, checkpoint)


@pytest.mark.parametrize("field", ["identity_head", "identity_audit_head", "staged_receipt_digest",
                                  "witness_preimage_digest", "signed_record_digest"])
def test_rehashed_response_substitution(field):
    request, response, checkpoint = exchange("GET_TRANSACTION", "COMMITTED_FINAL")
    response[field] = sha(99)
    with pytest.raises(ValueError, match="checkpoint response mismatch"):
        validate(request, response, checkpoint)


@pytest.mark.parametrize("field", ["witness_generation", "witness_object_key", "custodian_verification_digest",
                                  "custodian_nonce", "signed_record_digest"])
def test_finalize_request_must_match_verified_evidence(field):
    request, response, checkpoint = exchange("FINALIZE_MUTATION", "COMMITTED_FINAL")
    request["payload"][field] = "different"
    with pytest.raises(ValueError, match="FINALIZE evidence substitution"):
        validate(request, response, checkpoint)


def test_cross_scope_wrong_prepare_and_illegal_transition():
    request, response, checkpoint = exchange("GET_TRANSACTION", "IDENTITY_COMMITTED")
    request["case_id"] = "OTHER"
    with pytest.raises(ValueError, match="checkpoint scope"):
        validate(request, response, checkpoint)
    request["case_id"] = "TEST-CASE"
    request["payload"]["original_request_digest"] = sha(99)
    with pytest.raises(ValueError, match="original PREPARE"):
        validate(request, response, checkpoint)
    request["message_type"] = response["message_type"] = "ABORT_PREPARED"
    with pytest.raises(ValueError, match="response outcome"):
        validate(request, response, checkpoint)


@pytest.mark.parametrize("message", ["FINALIZE_MUTATION", "GET_TRANSACTION", "ABORT_PREPARED", "COMMIT_MUTATION"])
def test_indeterminate_cannot_disclose_state(message):
    request, response, checkpoint = exchange(message, "NOT_FINALIZABLE")
    for name in checkpoint["snapshot"].keys() - {"outcome"}:
        response[name] = ""
    response["denial_code"] = "RECONCILIATION_REQUIRED"
    validate(request, response, None)
    response["identity_audit_count"] = "1"
    with pytest.raises(ValueError, match="disclosure"):
        validate(request, response, None)


def test_control_does_not_extend_version_10():
    request, response, _ = exchange("GET_TRANSACTION", "PREPARED")
    request["contract"] = response["contract"] = "oi0002.kernel-identity-c09/1.0"
    del response["identity_audit_count"], response["identity_audit_head"]
    with pytest.raises(ValueError, match="response outcome"):
        validate(request, response, None)
