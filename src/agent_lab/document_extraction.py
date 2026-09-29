"""Hybrid, evidence-grounded document extraction for tax case ingestion.

Native text is preferred when usable. Image-only or weak PDFs escalate to a
vision model. Model output is schema-constrained and never treated as tax
truth without retaining document/page evidence and confidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ExtractedTaxField:
    name: str
    value: str
    page: int | None
    evidence: str
    confidence: float


@dataclass(frozen=True, slots=True)
class DocumentExtractionResult:
    document_type: str
    tax_category: str
    issuer: str | None
    document_date: str | None
    tax_year: int | None
    fields: tuple[ExtractedTaxField, ...]
    extraction_method: str
    confidence: float
    needs_human_review: bool
    notes: tuple[str, ...]


class VisionDocumentExtractor(Protocol):
    def extract(self, pdf_bytes: bytes, *, filename: str) -> DocumentExtractionResult: ...


def native_text_is_usable(text: str, *, minimum_chars: int = 200) -> bool:
    normalized = " ".join(text.split())
    if len(normalized) < minimum_chars:
        return False
    alpha_numeric = sum(ch.isalnum() for ch in normalized)
    return alpha_numeric / max(len(normalized), 1) >= 0.45


def choose_extraction_method(native_text: str) -> str:
    return "NATIVE_TEXT" if native_text_is_usable(native_text) else "VISION_LLM"


def requires_human_review(result: DocumentExtractionResult, *, threshold: float = 0.85) -> bool:
    if result.needs_human_review or result.confidence < threshold:
        return True
    return any(field.confidence < threshold or not field.evidence.strip() for field in result.fields)
