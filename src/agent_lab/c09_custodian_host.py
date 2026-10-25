"""Synthetic-only Custodian: signed Kernel proof and exact authenticated witness verification.

This module does not install services, access GCS, or grant operational authority.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils

from agent_lab.ipc_wire_primitives import canonical_json_bytes

CONTRACT = "ai-tax-agent.c09-custodian/1.0"
PROOF_DOMAIN = b"AI-TAX-AGENT\x00C09-KERNEL-PROOF\x00"
OPERATIONS = frozenset({"AUTHENTICATE_WITNESS", "VERIFY_WITNESS"})
BASE = frozenset({"contract", "operation", "deployment_id", "transaction_id",
                  "request_digest", "nonce", "issued_at", "expires_at", "kernel_proof"})
AUTH = BASE | frozenset({"staged_receipt_digest", "witness_preimage_digest",
                         "witness_preimage", "expected_epoch", "expected_sequence",
                         "previous_commitment", "kernel_pending_head",
                         "identity_new_head", "backup_generation"})
VERIFY = BASE | frozenset({"authenticated_record_bytes", "witness_object_key",
                           "witness_generation", "expected_preimage_digest",
                           "expected_receipt_digest", "expected_record_digest",
                           "expected_previous_commitment"})
PROOF_FIELDS = frozenset({"key_id", "algorithm", "signature"})
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
GENERATION = re.compile(r"[1-9][0-9]*\Z")


class CustodianError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class CustodianResult:
    outcome: str
    key_id: str
    algorithm: str
    authentication: str
    signed_record_digest: str


def _digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _canonical_load(raw: bytes) -> dict:
    if not isinstance(raw, bytes) or not raw or len(raw) > 65532 or raw.startswith(b"\xef\xbb\xbf"):
        raise CustodianError("invalid authenticated record bytes")
    try:
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("duplicate key")
                result[key] = value
            return result
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique)
        if not isinstance(value, dict) or canonical_json_bytes(value) != raw:
            raise ValueError("noncanonical record")
        return value
    except (ValueError, UnicodeError, TypeError) as exc:
        raise CustodianError("invalid canonical authenticated record") from exc


def sign_kernel_request(request: dict, private_key: ec.EllipticCurvePrivateKey) -> str:
    """Synthetic test helper; production private keys must never enter Custodian."""
    if not isinstance(private_key.curve, ec.SECP256R1):
        raise ValueError("P-256 required")
    unsigned = dict(request)
    unsigned["kernel_proof"] = {k: v for k, v in request["kernel_proof"].items() if k != "signature"}
    unsigned.pop("request_digest", None)
    signature = private_key.sign(PROOF_DOMAIN + canonical_json_bytes(unsigned), ec.ECDSA(hashes.SHA256()))
    r, s = utils.decode_dss_signature(signature)
    return base64.urlsafe_b64encode(r.to_bytes(32, "big") + s.to_bytes(32, "big")).rstrip(b"=").decode("ascii")


class SyntheticCustodianRuntime:
    """Fail-closed synthetic boundary; replay reservations are durable SQLite rows."""

    def __init__(self, *, key_id: str, synthetic_key: bytes,
                 kernel_public_key_pem: bytes, kernel_key_id: str,
                 replay_db_path: str, authorize: Callable[[dict], bool],
                 receipt_exists: Callable[[str, str], bool],
                 clock: Callable[[], datetime] | None = None) -> None:
        if not key_id or not isinstance(synthetic_key, bytes) or len(synthetic_key) < 32:
            raise CustodianError("synthetic custody material is unavailable")
        if not kernel_key_id or not replay_db_path:
            raise CustodianError("pinned Kernel identity and durable replay store required")
        try:
            key = serialization.load_pem_public_key(kernel_public_key_pem)
            if not isinstance(key, ec.EllipticCurvePublicKey) or not isinstance(key.curve, ec.SECP256R1):
                raise ValueError("pinned P-256 key required")
        except (ValueError, TypeError) as exc:
            raise CustodianError("invalid pinned Kernel public key") from exc
        self._public_key = key
        self._kernel_key_id = kernel_key_id
        self._key_id = key_id
        self._key = synthetic_key
        self._authorize = authorize
        self._receipt_exists = receipt_exists
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._db = sqlite3.connect(replay_db_path, isolation_level=None, timeout=5)
        self._db.execute("PRAGMA synchronous=FULL")
        self._db.execute("CREATE TABLE IF NOT EXISTS custodian_replays (deployment TEXT NOT NULL, nonce TEXT NOT NULL, request_digest TEXT NOT NULL, result_json TEXT NOT NULL, PRIMARY KEY(deployment, nonce))")
        self._running = False

    def start(self) -> None:
        if self._running:
            raise CustodianError("Custodian already running")
        self._running = True

    def stop(self) -> None:
        self._running = False

    def handle(self, request: dict) -> CustodianResult:
        if not self._running:
            raise CustodianError("Custodian is not running")
        if not isinstance(request, dict) or request.get("contract") != CONTRACT:
            raise CustodianError("invalid Custodian contract")
        operation = request.get("operation")
        fields = AUTH if operation == "AUTHENTICATE_WITNESS" else VERIFY if operation == "VERIFY_WITNESS" else None
        if fields is None or frozenset(request) != fields:
            raise CustodianError("Custodian operation schema is invalid")
        proof = request["kernel_proof"]
        if not isinstance(proof, dict) or frozenset(proof) != PROOF_FIELDS:
            raise CustodianError("Kernel proof schema is invalid")
        if proof["key_id"] != self._kernel_key_id or proof["algorithm"] != "ECDSA-P256-SHA256":
            raise CustodianError("unpinned Kernel identity")
        try:
            issued = datetime.strptime(request["issued_at"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
            expires = datetime.strptime(request["expires_at"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        except (TypeError, ValueError) as exc:
            raise CustodianError("invalid authorization time") from exc
        if expires <= issued or (expires - issued).total_seconds() > 5 or not issued <= self._clock() <= expires:
            raise CustodianError("stale or expired Kernel proof")
        if not isinstance(request["nonce"], str) or len(request["nonce"].encode("utf-8")) != 32:
            raise CustodianError("invalid nonce")
        unsigned = dict(request)
        unsigned.pop("request_digest")
        if request["request_digest"] != _digest(canonical_json_bytes(unsigned)):
            raise CustodianError("request digest mismatch")
        try:
            signature_text = proof["signature"]
            signature = base64.urlsafe_b64decode(signature_text + "=" * (-len(signature_text) % 4))
            if len(signature) != 64 or base64.urlsafe_b64encode(signature).rstrip(b"=").decode() != signature_text:
                raise ValueError("invalid signature encoding")
            r, s = int.from_bytes(signature[:32], "big"), int.from_bytes(signature[32:], "big")
            unsigned["kernel_proof"] = {k: v for k, v in proof.items() if k != "signature"}
            self._public_key.verify(utils.encode_dss_signature(r, s), PROOF_DOMAIN + canonical_json_bytes(unsigned), ec.ECDSA(hashes.SHA256()))
        except (InvalidSignature, ValueError, TypeError) as exc:
            raise CustodianError("invalid pinned Kernel signature") from exc
        # Reserve/check the nonce before any external authorization or receipt lookup.
        # An exact, signed retry returns the committed result without dependencies.
        self._db.execute("BEGIN IMMEDIATE")
        try:
            row = self._db.execute("SELECT request_digest,result_json FROM custodian_replays WHERE deployment=? AND nonce=?",
                                   (request["deployment_id"], request["nonce"])).fetchone()
            if row:
                if row[0] != request["request_digest"]:
                    raise CustodianError("changed replay denied")
                previous = CustodianResult(**json.loads(row[1]))
                self._db.execute("COMMIT")
                return previous
            if not self._authorize(request):
                raise CustodianError("Kernel authorization denied")
            result = self._authenticate(request) if operation == "AUTHENTICATE_WITNESS" else self._verify(request)
            self._db.execute("INSERT INTO custodian_replays VALUES (?,?,?,?)",
                             (request["deployment_id"], request["nonce"], request["request_digest"],
                              json.dumps({k: getattr(result, k) for k in result.__slots__})))
            self._db.execute("COMMIT")
            return result
        except Exception:
            self._db.execute("ROLLBACK")
            raise

    def _authenticate(self, request: dict) -> CustodianResult:
        preimage = request["witness_preimage"]
        if not isinstance(preimage, dict) or _digest(canonical_json_bytes(preimage)) != request["witness_preimage_digest"]:
            raise CustodianError("witness preimage mismatch")
        if not self._receipt_exists(request["transaction_id"], request["staged_receipt_digest"]):
            raise CustodianError("missing staged receipt")
        bindings = {
            "deployment_id": "deployment_id",
            "transaction_id": "transaction_id",
            "epoch": "expected_epoch",
            "sequence": "expected_sequence",
            "previous_commitment": "previous_commitment",
            "kernel_pending_head": "kernel_pending_head",
            "identity_new_head": "identity_new_head",
            "backup_generation": "backup_generation",
        }
        for preimage_field, request_field in bindings.items():
            if preimage.get(preimage_field) != request[request_field]:
                raise CustodianError("witness field substitution: " + preimage_field)
        mac = hmac.new(self._key, canonical_json_bytes(preimage), hashlib.sha256).hexdigest()
        record = {"key_id": self._key_id, "preimage": preimage, "receipt_digest": request["staged_receipt_digest"], "mac": mac}
        return CustodianResult("AUTHENTICATED", self._key_id, "HMAC-SHA256", mac, _digest(canonical_json_bytes(record)))

    def _verify(self, request: dict) -> CustodianResult:
        try:
            raw = base64.urlsafe_b64decode(request["authenticated_record_bytes"] + "=" * (-len(request["authenticated_record_bytes"]) % 4))
            if base64.urlsafe_b64encode(raw).rstrip(b"=").decode() != request["authenticated_record_bytes"]:
                raise ValueError("noncanonical base64")
        except (ValueError, TypeError) as exc:
            raise CustodianError("invalid witness record encoding") from exc
        record = _canonical_load(raw)
        if frozenset(record) != {"key_id", "preimage", "receipt_digest", "mac"} or record["key_id"] != self._key_id:
            raise CustodianError("wrong authenticated record schema or key")
        if not GENERATION.fullmatch(str(request["witness_generation"])) or not isinstance(request["witness_object_key"], str) or not request["witness_object_key"]:
            raise CustodianError("missing exact GCS key/generation")
        if _digest(raw) != request["expected_record_digest"] or _digest(canonical_json_bytes(record["preimage"])) != request["expected_preimage_digest"]:
            raise CustodianError("authenticated witness digest mismatch")
        if record["receipt_digest"] != request["expected_receipt_digest"] or record["preimage"].get("previous_commitment") != request["expected_previous_commitment"]:
            raise CustodianError("receipt or chain predecessor mismatch")
        if not self._receipt_exists(request["transaction_id"], record["receipt_digest"]):
            raise CustodianError("missing staged receipt")
        if record["preimage"].get("deployment_id") != request["deployment_id"] or record["preimage"].get("transaction_id") != request["transaction_id"]:
            raise CustodianError("record identity mismatch")
        expected = hmac.new(self._key, canonical_json_bytes(record["preimage"]), hashlib.sha256).hexdigest()
        if not isinstance(record["mac"], str) or not hmac.compare_digest(record["mac"], expected):
            raise CustodianError("authenticated witness MAC mismatch")
        return CustodianResult("VERIFIED", self._key_id, "HMAC-SHA256", record["mac"], _digest(raw))
