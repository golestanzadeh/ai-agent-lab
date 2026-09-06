"""Case-scoped metadata-only document inventory service.

This layer consumes the already verified case-scoped storage adapter. It never
reads document content and never performs unscoped storage discovery.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from agent_lab.storage import CaseScopedStorageAdapter, StorageObjectMetadata


@dataclass(frozen=True, slots=True)
class DocumentInventoryItem:
    object_id: str
    name: str
    mime_type: str
    parent_ids: tuple[str, ...]
    is_folder: bool


@dataclass(frozen=True, slots=True)
class DocumentInventory:
    case_id: str
    generated_at: datetime
    items: tuple[DocumentInventoryItem, ...]

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id is required")
        if self.generated_at.tzinfo is None:
            raise ValueError("generated_at must be timezone-aware")

    @property
    def document_count(self) -> int:
        return sum(not item.is_folder for item in self.items)

    @property
    def folder_count(self) -> int:
        return sum(item.is_folder for item in self.items)


class DocumentInventoryService:
    """Build a deterministic, case-scoped metadata inventory."""

    def __init__(self, storage: CaseScopedStorageAdapter) -> None:
        self._storage = storage

    def build(self, case_id: str) -> DocumentInventory:
        if not case_id.strip():
            raise ValueError("case_id is required")

        metadata = self._storage.list_children(case_id)
        items = tuple(
            self._to_item(item)
            for item in sorted(metadata, key=lambda value: (value.name.casefold(), value.object_id))
        )
        return DocumentInventory(
            case_id=case_id,
            generated_at=datetime.now(timezone.utc),
            items=items,
        )

    @staticmethod
    def _to_item(metadata: StorageObjectMetadata) -> DocumentInventoryItem:
        return DocumentInventoryItem(
            object_id=metadata.object_id,
            name=metadata.name,
            mime_type=metadata.mime_type,
            parent_ids=metadata.parent_ids,
            is_folder=metadata.is_folder,
        )
