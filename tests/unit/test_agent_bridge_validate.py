from scripts.agent_bridge_validate import validate_request


def request(**changes):
    payload = {
        "protocol_version": 1,
        "task_id": "AB-TEST-001",
        "sender": "work",
        "recipient": "codex",
        "repository": "golestanzadeh/ai-agent-lab",
        "ref": "agent-bridge-test",
        "base_commit": "0123456789abcdef",
        "status": "REQUEST",
        "task": "Validate passive bridge",
        "acceptance": ["validator passes"],
        "allowed_scope": ["tests/"],
        "forbidden_actions": ["merge", "release", "runtime migration"],
        "risk_class": "low",
    }
    payload.update(changes)
    return payload


def test_valid_low_risk_request_is_passive_only():
    result = validate_request(request())
    assert result.valid is True
    assert result.outcome == "PASSIVE_VALID"


def test_missing_required_field_fails_closed():
    payload = request()
    del payload["base_commit"]
    result = validate_request(payload)
    assert result.valid is False
    assert result.outcome == "BLOCKED"


def test_wrong_route_fails_closed():
    result = validate_request(request(sender="codex"))
    assert result.valid is False
    assert result.outcome == "BLOCKED"


def test_unsupported_protocol_fails_closed():
    result = validate_request(request(protocol_version=2))
    assert result.valid is False
    assert result.outcome == "BLOCKED"


def test_architecture_risk_requires_human():
    result = validate_request(request(risk_class="architecture"))
    assert result.valid is True
    assert result.outcome == "HUMAN_REQUIRED"


def test_security_risk_requires_human():
    result = validate_request(request(risk_class="security"))
    assert result.valid is True
    assert result.outcome == "HUMAN_REQUIRED"
