import json
from hashlib import sha256
from pathlib import Path

import pytest

from agent_lab.official_source_resolver import (
    OfficialSourceIntegrityFailure,
    OfficialSourceMissing,
    OfficialSourceResolver,
)


def registry(tmp_path: Path, content: bytes = b"official") -> tuple[Path, Path]:
    root = tmp_path / "store"
    source = root / "ELSTER" / "ERiC" / "44.3.6.0" / "artifact.bin"
    source.parent.mkdir(parents=True)
    source.write_bytes(content)
    contract = tmp_path / "registry.json"
    contract.write_text(json.dumps({
        "schema_version": 1,
        "release": "44.3.6.0",
        "sources": [{
            "logical_source_id": "TEST_SOURCE",
            "relative_path": "ELSTER/ERiC/44.3.6.0/artifact.bin",
            "sha256": sha256(content).hexdigest(),
            "size_bytes": len(content),
        }],
    }), encoding="utf-8")
    return root, contract


def test_resolves_exact_hash_pinned_source(tmp_path):
    root, contract = registry(tmp_path)
    result = OfficialSourceResolver(protected_root=root, registry_path=contract).resolve("TEST_SOURCE")
    assert result.release == "44.3.6.0"
    assert result.path == (root / "ELSTER/ERiC/44.3.6.0/artifact.bin").resolve()


def test_root_is_portable_configuration(monkeypatch, tmp_path):
    root, contract = registry(tmp_path)
    monkeypatch.setenv("AI_TAX_PROTECTED_SOURCE_ROOT", str(root))
    assert OfficialSourceResolver(registry_path=contract).resolve("TEST_SOURCE").path.is_file()


def test_missing_root_or_source_fails_closed(monkeypatch, tmp_path):
    monkeypatch.delenv("AI_TAX_PROTECTED_SOURCE_ROOT", raising=False)
    with pytest.raises(OfficialSourceMissing, match="OFFICIAL_SOURCE_MISSING"):
        OfficialSourceResolver(registry_path=tmp_path / "none")
    root, contract = registry(tmp_path)
    with pytest.raises(OfficialSourceMissing, match="OFFICIAL_SOURCE_MISSING"):
        OfficialSourceResolver(protected_root=root, registry_path=contract).resolve("OTHER_RELEASE")


def test_corruption_fails_closed(tmp_path):
    root, contract = registry(tmp_path)
    (root / "ELSTER/ERiC/44.3.6.0/artifact.bin").write_bytes(b"corrupt!")
    with pytest.raises(OfficialSourceIntegrityFailure, match="OFFICIAL_SOURCE_INTEGRITY_FAILURE"):
        OfficialSourceResolver(protected_root=root, registry_path=contract).resolve("TEST_SOURCE")


def test_registry_escape_fails_closed(tmp_path):
    root, contract = registry(tmp_path)
    data = json.loads(contract.read_text(encoding="utf-8"))
    data["sources"][0]["relative_path"] = "../artifact.bin"
    contract.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(OfficialSourceIntegrityFailure, match="escapes"):
        OfficialSourceResolver(protected_root=root, registry_path=contract).resolve("TEST_SOURCE")
