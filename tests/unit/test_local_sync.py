from pathlib import Path

import pytest

from agent_lab.local_sync import LocalSyncAgent, LocalSyncError, SyncAction


class FakeGit:
    def __init__(self, repo: Path, *, branch="d021-agent-case-provisioning", status="", local="L", remote="R", base="L"):
        self.repo = repo
        self.branch = branch
        self.status = status
        self.local = local
        self.remote = remote
        self.base = base
        self.calls: list[tuple[str, ...]] = []
        self.fail_remote = False

    def run(self, *args: str) -> str:
        self.calls.append(tuple(args))
        if args == ("rev-parse", "--show-toplevel"):
            return str(self.repo)
        if args == ("symbolic-ref", "--quiet", "--short", "HEAD"):
            return self.branch
        if args == ("status", "--porcelain"):
            return self.status
        if args == ("fetch", "--prune", "origin", "d021-agent-case-provisioning"):
            return ""
        if args == ("fetch", "--prune", "origin", "main"):
            return ""
        if args == ("rev-parse", "HEAD"):
            return self.local
        if args in {
            ("rev-parse", "origin/d021-agent-case-provisioning"),
            ("rev-parse", "origin/main"),
        }:
            if self.fail_remote:
                raise LocalSyncError("missing remote")
            return self.remote
        if args in {
            ("merge-base", "HEAD", "origin/d021-agent-case-provisioning"),
            ("merge-base", "HEAD", "origin/main"),
        }:
            return self.base
        if args in {
            ("merge", "--ff-only", "origin/d021-agent-case-provisioning"),
            ("merge", "--ff-only", "origin/main"),
        }:
            self.local = self.remote
            return ""
        if args == ("push", "origin", "HEAD:refs/heads/d021-agent-case-provisioning"):
            self.remote = self.local
            return ""
        raise AssertionError(f"unexpected git call: {args}")


def agent(tmp_path, fake, branch="d021-agent-case-provisioning"):
    return LocalSyncAgent(repo_path=tmp_path, branch=branch, runner=fake)


def test_up_to_date_is_noop(tmp_path):
    fake = FakeGit(tmp_path, local="A", remote="A", base="A")
    result = agent(tmp_path, fake).sync_once()
    assert result.action is SyncAction.UP_TO_DATE
    assert not any(call[0] in {"merge", "push"} for call in fake.calls)


def test_strictly_behind_fast_forwards_only(tmp_path):
    fake = FakeGit(tmp_path, local="A", remote="B", base="A")
    result = agent(tmp_path, fake).sync_once()
    assert result.action is SyncAction.PULLED
    assert ("merge", "--ff-only", "origin/d021-agent-case-provisioning") in fake.calls
    assert not any(call[0] == "push" for call in fake.calls)


def test_strictly_ahead_non_main_pushes_existing_commit(tmp_path):
    fake = FakeGit(tmp_path, local="B", remote="A", base="A")
    result = agent(tmp_path, fake).sync_once()
    assert result.action is SyncAction.PUSHED
    assert ("push", "origin", "HEAD:refs/heads/d021-agent-case-provisioning") in fake.calls


def test_main_is_never_auto_pushed(tmp_path):
    fake = FakeGit(tmp_path, branch="main", local="B", remote="A", base="A")
    result = agent(tmp_path, fake, branch="main").sync_once()
    assert result.action is SyncAction.BLOCKED_PUSH_MAIN
    assert not any(call[0] == "push" for call in fake.calls)


def test_dirty_tree_blocks_before_fetch(tmp_path):
    fake = FakeGit(tmp_path, status=" M file.py")
    result = agent(tmp_path, fake).sync_once()
    assert result.action is SyncAction.BLOCKED_DIRTY
    assert not any(call[0] == "fetch" for call in fake.calls)


def test_branch_mismatch_blocks_before_status_or_fetch(tmp_path):
    fake = FakeGit(tmp_path, branch="other")
    result = agent(tmp_path, fake).sync_once()
    assert result.action is SyncAction.BLOCKED_BRANCH
    assert not any(call[0] in {"status", "fetch"} for call in fake.calls)


def test_divergence_blocks_without_mutation(tmp_path):
    fake = FakeGit(tmp_path, local="L", remote="R", base="BASE")
    result = agent(tmp_path, fake).sync_once()
    assert result.action is SyncAction.BLOCKED_DIVERGED
    assert not any(call[0] in {"merge", "push"} for call in fake.calls)


def test_missing_remote_ref_fails_closed(tmp_path):
    fake = FakeGit(tmp_path, local="L")
    fake.fail_remote = True
    result = agent(tmp_path, fake).sync_once()
    assert result.action is SyncAction.BLOCKED_REMOTE
    assert not any(call[0] in {"merge", "push"} for call in fake.calls)


def test_repository_root_must_match_exactly(tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    fake = FakeGit(other)
    with pytest.raises(LocalSyncError):
        agent(tmp_path, fake).sync_once()


def test_forbidden_git_operations_are_absent_from_all_paths(tmp_path):
    scenarios = [
        FakeGit(tmp_path, local="A", remote="A", base="A"),
        FakeGit(tmp_path, local="A", remote="B", base="A"),
        FakeGit(tmp_path, local="B", remote="A", base="A"),
        FakeGit(tmp_path, local="L", remote="R", base="BASE"),
    ]
    forbidden = {"commit", "reset", "rebase", "stash", "checkout", "switch"}
    for fake in scenarios:
        agent(tmp_path, fake).sync_once()
        assert not any(call[0] in forbidden for call in fake.calls)
        assert not any("--force" in call or "-f" in call for call in fake.calls)
