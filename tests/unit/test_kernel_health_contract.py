import json
import pytest
from agent_lab.kernel_health_contract import (
    HealthProtocolError, encode_request, handle_request, validate_response,
)

def test_health_roundtrip():
    request = encode_request("deployment-1", "req-1")
    response = handle_request(request, "deployment-1")
    assert validate_response(response, request)["status"] == "ALIVE_RESTRICTED"

@pytest.mark.parametrize("raw", [
    b"{}", b"not json", b"\xef\xbb\xbf{}", b"x" * 4097,
    b'{"contract":"a","contract":"b"}',
])
def test_invalid_request(raw):
    with pytest.raises(HealthProtocolError):
        handle_request(raw, "deployment-1")

def test_denies_other_deployment():
    with pytest.raises(HealthProtocolError, match="deployment"):
        handle_request(encode_request("deployment-1", "req-1"), "deployment-2")

def test_denies_extra_operation():
    raw = encode_request("deployment-1", "req-1").replace(b"HEALTH", b"CREATE_CASE")
    with pytest.raises(HealthProtocolError):
        handle_request(raw, "deployment-1")

def test_denies_extra_field():
    value = json.loads(encode_request("deployment-1", "req-1"))
    value["owner_id"] = "owner"
    with pytest.raises(HealthProtocolError):
        handle_request(json.dumps(value, sort_keys=True, separators=(",", ":")).encode(), "deployment-1")

def test_rejects_wrong_correlation_and_digest():
    request = encode_request("deployment-1", "req-1")
    response = handle_request(request, "deployment-1")
    other = encode_request("deployment-1", "req-2")
    with pytest.raises(HealthProtocolError):
        validate_response(response, other)
    altered = response.replace(b"ALIVE_RESTRICTED", b"READY_PROTECTED")
    with pytest.raises(HealthProtocolError):
        validate_response(altered, request)
