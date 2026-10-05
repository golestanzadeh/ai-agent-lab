import pytest

from agent_lab.host_control import HostControlError, _safe_path, _validate_common


def request(**changes):
    value = {
        "protocol_version": 1,
        "request_id": "HOST-CONTROL-001",
        "operation": "SCHEDULER_VERIFY",
        "repository": "golestanzadeh/ai-agent-lab",
        "branch": "d021-agent-case-provisioning",
        "requested_by": "work",
        "payload": {},
    }
    value.update(changes)
    return value


def test_valid_bound_request():
    rid, op = _validate_common(request())
    assert rid == "HOST-CONTROL-001"
    assert op == "SCHEDULER_VERIFY"


@pytest.mark.parametrize("field,value", [
    ("repository", "other/repo"),
    ("branch", "main"),
    ("requested_by", "codex"),
    ("protocol_version", 2),
])
def test_binding_changes_fail_closed(field, value):
    with pytest.raises(HostControlError):
        _validate_common(request(**{field: value}))


def test_unknown_operation_fails_closed():
    with pytest.raises(HostControlError):
        _validate_common(request(operation="RUN_SHELL"))


@pytest.mark.parametrize("path", [
    ".git/config",
    ".codex/config.toml",
    ".windows-relay-local/state.json",
    "../outside.txt",
    "/absolute.txt",
    "dir\\windows.txt",
])
def test_protected_or_unsafe_publish_paths_fail_closed(path):
    with pytest.raises(HostControlError):
        _safe_path(path)


@pytest.mark.parametrize("path", [
    "CONSTITUTION.md",
    "docs/decision.md",
    "src/agent_lab/windows_relay.py",
])
def test_normal_repository_paths_are_allowed(path):
    assert _safe_path(path) == path
