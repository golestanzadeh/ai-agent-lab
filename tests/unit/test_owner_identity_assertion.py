"""Owner-proof verification vectors; ephemeral test keys, no enrollment."""
import base64
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils

from agent_lab.owner_identity_assertion import (
    CONTRACT, RP_ID, ORIGIN, SCOPE, EnrolledOwnerCredential, OwnerAssertionError,
    intent_challenge, verify_owner_assertion, P256_ORDER,
)


def vector():
    key=ec.generate_private_key(ec.SECP256R1())
    intent=dict(contract=CONTRACT,operation="CORRECT_PERSON",owner_id="TEST-OWNER",case_id="TEST-CASE",
        tax_year="2026",subject_id="TEST-PERSON",input_digest="sha256:"+"1"*64,deployment_id="TEST-DEPLOYMENT",
        store_id="TEST-STORE",task_id="TEST-TASK",manifest_id="TEST-MANIFEST",run_id="TEST-RUN",nonce="2"*64,
        issued_at="2026-11-23T10:00:00.000000Z",expires_at="2026-11-23T10:05:00.000000Z")
    client=json.dumps(dict(type="webauthn.get",challenge=base64.urlsafe_b64encode(intent_challenge(intent)).rstrip(b"=").decode(),
        origin=ORIGIN,crossOrigin=False),separators=(",",":")).encode()
    auth=hashlib.sha256(RP_ID.encode()).digest()+b"\x05"+(1).to_bytes(4,"big")
    binding=EnrolledOwnerCredential("TEST-OWNER",b"TEST-CREDENTIAL",key.public_key().public_bytes(
        serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo),0)
    arguments=dict(intent=intent,expected_scope={name:intent[name] for name in SCOPE},enrollment=binding,
        credential_id=b"TEST-CREDENTIAL",client_data_json=client,authenticator_data=auth,
        signature=key.sign(auth+hashlib.sha256(client).digest(),ec.ECDSA(hashes.SHA256())),
        now=datetime(2026,11,23,10,1,tzinfo=timezone.utc))
    return key,arguments


def test_verified_signature_is_not_an_approval_or_nonce_consumer():
    _,arguments=vector()
    result=verify_owner_assertion(**arguments)
    assert result.nonce==arguments["intent"]["nonce"] and result.counter==1
    assert result.intent_digest=="sha256:"+intent_challenge(arguments["intent"]).hex()
    assert verify_owner_assertion(**arguments)==result  # Kernel consumption is separate and mandatory.


def test_ecdsa_twin_has_one_canonical_proof_commitment():
    _,arguments=vector()
    original=verify_owner_assertion(**arguments)
    r,s=utils.decode_dss_signature(arguments["signature"])
    arguments["signature"]=utils.encode_dss_signature(r,P256_ORDER-s)
    assert verify_owner_assertion(**arguments)==original


@pytest.mark.parametrize("r,s",[(0,1),(1,0),(P256_ORDER,1),(1,P256_ORDER)])
def test_signature_scalar_boundaries_denied(r,s):
    _,arguments=vector()
    arguments["signature"]=utils.encode_dss_signature(r,s)
    with pytest.raises(OwnerAssertionError):verify_owner_assertion(**arguments)


@pytest.mark.parametrize("field",sorted(SCOPE))
def test_scope_substitution_denied(field):
    _,arguments=vector()
    arguments["expected_scope"]={**arguments["expected_scope"],field:"OTHER"}
    with pytest.raises(OwnerAssertionError):verify_owner_assertion(**arguments)


@pytest.mark.parametrize("attack",["signature","credential","key","expired","future","nonce","input","no_uv","no_up","backup","extension","rp","counter","duplicate","origin","cross_origin","bool_zero","size","type"])
def test_adversarial_assertions_denied(attack):
    key,a=vector()
    if attack=="signature":a["signature"]=b"invalid signature"
    if attack=="credential":a["credential_id"]=b"OTHER"
    if attack=="key":
        other=ec.generate_private_key(ec.SECP256R1()).public_key().public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)
        a["enrollment"]=replace(a["enrollment"],public_key_der=other)
    if attack=="expired":a["now"]=datetime(2026,11,23,10,5,tzinfo=timezone.utc)
    if attack=="future":a["now"]=datetime(2026,11,23,9,59,tzinfo=timezone.utc)
    if attack in {"nonce","input"}:
        field="nonce" if attack=="nonce" else "input_digest"
        a["intent"]={**a["intent"],field:("3"*64 if field=="nonce" else "sha256:"+"3"*64)}
        a["expected_scope"]={name:a["intent"][name] for name in SCOPE}
    if attack in {"no_uv","no_up","backup","extension"}:
        flags={"no_uv":1,"no_up":4,"backup":13,"extension":133}[attack]
        a["authenticator_data"]=a["authenticator_data"][:32]+bytes([flags])+a["authenticator_data"][33:]
        a["signature"]=key.sign(a["authenticator_data"]+hashlib.sha256(a["client_data_json"]).digest(),ec.ECDSA(hashes.SHA256()))
    if attack=="rp":a["authenticator_data"]=b"x"*32+a["authenticator_data"][32:]
    if attack=="counter":a["enrollment"]=replace(a["enrollment"],previous_counter=1)
    if attack=="duplicate":a["client_data_json"]=a["client_data_json"][:-1]+b',"origin":"http://localhost:8766"}'
    if attack in {"origin","cross_origin","bool_zero","type"}:
        data=json.loads(a["client_data_json"])
        field,value={"origin":("origin","https://hostile.invalid"),"cross_origin":("crossOrigin",True),
                     "bool_zero":("crossOrigin",0),"type":("type","webauthn.create")}[attack]
        data[field]=value;a["client_data_json"]=json.dumps(data).encode()
        a["signature"]=key.sign(a["authenticator_data"]+hashlib.sha256(a["client_data_json"]).digest(),ec.ECDSA(hashes.SHA256()))
    if attack=="size":a["authenticator_data"]+=b"x"
    with pytest.raises(OwnerAssertionError):verify_owner_assertion(**a)
