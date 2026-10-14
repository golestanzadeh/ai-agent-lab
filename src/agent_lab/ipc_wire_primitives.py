"""Non-operational canonical IPC wire primitives.

This module only validates and frames synthetic messages.  It performs no I/O,
peer authentication, authorization, transaction, persistence, finality, backup,
or restore operation and earns no operational OI-0002 acceptance credit.
"""

from __future__ import annotations

import hashlib
import json
import struct
from collections.abc import Mapping, Sequence
from typing import Any


MAX_PAYLOAD_BYTES = 65_532
MAX_NESTING_DEPTH = 12


class WireFormatError(ValueError):
    """The supplied value or frame violates the frozen development profile."""


def _validate_scalar_text(value: str) -> None:
    for character in value:
        point = ord(character)
        if 0xD800 <= point <= 0xDFFF:
            raise WireFormatError("Unicode surrogates are forbidden")
        if 0xFDD0 <= point <= 0xFDEF or point & 0xFFFF in {0xFFFE, 0xFFFF}:
            raise WireFormatError("Unicode noncharacters are forbidden")


def _utf16_sort_key(value: str) -> bytes:
    return value.encode("utf-16-be")


def _normalize(value: Any, *, depth: int = 1) -> Any:
    if depth > MAX_NESTING_DEPTH:
        raise WireFormatError("maximum nesting depth exceeded")
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        _validate_scalar_text(value)
        return value
    if value is None or isinstance(value, (int, float)):
        raise WireFormatError("numbers and null are forbidden")
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise WireFormatError("object keys must be strings")
        for key in value:
            _validate_scalar_text(key)
        return {
            key: _normalize(value[key], depth=depth + 1)
            for key in sorted(value, key=_utf16_sort_key)
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_normalize(item, depth=depth + 1) for item in value]
    raise WireFormatError(f"unsupported JSON value type: {type(value).__name__}")


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    """Return strict canonical UTF-8 bytes for a synthetic object."""

    if not isinstance(value, Mapping):
        raise WireFormatError("top-level value must be an object")
    normalized = _normalize(value)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_sha256(value: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def encode_frame(value: Mapping[str, Any]) -> bytes:
    payload = canonical_json_bytes(value)
    if not 1 <= len(payload) <= MAX_PAYLOAD_BYTES:
        raise WireFormatError("payload length is outside the permitted range")
    return struct.pack("<I", len(payload)) + payload


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise WireFormatError("duplicate object key")
        result[key] = value
    return result


def decode_frame(frame: bytes) -> dict[str, Any]:
    """Decode exactly one complete canonical frame; trailing bytes are denied."""

    if not isinstance(frame, bytes) or len(frame) < 5:
        raise WireFormatError("frame is incomplete")
    declared = struct.unpack("<I", frame[:4])[0]
    if not 1 <= declared <= MAX_PAYLOAD_BYTES:
        raise WireFormatError("declared payload length is outside the permitted range")
    if len(frame) != declared + 4:
        raise WireFormatError("frame length mismatch or trailing bytes")
    payload = frame[4:]
    if payload.startswith(b"\xef\xbb\xbf"):
        raise WireFormatError("UTF-8 BOM is forbidden")
    try:
        text = payload.decode("utf-8", errors="strict")
        value = json.loads(text, object_pairs_hook=_reject_duplicate_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WireFormatError("invalid UTF-8 or JSON") from exc
    if not isinstance(value, dict):
        raise WireFormatError("top-level value must be an object")
    canonical = canonical_json_bytes(value)
    if canonical != payload:
        raise WireFormatError("payload is not in canonical form")
    return value
