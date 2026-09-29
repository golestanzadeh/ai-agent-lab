"""Fail-closed resolution of hash-pinned protected official source material."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path


PROTECTED_ROOT_ENV = "AI_TAX_PROTECTED_SOURCE_ROOT"
DEFAULT_REGISTRY = Path(__file__).resolve().parents[2] / "contracts" / "official-source-registry-v1.json"


class OfficialSourceError(RuntimeError):
    """Base error carrying a stable fail-closed state."""

    state: str

    def __init__(self, state: str, message: str) -> None:
        super().__init__(f"{state}: {message}")
        self.state = state


class OfficialSourceMissing(OfficialSourceError):
    def __init__(self, message: str) -> None:
        super().__init__("OFFICIAL_SOURCE_MISSING", message)


class OfficialSourceIntegrityFailure(OfficialSourceError):
    def __init__(self, message: str) -> None:
        super().__init__("OFFICIAL_SOURCE_INTEGRITY_FAILURE", message)


@dataclass(frozen=True, slots=True)
class ResolvedOfficialSource:
    logical_source_id: str
    path: Path
    sha256: str
    size_bytes: int
    release: str


def _digest(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class OfficialSourceResolver:
    def __init__(self, *, protected_root: Path | None = None, registry_path: Path = DEFAULT_REGISTRY) -> None:
        configured = protected_root or (Path(value) if (value := os.environ.get(PROTECTED_ROOT_ENV)) else None)
        if configured is None:
            raise OfficialSourceMissing(f"{PROTECTED_ROOT_ENV} is not configured")
        self._root = configured.resolve()
        try:
            self._registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise OfficialSourceIntegrityFailure("source registry cannot be loaded") from exc
        if self._registry.get("schema_version") != 1:
            raise OfficialSourceIntegrityFailure("unsupported source registry schema")

    def resolve(self, logical_source_id: str) -> ResolvedOfficialSource:
        matches = [item for item in self._registry.get("sources", []) if item.get("logical_source_id") == logical_source_id]
        if len(matches) != 1:
            raise OfficialSourceMissing(f"unknown or ambiguous logical source ID {logical_source_id!r}")
        item = matches[0]
        relative = Path(item["relative_path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise OfficialSourceIntegrityFailure("registry path escapes the configured protected root")
        candidate = (self._root / relative).resolve()
        if candidate != self._root and self._root not in candidate.parents:
            raise OfficialSourceIntegrityFailure("resolved path escapes the configured protected root")
        if not candidate.is_file():
            raise OfficialSourceMissing(f"{logical_source_id} is absent from the protected store")
        actual_size = candidate.stat().st_size
        expected_size = item.get("size_bytes")
        if actual_size != expected_size:
            raise OfficialSourceIntegrityFailure(f"{logical_source_id} size mismatch")
        actual_hash = _digest(candidate)
        expected_hash = item.get("sha256")
        if actual_hash != expected_hash:
            raise OfficialSourceIntegrityFailure(f"{logical_source_id} SHA-256 mismatch")
        return ResolvedOfficialSource(
            logical_source_id=logical_source_id,
            path=candidate,
            sha256=actual_hash,
            size_bytes=actual_size,
            release=self._registry["release"],
        )
