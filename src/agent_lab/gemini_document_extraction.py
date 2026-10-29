"""Gemini native-PDF vision fallback for evidence-grounded tax extraction."""
from __future__ import annotations

import base64
import json
import math
from typing import Any

from agent_lab.document_extraction import DocumentExtractionResult, ExtractedTaxField

MODEL = "gemini-3.8-flash"

FIELD_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "value": {"type": "string"},
        "page": {"type": ["integer", "null"]},
        "evidence": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": ["name", "value", "page", "evidence", "confidence"],
    "additionalProperties": False,
}

RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "document_type": {"type": "string"},
        "tax_category": {"type": "string"},
        "issuer": {"type": ["string", "null"]},
        "document_date": {"type": ["string", "null"]},
        "tax_year": {"type": ["integer", "null"]},
        "fields": {"type": "array", "items": FIELD_SCHEMA},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "needs_human_review": {"type": "boolean"},
        "notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "document_type", "tax_category", "issuer", "document_date", "tax_year",
        "fields", "confidence", "needs_human_review", "notes",
    ],
    "additionalProperties": False,
}

PROMPT = """Analyze this tax-case PDF. Extract only facts visibly supported by the document.
Do not infer missing amounts, payment dates, reimbursements, family relationships, or tax eligibility.
For every extracted field include a short verbatim evidence fragment and the 1-based page number.
Use tax_category as a candidate classification, not a legal conclusion. Set needs_human_review=true
for ambiguity, conflicting dates, uncertain numbers, missing payment proof, or uncertain tax treatment.
Return only the requested JSON structure."""


class GeminiDocumentExtractor:
    def __init__(self, client: Any, *, model: str = MODEL) -> None:
        self._client = client
        self._model = model

    def extract(self, pdf_bytes: bytes, *, filename: str) -> DocumentExtractionResult:
        if not pdf_bytes:
            raise ValueError("pdf_bytes must not be empty")
        interaction = self._client.interactions.create(
            model=self._model,
            store=False,
            timeout=90,
            automatic_continuation=False,
            generation_config={'max_output_tokens': 12800},
            input=[
                {"type": "text", "text": f"Filename: {filename}\n{PROMPT}"},
                {"type": "document", "data": base64.b64encode(pdf_bytes).decode("ascii"), "mime_type": "application/pdf"},
            ],
            response_format={"type": "text", "mime_type": "application/json", "schema": RESULT_SCHEMA},
        )
        return _parse_result(interaction.output_text)


def _parse_result(raw: str) -> DocumentExtractionResult:
    if not isinstance(raw, str) or len(raw.encode('utf-8')) > 512 * 1024:
        raise ValueError('Invalid or oversized provider response')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate provider field')
            result[key] = value
        return result
    payload = json.loads(raw, object_pairs_hook=unique,
                         parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite provider number')))
    if not isinstance(payload, dict) or set(payload) != set(RESULT_SCHEMA['required']):
        raise ValueError('Closed provider response schema required')
    for key in ('document_type', 'tax_category'):
        if not isinstance(payload[key], str) or not payload[key].strip():
            raise ValueError('Invalid document classification')
    for key in ('issuer', 'document_date'):
        if payload[key] is not None and not isinstance(payload[key], str):
            raise ValueError('Invalid optional text field')
    if payload['tax_year'] is not None and (type(payload['tax_year']) is not int or not 1900 <= payload['tax_year'] <= 2200):
        raise ValueError('Invalid document year')
    if type(payload['needs_human_review']) is not bool or not isinstance(payload['notes'], list) or any(not isinstance(n, str) for n in payload['notes']):
        raise ValueError('Invalid review metadata')
    def confidence(value):
        return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1
    if not confidence(payload['confidence']) or not isinstance(payload['fields'], list):
        raise ValueError('Invalid extraction confidence or fields')
    if not payload['fields'] or len(payload['fields']) > 500:
        raise ValueError('Missing or excessive extraction fields')
    for item in payload['fields']:
        if (not isinstance(item, dict) or set(item) != set(FIELD_SCHEMA['required'])
                or any(not isinstance(item[k], str) for k in ('name', 'value', 'evidence'))
                or not item['name'].strip() or not item['evidence'].strip()
                or type(item['page']) is not int or not 1 <= item['page'] <= 1000
                or not confidence(item['confidence'])):
            raise ValueError('Missing page/evidence or malformed field')
    fields = tuple(
        ExtractedTaxField(
            name=str(item["name"]),
            value=str(item["value"]),
            page=item["page"],
            evidence=str(item["evidence"]),
            confidence=float(item["confidence"]),
        )
        for item in payload["fields"]
    )
    return DocumentExtractionResult(
        document_type=str(payload["document_type"]),
        tax_category=str(payload["tax_category"]),
        issuer=payload["issuer"],
        document_date=payload["document_date"],
        tax_year=payload["tax_year"],
        fields=fields,
        extraction_method="GEMINI_DOCUMENT_VISION",
        confidence=float(payload["confidence"]),
        needs_human_review=bool(payload["needs_human_review"]),
        notes=tuple(str(note) for note in payload["notes"]),
    )
