"""One-shot CLI for the bounded Windows Relay."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent_lab.windows_relay import (  # noqa: E402
    DEFAULT_BRANCH,
    DEFAULT_REPOSITORY,
    RelayError,
    RelayStatus,
    WindowsRelay,
)


DEFAULT_REPO = Path(r"C:\Users\rezag\ai-agent-lab")
LOCK_NAME = "windows-relay.lock"
LOCK_STALE_SECONDS = 600


def _acquire_lock(repo: Path) -> Path:
    lock = repo / ".git" / LOCK_NAME
    lock.parent.mkdir(parents=True, exist_ok=True)
    if lock.exists():
        age = time.time() - lock.stat().st_mtime
        if age <= LOCK_STALE_SECONDS:
            raise RelayError("relay lock is active")
        lock.unlink()
    try:
        lock.write_text(str(time.time()), encoding="ascii")
    except OSError as exc:
        raise RelayError("unable to create relay lock") from exc
    return lock


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one bounded Windows Relay iteration")
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    args = parser.parse_args(argv)

    repo = args.repo.resolve()
    lock: Path | None = None
    try:
        lock = _acquire_lock(repo)
        relay = WindowsRelay(repo_path=repo, repository=args.repository, branch=args.branch)
        result = relay.run_once()
        if result.status in {RelayStatus.PASS, RelayStatus.BLOCKED}:
            relay.publish_response(result)
        print(json.dumps(result.as_dict(), sort_keys=True))
        return 0 if result.status in {
            RelayStatus.PASS,
            RelayStatus.NO_REQUEST,
            RelayStatus.ALREADY_PROCESSED,
        } else 2
    except RelayError as exc:
        print(json.dumps({"status": "BLOCKED", "detail": str(exc)}, sort_keys=True))
        return 2
    finally:
        if lock is not None:
            lock.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
