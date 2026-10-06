"""One-shot unattended Local Sync Agent CLI.

Intended to be called by Windows Task Scheduler once per minute.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from agent_lab.local_sync import LocalSyncAgent, LocalSyncError  # noqa: E402


STALE_LOCK_SECONDS = 600


def acquire_lock(lock_path: Path):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(2):
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if attempt == 0:
                try:
                    age = time.time() - lock_path.stat().st_mtime
                except FileNotFoundError:
                    continue
                if age > STALE_LOCK_SECONDS:
                    try:
                        lock_path.unlink()
                    except FileNotFoundError:
                        pass
                    continue
            return None
        os.write(fd, str(os.getpid()).encode("ascii"))
        return fd
    return None


def release_lock(fd: int | None, lock_path: Path) -> None:
    if fd is None:
        return
    try:
        os.close(fd)
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--remote", default="origin")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    lock_path = repo / ".git" / "local-sync-agent.lock"
    fd = acquire_lock(lock_path)
    if fd is None:
        print(json.dumps({"status": "SKIPPED_LOCKED"}, separators=(",", ":")))
        return 0

    try:
        result = LocalSyncAgent(
            repo_path=repo,
            branch=args.branch,
            remote=args.remote,
        ).sync_once()
        print(json.dumps({
            "status": result.action.value,
            "branch": result.branch,
            "local_sha": result.local_sha,
            "remote_sha": result.remote_sha,
        }, separators=(",", ":")))
        return 0
    except LocalSyncError as exc:
        print(json.dumps({
            "status": "FAILED_CLOSED",
            "error": type(exc).__name__,
        }, separators=(",", ":")))
        return 2
    finally:
        release_lock(fd, lock_path)


if __name__ == "__main__":
    sys.exit(main())
