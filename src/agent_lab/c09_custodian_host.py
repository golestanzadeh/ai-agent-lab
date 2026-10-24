"""Synthetic-only Custodian boundary; operational key providers remain a Human Gate."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Callable

from agent_lab.ipc_wire_primitives import canonical_json_bytes


class CustodianError(RuntimeError):
    pass


CONTRACT = "ai-tax-agent.c09-custodian/1.0"
OPERATIONS = frozenset({"AUTHENTICATE_WITNESS", "VERIFY_WITNESS"})
FIELDS = frozenset({
    "contract", "operation", "deployment_id", "transaction_id", "request_digest",
    "staged_receipt_digest", "witness_preimage_digest", "witness_preimage",
    "expected_epoch", "expected_sequence", "previous_commitment", "kernel_pending_head",
    "identity_new_head", "backup_generation", "nonce", "issued_at", "expires_at",
    "kernel_authorization_proof_digest",
})


@dataclass(frozen=True, slots=True)
class CustodianResult:
    outcome: str
    key_id: str
    algorithm: str
    authentication: str
    signed_record_digest: str


class SyntheticCustodianRuntime:
    """Test boundary: never exposes key bytes and grants no transaction authority."""
    def __init__(self, *, key_id: str, synthetic_key: bytes,
                 authorize: Callable[[dict], bool], receipt_exists: Callable[[str, str], bool],
                 clock: Callable[[], datetime] | None = None) -> None:
        if not key_id or not isinstance(synthetic_key, bytes) or len(synthetic_key) < 32:
            raise CustodianError("synthetic custody material is unavailable")
        self._key_id = key_id
        self._key = synthetic_key
        self._authorize = authorize
        self._receipt_exists = receipt_exists
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._replays: dict[tuple[str, str], tuple[str, CustodianResult]] = {}
        self._running = False

    def start(self) -> None:
        if self._running: raise CustodianError("Custodian already running")
        self._running = True

    def stop(self) -> None:
        self._running = False

    def handle(self, request: dict) -> CustodianResult:
        if not self._running: raise CustodianError("Custodian is not running")
        if not isinstance(request, dict) or frozenset(request) != FIELDS or request.get("contract") != CONTRACT or request.get("operation") not in OPERATIONS:
            raise CustodianError("Custodian request schema is invalid")
        try:
            issued = datetime.strptime(request["issued_at"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
            expires = datetime.strptime(request["expires_at"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        except (TypeError, ValueError) as exc:
            raise CustodianError("Custodian request time is invalid") from exc
        if expires <= issued or (expires - issued).total_seconds() > 5 or not issued <= self._clock() <= expires:
            raise CustodianError("Custodian request is expired or outside the five-second window")
        if not isinstance(request["nonce"], str) or len(request["nonce"].encode()) != 32:
            raise CustodianError("Custodian nonce is invalid")
        if not self._authorize(request): raise CustodianError("Kernel authorization denied")
        if not self._receipt_exists(request["transaction_id"], request["staged_receipt_digest"]):
            raise CustodianError("exact staged receipt is unavailable")
        if not isinstance(request["witness_preimage"], dict): raise CustodianError("witness preimage is invalid")
        preimage = canonical_json_bytes(request["witness_preimage"])
        digest = "sha256:" + hashlib.sha256(preimage).hexdigest()
        if not hmac.compare_digest(digest, request["witness_preimage_digest"]):
            raise CustodianError("witness preimage digest mismatch")
        request_digest = "sha256:" + hashlib.sha256(canonical_json_bytes({k: v for k, v in request.items() if k != "request_digest"})).hexdigest()
        if not hmac.compare_digest(request_digest, request["request_digest"]):
            raise CustodianError("Custodian request digest mismatch")
        replay_key = (request["transaction_id"], request["nonce"])
        existing = self._replays.get(replay_key)
        if existing:
            if not hmac.compare_digest(existing[0], request_digest): raise CustodianError("changed replay denied")
            return existing[1]
        authentication = hmac.new(self._key, preimage, hashlib.sha256).hexdigest()
        signed = dict(request["witness_preimage"]); signed.update(key_id=self._key_id, algorithm="HMAC-SHA-256", authentication=authentication)
        signed_digest = "sha256:" + hashlib.sha256(canonical_json_bytes(signed)).hexdigest()
        result = CustodianResult("AUTHENTICATED" if request["operation"] == "AUTHENTICATE_WITNESS" else "VERIFIED", self._key_id, "HMAC-SHA-256", authentication, signed_digest)
        self._replays[replay_key] = (request_digest, result)
        return result
