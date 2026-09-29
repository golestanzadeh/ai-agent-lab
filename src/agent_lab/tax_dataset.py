"""Evidence-first tax dataset model for D-022."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Iterable

@dataclass(frozen=True, slots=True)
class TaxDatasetField:
    key: str
    value: str
    document: str
    page: int | None
    evidence: str
    confidence: float
    tax_category: str
    status: str = "CANDIDATE"
    payment_year: int | None = None
    service_year: int | None = None
    address_from: str | None = None
    address_to: str | None = None
    route_relevant: bool = False


def validate_fields(fields: Iterable[TaxDatasetField], *, threshold: float = 0.85) -> list[str]:
    issues: list[str] = []
    for field in fields:
        if not field.document or not field.evidence.strip():
            issues.append(f"{field.key}:MISSING_EVIDENCE")
        if not 0 <= field.confidence <= 1 or field.confidence < threshold:
            issues.append(f"{field.key}:LOW_CONFIDENCE")
        if field.route_relevant and not (field.address_from and field.address_to):
            issues.append(f"{field.key}:ROUTE_ENDPOINTS_REQUIRED")
        if field.payment_year and field.service_year and field.payment_year != field.service_year:
            issues.append(f"{field.key}:CROSS_YEAR_REVIEW")
    return issues


def serialize_dataset(fields: Iterable[TaxDatasetField]) -> list[dict[str, object]]:
    return [asdict(field) for field in fields]
