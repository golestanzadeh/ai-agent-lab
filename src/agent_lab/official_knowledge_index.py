"""Trusted, versioned access to bounded previously-reviewed official semantics."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any, Mapping

INDEX_VERSION = 1
AUDIT_VERSION = 1
DEFAULT_INDEX = Path(__file__).resolve().parents[2] / "contracts" / "official-knowledge-index-v1.json"
DEFAULT_MANIFEST = Path(__file__).resolve().parents[2] / "contracts" / "official-knowledge-manifest-v1.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
STABLE_ID = re.compile(r"^[A-Z0-9]+(?:[._][A-Z0-9]+)+$")
ACCEPTED_STATUS = "VERIFIED_ACCEPTED"

@dataclass(frozen=True, slots=True)
class OfficialKnowledgeReopenAuditRecord:
    schema_version: int
    state: str
    stable_id: str
    reason: str
    tax_year: int
    release: str
    logical_source_id: str
    source_sha256: str
    source_locator: str
    index_reference: str
    observed: str
    required_review_scope: str

@dataclass(frozen=True, slots=True)
class OfficialKnowledgeReopenCompletion:
    schema_version: int
    request: OfficialKnowledgeReopenAuditRecord
    section_inspected: str
    canonical_knowledge_change: str
    acceptance_result: str

    def __post_init__(self) -> None:
        if self.schema_version != AUDIT_VERSION:
            raise ValueError("unsupported reopen completion schema")
        if not isinstance(self.request, OfficialKnowledgeReopenAuditRecord):
            raise ValueError("completion requires an exact reopen audit record")
        if self.request.state != "REOPEN_REQUIRED":
            raise ValueError("completion requires a governed reopen request")
        if not self.section_inspected.strip():
            raise ValueError("exact inspected section is required")
        if self.canonical_knowledge_change not in {"ADDED", "CHANGED", "UNCHANGED"}:
            raise ValueError("invalid canonical knowledge change")
        if self.acceptance_result not in {"PASS", "FAIL"}:
            raise ValueError("invalid reopen acceptance result")

class OfficialKnowledgeError(RuntimeError):
    state = "OFFICIAL_KNOWLEDGE_INTEGRITY_FAILURE"
    def __init__(self, message: str, *, audit_record: OfficialKnowledgeReopenAuditRecord) -> None:
        super().__init__(f"{self.state}: {message}")
        self.audit_record = audit_record
        self.reopen_scope = audit_record

class OfficialKnowledgeMissing(OfficialKnowledgeError): state = "OFFICIAL_KNOWLEDGE_MISSING"
class OfficialKnowledgeMismatch(OfficialKnowledgeError): state = "OFFICIAL_KNOWLEDGE_MISMATCH"
class OfficialKnowledgeUnresolved(OfficialKnowledgeError): state = "OFFICIAL_KNOWLEDGE_UNRESOLVED"

@dataclass(frozen=True, slots=True)
class OfficialKnowledgeEntry:
    stable_id: str
    status: str
    independent_acceptance: str
    verification_reference: str
    tax_year: int
    release: str
    source_family: str
    authority: str
    provider: str
    extraction_version: str
    logical_source_id: str
    source_sha256: str
    source_locator: str
    form: str
    topic: str
    datatype: str
    transformation: str
    dependencies: tuple[str, ...]
    field_ids: tuple[str, ...]
    rule_ids: tuple[str, ...]
    semantics: Mapping[str, str]
    entry_sha256: str
    index_sha256: str

@dataclass(frozen=True, slots=True)
class OfficialKnowledgeChange:
    stable_id: str
    disposition: str
    previous_entry_sha256: str | None
    current_entry_sha256: str | None

def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def _hash(value: Any) -> str: return sha256(_canonical(value)).hexdigest()

class OfficialKnowledgeIndex:
    """Resolve only manifest-pinned and independently accepted semantics."""
    def __init__(self, index_path: Path = DEFAULT_INDEX, *, trusted_canonical_sha256: str | None = None,
                 manifest_path: Path = DEFAULT_MANIFEST) -> None:
        index_path = Path(index_path)
        try: data = json.loads(index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise self._bootstrap_error("knowledge index cannot be loaded", "INDEX_UNAVAILABLE") from exc
        canonical_hash = _hash(data)
        if index_path.resolve() == DEFAULT_INDEX.resolve():
            if trusted_canonical_sha256 is not None:
                raise self._bootstrap_error("default index trust must come from its manifest", "TRUST_CONFIGURATION_INVALID")
            trusted_canonical_sha256 = self._load_default_pin(manifest_path, data)
        elif trusted_canonical_sha256 is None:
            raise self._bootstrap_error("custom index requires an explicit trusted canonical hash", "TRUST_PIN_MISSING")
        if not SHA256.fullmatch(trusted_canonical_sha256) or canonical_hash != trusted_canonical_sha256:
            raise self._bootstrap_error("knowledge-index canonical hash differs from trusted pin", "INDEX_DRIFT")
        self._data, self._index_sha256 = data, canonical_hash
        self._validate()

    @staticmethod
    def _bootstrap_error(message: str, reason: str) -> OfficialKnowledgeError:
        record = OfficialKnowledgeReopenAuditRecord(AUDIT_VERSION, "REOPEN_REQUIRED", "UNKNOWN", reason, -1,
            "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN",
            "official knowledge index trust boundary")
        return OfficialKnowledgeError(message, audit_record=record)

    @staticmethod
    def _load_default_pin(manifest_path: Path, data: Mapping[str, Any]) -> str:
        try: manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise OfficialKnowledgeIndex._bootstrap_error("trusted knowledge manifest cannot be loaded", "MANIFEST_UNAVAILABLE") from exc
        expected = {"schema_version": 1, "manifest_id": "ELSTER_E10_OFFICIAL_KNOWLEDGE_MANIFEST_V1",
                    "index_id": data.get("index_id"), "index_path": DEFAULT_INDEX.name}
        if any(manifest.get(k) != v for k, v in expected.items()):
            raise OfficialKnowledgeIndex._bootstrap_error("trusted knowledge manifest metadata mismatch", "MANIFEST_DRIFT")
        pin = manifest.get("canonical_sha256")
        if not isinstance(pin, str) or not SHA256.fullmatch(pin):
            raise OfficialKnowledgeIndex._bootstrap_error("trusted knowledge manifest has invalid hash", "MANIFEST_DRIFT")
        return pin

    @property
    def reference(self) -> str: return "sha256:" + self._index_sha256

    def _audit(self, stable_id: str, reason: str, observed: str) -> OfficialKnowledgeReopenAuditRecord:
        source = self._data.get("source", {})
        matches = [e for e in self._data.get("entries", []) if isinstance(e, dict) and e.get("stable_id") == stable_id]
        locator = matches[0].get("source_locator", "UNKNOWN") if len(matches) == 1 else "UNKNOWN"
        return OfficialKnowledgeReopenAuditRecord(AUDIT_VERSION, "REOPEN_REQUIRED", stable_id, reason,
            self._data.get("tax_year", -1), self._data.get("release", "UNKNOWN"),
            source.get("logical_source_id", "UNKNOWN"), source.get("sha256", "UNKNOWN"), locator,
            self.reference, observed, f"only {stable_id} at {locator}")

    def _fail(self, message: str, stable_id: str = "UNKNOWN") -> None:
        raise OfficialKnowledgeError(message, audit_record=self._audit(stable_id, "INDEX_DRIFT", message))

    def _validate(self) -> None:
        data = self._data
        if not isinstance(data, dict) or data.get("schema_version") != INDEX_VERSION: self._fail("unsupported knowledge-index schema")
        for key in ("index_id", "source_family", "authority", "provider", "release", "extraction_version"):
            if not isinstance(data.get(key), str) or not data[key]: self._fail(f"invalid index metadata {key}")
        if not isinstance(data.get("tax_year"), int): self._fail("invalid tax year")
        source = data.get("source")
        if not isinstance(source, dict) or not source.get("logical_source_id") or not SHA256.fullmatch(str(source.get("sha256", ""))): self._fail("invalid source provenance")
        entries = data.get("entries")
        if not isinstance(entries, list) or not entries: self._fail("knowledge index has no entries")
        seen: set[str] = set(); allowed = {ACCEPTED_STATUS, "EXTRACTED_UNRESOLVED"}
        strings = ("independent_acceptance", "verification_reference", "form", "topic", "source_locator", "datatype", "transformation")
        for entry in entries:
            stable_id = entry.get("stable_id", "UNKNOWN") if isinstance(entry, dict) else "UNKNOWN"
            if not isinstance(entry, dict) or not STABLE_ID.fullmatch(stable_id) or stable_id in seen: self._fail("invalid or duplicate stable entry ID", stable_id)
            seen.add(stable_id)
            if entry.get("status") not in allowed: self._fail("invalid knowledge lifecycle status", stable_id)
            acceptance = entry.get("independent_acceptance")
            if acceptance not in {"PASS", "FAIL", "PENDING"}: self._fail("invalid independent acceptance state", stable_id)
            if entry.get("status") == ACCEPTED_STATUS and acceptance != "PASS": self._fail("accepted entry lacks independent acceptance", stable_id)
            if entry.get("status") != ACCEPTED_STATUS and acceptance == "PASS": self._fail("unresolved entry cannot claim acceptance", stable_id)
            if entry.get("tax_year") != data["tax_year"] or entry.get("release") != data["release"] or entry.get("source") != source: self._fail("entry provenance differs from index provenance", stable_id)
            if any(not isinstance(entry.get(k), str) or not entry[k] for k in strings): self._fail("entry metadata is incomplete", stable_id)
            for key in ("field_ids", "rule_ids", "dependencies"):
                values = entry.get(key)
                if not isinstance(values, list) or not all(isinstance(v, str) and v for v in values) or len(values) != len(set(values)): self._fail(f"entry {key} is malformed", stable_id)
            semantics = entry.get("semantics")
            if not isinstance(semantics, dict) or not semantics or not all(isinstance(k, str) and isinstance(v, str) and v for k, v in semantics.items()): self._fail("entry semantics are malformed", stable_id)

    def resolve(self, stable_id: str, *, tax_year: int, release: str, source_sha256: str) -> OfficialKnowledgeEntry:
        audit = self._audit(stable_id, "LOOKUP_MISMATCH", "lookup did not match exact provenance")
        if tax_year != self._data["tax_year"]: raise OfficialKnowledgeMismatch("tax year does not match indexed semantics", audit_record=audit)
        if release != self._data["release"]: raise OfficialKnowledgeMismatch("release does not match indexed semantics", audit_record=audit)
        if not SHA256.fullmatch(source_sha256) or source_sha256 != self._data["source"]["sha256"]: raise OfficialKnowledgeMismatch("official source hash does not match indexed provenance", audit_record=audit)
        matches = [e for e in self._data["entries"] if e["stable_id"] == stable_id]
        if len(matches) != 1: raise OfficialKnowledgeMissing("semantic entry is absent or ambiguous", audit_record=audit)
        item = matches[0]
        if item["status"] != ACCEPTED_STATUS:
            raise OfficialKnowledgeUnresolved("semantic entry is not independently accepted", audit_record=self._audit(stable_id, "ENTRY_UNRESOLVED", item["status"]))
        entry_hash = _hash(item)
        return OfficialKnowledgeEntry(stable_id, item["status"], item["independent_acceptance"], item["verification_reference"], item["tax_year"], item["release"],
            self._data["source_family"], self._data["authority"], self._data["provider"], self._data["extraction_version"], item["source"]["logical_source_id"],
            item["source"]["sha256"], item["source_locator"], item["form"], item["topic"], item["datatype"], item["transformation"], tuple(item["dependencies"]),
            tuple(item["field_ids"]), tuple(item["rule_ids"]), MappingProxyType(dict(item["semantics"])), "sha256:" + entry_hash, self.reference)

    def compare(self, current: "OfficialKnowledgeIndex") -> tuple[OfficialKnowledgeChange, ...]:
        if not isinstance(current, OfficialKnowledgeIndex): raise TypeError("current must be a trusted OfficialKnowledgeIndex")
        previous = {e["stable_id"]: _hash(e) for e in self._data["entries"]}; latest = {e["stable_id"]: _hash(e) for e in current._data["entries"]}
        changes = []
        for stable_id in sorted(previous.keys() | latest.keys()):
            old, new = previous.get(stable_id), latest.get(stable_id)
            disposition = "NEW" if old is None else "REMOVED" if new is None else "UNCHANGED" if old == new else "CHANGED"
            changes.append(OfficialKnowledgeChange(stable_id, disposition, "sha256:" + old if old else None, "sha256:" + new if new else None))
        return tuple(changes)
