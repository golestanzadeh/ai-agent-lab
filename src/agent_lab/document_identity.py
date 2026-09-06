"""Case-scoped deterministic Document Identity registry.

This module assigns stable logical document IDs to source-object observations.
It does not read document content and does not perform global discovery.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
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
            raise ValueError("source_provider and source_object_id are required")
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

    def __init__(self, case_registry: CaseRegistry, case_state: CaseStateStore) -> None:
        self._case_registry = case_registry
        self._case_state = case_state
        self._records: dict[str, DocumentRecord] = {}
        self._observations: dict[str, SourceObservation] = {}
        self._source_index: dict[tuple[str, str, str], str] = {}
        self._sequence = 0
        self._observation_sequence = 0
        self._lock = RLock()

    def resolve_inventory_item(
        self,
        case_id: str,
        run_id: str,
        item: DocumentInventoryItem,
        *,
        source_provider: str,
        source_scope_ref: str,
    ) -> tuple[DocumentRecord, SourceObservation]:
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
                record = DocumentRecord(
                    document_id=document_id,
                    case_id=case_id,
                    source_provider=source_provider,
                    source_object_id=item.object_id,
                    source_scope_ref=source_scope_ref,
                    current_name=item.name,
                    mime_type=item.mime_type,
                    parent_ids=item.parent_ids,
                    is_folder=item.is_folder,
                    first_seen_run_id=run_id,
                    last_seen_run_id=run_id,
                    first_seen_at=now,
                    last_seen_at=now,
                    source_status=SourceStatus.ACTIVE,
                )
                self._records[document_id] = record
                self._source_index[key] = document_id
            else:
                previous = self._records[document_id]
                if previous.case_id != case_id:
                    raise PermissionError("document belongs to another case")
                record = DocumentRecord(
                    document_id=previous.document_id,
                    case_id=previous.case_id,
                    source_provider=previous.source_provider,
                    source_object_id=previous.source_object_id,
                    source_scope_ref=source_scope_ref,
                    current_name=item.name,
                    mime_type=item.mime_type,
                    parent_ids=item.parent_ids,
                    is_folder=item.is_folder,
                    first_seen_run_id=previous.first_seen_run_id,
                    last_seen_run_id=run_id,
                    first_seen_at=previous.first_seen_at,
                    last_seen_at=now,
                    source_status=SourceStatus.ACTIVE,
                    content_fingerprint=previous.content_fingerprint,
                    schema_version=previous.schema_version,
                )
                self._records[document_id] = record

            self._observation_sequence += 1
            observation = SourceObservation(
                observation_id=f"OBS-{case_id}-{self._observation_sequence:08d}",
                document_id=document_id,
                case_id=case_id,
                run_id=run_id,
                observed_at=now,
                source_provider=source_provider,
                source_object_id=item.object_id,
                source_scope_ref=source_scope_ref,
                name=item.name,
                mime_type=item.mime_type,
                parent_ids=item.parent_ids,
                is_folder=item.is_folder,
            )
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
            return tuple(sorted(
                (r for r in self._records.values() if r.case_id == case_id),
                key=lambda r: r.document_id,
            ))

    def observations_for_document(
        self, case_id: str, document_id: str
    ) -> tuple[SourceObservation, ...]:
        with self._lock:
            self.get(case_id, document_id)
            return tuple(sorted(
                (o for o in self._observations.values() if o.case_id == case_id and o.document_id == document_id),
                key=lambda o: o.observation_id,
            ))

    def _require_case(self, case_id: str) -> None:
        if not case_id.strip() or self._case_registry.get(case_id) is None:
            raise DocumentIdentityError(f"unknown case_id: {case_id}")

    def _require_case_and_run(self, case_id: str, run_id: str) -> None:
        self._require_case(case_id)
        self._case_state.get_run(case_id, run_id)
