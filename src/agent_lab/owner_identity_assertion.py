"""Pinned Windows WebAuthn Owner proof verification for the existing broker.

No key creation, enrollment, approval issuance, database access or HTTP grant.
The caller must obtain the pin from accepted enrollment, reserve the challenge
in the existing Kernel and atomically consume its nonce with approval issuance.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import base64
import hashlib
import hmac
import json
import re
import sys

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils

from agent_lab.ipc_wire_primitives import canonical_json_bytes

CONTRACT = "ai-tax-agent.owner-identity-intent/1"
DOMAIN = b"AI-TAX-AGENT\0OWNER-IDENTITY-INTENT\0"
P256_ORDER = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
RP_ID = "localhost"
ORIGIN = "http://localhost:8766"
OPERATIONS = frozenset({"REGISTER_IDENTITY", "CORRECT_PERSON", "BIND_PARTY", "CORRECT_PARTY_ROLE", "BIND_FACT"})
FIELDS = frozenset("contract operation owner_id case_id tax_year subject_id input_digest deployment_id store_id task_id manifest_id run_id nonce issued_at expires_at".split())
SCOPE = FIELDS - {"contract", "nonce", "issued_at", "expires_at"}


class OwnerAssertionError(PermissionError):
    pass


def _utc(value):
    if not isinstance(value,str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z",value):
        raise OwnerAssertionError("canonical Owner intent time required")
    return datetime.strptime(value,"%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)


def intent_challenge(intent):
    if type(intent) is not dict or set(intent)!=FIELDS:
        raise OwnerAssertionError("closed Owner intent required")
    if any(type(value) is not str or not 1<=len(value.encode("utf-8"))<=256 for value in intent.values()):
        raise OwnerAssertionError("bounded Owner intent strings required")
    if intent["contract"]!=CONTRACT or intent["operation"] not in OPERATIONS:
        raise OwnerAssertionError("unsupported Owner intent")
    if not re.fullmatch(r"[0-9a-f]{64}",intent["nonce"]) or not re.fullmatch(r"sha256:[0-9a-f]{64}",intent["input_digest"]):
        raise OwnerAssertionError("canonical Owner nonce/input commitment required")
    if not re.fullmatch(r"[0-9]{4}",intent["tax_year"]) or not 1900<=int(intent["tax_year"])<=9998:
        raise OwnerAssertionError("Owner intent year required")
    if not 0<(_utc(intent["expires_at"])-_utc(intent["issued_at"])).total_seconds()<=300:
        raise OwnerAssertionError("bounded Owner approval lease required")
    try:return hashlib.sha256(DOMAIN+canonical_json_bytes(intent)).digest()
    except (ValueError,UnicodeError):raise OwnerAssertionError("invalid canonical Owner intent") from None


@dataclass(frozen=True)
class EnrolledOwnerCredential:
    """An input pin, not proof that enrollment was accepted by its constructor."""
    owner_id: str
    credential_id: bytes
    public_key_der: bytes
    previous_counter: int


@dataclass(frozen=True)
class VerifiedOwnerAssertion:
    intent_digest: str
    proof_digest: str
    nonce: str
    counter: int


def _pairs(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise OwnerAssertionError("duplicate Owner client-data field")
        result[key]=value
    return result


def verify_owner_assertion(*,intent,expected_scope,enrollment,credential_id,client_data_json,
                           authenticator_data,signature,now):
    """Verify real UV + signature against a caller-supplied ACCEPTED credential.

    Returning this value is not a single-use grant: the existing Kernel must
    verify/reserve/consume this nonce and audit it in its authoritative store.
    """
    challenge=intent_challenge(intent)
    if (type(expected_scope) is not dict or set(expected_scope)!=SCOPE or
            any(intent[name]!=value for name,value in expected_scope.items())):
        raise OwnerAssertionError("Owner intent execution scope mismatch")
    if (not isinstance(now,datetime) or now.utcoffset() is None or
            not _utc(intent["issued_at"])<=now<_utc(intent["expires_at"])):
        raise OwnerAssertionError("Owner approval expired or not yet valid")
    return verify_challenge_assertion(challenge=challenge,nonce=intent['nonce'],owner_id=intent['owner_id'],
        enrollment=enrollment,credential_id=credential_id,client_data_json=client_data_json,
        authenticator_data=authenticator_data,signature=signature)


def verify_challenge_assertion(*,challenge,nonce,owner_id,enrollment,credential_id,client_data_json,
                               authenticator_data,signature):
    """Cryptographic primitive only; caller owns closed challenge/lease validation."""
    if type(challenge) is not bytes or len(challenge)!=32:
        raise OwnerAssertionError('bounded challenge required')
    if (not isinstance(enrollment,EnrolledOwnerCredential) or enrollment.owner_id!=owner_id or
            type(enrollment.credential_id) is not bytes or not 1<=len(enrollment.credential_id)<=1024 or
            type(enrollment.public_key_der) is not bytes or not 1<=len(enrollment.public_key_der)<=512 or
            type(enrollment.previous_counter) is not int or not 0<=enrollment.previous_counter<=0xffffffff or
            type(credential_id) is not bytes or not hmac.compare_digest(credential_id,enrollment.credential_id)):
        raise OwnerAssertionError("accepted Owner credential binding required")
    if (type(client_data_json) is not bytes or not 1<=len(client_data_json)<=2048 or
            type(authenticator_data) is not bytes or len(authenticator_data)!=37 or
            type(signature) is not bytes or not 8<=len(signature)<=80):
        raise OwnerAssertionError("bounded Owner assertion required")
    try:
        client=json.loads(client_data_json.decode("utf-8"),object_pairs_hook=_pairs)
    except (ValueError,UnicodeError,RecursionError) as exc:
        raise OwnerAssertionError("invalid Owner client data") from None
    expected={"type":"webauthn.get","challenge":base64.urlsafe_b64encode(challenge).rstrip(b"=").decode(),
              "origin":ORIGIN,"crossOrigin":False}
    if type(client) is not dict or client!=expected or type(client.get("crossOrigin")) is not bool:
        raise OwnerAssertionError("Owner challenge/origin/type mismatch")
    if not hmac.compare_digest(authenticator_data[:32],hashlib.sha256(RP_ID.encode()).digest()):
        raise OwnerAssertionError("Owner relying-party mismatch")
    # This narrow profile accepts device-bound UP+UV, no extensions/attestation
    # or backup eligibility flags; no hardware/TPM attestation is inferred.
    if authenticator_data[32]!=0x05:
        raise OwnerAssertionError("device-bound Owner user verification required")
    counter=int.from_bytes(authenticator_data[33:37],"big")
    if enrollment.previous_counter and counter<=enrollment.previous_counter:
        raise OwnerAssertionError("Owner authenticator counter rollback")
    try:
        r,s=utils.decode_dss_signature(signature)
        if not (0<r<P256_ORDER and 0<s<P256_ORDER) or utils.encode_dss_signature(r,s)!=signature:
            raise ValueError("canonical P-256 signature required")
        # Native authenticators can return either S representation. Both verify,
        # but their one proof commitment must use the same strict low-S encoding.
        canonical_signature=utils.encode_dss_signature(r,min(s,P256_ORDER-s))
        public=serialization.load_der_public_key(enrollment.public_key_der)
        if not isinstance(public,ec.EllipticCurvePublicKey) or not isinstance(public.curve,ec.SECP256R1):
            raise ValueError("P-256 required")
        public.verify(canonical_signature,authenticator_data+hashlib.sha256(client_data_json).digest(),ec.ECDSA(hashes.SHA256()))
    except Exception:
        raise OwnerAssertionError("Owner assertion signature denied") from None
    intent_digest="sha256:"+challenge.hex()
    proof={"intent_digest":intent_digest,"credential_id":base64.urlsafe_b64encode(credential_id).rstrip(b"=").decode(),
           "client_data_sha256":hashlib.sha256(client_data_json).hexdigest(),
           "authenticator_data_sha256":hashlib.sha256(authenticator_data).hexdigest(),"signature_sha256":hashlib.sha256(canonical_signature).hexdigest()}
    return VerifiedOwnerAssertion(intent_digest,"sha256:"+hashlib.sha256(DOMAIN+canonical_json_bytes(proof)).hexdigest(),nonce,counter)


def probe_windows_owner_authenticator():
    """Read-only native capability query. Never creates a key or prompts."""
    if sys.platform!="win32":return {"status":"UNAVAILABLE","reason":"WINDOWS_REQUIRED"}
    import ctypes
    try:
        api=ctypes.WinDLL("webauthn.dll")
        api.WebAuthNGetApiVersionNumber.restype=ctypes.c_uint32
        version=api.WebAuthNGetApiVersionNumber()
        available=ctypes.c_int()
        query=api.WebAuthNIsUserVerifyingPlatformAuthenticatorAvailable
        query.argtypes=[ctypes.POINTER(ctypes.c_int)];query.restype=ctypes.c_long
        code=query(ctypes.byref(available)) & 0xffffffff
        return {"status":"AVAILABLE" if code==0 and available.value else "UNAVAILABLE",
                "api_version":version,"hresult":code,"enrollment_performed":False}
    except OSError as exc:
        return {"status":"UNAVAILABLE","reason":"NATIVE_API_UNAVAILABLE","winerror":exc.winerror}
