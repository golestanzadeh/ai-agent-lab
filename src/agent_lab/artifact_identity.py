"""Deterministic identities for immutable migration artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping


ARTIFACT_IDENTITY_VERSION = "1"


@dataclass(frozen=True, slots=True)
class ArtifactIdentity:
    """Stable identity metadata for a canonical artifact representation."""

    kind: str
    version: str
    reference: str

    def __post_init__(self) -> None:
        if not self.kind.strip() or not self.version.strip() or not self.reference.strip():
            raise ValueError("artifact identity fields are required")


def _canonicalize(value: Any) -> Any:
    if is_dataclass(value):
        return _canonicalize(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _canonicalize(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (tuple, list)):
        return [_canonicalize(item) for item in value]
    if isinstance(value, set):
        return sorted((_canonicalize(item) for item in value), key=lambda item: json.dumps(item, sort_keys=True))
    return value


def canonical_json(payload: Any) -> str:
    """Return the deterministic JSON representation used for hashing."""
    return json.dumps(
        _canonicalize(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def build_artifact_identity(*, kind: str, version: str, payload: Any) -> ArtifactIdentity:
    """Build an artifact identity from canonical content, excluding identity itself."""
    if not kind.strip() or not version.strip():
        raise ValueError("artifact kind and version are required")
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return ArtifactIdentity(kind=kind, version=version, reference=f"sha256:{digest}")
