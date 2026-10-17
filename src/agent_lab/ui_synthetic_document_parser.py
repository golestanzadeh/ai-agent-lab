"""Closed parser for one synthetic UTF-8 wage-statement fixture format."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re


PARSER_SCHEMA = "ui25.synthetic-wage-statement/1"
DOCUMENT_TYPE = "SYNTHETIC_WAGE_STATEMENT"
MAX_CONTENT_BYTES = 32_768
CONTENT_TYPE = "text/plain"
_EMPLOYER = re.compile(r"^TEST-EMPLOYER-[A-Z0-9_-]{1,48}$")
_FIELDS = (
    "DOCUMENT_TYPE", "TAX_YEAR", "EMPLOYER_ID",
    "GROSS_EMPLOYMENT_INCOME", "WITHHELD_WAGE_TAX", "CURRENCY",
)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


@dataclass(frozen=True, slots=True)
class SyntheticExtraction:
    schema_version: str
    document_type: str
    tax_year: int
    employer_id: str
    gross_employment_income: str
    withheld_wage_tax: str
    currency: str
    field_lineage: tuple[tuple[str, int], ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "document_type": self.document_type,
            "tax_year": self.tax_year,
            "employer_id": self.employer_id,
            "gross_employment_income": self.gross_employment_income,
            "withheld_wage_tax": self.withheld_wage_tax,
            "currency": self.currency,
            "field_lineage": [
                {"field": field, "source_line": line}
                for field, line in self.field_lineage
            ],
        }

    @property
    def digest(self) -> str:
        return "sha256:" + hashlib.sha256(_canonical(self.as_dict())).hexdigest()


def _amount(raw: str, field: str) -> str:
    if not re.fullmatch(r"(?:0|[1-9][0-9]{0,8})\.[0-9]{2}", raw):
        raise ValueError(f"{field} must be a non-negative decimal with two digits")
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"{field} is invalid") from exc
    if value > Decimal("999999999.99"):
        raise ValueError(f"{field} is outside the bounded range")
    return format(value, ".2f")


def parse_synthetic_wage_statement(data: bytes, content_type: str) -> SyntheticExtraction:
    if content_type != CONTENT_TYPE:
        raise ValueError("unsupported synthetic document content type")
    if not isinstance(data, bytes) or not data or len(data) > MAX_CONTENT_BYTES:
        raise ValueError("synthetic document size is invalid")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("synthetic document is not valid UTF-8") from exc
    if "\r" in text or not text.endswith("\n"):
        raise ValueError("synthetic document must use canonical LF lines")
    values: dict[str, str] = {}
    lines: dict[str, int] = {}
    for number, line in enumerate(text.splitlines(), start=1):
        if not line or line.count("=") != 1:
            raise ValueError("synthetic document contains a malformed or ambiguous line")
        key, value = line.split("=", 1)
        if key not in _FIELDS or not value or value != value.strip():
            raise ValueError("synthetic document contains an unsupported field")
        if key in values:
            raise ValueError("synthetic document contains a duplicate field")
        values[key] = value
        lines[key] = number
    if tuple(values) != _FIELDS:
        raise ValueError("synthetic document fields are missing, reordered, or conflicting")
    if values["DOCUMENT_TYPE"] != DOCUMENT_TYPE:
        raise ValueError("unsupported synthetic document type")
    if values["TAX_YEAR"] != "2025":
        raise ValueError("synthetic extraction is restricted to tax year 2025")
    if not _EMPLOYER.fullmatch(values["EMPLOYER_ID"]):
        raise ValueError("invalid synthetic employer identifier")
    if values["CURRENCY"] != "EUR":
        raise ValueError("unsupported currency")
    gross = _amount(values["GROSS_EMPLOYMENT_INCOME"], "gross employment income")
    withheld = _amount(values["WITHHELD_WAGE_TAX"], "withheld wage tax")
    if Decimal(withheld) > Decimal(gross):
        raise ValueError("withheld wage tax conflicts with gross employment income")
    return SyntheticExtraction(
        schema_version=PARSER_SCHEMA,
        document_type=DOCUMENT_TYPE,
        tax_year=2025,
        employer_id=values["EMPLOYER_ID"],
        gross_employment_income=gross,
        withheld_wage_tax=withheld,
        currency="EUR",
        field_lineage=tuple((field, lines[field]) for field in _FIELDS),
    )
