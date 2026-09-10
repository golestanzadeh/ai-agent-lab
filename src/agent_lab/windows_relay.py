"""Bounded GitHub-to-Windows relay for explicitly allowlisted local tasks.

This module is deliberately not a remote shell. Requests are strict data contracts;
unknown fields and unknown task types fail closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import re
import subprocess
from typing import Callable, Protocol

from agent_lab.local_sync import LocalSyncAgent, LocalSyncError, SyncAction


PROTOCOL_VERSION = 1
DEFAULT_REPOSITORY = "golestanzadeh/ai-agent-lab"
DEFAULT_BRANCH = "d021-agent-case-provisioning"
REQUEST_PATH = ".github/windows-relay/request.json"
RESPONSE_PATH = ".github/windows-relay/response.json"
STATE_RELATIVE_PATH = Path(".git") / "windows-relay-state.json"
_TASK_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9._-]{2,79}$")


class RelayError(RuntimeError):
    """Base fail-closed Windows Relay error."""


class RelayStatus(str, Enum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"
    NO_REQUEST = "NO_REQUEST"
    ALREADY_PROCESSED = "ALREADY_PROCESSED"


class RelayTaskType(str, Enum):
    LOCAL_SYNC_BOOTSTRAP = "LOCAL_SYNC_BOOTSTRAP"


@dataclass(frozen=True, slots=True)
class RelayRequest:
    protocol_version: int
    task_id: str
    task_type: RelayTaskType
    repository: str
    branch: str
    requested_by: str


@dataclass(frozen=True, slots=True)
class RelayResult:
    task_id: str
    status: RelayStatus
    task_type: str
    local_tests: str
    scheduled_task: str
    smoke_test: str
    detail: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "protocol_version": PROTOCOL_VERSION,
            "task_id": self.task_id,
            "status": self.status.value,
            "task_type": self.task_type,
            "local_tests": self.local_tests,
            "scheduled_task": self.scheduled_task,
            "smoke_test": self.smoke_test,
            "detail": self.detail,
        }


class GitRunner(Protocol):
    def run(self, *args: str) -> str: ...


class ProcessRunner(Protocol):
    def run(self, argv: list[str]) -> None: ...


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
            raise RelayError(f"git command failed: {args[0] if args else 'unknown'}")
        return completed.stdout.strip()


class SubprocessRunner:
    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path.resolve()

    def run(self, argv: list[str]) -> None:
        if not argv:
            raise RelayError("empty process command")
        completed = subprocess.run(
            argv,
            cwd=self.repo_path,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if completed.returncode != 0:
            raise RelayError(f"local step failed: {Path(argv[0]).name}")


def parse_request(
    raw: str,
    *,
    repository: str = DEFAULT_REPOSITORY,
    branch: str = DEFAULT_BRANCH,
) -> RelayRequest:
    """Parse the exact relay request schema and reject all extensions."""
    try:
        payload = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise RelayError("invalid request JSON") from exc
    if not isinstance(payload, dict):
        raise RelayError("request must be a JSON object")

    expected = {
        "protocol_version",
        "task_id",
        "task_type",
        "repository",
        "branch",
        "requested_by",
    }
    if set(payload) != expected:
        raise RelayError("request schema mismatch")
    if payload["protocol_version"] != PROTOCOL_VERSION:
        raise RelayError("unsupported protocol version")
    if payload["repository"] != repository:
        raise RelayError("repository mismatch")
    if payload["branch"] != branch:
        raise RelayError("branch mismatch")
    if payload["requested_by"] != "work":
        raise RelayError("requester mismatch")

    task_id = payload["task_id"]
    if not isinstance(task_id, str) or not _TASK_ID_RE.fullmatch(task_id):
        raise RelayError("invalid task_id")
    try:
        task_type = RelayTaskType(payload["task_type"])
    except (TypeError, ValueError) as exc:
        raise RelayError("task type is not allowlisted") from exc

    return RelayRequest(
        protocol_version=PROTOCOL_VERSION,
        task_id=task_id,
        task_type=task_type,
        repository=repository,
        branch=branch,
        requested_by="work",
    )


class WindowsRelay:
    """One-shot relay processor for one configured Windows checkout."""

    def __init__(
        self,
        *,
        repo_path: Path,
        repository: str = DEFAULT_REPOSITORY,
        branch: str = DEFAULT_BRANCH,
        remote: str = "origin",
        git: GitRunner | None = None,
        process: ProcessRunner | None = None,
        platform_name: str | None = None,
        python_executable: str = "python",
    ) -> None:
        self.repo_path = repo_path.resolve()
        self.repository = repository
        self.branch = branch
        self.remote = remote
        self.git = git or SubprocessGitRunner(self.repo_path)
        self.process = process or SubprocessRunner(self.repo_path)
        self.platform_name = platform_name
        self.python_executable = python_executable
        self.state_path = self.repo_path / STATE_RELATIVE_PATH

    def run_once(self) -> RelayResult:
        self._validate_host_and_checkout()
        self.git.run("fetch", "--prune", self.remote, self.branch)
        raw = self._read_remote_request()
        if raw is None:
            return RelayResult("", RelayStatus.NO_REQUEST, "", "NOT_RUN", "NOT_RUN", "NOT_RUN")

        request = parse_request(raw, repository=self.repository, branch=self.branch)
        state = self._load_state()
        if state.get("task_id") == request.task_id:
            previous = str(state.get("status", ""))
            if previous in {RelayStatus.PASS.value, RelayStatus.BLOCKED.value, "IN_PROGRESS"}:
                return RelayResult(
                    request.task_id,
                    RelayStatus.ALREADY_PROCESSED,
                    request.task_type.value,
                    str(state.get("local_tests", "NOT_RUN")),
                    str(state.get("scheduled_task", "NOT_RUN")),
                    str(state.get("smoke_test", "NOT_RUN")),
                    "terminal or interrupted task already recorded",
                )

        if self.git.run("status", "--porcelain").strip():
            return self._terminal_block(request, "working tree is not clean")

        self._store_state({"task_id": request.task_id, "status": "IN_PROGRESS"})
        try:
            result = self._execute(request)
        except (RelayError, LocalSyncError):
            result = RelayResult(
                request.task_id,
                RelayStatus.BLOCKED,
                request.task_type.value,
                "BLOCKED",
                "BLOCKED",
                "BLOCKED",
                "bounded local execution failed",
            )
        self._store_state(result.as_dict())
        return result

    def publish_response(self, result: RelayResult) -> None:
        """Commit/push only the bounded response file on the approved non-main branch."""
        if not result.task_id or result.status not in {RelayStatus.PASS, RelayStatus.BLOCKED}:
            return
        if self.branch == "main":
            raise RelayError("response publication to main is forbidden")
        if self.git.run("status", "--porcelain").strip():
            raise RelayError("working tree must be clean before response publication")

        response_path = self.repo_path / RESPONSE_PATH
        response_path.parent.mkdir(parents=True, exist_ok=True)
        response_path.write_text(
            json.dumps(result.as_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.git.run("add", "--", RESPONSE_PATH)
        staged = self.git.run("diff", "--cached", "--name-only").splitlines()
        if staged != [RESPONSE_PATH]:
            self.git.run("restore", "--staged", "--", RESPONSE_PATH)
            response_path.unlink(missing_ok=True)
            raise RelayError("unexpected staged paths")
        self.git.run("commit", "-m", f"Windows Relay response {result.task_id}", "--", RESPONSE_PATH)
        self.git.run("push", self.remote, f"HEAD:refs/heads/{self.branch}")

    def _execute(self, request: RelayRequest) -> RelayResult:
        if request.task_type is not RelayTaskType.LOCAL_SYNC_BOOTSTRAP:
            raise RelayError("task type is not implemented")

        sync = LocalSyncAgent(repo_path=self.repo_path, branch=self.branch, remote=self.remote)
        sync_result = sync.sync_once()
        if sync_result.action not in {SyncAction.UP_TO_DATE, SyncAction.PULLED}:
            raise RelayError(f"unsafe pre-bootstrap sync state: {sync_result.action.value}")

        self.process.run([
            self.python_executable,
            "-m",
            "pytest",
            "-q",
            "tests/unit/test_local_sync.py",
            "tests/unit/test_windows_relay.py",
        ])
        self.process.run([
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self.repo_path / "scripts" / "install_local_sync_task.ps1"),
        ])
        self.process.run([
            self.python_executable,
            str(self.repo_path / "scripts" / "local_sync_agent.py"),
            "--repo",
            str(self.repo_path),
            "--branch",
            self.branch,
        ])
        self.process.run([
            "schtasks.exe",
            "/Query",
            "/TN",
            "AI-Tax-Agent Local Sync",
        ])
        return RelayResult(
            request.task_id,
            RelayStatus.PASS,
            request.task_type.value,
            "PASS",
            "INSTALLED",
            "PASS",
            "",
        )

    def _validate_host_and_checkout(self) -> None:
        platform_name = self.platform_name
        if platform_name is None:
            import os

            platform_name = os.name
        if platform_name != "nt":
            raise RelayError("Windows host required")
        if not self.repo_path.exists() or not self.repo_path.is_dir():
            raise RelayError("repository path unavailable")
        top = Path(self.git.run("rev-parse", "--show-toplevel")).resolve()
        if top != self.repo_path:
            raise RelayError("configured path is not repository root")
        current = self.git.run("symbolic-ref", "--quiet", "--short", "HEAD").strip()
        if current != self.branch:
            raise RelayError("configured branch is not checked out")

    def _read_remote_request(self) -> str | None:
        try:
            return self.git.run("show", f"{self.remote}/{self.branch}:{REQUEST_PATH}")
        except RelayError:
            return None

    def _load_state(self) -> dict[str, object]:
        if not self.state_path.exists():
            return {}
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RelayError("relay state is unreadable") from exc
        if not isinstance(data, dict):
            raise RelayError("relay state is invalid")
        return data

    def _store_state(self, state: dict[str, object]) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.state_path.with_suffix(".tmp")
        temp.write_text(json.dumps(state, sort_keys=True) + "\n", encoding="utf-8")
        temp.replace(self.state_path)

    def _terminal_block(self, request: RelayRequest, detail: str) -> RelayResult:
        result = RelayResult(
            request.task_id,
            RelayStatus.BLOCKED,
            request.task_type.value,
            "NOT_RUN",
            "NOT_RUN",
            "NOT_RUN",
            detail,
        )
        self._store_state(result.as_dict())
        return result
