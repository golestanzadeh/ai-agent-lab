"""Fail-closed one-shot synchronization between a local Git checkout and GitHub.

The engine never commits, rebases, resets, stashes, force-pushes, changes branch,
or edits working-tree files. It only fetches, fast-forwards a clean local branch,
or pushes an already committed strictly-ahead non-main branch.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import subprocess
from typing import Protocol


class LocalSyncError(RuntimeError):
    """Base fail-closed Local Sync Agent error."""


class SyncAction(str, Enum):
    UP_TO_DATE = "UP_TO_DATE"
    PULLED = "PULLED"
    PUSHED = "PUSHED"
    BLOCKED_DIRTY = "BLOCKED_DIRTY"
    BLOCKED_BRANCH = "BLOCKED_BRANCH"
    BLOCKED_DIVERGED = "BLOCKED_DIVERGED"
    BLOCKED_PUSH_MAIN = "BLOCKED_PUSH_MAIN"
    BLOCKED_REMOTE = "BLOCKED_REMOTE"


@dataclass(frozen=True, slots=True)
class SyncResult:
    action: SyncAction
    branch: str
    local_sha: str
    remote_sha: str


class GitRunner(Protocol):
    def run(self, *args: str) -> str: ...


class SubprocessGitRunner:
    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path.resolve()

    def run(self, *args: str) -> str:
        completed = subprocess.run(
            ["git", *args],
            cwd=self.repo_path,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if completed.returncode != 0:
            raise LocalSyncError(f"git command failed: {args[0] if args else 'unknown'}")
        return completed.stdout.strip()


class LocalSyncAgent:
    """Synchronize one explicitly allowed branch without destructive Git behavior."""

    def __init__(
        self,
        *,
        repo_path: Path,
        branch: str,
        remote: str = "origin",
        runner: GitRunner | None = None,
    ) -> None:
        self.repo_path = repo_path.resolve()
        self.branch = branch.strip()
        self.remote = remote.strip()
        if not self.branch or not self.remote:
            raise ValueError("branch and remote are required")
        self.runner = runner or SubprocessGitRunner(self.repo_path)

    def sync_once(self) -> SyncResult:
        self._validate_checkout()
        current_branch = self.runner.run("symbolic-ref", "--quiet", "--short", "HEAD").strip()
        if current_branch != self.branch:
            return SyncResult(SyncAction.BLOCKED_BRANCH, current_branch, "", "")

        if self.runner.run("status", "--porcelain").strip():
            local = self.runner.run("rev-parse", "HEAD")
            return SyncResult(SyncAction.BLOCKED_DIRTY, self.branch, local, "")

        self.runner.run("fetch", "--prune", self.remote, self.branch)
        local_sha = self.runner.run("rev-parse", "HEAD")
        try:
            remote_sha = self.runner.run("rev-parse", f"{self.remote}/{self.branch}")
        except LocalSyncError:
            return SyncResult(SyncAction.BLOCKED_REMOTE, self.branch, local_sha, "")

        if local_sha == remote_sha:
            return SyncResult(SyncAction.UP_TO_DATE, self.branch, local_sha, remote_sha)

        base_sha = self.runner.run("merge-base", "HEAD", f"{self.remote}/{self.branch}")
        if base_sha == local_sha:
            self.runner.run("merge", "--ff-only", f"{self.remote}/{self.branch}")
            new_local = self.runner.run("rev-parse", "HEAD")
            if new_local != remote_sha:
                raise LocalSyncError("fast-forward did not reach remote head")
            return SyncResult(SyncAction.PULLED, self.branch, new_local, remote_sha)

        if base_sha == remote_sha:
            if self.branch == "main":
                return SyncResult(SyncAction.BLOCKED_PUSH_MAIN, self.branch, local_sha, remote_sha)
            self.runner.run("push", self.remote, f"HEAD:refs/heads/{self.branch}")
            return SyncResult(SyncAction.PUSHED, self.branch, local_sha, local_sha)

        return SyncResult(SyncAction.BLOCKED_DIVERGED, self.branch, local_sha, remote_sha)

    def _validate_checkout(self) -> None:
        if not self.repo_path.exists() or not self.repo_path.is_dir():
            raise LocalSyncError("repository path is unavailable")
        top_level = Path(self.runner.run("rev-parse", "--show-toplevel")).resolve()
        if top_level != self.repo_path:
            raise LocalSyncError("configured path is not the repository root")
