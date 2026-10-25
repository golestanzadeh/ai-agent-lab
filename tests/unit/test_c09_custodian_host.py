import base64
import hashlib
from datetime import datetime, timezone

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from agent_lab.c09_custodian_host import CustodianError, SyntheticCustodianRuntime, sign_kernel_request
from agent_lab.ipc_wire_primitives import canonical_json_bytes

KEY = b"S" * 32
PRIVATE = ec.generate_private_key(ec.SECP256R1())
PUBLIC = PRIVATE.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
CLOCK = lambda: datetime(2026, 10, 24, 0, 0, 2, tzinfo=timezone.utc)


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def sign(request, key=PRIVATE):
    request["kernel_proof"]["signature"] = sign_kernel_request(request, key)
    request["request_digest"] = digest(canonical_json_bytes({k: v for k, v in request.items() if k != "request_digest"}))
    return request


def auth_request(**changes):
    preimage = {
        "deployment_id": "C09-R3-SYNTHETIC", "transaction_id": "TX-1",
        "epoch": "1", "sequence": "1",
        "previous_commitment": "sha256:" + "0" * 64,
        "kernel_pending_head": "sha256:" + "b" * 64,
        "identity_new_head": "sha256:" + "c" * 64,
        "backup_generation": "1",
    }
    request = {
        "contract": "ai-tax-agent.c09-custodian/1.0", "operation": "AUTHENTICATE_WITNESS",
        "deployment_id": "C09-R3-SYNTHETIC", "transaction_id": "TX-1",
        "staged_receipt_digest": "sha256:" + "a" * 64,
        "witness_preimage_digest": digest(canonical_json_bytes(preimage)),
        "witness_preimage": preimage, "expected_epoch": "1", "expected_sequence": "1",
        "previous_commitment": "sha256:" + "0" * 64, "kernel_pending_head": "sha256:" + "b" * 64,
        "identity_new_head": "sha256:" + "c" * 64, "backup_generation": "1",
        "nonce": "N" * 32, "issued_at": "2026-10-24T00:00:00.000000Z",
        "expires_at": "2026-10-24T00:00:05.000000Z",
        "kernel_proof": {"key_id": "SYNTHETIC-KERNEL", "algorithm": "ECDSA-P256-SHA256", "signature": ""},
    }
    request.update(changes)
    return sign(request)


def runtime(tmp_path, **changes):
    kwargs = dict(key_id="SYNTHETIC-KEY-1", synthetic_key=KEY,
                  kernel_public_key_pem=PUBLIC, kernel_key_id="SYNTHETIC-KERNEL",
                  replay_db_path=str(tmp_path / "replays.sqlite"),
                  authorize=lambda request: True, receipt_exists=lambda tx, digest: True, clock=CLOCK)
    kwargs.update(changes)
    candidate = SyntheticCustodianRuntime(**kwargs)
    candidate.start()
    return candidate


def test_authenticate_signed_and_durable_idempotent(tmp_path):
    req = auth_request()
    first = runtime(tmp_path).handle(req)
    assert first.outcome == "AUTHENTICATED"
    assert runtime(tmp_path).handle(req) == first
    assert KEY.hex() not in repr(first)


def make_verified_request(tmp_path):
    import hmac
    preimage = auth_request()["witness_preimage"]
    mac = hmac.new(KEY, canonical_json_bytes(preimage), hashlib.sha256).hexdigest()
    record = {"key_id": "SYNTHETIC-KEY-1", "preimage": preimage,
              "receipt_digest": "sha256:" + "a" * 64, "mac": mac}
    raw = canonical_json_bytes(record)
    req = auth_request(operation="VERIFY_WITNESS", nonce="V" * 32)
    for name in list(req):
        if name not in {"contract", "operation", "deployment_id", "transaction_id", "request_digest",
                        "nonce", "issued_at", "expires_at", "kernel_proof"}:
            del req[name]
    req.update(authenticated_record_bytes=base64.urlsafe_b64encode(raw).rstrip(b"=").decode(),
               witness_object_key="witness/v1/C09-R3-SYNTHETIC/sequence-00000000000000000001.json",
               witness_generation="123", expected_preimage_digest=digest(canonical_json_bytes(preimage)),
               expected_receipt_digest=record["receipt_digest"], expected_record_digest=digest(raw),
               expected_previous_commitment=preimage["previous_commitment"])
    sign(req)
    assert runtime(tmp_path).handle(req).outcome == "VERIFIED"
    return req


