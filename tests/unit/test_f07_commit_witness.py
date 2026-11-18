from copy import deepcopy
from datetime import datetime

import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from agent_lab.f07_commit_witness import commit_witness_material, slot_projection
from agent_lab.identity_logical_continuity import H, sign_kernel_proof
from agent_lab.ipc_operational_read import read_projection, validate_request
from f07_contract_vectors import build_vectors


def sha(value):
    return "sha256:" + value * 64


KEY = ec.derive_private_key(1, ec.SECP256R1())
SCOPE_FIELDS = "deployment_id case_id tax_year run_id task_id manifest_id actor_instance_id role_id".split()


def candidate():
    request = deepcopy(build_vectors()["commit"])
    request["contract"] = "oi0002.kernel-identity-c09/1.1"
    request["deployment_id"] = "TEST-DEPLOYMENT"
    proof = request["kernel_proof"]
    proof["kernel_projection"] = dict(witnessed_audit_count="3", witnessed_audit_head=sha("a"), recovery_request_digest="")
    projection = read_projection(request)
    projection.update(projected_epoch=str(int(request["expected_epoch"]) + 1),
                      projected_head=sha("b"), kernel_pending_head=sha("c"))
    projection["mutation_witness_slot"] = slot_projection(
        request, previous_epoch="2", previous_sequence="9", previous_record=sha("d"), backup_generation="4")
    proof["kernel_projection"] = projection
    return resign(request)


def resign(request):
    request["kernel_proof"]["pending_row_digest"] = H(request["kernel_proof"]["kernel_projection"])
    return sign_kernel_proof(request, KEY)


