"""Synthetic metadata-only document presentation contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agent_lab.ui_state_contract import UIWorkspaceState

DOCUMENT_VIEW_VERSION = "1"
ALLOWED_CATEGORIES = ("INCOME", "EXPENSE", "OTHER")


class UIDocumentError(ValueError):
    """Raised when document presentation would expose or cross scope."""


class DocumentViewStatus(str, Enum):
    INDEXED = "INDEXED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCKED = "BLOCKED"


def _reference(name: str, value: str) -> None:
    digest = value[7:] if isinstance(value, str) and value.startswith("sha256:") else ""
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise UIDocumentError(f"{name} must be a canonical sha256 reference")


@dataclass(frozen=True, slots=True)
class SyntheticDocumentView:
    case_id: str
    run_id: str
    document_reference: str
    provenance_reference: str
    display_label: str
    category: str
    mime_label: str
    status: DocumentViewStatus
    contains_content: bool = False
    external_source_access: bool = False

    def __post_init__(self) -> None:
        if not self.case_id.startswith("SYNTH-") or not self.run_id.startswith("SYNTH-"):
            raise UIDocumentError("document view scope must be synthetic")
        _reference("document_reference", self.document_reference)
        _reference("provenance_reference", self.provenance_reference)
        if self.document_reference == self.provenance_reference:
            raise UIDocumentError("document and provenance references must differ")
        if not self.display_label.startswith("مدرک مصنوعی "):
            raise UIDocumentError("only generic synthetic display labels are permitted")
        if self.category not in ALLOWED_CATEGORIES:
            raise UIDocumentError("unsupported synthetic category")
        if self.mime_label not in ("PDF مصنوعی", "تصویر مصنوعی"):
            raise UIDocumentError("unsupported synthetic mime label")
        if self.contains_content is not False or self.external_source_access is not False:
            raise UIDocumentError("document view cannot expose content or access a source")


@dataclass(frozen=True, slots=True)
class SyntheticDocumentInventoryView:
    case_id: str
    run_id: str
    documents: tuple[SyntheticDocumentView, ...]
    version: str = DOCUMENT_VIEW_VERSION
    data_classification: str = "SYNTHETIC_METADATA_ONLY"
    upload_enabled: bool = False
    persistence_enabled: bool = False
    network_calls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.case_id.startswith("SYNTH-") or not self.run_id.startswith("SYNTH-"):
            raise UIDocumentError("inventory scope must be synthetic")
        if not self.documents or any(item.case_id != self.case_id or item.run_id != self.run_id for item in self.documents):
            raise UIDocumentError("every document must match inventory case/run scope")
        references = tuple(item.document_reference for item in self.documents)
        if len(set(references)) != len(references):
            raise UIDocumentError("document references must be unique")
        if self.version != DOCUMENT_VIEW_VERSION or self.data_classification != "SYNTHETIC_METADATA_ONLY":
            raise UIDocumentError("document inventory classification cannot change")
        if self.upload_enabled is not False or self.persistence_enabled is not False or self.network_calls != ():
            raise UIDocumentError("upload, persistence, and networking remain disabled")


def build_synthetic_document_inventory(workspace: UIWorkspaceState) -> SyntheticDocumentInventoryView:
    if not isinstance(workspace, UIWorkspaceState) or workspace.run_id is None or not workspace.document_references:
        raise UIDocumentError("a populated workspace with document references is required")
    provenance = ("sha256:" + "f" * 64, "sha256:" + "9" * 64)
    documents = tuple(
        SyntheticDocumentView(
            case_id=workspace.case_id,
            run_id=workspace.run_id,
            document_reference=reference,
            provenance_reference=provenance[index],
            display_label=f"مدرک مصنوعی {index + 1}",
            category=("INCOME", "EXPENSE")[index],
            mime_label=("PDF مصنوعی", "تصویر مصنوعی")[index],
            status=(DocumentViewStatus.INDEXED, DocumentViewStatus.REVIEW_REQUIRED)[index],
        )
        for index, reference in enumerate(workspace.document_references)
    )
    return SyntheticDocumentInventoryView(case_id=workspace.case_id, run_id=workspace.run_id, documents=documents)
