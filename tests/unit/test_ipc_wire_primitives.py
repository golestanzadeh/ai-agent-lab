import struct

import pytest

from agent_lab.ipc_wire_primitives import (
    MAX_PAYLOAD_BYTES,
    WireFormatError,
    canonical_json_bytes,
    canonical_sha256,
    decode_frame,
    encode_frame,
)


def test_normative_unicode_vector_matches_exact_frame_and_digest():
    value = {"z": True, "a": "é"}
    assert canonical_json_bytes(value) == '{"a":"é","z":true}'.encode()
    assert encode_frame(value).hex() == "130000007b2261223a22c3a9222c227a223a747275657d"
    assert canonical_sha256(value) == "sha256:13b252049f10ae83cae57a1523146622d05d2cf435237982d6db1f1d1ee89298"
    assert decode_frame(encode_frame(value)) == {"a": "é", "z": True}


def test_normative_control_character_vector_matches_exact_frame_and_digest():
    value = {"b": ["x", False], "a": "\x0f"}
    assert encode_frame(value).hex() == "1e0000007b2261223a225c7530303066222c2262223a5b2278222c66616c73655d7d"
    assert canonical_sha256(value) == "sha256:cd9de0b0f795c4857886b4475f93da16bd4a94b17f74b2a1f7b85be525b2e1b9"


@pytest.mark.parametrize("value", [{"n": None}, {"n": 0}, {"n": 1.0}])
def test_numbers_and_null_fail_closed(value):
    with pytest.raises(WireFormatError, match="numbers and null"):
        encode_frame(value)


@pytest.mark.parametrize(
    "payload",
    [
        b'{"z":true,"a":"x"}',
        b'{"a": "x"}',
        b'{"a":"x","a":"x"}',
        b'\xef\xbb\xbf{"a":"x"}',
        b'{"a":1}',
        b'{"a":null}',
    ],
)
def test_noncanonical_or_forbidden_payloads_are_rejected(payload):
    with pytest.raises(WireFormatError):
        decode_frame(struct.pack("<I", len(payload)) + payload)


def test_frame_rejects_early_eof_trailing_bytes_and_invalid_lengths():
    frame = encode_frame({"a": "x"})
    for invalid in (frame[:-1], frame + b"x", b"\x00\x00\x00\x00", struct.pack("<I", MAX_PAYLOAD_BYTES + 1) + b"x"):
        with pytest.raises(WireFormatError):
            decode_frame(invalid)


def test_exact_maximum_payload_round_trips_and_next_byte_is_rejected():
    exact = {"a": "x" * (MAX_PAYLOAD_BYTES - len(b'{"a":""}'))}
    frame = encode_frame(exact)
    assert len(frame) == MAX_PAYLOAD_BYTES + 4
    assert decode_frame(frame) == exact
    with pytest.raises(WireFormatError, match="payload length"):
        encode_frame({"a": exact["a"] + "x"})


def test_unicode_composition_is_not_normalized_or_digest_equivalent():
    composed = {"a": "é"}
    decomposed = {"a": "e\u0301"}
    assert canonical_json_bytes(composed) != canonical_json_bytes(decomposed)
    assert canonical_sha256(composed) != canonical_sha256(decomposed)


@pytest.mark.parametrize("token", [b"-0", b"1e2", b"NaN", b"Infinity"])
def test_additional_numeric_tokens_fail_closed(token):
    payload = b'{"a":' + token + b"}"
    with pytest.raises(WireFormatError):
        decode_frame(struct.pack("<I", len(payload)) + payload)


def test_utf16_key_order_is_used_instead_of_unicode_code_point_order():
    supplementary = "\U00010000"
    bmp = "\ue000"
    encoded = canonical_json_bytes({bmp: "bmp", supplementary: "supplementary"}).decode()
    assert encoded.index(supplementary) < encoded.index(bmp)


def test_surrogates_noncharacters_and_excessive_depth_are_rejected():
    for value in ({"a": "\ud800"}, {"a": "\ufdd0"}):
        with pytest.raises(WireFormatError):
            encode_frame(value)
    nested = "leaf"
    for _ in range(12):
        nested = [nested]
    with pytest.raises(WireFormatError, match="nesting"):
        encode_frame({"a": nested})


def test_module_has_no_transport_or_operational_dispatch_surface():
    import agent_lab.ipc_wire_primitives as wire

    forbidden = {"connect", "listen", "send", "commit", "restore", "mutate", "authorize"}
    assert forbidden.isdisjoint(set(wire.__dict__))
