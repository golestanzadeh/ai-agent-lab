import json

from agent_lab.document_extraction import (
    DocumentExtractionResult,
    ExtractedTaxField,
    choose_extraction_method,
    requires_human_review,
)
from agent_lab.gemini_document_extraction import GeminiDocumentExtractor


def test_native_text_preferred_when_usable():
    text = "Invoice 2024 amount 123.45 EUR " * 20
    assert choose_extraction_method(text) == "NATIVE_TEXT"


def test_weak_text_escalates_to_vision():
    assert choose_extraction_method("scan") == "VISION_LLM"


def test_missing_evidence_forces_review():
    result = DocumentExtractionResult(
        document_type="INVOICE",
        tax_category="CANDIDATE",
        issuer=None,
        document_date=None,
        tax_year=2024,
        fields=(ExtractedTaxField("amount", "12.00", 1, "", 0.99),),
        extraction_method="VISION_LLM",
        confidence=0.99,
        needs_human_review=False,
        notes=(),
    )
    assert requires_human_review(result)
