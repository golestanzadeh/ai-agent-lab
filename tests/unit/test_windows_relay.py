import json
from pathlib import Path

import pytest

from agent_lab.windows_relay import (
    DEFAULT_BRANCH,
    DEFAULT_REPOSITORY,
    REQUEST_PATH,
    RESPONSE_PATH,
    RelayError,
    RelayResult,
    RelayStatus,
    RelayTaskType,
    WindowsRelay,
    parse_request,
)


def request_payload(**changes):
    payload = {
        "protocol_version": 1,
        "task_id": "LOCAL-SYNC-LIVE-001",
        "task_type": "LOCAL_SYNC_BOOTSTRAP",
        "repository": DEFAULT_REPOSITORY,
        "branch": DEFAULT_BRANCH,
        "requested_by": "work",
    }
    payload.update(changes)
    return payload


class FakeGit:
    def __init__(self, repo: Path, *, request: str | None = None, status: str = "", branch: str = DEFAULT_BRANCH):
        self.repo = repo
        self.request = request
        self.status = status
        self.branch = branch
        self.calls: list[tuple[str, ...]] = []
        self.staged = [RESPONSE_PATH]

    def run(self, *args: str) -> str:
        self.calls.append(tuple(args))
        if args == ("rev-parse", "--show-toplevel"):
            return str(self.repo)
        if args == ("symbolic-ref", "--quiet", "--short", "HEAD"):
            return self.branch
        if args == ("fetch", "--prune", "origin", DEFAULT_BRANCH):
            return ""
        if args == ("status", "--porcelain"):
            return self.status
        if args == ("show", f"origin/{DEFAULT_BRANCH}:{REQUEST_PATH}"):
            if self.request is None:
                raise RelayError("missing request")
            return self.request
        if args == ("add", "--", RESPONSE_PATH):
            return ""
        if args == ("diff", "--cached", "--name-only"):
            return "\n".join(self.staged)
        if args[:3] == ("commit", "-m", "Windows Relay response LOCAL-SYNC-LIVE-001"):
            return ""
        if args == ("push", "origin", f"HEAD:refs/heads/{DEFAULT_BRANCH}"):
            return ""
        if args == ("restore", "--staged", "--", RESPONSE_PATH):
            return ""
        raise AssertionError(f"unexpected git call: {args}")


class ProbeRelay(WindowsRelay):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.executions = 0

    def _execute(self, request):
        self.executions += 1
        return RelayResult(
            request.task_id,
            RelayStatus.PASS,
            request.task_type.value,
            "PASS",
            "INSTALLED",
            "PASS",
            "",
        )


def make_repo(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    return tmp_path


def test_valid_request_parses_exact_contract():
    parsed = parse_request(json.dumps(request_payload()))
    assert parsed.task_id == "LOCAL-SYNC-LIVE-001"
    assert parsed.task_type is RelayTaskType.LOCAL_SYNC_BOOTSTRAP
    assert parsed.repository == DEFAULT_REPOSITORY
    assert parsed.branch == DEFAULT_BRANCH


def test_unknown_field_is_rejected_including_command_payload():
    with pytest.raises(RelayError, match="schema mismatch"):
        parse_request(json.dumps(request_payload(command="powershell whoami")))


def test_unknown_task_type_is_rejected():
    with pytest.raises(RelayError, match="not allowlisted"):
        parse_request(json.dumps(request_payload(task_type="RUN_SHELL")))


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("repository", "someone/else", "repository mismatch"),
        ("branch", "main", "branch mismatch"),
        ("requested_by", "codex", "requester mismatch"),
        ("protocol_version", 2, "unsupported protocol version"),
        ("task_id", "bad task id", "invalid task_id"),
    ],
)
def test_binding_mismatches_fail_closed(field, value, message):
    with pytest.raises(RelayError, match=message):
        parse_request(json.dumps(request_payload(**{field: value})))


def test_non_windows_host_fails_before_fetch(tmp_path):
    repo = make_repo(tmp_path)
    fake = FakeGit(repo, request=json.dumps(request_payload()))
    relay = WindowsRelay(repo_path=repo, git=fake, platform_name="posix")
    with pytest.raises(RelayError, match="Windows host required"):
        relay.run_once()
    assert not any(call[0] == "fetch" for call in fake.calls)


def test_missing_request_is_safe_noop(tmp_path):
    repo = make_repo(tmp_path)
    fake = FakeGit(repo, request=None)
    relay = WindowsRelay(repo_path=repo, git=fake, platform_name="nt")
    result = relay.run_once()
    assert result.status is RelayStatus.NO_REQUEST


def test_dirty_tree_blocks_without_execution(tmp_path):
    repo = make_repo(tmp_path)
    fake = FakeGit(repo, request=json.dumps(request_payload()), status=" M private.txt")
    relay = ProbeRelay(repo_path=repo, git=fake, platform_name="nt")
    result = relay.run_once()
    assert result.status is RelayStatus.BLOCKED
    assert relay.executions == 0
    state = json.loads((repo / ".git" / "windows-relay-state.json").read_text())
    assert state["status"] == "BLOCKED"


def test_task_id_is_not_replayed_after_terminal_state(tmp_path):
    repo = make_repo(tmp_path)
    fake = FakeGit(repo, request=json.dumps(request_payload()))
    relay = ProbeRelay(repo_path=repo, git=fake, platform_name="nt")
    first = relay.run_once()
    second = relay.run_once()
    assert first.status is RelayStatus.PASS
    assert second.status is RelayStatus.ALREADY_PROCESSED
    assert relay.executions == 1


def test_publish_response_commits_only_bounded_response_path(tmp_path):
    repo = make_repo(tmp_path)
    fake = FakeGit(repo)
    relay = WindowsRelay(repo_path=repo, git=fake, platform_name="nt")
    result = RelayResult(
        "LOCAL-SYNC-LIVE-001",
        RelayStatus.PASS,
        "LOCAL_SYNC_BOOTSTRAP",
        "PASS",
        "INSTALLED",
        "PASS",
        "",
    )
    relay.publish_response(result)
    payload = json.loads((repo / RESPONSE_PATH).read_text())
    assert payload["task_id"] == "LOCAL-SYNC-LIVE-001"
    assert payload["status"] == "PASS"
    assert ("add", "--", RESPONSE_PATH) in fake.calls
    assert ("push", "origin", f"HEAD:refs/heads/{DEFAULT_BRANCH}") in fake.calls
    assert not any("--force" in call or "-f" in call for call in fake.calls)


def test_publish_response_refuses_main(tmp_path):
    repo = make_repo(tmp_path)
    fake = FakeGit(repo)
    relay = WindowsRelay(repo_path=repo, branch="main", git=fake, platform_name="nt")
    result = RelayResult(
        "LOCAL-SYNC-LIVE-001",
        RelayStatus.PASS,
        "LOCAL_SYNC_BOOTSTRAP",
        "PASS",
        "INSTALLED",
        "PASS",
        "",
    )
    with pytest.raises(RelayError, match="main is forbidden"):
        relay.publish_response(result)
