"""Case-scoped deterministic Document Identity registry."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
from threading import RLock

from agent_lab.case_registry import CaseRegistry
from agent_lab.case_state import CaseStateStore
from agent_lab.document_inventory import DocumentInventoryItem


class SourceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    MISSING = "MISSING"
    TRASHED = "TRASHED"
    REPLACED = "REPLACED"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True, slots=True)
class SourceObservation:
    observation_id: str
    document_id: str
    case_id: str
    run_id: str
    observed_at: datetime
    source_provider: str
    source_object_id: str
    source_scope_ref: str
    name: str
    mime_type: str
    parent_ids: tuple[str, ...]
    is_folder: bool
    source_status: SourceStatus = SourceStatus.ACTIVE

    def __post_init__(self) -> None:
        if not self.observation_id.strip() or not self.document_id.strip():
            raise ValueError("observation_id and document_id are required")
        if not self.case_id.strip() or not self.run_id.strip():
            raise ValueError("case_id and run_id are required")
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
        if not self.source_provider.strip() or not self.source_object_id.strip():
            raise ValueError("source provider and object ID are required")
        if not self.source_scope_ref.strip():
            raise ValueError("source_scope_ref is required")


@dataclass(frozen=True, slots=True)
class DocumentRecord:
    document_id: str
    case_id: str
    source_provider: str
    source_object_id: str
    source_scope_ref: str
    current_name: str
    mime_type: str
    parent_ids: tuple[str, ...]
    is_folder: bool
    first_seen_run_id: str
    last_seen_run_id: str
    first_seen_at: datetime
    last_seen_at: datetime
    source_status: SourceStatus
    content_fingerprint: str | None = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        if not self.document_id.strip() or not self.case_id.strip():
            raise ValueError("document_id and case_id are required")
        if not self.source_provider.strip() or not self.source_object_id.strip():
            raise ValueError("source provider and object ID are required")
        if not self.source_scope_ref.strip():
            raise ValueError("source_scope_ref is required")
        if self.first_seen_at.tzinfo is None or self.last_seen_at.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware")
        if self.schema_version < 1:
            raise ValueError("schema_version must be >= 1")


class DocumentIdentityError(RuntimeError):
    """Base error for fail-closed identity operations."""


class DocumentIdentityNotFoundError(DocumentIdentityError):
    pass


class DocumentIdentityRegistry:
    """In-memory, case-scoped logical document identity registry."""

    SNAPSHOT_SCHEMA_VERSION = 1

    def __init__(self, case_registry: CaseRegistry, case_state: CaseStateStore) -> None:
        self._case_registry = case_registry
        self._case_state = case_state
        self._records: dict[str, DocumentRecord] = {}
        self._observations: dict[str, SourceObservation] = {}
        self._source_index: dict[tuple[str, str, str], str] = {}
        self._sequence = 0
        self._observation_sequence = 0
        self._lock = RLock()

    def resolve_inventory_item(self, case_id: str, run_id: str, item: DocumentInventoryItem, *, source_provider: str, source_scope_ref: str) -> tuple[DocumentRecord, SourceObservation]:
        with self._lock:
            self._require_case_and_run(case_id, run_id)
            if not source_provider.strip() or not source_scope_ref.strip():
                raise ValueError("source_provider and source_scope_ref are required")
            key = (case_id, source_provider, item.object_id)
            now = datetime.now(timezone.utc)
            document_id = self._source_index.get(key)
            if document_id is None:
                self._sequence += 1
                document_id = f"DOC-{case_id}-{self._sequence:08d}"
                record = DocumentRecord(document_id=document_id, case_id=case_id, source_provider=source_provider, source_object_id=item.object_id, source_scope_ref=source_scope_ref, current_name=item.name, mime_type=item.mime_type, parent_ids=item.parent_ids, is_folder=item.is_folder, first_seen_run_id=run_id, last_seen_run_id=run_id, first_seen_at=now, last_seen_at=now, source_status=SourceStatus.ACTIVE)
                self._records[document_id] = record
                self._source_index[key] = document_id
            else:
                previous = self._records[document_id]
                if previous.case_id != case_id:
                    raise PermissionError("document belongs to another case")
                record = DocumentRecord(document_id=previous.document_id, case_id=previous.case_id, source_provider=previous.source_provider, source_object_id=previous.source_object_id, source_scope_ref=source_scope_ref, current_name=item.name, mime_type=item.mime_type, parent_ids=item.parent_ids, is_folder=item.is_folder, first_seen_run_id=previous.first_seen_run_id, last_seen_run_id=run_id, first_seen_at=previous.first_seen_at, last_seen_at=now, source_status=SourceStatus.ACTIVE, content_fingerprint=previous.content_fingerprint, schema_version=previous.schema_version)
                self._records[document_id] = record
            self._observation_sequence += 1
            observation = SourceObservation(observation_id=f"OBS-{case_id}-{self._observation_sequence:08d}", document_id=document_id, case_id=case_id, run_id=run_id, observed_at=now, source_provider=source_provider, source_object_id=item.object_id, source_scope_ref=source_scope_ref, name=item.name, mime_type=item.mime_type, parent_ids=item.parent_ids, is_folder=item.is_folder)
            self._observations[observation.observation_id] = observation
            return record, observation

    def get(self, case_id: str, document_id: str) -> DocumentRecord:
        with self._lock:
            self._require_case(case_id)
            record = self._records.get(document_id)
            if record is None or record.case_id != case_id:
                raise DocumentIdentityNotFoundError(document_id)
            return record

    def list_for_case(self, case_id: str) -> tuple[DocumentRecord, ...]:
        with self._lock:
            self._require_case(case_id)
            return tuple(sorted((r for r in self._records.values() if r.case_id == case_id), key=lambda r: r.document_id))

    def observations_for_document(self, case_id: str, document_id: str) -> tuple[SourceObservation, ...]:
        with self._lock:
            self.get(case_id, document_id)
            return tuple(sorted((o for o in self._observations.values() if o.case_id == case_id and o.document_id == document_id), key=lambda o: o.observation_id))

    def export_snapshot(self, case_id: str) -> dict[str, object]:
        """Export one case's identity state for local persistence only."""
        with self._lock:
            self._require_case(case_id)
            return {
                "schema_version": self.SNAPSHOT_SCHEMA_VERSION,
                "case_id": case_id,
                "sequence": self._sequence,
                "observation_sequence": self._observation_sequence,
                "records": [self._record_to_dict(r) for r in self.list_for_case(case_id)],
                "observations": [self._observation_to_dict(o) for o in sorted((o for o in self._observations.values() if o.case_id == case_id), key=lambda o: o.observation_id)],
            }

    def save_snapshot(self, case_id: str, path: str | Path) -> None:
        """Persist one case snapshot to local JSON. It may contain private object IDs."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.export_snapshot(case_id), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def load_snapshot(self, case_id: str, path: str | Path) -> None:
        target = Path(path)
        self.import_snapshot(case_id, json.loads(target.read_text(encoding="utf-8")))

    def import_snapshot(self, case_id: str, payload: dict[str, object]) -> None:
        """Restore a validated snapshot, replacing this registry's in-memory state."""
        with self._lock:
            self._require_case(case_id)
            case = self._case_registry.get(case_id)
            assert case is not None
            expected_scope = f"{case.storage_scope_reference.provider}:{case.storage_scope_reference.root_id}"
            if payload.get("schema_version") != self.SNAPSHOT_SCHEMA_VERSION or payload.get("case_id") != case_id:
                raise DocumentIdentityError("invalid or cross-case document identity snapshot")
            raw_records = payload.get("records")
            raw_observations = payload.get("observations")
            if not isinstance(raw_records, list) or not isinstance(raw_observations, list):
                raise DocumentIdentityError("invalid document identity snapshot")
            records: dict[str, DocumentRecord] = {}
            source_index: dict[tuple[str, str, str], str] = {}
            observations: dict[str, SourceObservation] = {}
            for raw in raw_records:
                if not isinstance(raw, dict):
                    raise DocumentIdentityError("invalid document identity record")
                record = self._record_from_dict(raw)
                if record.case_id != case_id:
                    raise DocumentIdentityError("document identity crosses case boundary")
                if f"{record.source_provider}:{record.source_scope_ref}" != expected_scope and record.source_scope_ref != expected_scope:
                    raise DocumentIdentityError("document identity source scope does not match registered case scope")
                key = (record.case_id, record.source_provider, record.source_object_id)
                if record.document_id in records or key in source_index:
                    raise DocumentIdentityError("duplicate document identity in snapshot")
                records[record.document_id] = record
                source_index[key] = record.document_id
            for raw in raw_observations:
                if not isinstance(raw, dict):
                    raise DocumentIdentityError("invalid document identity observation")
                observation = self._observation_from_dict(raw)
                if observation.case_id != case_id or observation.document_id not in records:
                    raise DocumentIdentityError("observation crosses case boundary or references unknown document")
                if f"{observation.source_provider}:{observation.source_scope_ref}" != expected_scope and observation.source_scope_ref != expected_scope:
                    raise DocumentIdentityError("observation source scope does not match registered case scope")
                if observation.observation_id in observations:
                    raise DocumentIdentityError("duplicate observation in snapshot")
                observations[observation.observation_id] = observation
            sequence = payload.get("sequence")
            observation_sequence = payload.get("observation_sequence")
            if not isinstance(sequence, int) or sequence < 0 or not isinstance(observation_sequence, int) or observation_sequence < 0:
                raise DocumentIdentityError("invalid document identity sequence")
            self._records, self._source_index, self._observations = records, source_index, observations
            self._sequence, self._observation_sequence = sequence, observation_sequence

    @staticmethod
    def _record_to_dict(record: DocumentRecord) -> dict[str, object]:
        data = asdict(record)
        data["source_status"] = record.source_status.value
        data["parent_ids"] = list(record.parent_ids)
        data["first_seen_at"] = record.first_seen_at.isoformat()
        data["last_seen_at"] = record.last_seen_at.isoformat()
        return data

    @staticmethod
    def _record_from_dict(data: dict[str, object]) -> DocumentRecord:
        return DocumentRecord(document_id=str(data["document_id"]), case_id=str(data["case_id"]), source_provider=str(data["source_provider"]), source_object_id=str(data["source_object_id"]), source_scope_ref=str(data["source_scope_ref"]), current_name=str(data["current_name"]), mime_type=str(data["mime_type"]), parent_ids=tuple(str(v) for v in data["parent_ids"]), is_folder=bool(data["is_folder"]), first_seen_run_id=str(data["first_seen_run_id"]), last_seen_run_id=str(data["last_seen_run_id"]), first_seen_at=datetime.fromisoformat(str(data["first_seen_at"])), last_seen_at=datetime.fromisoformat(str(data["last_seen_at"])), source_status=SourceStatus(str(data["source_status"])), content_fingerprint=(str(data["content_fingerprint"]) if data.get("content_fingerprint") is not None else None), schema_version=int(data["schema_version"]))

    @staticmethod
    def _observation_to_dict(observation: SourceObservation) -> dict[str, object]:
        data = asdict(observation)
        data["source_status"] = observation.source_status.value
        data["parent_ids"] = list(observation.parent_ids)
        data["observed_at"] = observation.observed_at.isoformat()
        return data

    @staticmethod
    def _observation_from_dict(data: dict[str, object]) -> SourceObservation:
        return SourceObservation(observation_id=str(data["observation_id"]), document_id=str(data["document_id"]), case_id=str(data["case_id"]), run_id=str(data["run_id"]), observed_at=datetime.fromisoformat(str(data["observed_at"])), source_provider=str(data["source_provider"]), source_object_id=str(data["source_object_id"]), source_scope_ref=str(data["source_scope_ref"]), name=str(data["name"]), mime_type=str(data["mime_type"]), parent_ids=tuple(str(v) for v in data["parent_ids"]), is_folder=bool(data["is_folder"]), source_status=SourceStatus(str(data.get("source_status", SourceStatus.ACTIVE.value))))

    def _require_case(self, case_id: str) -> None:
        if not case_id.strip() or self._case_registry.get(case_id) is None:
            raise DocumentIdentityError(f"unknown case_id: {case_id}")

    def _require_case_and_run(self, case_id: str, run_id: str) -> None:
        self._require_case(case_id)
        self._case_state.get_run(case_id, run_id)
