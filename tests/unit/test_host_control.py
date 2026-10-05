import pytest

from agent_lab.host_control import HostControlError, _continuation_binding, _safe_path, _validate_common


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


def test_retired_codex_scheduler_arm_fails_closed():
    with pytest.raises(HostControlError, match="operation not allowlisted"):
        _validate_common(request(operation="SCHEDULER_ARM"))


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


def test_scheduler_request_is_bound_to_hot_context(tmp_path, monkeypatch):
    import json
    from agent_lab.project_execution_graph import digest
    hot={"schema_version":1,"project":"AI-Tax-Agent","repository":"golestanzadeh/ai-agent-lab","branch":"d021-agent-case-provisioning","head":"C1","recovery_checkpoint":"C1","graph_digest":"sha256:g","next_authorized_action":{"action_id":"DR-04-REMEDIATE-AND-ACCEPT","graph_digest":"sha256:g","outcome":"CAPACITY_DEFERRED","human_gate":"NONE","reset_timestamp":"2026-10-05T06:40:04+00:00"},"capacity":{},"supporting_contract":"contracts/project-execution/v1/master-execution-graph.json"}
    hot["context_digest"]=digest(hot)
    committed=json.dumps(hot)
    (tmp_path / "PROJECT_HOT_CONTEXT.json").write_text(committed)
    (tmp_path / ".git").mkdir()
    payload={"action_id":"DR-04-REMEDIATE-AND-ACCEPT","checkpoint":"C1","graph_digest":"sha256:g","expected_head":"C1"}
    monkeypatch.setattr("agent_lab.host_control._verify_repo",lambda repo:"C1")
    monkeypatch.setattr("agent_lab.host_control._git",lambda repo,*args: committed if args==("show","HEAD:PROJECT_HOT_CONTEXT.json") else "")
    observed, rrule = _continuation_binding(tmp_path,payload,include_rrule=False)
    assert observed["recovery_checkpoint"] == "C1" and rrule is None
    with pytest.raises(HostControlError,match="durable continuation"):
        _continuation_binding(tmp_path,{**payload,"action_id":"OTHER"},include_rrule=False)
    hot["head"]="STALE"; committed=json.dumps(hot)
    with pytest.raises(HostControlError,match="digest mismatch"):
        _continuation_binding(tmp_path,payload,include_rrule=False)


def test_scheduler_contract_rejects_arbitrary_payload(tmp_path):
    (tmp_path / "PROJECT_HOT_CONTEXT.json").write_text('{}')
    with pytest.raises(HostControlError,match="payload mismatch"):
        _continuation_binding(tmp_path,{"command":"whoami"},include_rrule=False)