def verify(request, *, opt_in=True):
    proof = request["kernel_proof"]
    return validate_request(request, KEY.public_key(),
                            expected_scope={k: request[k] for k in SCOPE_FIELDS},
                            now=datetime.strptime(proof["issued_at"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                            expected_key_id=proof["key_id"], expected_contract=request["contract"],
                            mutation_commit_contract=opt_in)


def material(request):
    return commit_witness_material(request, store_id="TEST-STORE", backup_generation="4",
                                   audit_count="4", audit_head=sha("e"), result_digest=sha("f"))


def test_frozen_pre_response_golden_vector():
    request = candidate()
    verify(request)
    slot = request["kernel_proof"]["kernel_projection"]["mutation_witness_slot"]
    receipt, unsigned = material(request)
    assert slot["object_key"] == "witness/v1/TEST-DEPLOYMENT/epoch-00000000000000000002/sequence-00000000000000000010.json"
    assert slot["operation_id"] == "MUTATION:AE13717B72CA2F336DA4FEB6E586A6FDEA0A19D79F4BF57AC153C02F1E4A4EAD"
    assert receipt["witness_preimage_digest"] == "sha256:b385f42d206c2626c4a3511068bfa1df44763acb12f0596761af6ced792b3cb2"
    assert H(receipt) == "sha256:370e6ece555e1caa733f437922af37f8b5a780274217eef48c835576998fed20"
    assert b"response_digest" not in unsigned
    with pytest.raises(ValueError, match="operation disabled"):
        verify(request, opt_in=False)


@pytest.mark.parametrize("field,value", [
    ("epoch", "3"), ("sequence", "11"), ("backup_generation", "04"),
    ("previous_record", sha("0")), ("operation_id", "MUTATION:OTHER"),
    ("object_key", "another/key"), ("profile", "identity-mutation-witness-slot/2"),
])
def test_even_valid_signature_cannot_authorize_noncanonical_slot(field, value):
    request = candidate()
    request["kernel_proof"]["kernel_projection"]["mutation_witness_slot"][field] = value
    with pytest.raises(ValueError):
        verify(resign(request))


def test_rebinding_slot_requires_new_signature_and_durable_slot_comparison():
    from cryptography.exceptions import InvalidSignature
    from agent_lab.ipc_operational_read import unsigned
    request = candidate()
    proof = request["kernel_proof"]
    slot = proof["kernel_projection"]["mutation_witness_slot"]
    proof["kernel_projection"]["mutation_witness_slot"] = slot_projection(
        request, previous_epoch="2", previous_sequence="10", previous_record=sha("e"), backup_generation="4")
    proof["pending_row_digest"] = H(proof["kernel_projection"])
    request["request_digest"] = H(unsigned(request, True))
    with pytest.raises(InvalidSignature):
        verify(request)
    assert proof["kernel_projection"]["mutation_witness_slot"] != slot


def test_renewed_proof_preserves_slot_and_unsigned_bytes():
    original = candidate()
    renewed = deepcopy(original)
    renewed["kernel_proof"]["nonce"] = "b" * 64
    renewed = resign(renewed)
    verify(renewed)
    assert renewed["request_digest"] != original["request_digest"]
    assert material(renewed)[1] == material(original)[1]
    # The durable receipt remains the one from the first successful COMMIT.
    assert material(renewed)[0]["request_digest"] != material(original)[0]["request_digest"]


def test_commit_must_bind_local_generation_and_advancing_audit_cut():
    request = candidate()
    for generation, count in (("5", "4"), ("4", "3")):
        with pytest.raises(ValueError):
            commit_witness_material(request, store_id="STORE", backup_generation=generation,
                                    audit_count=count, audit_head=sha("e"), result_digest=sha("f"))


def recovery_exchange():
    from agent_lab.c09_custodian_operational import pack
    from agent_lab.identity_logical_continuity import successor_preimage
    from agent_lab.ipc_operational_read import CONTROL_SCOPE, SNAPSHOT_FIELDS
    commit = candidate()
    stable = {key: item for key, item in commit.items() if key not in {
        "message_type", "request_digest", "kernel_proof", "expires_at", "prepared_request_digest"}}
    successor = successor_preimage(
        deployment_id=commit["deployment_id"], prior_epoch=commit["expected_epoch"], prior_head=commit["expected_head"],
        case_id=commit["case_id"], tax_year=commit["tax_year"], transaction_id=commit["transaction_id"],
        domain_operation=commit["domain_operation"], mutation_content_digest=H(stable), domain_result_digest=sha("f"))
    commit["kernel_proof"]["kernel_projection"]["projected_head"] = H(successor)
    commit = resign(commit)
    verify(commit)
    receipt, unsigned = material(commit)
    request = dict(commit, message_type="GET_TRANSACTION", request_digest=sha("9"),
                   payload={"original_request_digest": commit["prepared_request_digest"]})
    response = {field: request[field] for field in ("contract", "message_type", "transaction_id", "request_digest")}
    response.update(outcome="IDENTITY_COMMITTED", identity_epoch=receipt["logical_epoch"],
                    identity_head=receipt["logical_head"], identity_audit_count=receipt["audit_cut_count"],
                    identity_audit_head=receipt["audit_cut_head"], staged_receipt_digest=H(receipt),
                    witness_preimage_digest=receipt["witness_preimage_digest"], signed_record_digest="", denial_code="",
                    result=dict(profile="identity-mutation-commit-material/1", receipt=receipt, unsigned_record_bytes=pack(unsigned)))
    checkpoint = dict(scope={key: commit[key] for key in CONTROL_SCOPE}, prepare_digest=commit["prepared_request_digest"],
                      snapshot={key: response[key] for key in SNAPSHOT_FIELDS}, finalize_payload=None)
    context = dict(original_commit=commit, store_id="TEST-STORE", backup_generation="4")
    return request, response, checkpoint, context, unsigned


def test_lost_commit_response_recovers_exact_custodian_input():
    from agent_lab.c09_custodian_operational import unpack
    from agent_lab.ipc_operational_read import validate_response
    from agent_lab.ipc_wire_primitives import canonical_json_bytes, decode_frame, encode_frame

    request, response, checkpoint, context, unsigned = recovery_exchange()
    framed = decode_frame(encode_frame(dict(response, response_digest=H(response))))
    validate_response(framed, request, transaction_checkpoint=checkpoint, mutation_material_context=context)
    assert unpack(framed["result"]["unsigned_record_bytes"], 4096) == unsigned
    assert H(framed["result"]["receipt"]) == framed["staged_receipt_digest"]
    assert canonical_json_bytes(framed["result"]["receipt"]) == canonical_json_bytes(material(context["original_commit"])[0])
    with pytest.raises(ValueError, match="nonread result"):
        validate_response(framed, request, transaction_checkpoint=checkpoint)
    commit = context["original_commit"]
    response.update(message_type=commit["message_type"], request_digest=commit["request_digest"])
    validate_response(dict(response, response_digest=H(response)), commit, mutation_material_context=context)


@pytest.mark.parametrize("field,value", [
    ("store_id", "OTHER-STORE"), ("domain_result_digest", sha("0")),
    ("request_digest", sha("1")), ("witness_slot", {}), ("audit_cut_count", "5"),
])
def test_receipt_substitution_rejected_even_with_rehashed_envelope(field, value):
    from agent_lab.ipc_operational_read import validate_response
    request, response, checkpoint, context, _ = recovery_exchange()
    response["result"]["receipt"][field] = value
    response["staged_receipt_digest"] = H(response["result"]["receipt"])
    checkpoint["snapshot"]["staged_receipt_digest"] = response["staged_receipt_digest"]
    with pytest.raises(ValueError, match="material binding"):
        validate_response(dict(response, response_digest=H(response)), request, transaction_checkpoint=checkpoint,
                          mutation_material_context=context)


def test_noncanonical_unsigned_material_rejected():
    from agent_lab.ipc_operational_read import validate_response
    request, response, checkpoint, context, _ = recovery_exchange()
    response["result"]["unsigned_record_bytes"] += "="
    with pytest.raises(ValueError, match="material binding"):
        validate_response(dict(response, response_digest=H(response)), request, transaction_checkpoint=checkpoint,
                          mutation_material_context=context)
