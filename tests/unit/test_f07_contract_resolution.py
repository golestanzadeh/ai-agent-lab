"""Offline F07 contract conformance evidence, not operational authorization."""
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path

import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization

from agent_lab.ipc_wire_primitives import canonical_json_bytes,canonical_sha256,decode_frame,encode_frame
from f07_contract_vectors import (build_vectors,pending_projection,signing_bytes,unsigned,sign,
    stable_content_digest,validate_renewed_attempt,validate_request,validate_response,validate_prepare_commit)

FIXTURE=Path(__file__).parents[1]/"fixtures"/"f07-operational-contract-v1.json"
V=json.loads(FIXTURE.read_text(encoding="utf-8"))
KEY=serialization.load_pem_public_key(V["public_key_pem"].encode())
SCOPE={"case_id":"TEST-CASE","tax_year":"2024","run_id":"TEST-RUN"}
NOW=datetime(2026,1,1,0,0,1)


def verify(request):
    validate_request(request,KEY,expected_scope=SCOPE,now=NOW)


def test_frozen_vectors_reproduce_byte_for_byte():
    assert build_vectors()==V


@pytest.mark.parametrize("vector",V["vectors"],ids=lambda v:v["name"])
def test_positive_request_and_read_vectors(vector):
    request=vector["request"];response=vector["response"]
    verify(request);validate_response(response,request)
    assert canonical_json_bytes(request).hex()==vector["request_bytes_hex"]
    assert encode_frame(request).hex()==vector["frame_hex"]
    assert decode_frame(bytes.fromhex(vector["frame_hex"]))==request
    assert canonical_json_bytes(unsigned(request,True)).hex()==vector["request_preimage_hex"]
    assert signing_bytes(request).hex()==vector["signature_preimage_hex"]
    assert pending_projection(request)==vector["pending_projection"]
    assert canonical_sha256(vector["pending_projection"])==request["kernel_proof"]["pending_row_digest"]
    assert canonical_json_bytes(response).hex()==vector["response_bytes_hex"]
    assert encode_frame(response).hex()==vector["response_frame_hex"]


def test_prepare_commit_has_distinct_digest_and_explicit_link():
    prepare=V["vectors"][0]["request"];commit=V["commit"]
    verify(commit);validate_prepare_commit(prepare,commit)
    validate_response(V["commit_response"],commit)
    assert prepare["request_digest"]!=commit["request_digest"]
    assert encode_frame(commit).hex()==V["commit_frame_hex"]
    assert signing_bytes(commit).hex()==V["commit_signature_preimage_hex"]
    assert pending_projection(commit)==V["commit_pending_projection"]
    assert encode_frame(V["commit_response"]).hex()==V["commit_response_frame_hex"]
    wrong=deepcopy(commit);wrong["prepared_request_digest"]=commit["request_digest"]
    with pytest.raises(ValueError):validate_prepare_commit(prepare,wrong)


@pytest.mark.parametrize("vector",V["negative_vectors"],ids=lambda v:v["name"])
def test_frozen_hostile_vectors_fail_closed(vector):
    frame=(bytes.fromhex(vector["header_hex"])+bytes.fromhex(vector["byte_hex"])*int(vector["count"])) if vector["kind"]=="wire-repeat" else bytes.fromhex(vector["frame_hex"])
    with pytest.raises((ValueError,InvalidSignature)):
        value=decode_frame(frame)
        if vector["kind"]=="response":validate_response(value,V["vectors"][int(vector["base"])]["request"])
        else:verify(value)


@pytest.mark.parametrize("field",["contract","transaction_id","request_digest","result"])
def test_response_digest_covers_correlation_and_result(field):
    vector=V["vectors"][1];response=deepcopy(vector["response"])
    response[field]="modified"
    with pytest.raises(ValueError):validate_response(response,vector["request"])


def test_runtime_contract_remains_separate():
    from agent_lab.ipc_envelope import validate_envelope
    with pytest.raises(ValueError):validate_envelope(V["vectors"][1]["request"])


def test_expired_proof_can_only_renew_same_stage_content_with_fresh_nonce():
    from cryptography.hazmat.primitives.asymmetric import ec
    old=V["vectors"][0]["request"];new=V["renewed_prepare"]
    with pytest.raises(ValueError):validate_request(old,KEY,expected_scope=SCOPE,now=datetime(2026,1,1,0,0,7))
    validate_request(new,KEY,expected_scope=SCOPE,now=datetime(2026,1,1,0,0,7))
    validate_renewed_attempt(old,new,{old["kernel_proof"]["nonce"]})
    assert stable_content_digest(old)==stable_content_digest(new)
    assert old["request_digest"]!=new["request_digest"]
    assert encode_frame(new).hex()==V["renewed_prepare_frame_hex"]
    with pytest.raises(ValueError):validate_renewed_attempt(old,new,{new["kernel_proof"]["nonce"]})
    changed=deepcopy(new);changed["task_id"]="TEST-ALTERED"
    changed=sign(changed,ec.derive_private_key(1,ec.SECP256R1()))
    with pytest.raises(ValueError):validate_renewed_attempt(old,changed,set())


def test_commit_renewal_preserves_first_accepted_prepare_link():
    from cryptography.hazmat.primitives.asymmetric import ec
    prepare=V["vectors"][0]["request"];commit=V["commit"]
    renewed=deepcopy(commit);renewed["expires_at"]="2026-01-01T00:00:11.000000Z"
    renewed["kernel_proof"].update(issued_at="2026-01-01T00:00:06.000000Z",not_after=renewed["expires_at"],nonce="9"*64)
    renewed=sign(renewed,ec.derive_private_key(1,ec.SECP256R1()))
    validate_request(renewed,KEY,expected_scope=SCOPE,now=datetime(2026,1,1,0,0,7))
    validate_prepare_commit(prepare,renewed)
    validate_renewed_attempt(commit,renewed,{commit["kernel_proof"]["nonce"]})
