import hashlib
from datetime import datetime, timezone

import pytest

from agent_lab.c09_custodian_host import CustodianError, SyntheticCustodianRuntime
from agent_lab.ipc_wire_primitives import canonical_json_bytes


KEY = b"S" * 32


def request(**changes):
    preimage = {"deployment_id": "C09-R3-SYNTHETIC", "transaction_id": "TX-1"}
    value = {
        "contract": "ai-tax-agent.c09-custodian/1.0", "operation": "AUTHENTICATE_WITNESS",
        "deployment_id": "C09-R3-SYNTHETIC", "transaction_id": "TX-1", "request_digest": "",
        "staged_receipt_digest": "sha256:" + "a" * 64,
        "witness_preimage_digest": "sha256:" + hashlib.sha256(canonical_json_bytes(preimage)).hexdigest(),
        "witness_preimage": preimage, "expected_epoch": "1", "expected_sequence": "1",
        "previous_commitment": "sha256:" + "0" * 64, "kernel_pending_head": "sha256:" + "b" * 64,
        "identity_new_head": "sha256:" + "c" * 64, "backup_generation": "1", "nonce": "N" * 32,
        "issued_at": "2026-10-24T00:00:00.000000Z", "expires_at": "2026-10-24T00:00:05.000000Z",
        "kernel_authorization_proof_digest": "sha256:" + "d" * 64,
    }
    value.update(changes)
    value["request_digest"] = "sha256:" + hashlib.sha256(canonical_json_bytes({k: v for k, v in value.items() if k != "request_digest"})).hexdigest()
    return value


def runtime(authorize=lambda value: True, receipt=lambda tx, digest: True):
    result = SyntheticCustodianRuntime(key_id="SYNTHETIC-KEY-1", synthetic_key=KEY, authorize=authorize, receipt_exists=receipt, clock=lambda: datetime(2026, 10, 24, 0, 0, 2, tzinfo=timezone.utc))
    result.start(); return result


def test_authenticate_is_deterministic_and_key_is_not_returned():
    candidate = runtime(); first = candidate.handle(request()); second = candidate.handle(request())
    assert first == second and first.outcome == "AUTHENTICATED"
    assert first.authentication and KEY.hex() not in repr(first)


def test_verify_uses_closed_operation():
    result = runtime().handle(request(operation="VERIFY_WITNESS"))
    assert result.outcome == "VERIFIED"


@pytest.mark.parametrize("change", [
    {"operation": "SIGN_ARBITRARY"}, {"contract": "unknown"}, {"witness_preimage_digest": "sha256:" + "f" * 64}, {"extra": "x"},
])
def test_unknown_operation_schema_and_preimage_substitution_fail_closed(change):
    with pytest.raises(CustodianError): runtime().handle(request(**change))


def test_authorization_receipt_and_role_substitution_fail_closed():
    with pytest.raises(CustodianError, match="authorization"): runtime(authorize=lambda value: False).handle(request())
    with pytest.raises(CustodianError, match="receipt"): runtime(receipt=lambda tx, digest: False).handle(request())


def test_changed_replay_is_denied():
    candidate = runtime(); candidate.handle(request())
    changed = request(identity_new_head="sha256:" + "e" * 64)
    with pytest.raises(CustodianError, match="replay"): candidate.handle(changed)


def test_missing_key_and_stopped_runtime_fail_closed():
    with pytest.raises(CustodianError): SyntheticCustodianRuntime(key_id="", synthetic_key=b"", authorize=lambda value: True, receipt_exists=lambda tx, digest: True)
    candidate = runtime(); candidate.stop()
    with pytest.raises(CustodianError, match="not running"): candidate.handle(request())


@pytest.mark.parametrize("times", [
    {"issued_at": "2026-10-24T00:00:00.000000Z", "expires_at": "2026-10-24T00:00:06.000000Z"},
    {"issued_at": "2026-10-23T23:59:50.000000Z", "expires_at": "2026-10-23T23:59:55.000000Z"},
    {"issued_at": "bad", "expires_at": "bad"},
])
def test_expired_overlong_and_malformed_authorization_windows_fail_closed(times):
    with pytest.raises(CustodianError): runtime().handle(request(**times))