def test_verify_exact_existing_authenticated_record(tmp_path):
    assert make_verified_request(tmp_path)["operation"] == "VERIFY_WITNESS"


@pytest.mark.parametrize("field,value", [
    ("expected_record_digest", "sha256:" + "f" * 64),
    ("witness_generation", "0"),
    ("expected_receipt_digest", "sha256:" + "f" * 64),
    ("expected_previous_commitment", "sha256:" + "f" * 64),
])
def test_verify_substitution_denied(tmp_path, field, value):
    req = make_verified_request(tmp_path)
    req["nonce"] = "W" * 32
    req[field] = value
    sign(req)
    with pytest.raises(CustodianError):
        runtime(tmp_path).handle(req)


def test_forged_kernel_signature_denied(tmp_path):
    req = auth_request()
    req["kernel_proof"]["signature"] = "A" * 86
    req["request_digest"] = digest(canonical_json_bytes({k: v for k, v in req.items() if k != "request_digest"}))
    with pytest.raises(CustodianError, match="signature"):
        runtime(tmp_path).handle(req)


def test_substituted_kernel_public_key_denied(tmp_path):
    other = ec.generate_private_key(ec.SECP256R1())
    req = auth_request()
    req["kernel_proof"]["signature"] = sign_kernel_request(req, other)
    req["request_digest"] = digest(canonical_json_bytes(
        {k: v for k, v in req.items() if k != "request_digest"}))
    with pytest.raises(CustodianError, match="signature"):
        runtime(tmp_path).handle(req)


def test_changed_replay_denied_across_restart(tmp_path):
    runtime(tmp_path).handle(auth_request())
    with pytest.raises(CustodianError, match="replay"):
        runtime(tmp_path).handle(auth_request(identity_new_head="sha256:" + "e" * 64))


def test_stale_signature_denied(tmp_path):
    with pytest.raises(CustodianError, match="stale"):
        runtime(tmp_path).handle(auth_request(expires_at="2026-10-24T00:00:01.000000Z"))


def test_boolean_authorization_cannot_bypass_signature(tmp_path):
    req = auth_request()
    req["kernel_proof"]["signature"] = "bogus"
    req["request_digest"] = digest(canonical_json_bytes(
        {k: v for k, v in req.items() if k != "request_digest"}))
    with pytest.raises(CustodianError, match="signature"):
        runtime(tmp_path, authorize=lambda value: True).handle(req)


@pytest.mark.parametrize("field,top_field", [
    ("deployment_id", "deployment_id"),
    ("transaction_id", "transaction_id"),
    ("epoch", "expected_epoch"),
    ("sequence", "expected_sequence"),
    ("previous_commitment", "previous_commitment"),
    ("kernel_pending_head", "kernel_pending_head"),
    ("identity_new_head", "identity_new_head"),
    ("backup_generation", "backup_generation"),
])
def test_p1_signed_but_conflicting_preimage_denied(tmp_path, field, top_field):
    req = auth_request()
    req["witness_preimage"][field] = "DIFFERENT"
    req["witness_preimage_digest"] = digest(canonical_json_bytes(req["witness_preimage"]))
    sign(req)
    with pytest.raises(CustodianError, match="witness field substitution"):
        runtime(tmp_path).handle(req)


def test_p2_exact_replay_without_live_dependencies(tmp_path):
    req = auth_request()
    first = runtime(tmp_path).handle(req)
    calls = []
    def unavailable(*args):
        calls.append(args)
        raise RuntimeError("dependency unavailable")
    second = runtime(tmp_path, authorize=unavailable, receipt_exists=unavailable)
    assert second.handle(req) == first
    assert calls == []


def test_p2_changed_replay_rejected_before_dependencies(tmp_path):
    runtime(tmp_path).handle(auth_request())
    calls = []
    def unavailable(*args):
        calls.append(args)
        raise RuntimeError("dependency unavailable")
    changed = auth_request(identity_new_head="sha256:" + "e" * 64)
    with pytest.raises(CustodianError, match="changed replay"):
        runtime(tmp_path, authorize=unavailable, receipt_exists=unavailable).handle(changed)
    assert calls == []
