"""Case-scoped evidence record for a verified document inventory snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock

from agent_lab.audit import ActorType, AuditEventType, AuditStatus, AuditStore
from agent_lab.case_registry import CaseRegistry
from agent_lab.case_state import CaseStateStore
from agent_lab.document_inventory import DocumentInventory


@dataclass(frozen=True, slots=True)
class InventoryEvidence:
    """Immutable logical record of one inventory snapshot."""

    evidence_id: str
    case_id: str
    run_id: str
    generated_at: datetime
    document_count: int
    folder_count: int
    item_refs: tuple[str, ...]
    source_provider: str
    source_scope_ref: str
    schema_version: int = 1

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("evidence_id is required")
        if not self.case_id.strip() or not self.run_id.strip():
            raise ValueError("case_id and run_id are required")
        if self.generated_at.tzinfo is None:
            raise ValueError("generated_at must be timezone-aware")
        if self.document_count < 0 or self.folder_count < 0:
            raise ValueError("counts cannot be negative")
        if self.schema_version < 1:
            raise ValueError("schema_version must be >= 1")
        if not self.source_provider.strip() or not self.source_scope_ref.strip():
            raise ValueError("source_provider and source_scope_ref are required")


class InventoryEvidenceError(RuntimeError):
    """Base error for fail-closed inventory evidence operations."""


class InventoryEvidenceNotFoundError(InventoryEvidenceError):
    pass


class InventoryEvidenceStore:
    """In-memory, case-scoped store for verified inventory evidence."""

    def __init__(
        self,
        case_registry: CaseRegistry,
        case_state: CaseStateStore,
        audit: AuditStore,
    ) -> None:
        self._case_registry = case_registry
        self._case_state = case_state
        self._audit = audit
        self._records: dict[str, InventoryEvidence] = {}
        self._snapshot_index: dict[tuple[str, str], str] = {}
        self._sequence = 0
        self._lock = RLock()

    def record(
        self,
        case_id: str,
        run_id: str,
        inventory: DocumentInventory,
        *,
        source_provider: str,
        source_scope_ref: str,
    ) -> InventoryEvidence:
        with self._lock:
            self._require_case_and_run(case_id, run_id)
            if inventory.case_id != case_id:
                raise InventoryEvidenceError("inventory belongs to another case")
            if not source_provider.strip() or not source_scope_ref.strip():
                raise ValueError("source_provider and source_scope_ref are required")

            snapshot_key = (case_id, self._fingerprint(inventory, source_provider, source_scope_ref))
            existing_id = self._snapshot_index.get(snapshot_key)
            if existing_id is not None:
                return self._records[existing_id]

            self._sequence += 1
            evidence = InventoryEvidence(
                evidence_id=f"EVIDENCE-INVENTORY-{self._sequence:08d}",
                case_id=case_id,
                run_id=run_id,
                generated_at=inventory.generated_at,
                document_count=inventory.document_count,
                folder_count=inventory.folder_count,
                item_refs=tuple(item.object_id for item in inventory.items),
                source_provider=source_provider,
                source_scope_ref=source_scope_ref,
            )
            self._records[evidence.evidence_id] = evidence
            self._snapshot_index[snapshot_key] = evidence.evidence_id

            self._case_state.update_state(case_id, evidence_ref=evidence.evidence_id, last_run_id=run_id)
            self._audit.append(
                case_id=case_id,
                run_id=run_id,
                event_type=AuditEventType.EVIDENCE_LINKED,
                actor_type=ActorType.SYSTEM,
                actor_id="inventory-evidence-store",
                operation="record_inventory_evidence",
                status=AuditStatus.SUCCESS,
                evidence_refs=(evidence.evidence_id,),
                input_refs=tuple(item.object_id for item in inventory.items),
                metadata={"source_provider": source_provider, "source_scope_ref": source_scope_ref},
            )
            return evidence

    def get(self, case_id: str, evidence_id: str) -> InventoryEvidence:
        with self._lock:
            self._require_case(case_id)
            record = self._records.get(evidence_id)
            if record is None or record.case_id != case_id:
                raise InventoryEvidenceNotFoundError(evidence_id)
            return record

    def list_for_case(self, case_id: str) -> tuple[InventoryEvidence, ...]:
        with self._lock:
            self._require_case(case_id)
            return tuple(
                sorted(
                    (record for record in self._records.values() if record.case_id == case_id),
                    key=lambda record: record.evidence_id,
                )
            )

    @staticmethod
    def _fingerprint(
        inventory: DocumentInventory, source_provider: str, source_scope_ref: str
    ) -> str:
        import hashlib

        payload = "|".join(
            [
                source_provider,
                source_scope_ref,
                *(f"{item.object_id}\x1f{item.name}\x1f{item.mime_type}" for item in inventory.items),
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _require_case(self, case_id: str) -> None:
        if not case_id.strip() or self._case_registry.get(case_id) is None:
            raise InventoryEvidenceError(f"unknown case_id: {case_id}")

    def _require_case_and_run(self, case_id: str, run_id: str) -> None:
        self._require_case(case_id)
        self._case_state.get_run(case_id, run_id)
