"""Closed, non-privileged Kernel health contract. Not an operational authorization."""
from __future__ import annotations

import hashlib
import hmac
import json
import re

CONTRACT = "ai-tax-agent.kernel-health/1.0"
MAX_BYTES = 4096
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,95}\Z")
_REQ = frozenset({"contract", "operation", "deployment_id", "request_id"})
_RES = _REQ | {"status", "request_digest"}
_OPERATION = "HEALTH"

class HealthProtocolError(ValueError):
    pass

def _canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")

def _parse(raw: bytes, fields: frozenset[str]) -> dict:
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_BYTES or raw.startswith(b"\xef\xbb\xbf"):
        raise HealthProtocolError("invalid message length or encoding")
    try:
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("duplicate key")
                result[key] = value
            return result
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique)
        if not isinstance(value, dict) or frozenset(value) != fields or _canonical(value) != raw:
            raise ValueError("noncanonical or unknown fields")
    except (UnicodeError, ValueError, TypeError) as exc:
        raise HealthProtocolError("invalid canonical health message") from exc
    for key in ("deployment_id", "request_id"):
        if not isinstance(value[key], str) or not _ID.fullmatch(value[key]):
            raise HealthProtocolError("invalid binding identifier")
    if value["contract"] != CONTRACT or value["operation"] != _OPERATION:
        raise HealthProtocolError("unsupported health contract or operation")
    return value

def encode_request(deployment_id: str, request_id: str) -> bytes:
    value = {"contract": CONTRACT, "operation": _OPERATION, "deployment_id": deployment_id, "request_id": request_id}
    raw = _canonical(value)
    _parse(raw, _REQ)
    return raw

def handle_request(raw: bytes, expected_deployment_id: str) -> bytes:
    request = _parse(raw, _REQ)
    if not isinstance(expected_deployment_id, str) or not hmac.compare_digest(request["deployment_id"], expected_deployment_id):
        raise HealthProtocolError("deployment mismatch")
    response = dict(request)
    response["status"] = "ALIVE_RESTRICTED"
    response["request_digest"] = "sha256:" + hashlib.sha256(raw).hexdigest()
    return _canonical(response)

def validate_response(raw: bytes, request_raw: bytes) -> dict:
    request = _parse(request_raw, _REQ)
    response = _parse(raw, _RES)
    for key in _REQ:
        if response[key] != request[key]:
            raise HealthProtocolError("request correlation mismatch")
    digest = response["request_digest"]
    if (response["status"] != "ALIVE_RESTRICTED" or not isinstance(digest, str)
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest)
            or not hmac.compare_digest(digest, "sha256:" + hashlib.sha256(request_raw).hexdigest())):
        raise HealthProtocolError("invalid status or digest")
    return response
