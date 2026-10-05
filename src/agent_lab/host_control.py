"""Bounded host-side control for Git publication and Codex continuation guard lifecycle."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess

PROTOCOL_VERSION = 1
REPOSITORY = "golestanzadeh/ai-agent-lab"
BRANCH = "d021-agent-case-provisioning"
REMOTE = "origin"
GUARD_ID = "plan-limit-continuation-guard"
LOCAL_DIR = ".windows-relay-local"
REQUEST_FILE = "request.json"
RESPONSE_FILE = "response.json"
STATE_FILE = "state.json"
AUTOMATION_PATH = Path.home() / ".codex" / "automations" / GUARD_ID / "automation.toml"
_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9._-]{2,79}$")
_ALLOWED_OPS = {"GIT_PUBLISH", "SCHEDULER_PAUSE_CONSUME", "SCHEDULER_RECONCILE", "SCHEDULER_VERIFY"}
_FORBIDDEN_PREFIXES = (".git/", ".codex/", LOCAL_DIR + "/")


class HostControlError(RuntimeError):
    pass


def _git(repo: Path, *args: str) -> str:
    p = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8")
    if p.returncode:
        raise HostControlError("git operation failed: " + (args[0] if args else "unknown"))
    return p.stdout.strip()


def _safe_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/") or ".." in Path(value).parts:
        raise HostControlError("unsafe repository path")
    norm = value.replace("\\", "/")
    if norm == ".git" or any(norm.startswith(p) for p in _FORBIDDEN_PREFIXES):
        raise HostControlError("protected repository path")
    return norm


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HostControlError("invalid local request") from exc
    if not isinstance(value, dict):
        raise HostControlError("request must be object")
    return value


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _validate_common(p: dict) -> tuple[str, str]:
    required = {"protocol_version", "request_id", "operation", "repository", "branch", "requested_by", "payload"}
    if set(p) != required:
        raise HostControlError("request schema mismatch")
    if p["protocol_version"] != PROTOCOL_VERSION or p["repository"] != REPOSITORY or p["branch"] != BRANCH or p["requested_by"] != "work":
        raise HostControlError("request binding mismatch")
    rid, op = p["request_id"], p["operation"]
    if not isinstance(rid, str) or not _ID_RE.fullmatch(rid):
        raise HostControlError("invalid request id")
    if op not in _ALLOWED_OPS or not isinstance(p["payload"], dict):
        raise HostControlError("operation not allowlisted")
    return rid, op


def _verify_repo(repo: Path) -> str:
    if Path(_git(repo, "rev-parse", "--show-toplevel")).resolve() != repo.resolve():
        raise HostControlError("repository root mismatch")
    if _git(repo, "branch", "--show-current") != BRANCH:
        raise HostControlError("branch mismatch")
    return _git(repo, "rev-parse", "HEAD")


def _git_publish(repo: Path, payload: dict) -> dict:
    if set(payload) != {"expected_head", "paths", "commit_message"}:
        raise HostControlError("git publish payload mismatch")
    head = _verify_repo(repo)
    if payload["expected_head"] != head:
        raise HostControlError("stale expected head")
    _git(repo, "fetch", REMOTE, BRANCH)
    if _git(repo, "rev-parse", f"{REMOTE}/{BRANCH}") != head:
        raise HostControlError("local remote head mismatch")
    paths = payload["paths"]
    if not isinstance(paths, list) or not paths or len(paths) > 64 or len(set(paths)) != len(paths):
        raise HostControlError("invalid publish path list")
    safe = [_safe_path(x) for x in paths]
    msg = payload["commit_message"]
    if not isinstance(msg, str) or not (3 <= len(msg) <= 120) or "\n" in msg or "\r" in msg:
        raise HostControlError("invalid commit message")
    changed = set(_git(repo, "status", "--porcelain", "--untracked-files=all").splitlines())
    if not changed:
        raise HostControlError("nothing to publish")
    for path in safe:
        _git(repo, "add", "--", path)
    staged = [x for x in _git(repo, "diff", "--cached", "--name-only").splitlines() if x]
    if sorted(staged) != sorted(safe):
        _git(repo, "restore", "--staged", "--", *safe)
        raise HostControlError("staged paths do not exactly match request")
    _git(repo, "commit", "-m", msg, "--", *safe)
    new_head = _git(repo, "rev-parse", "HEAD")
    _git(repo, "push", REMOTE, f"HEAD:refs/heads/{BRANCH}")
    if _git(repo, "ls-remote", REMOTE, f"refs/heads/{BRANCH}").split()[0] != new_head:
        raise HostControlError("remote verification failed")
    return {"status": "PASS", "operation": "GIT_PUBLISH", "previous_head": head, "new_head": new_head, "published_paths": safe}


def _read_automation() -> str:
    if not AUTOMATION_PATH.is_file():
        raise HostControlError("guard automation unavailable")
    text = AUTOMATION_PATH.read_text(encoding="utf-8")
    if f'id = "{GUARD_ID}"' not in text:
        raise HostControlError("guard identity mismatch")
    return text


def _replace_scalar(text: str, key: str, value: str) -> str:
    pattern = re.compile(rf'(?m)^{re.escape(key)}\s*=\s*".*"$')
    if len(pattern.findall(text)) != 1:
        raise HostControlError("automation field mismatch")
    return pattern.sub(f'{key} = "{value}"', text)


def _continuation_binding(repo: Path, payload: dict, *, include_rrule: bool) -> tuple[dict, str | None]:
    required = {"action_id", "checkpoint", "graph_digest", "expected_head"} | ({"rrule"} if include_rrule else set())
    if set(payload) != required:
        raise HostControlError("scheduler continuation payload mismatch")
    try:
        hot = json.loads(_git(repo, "show", "HEAD:PROJECT_HOT_CONTEXT.json"))
    except (HostControlError, json.JSONDecodeError) as exc:
        raise HostControlError("committed hot context unavailable") from exc
    stored_digest = hot.pop("context_digest", None)
    canonical = json.dumps(hot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    actual_digest = "sha256:" + __import__("hashlib").sha256(canonical).hexdigest()
    if stored_digest != actual_digest:
        raise HostControlError("hot context digest mismatch")
    if hot.get("repository") != REPOSITORY or hot.get("branch") != BRANCH:
        raise HostControlError("hot context repository binding mismatch")
    current_head = _verify_repo(repo)
    if payload["expected_head"] != current_head:
        raise HostControlError("scheduler expected head is stale")
    checkpoint = hot.get("recovery_checkpoint")
    try:
        _git(repo, "merge-base", "--is-ancestor", str(checkpoint), current_head)
    except HostControlError as exc:
        raise HostControlError("hot context checkpoint is not an ancestor") from exc
    action = hot.get("next_authorized_action")
    if not isinstance(action, dict):
        raise HostControlError("durable continuation action unavailable")
    exact = (
        payload["action_id"] == action.get("action_id")
        and payload["checkpoint"] == hot.get("recovery_checkpoint")
        and payload["graph_digest"] == hot.get("graph_digest") == action.get("graph_digest")
        and action.get("outcome") in {"CAPACITY_DEFERRED", "TOKEN_PAUSED", "READY_PACKAGE"}
        and action.get("human_gate") in {None, "NONE"}
    )
    if not exact:
        raise HostControlError("scheduler request is not bound to durable continuation")
    return hot, payload.get("rrule")


def _scheduler(repo: Path, op: str, payload: dict) -> dict:
    text = _read_automation()
    before_hash = __import__("hashlib").sha256(text.encode()).hexdigest()
    if op == "SCHEDULER_VERIFY":
        if payload:
            raise HostControlError("verify payload must be empty")
        return {"status": "PASS", "operation": op, "guard_id": GUARD_ID, "automation_sha256": before_hash}
    if op == "SCHEDULER_PAUSE_CONSUME":
        _continuation_binding(repo, payload, include_rrule=False)
        text = _replace_scalar(text, "status", "PAUSED")
    elif op == "SCHEDULER_RECONCILE":
        if set(payload) != {"expected_status", "action_id", "checkpoint", "graph_digest", "expected_head"} or payload["expected_status"] not in {"ACTIVE", "PAUSED"}:
            raise HostControlError("reconcile payload mismatch")
        _continuation_binding(repo, {k: payload[k] for k in ("action_id", "checkpoint", "graph_digest", "expected_head")}, include_rrule=False)
        current = re.search(r'(?m)^status\s*=\s*"([^"]+)"$', text)
        if not current or current.group(1) != payload["expected_status"]:
            raise HostControlError("scheduler state mismatch")
        return {"status": "PASS", "operation": op, "guard_id": GUARD_ID, "observed_status": current.group(1), "automation_sha256": before_hash}
    else:
        raise HostControlError("scheduler operation not implemented")
    tmp = AUTOMATION_PATH.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(AUTOMATION_PATH)
    after = _read_automation()
    after_hash = __import__("hashlib").sha256(after.encode()).hexdigest()
    return {"status": "PASS", "operation": op, "guard_id": GUARD_ID, "automation_sha256": after_hash}


def process_local_request(repo: Path) -> dict | None:
    inbox = repo / LOCAL_DIR
    request_path, response_path, state_path = inbox / REQUEST_FILE, inbox / RESPONSE_FILE, inbox / STATE_FILE
    if not request_path.exists():
        return None
    p = _read_json(request_path)
    rid, op = _validate_common(p)
    state = _read_json(state_path) if state_path.exists() else {}
    if state.get("request_id") == rid and state.get("terminal") is True:
        result = {"status": "ALREADY_PROCESSED", "request_id": rid, "operation": op}
        _atomic_json(response_path, result)
        request_path.unlink(missing_ok=True)
        return result
    _atomic_json(state_path, {"request_id": rid, "operation": op, "terminal": False})
    try:
        result = _git_publish(repo, p["payload"]) if op == "GIT_PUBLISH" else _scheduler(repo, op, p["payload"])
        result["request_id"] = rid
    except HostControlError as exc:
        result = {"status": "BLOCKED", "request_id": rid, "operation": op, "detail": str(exc)}
    _atomic_json(state_path, {**result, "terminal": True})
    _atomic_json(response_path, result)
    request_path.unlink(missing_ok=True)
    return result
