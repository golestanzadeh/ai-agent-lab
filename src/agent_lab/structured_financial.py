"""Deterministic, case-scoped ingestion for immutable bank CSV evidence.

The module parses source rows and reports data quality only.  It deliberately
does not infer tax eligibility from bank descriptions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import csv
import hashlib
import io
from typing import Iterable


SPARKASSE_HEADERS = (
    "Auftragskonto", "Buchungstag", "Valutadatum", "Buchungstext",
    "Verwendungszweck", "Glaeubiger ID", "Mandatsreferenz",
    "Kundenreferenz (End-to-End)", "Sammlerreferenz",
    "Lastschrift Ursprungsbetrag", "Auslagenersatz Ruecklastschrift",
    "Beguenstigter/Zahlungspflichtiger", "Kontonummer/IBAN",
    "BIC (SWIFT-Code)", "Betrag", "Waehrung", "Info", "Kategorie",
)


class StructuredFinancialIngestionError(ValueError):
    """Fail-closed structured-source parsing error."""


@dataclass(frozen=True, slots=True)
class FinancialTransaction:
    row_id: str
    source_id: str
    source_row_number: int
    booking_date: date
    value_date: date
    transaction_type: str
    counterparty: str
    counterparty_iban: str | None
    description: str
    amount: Decimal
    currency: str
    direction: str
    bank_category: str | None
    originals: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class StructuredFinancialIngestion:
    schema_version: int
    case_id: str
    tax_year: int
    source_id: str
    source_sha256: str
    encoding: str
    delimiter: str
    transactions: tuple[FinancialTransaction, ...]
    invalid_rows: tuple[dict[str, object], ...]
    exact_duplicate_groups: tuple[tuple[str, ...], ...]
    probable_duplicate_groups: tuple[tuple[str, ...], ...]
    reversal_pairs: tuple[tuple[str, str], ...]
    own_account_transfer_rows: tuple[str, ...]

    def summary(self) -> dict[str, object]:
        dates = [row.booking_date for row in self.transactions]
        currencies = sorted({row.currency for row in self.transactions})
        return {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "tax_year": self.tax_year,
            "source_id": self.source_id,
            "source_sha256": self.source_sha256,
            "parsed_row_count": len(self.transactions),
            "invalid_row_count": len(self.invalid_rows),
            "date_start": min(dates).isoformat() if dates else None,
            "date_end": max(dates).isoformat() if dates else None,
            "currencies": currencies,
            "exact_duplicate_group_count": len(self.exact_duplicate_groups),
            "exact_duplicate_extra_row_count": sum(len(g) - 1 for g in self.exact_duplicate_groups),
            "probable_duplicate_group_count": len(self.probable_duplicate_groups),
            "reversal_pair_count": len(self.reversal_pairs),
            "own_account_transfer_count": len(self.own_account_transfer_rows),
        }

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        for row in data["transactions"]:
            row["booking_date"] = row["booking_date"].isoformat()
            row["value_date"] = row["value_date"].isoformat()
            row["amount"] = str(row["amount"])
            row["originals"] = dict(row["originals"])
        return data


def ingest_sparkasse_csv(
    payload: bytes,
    *,
    case_id: str,
    tax_year: int,
    source_id: str,
) -> StructuredFinancialIngestion:
    if not case_id.strip() or not source_id.strip():
        raise StructuredFinancialIngestionError("case_id and source_id are required")
    if tax_year < 1900 or tax_year > 9999:
        raise StructuredFinancialIngestionError("invalid tax_year")
    try:
        text = payload.decode("cp1252")
    except UnicodeDecodeError as exc:
        raise StructuredFinancialIngestionError("CSV is not valid cp1252") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=";", quotechar='"')
    if tuple(reader.fieldnames or ()) != SPARKASSE_HEADERS:
        raise StructuredFinancialIngestionError("unexpected CSV schema")

    source_sha = hashlib.sha256(payload).hexdigest()
    valid: list[FinancialTransaction] = []
    invalid: list[dict[str, object]] = []
    for row_number, raw in enumerate(reader, start=2):
        if None in raw or tuple(raw) != SPARKASSE_HEADERS:
            invalid.append({"source_row_number": row_number, "errors": ["ROW_SHAPE_INVALID"]})
            continue
        errors: list[str] = []
        booking = _date(raw["Buchungstag"], errors, "BOOKING_DATE_INVALID")
        value = _date(raw["Valutadatum"], errors, "VALUE_DATE_INVALID")
        amount = _amount(raw["Betrag"], errors)
        currency = raw["Waehrung"].strip().upper()
        if not currency:
            errors.append("CURRENCY_EMPTY")
        if errors:
            invalid.append({"source_row_number": row_number, "errors": sorted(set(errors))})
            continue
        assert booking is not None and value is not None and amount is not None
        original_items = tuple((name, raw[name]) for name in SPARKASSE_HEADERS)
        canonical = "\x1f".join(value for _, value in original_items)
        row_id = "TX-" + hashlib.sha256(
            f"{source_id}\x1e{row_number}\x1e{canonical}".encode("utf-8")
        ).hexdigest()[:24]
        valid.append(FinancialTransaction(
            row_id=row_id,
            source_id=source_id,
            source_row_number=row_number,
            booking_date=booking,
            value_date=value,
            transaction_type=raw["Buchungstext"].strip(),
            counterparty=raw["Beguenstigter/Zahlungspflichtiger"].strip(),
            counterparty_iban=_optional(raw["Kontonummer/IBAN"]),
            description=raw["Verwendungszweck"].strip(),
            amount=amount,
            currency=currency,
            direction="CREDIT" if amount > 0 else "DEBIT" if amount < 0 else "ZERO",
            bank_category=_optional(raw["Kategorie"]),
            originals=original_items,
        ))

    exact = _groups(valid, lambda r: tuple(value for _, value in r.originals))
    probable = _groups(valid, lambda r: (
        r.booking_date, r.value_date, r.amount, r.currency,
        _fold(r.counterparty), _fold(r.description),
    ), exclude=exact)
    reversals = _reversal_pairs(valid)
    own = tuple(r.row_id for r in valid if r.counterparty_iban and _iban(r.counterparty_iban) == _iban(dict(r.originals)["Auftragskonto"]))
    return StructuredFinancialIngestion(
        schema_version=1, case_id=case_id, tax_year=tax_year,
        source_id=source_id, source_sha256=source_sha, encoding="cp1252",
        delimiter=";", transactions=tuple(valid), invalid_rows=tuple(invalid),
        exact_duplicate_groups=exact, probable_duplicate_groups=probable,
        reversal_pairs=reversals, own_account_transfer_rows=own,
    )


def _date(value: str, errors: list[str], code: str) -> date | None:
    try:
        return datetime.strptime(value.strip(), "%d.%m.%y").date()
    except ValueError:
        errors.append(code)
        return None


def _amount(value: str, errors: list[str]) -> Decimal | None:
    try:
        return Decimal(value.strip().replace(".", "").replace(",", "."))
    except InvalidOperation:
        errors.append("AMOUNT_INVALID")
        return None


def _optional(value: str) -> str | None:
    stripped = value.strip()
    return stripped or None


def _fold(value: str) -> str:
    return " ".join(value.casefold().split())


def _iban(value: str) -> str:
    return "".join(value.upper().split())


def _groups(
    rows: Iterable[FinancialTransaction],
    key,
    *,
    exclude: tuple[tuple[str, ...], ...] = (),
) -> tuple[tuple[str, ...], ...]:
    excluded = {row_id for group in exclude for row_id in group}
    grouped: dict[object, list[str]] = {}
    for row in rows:
        if row.row_id not in excluded:
            grouped.setdefault(key(row), []).append(row.row_id)
    return tuple(tuple(ids) for ids in grouped.values() if len(ids) > 1)


def _reversal_pairs(rows: Iterable[FinancialTransaction]) -> tuple[tuple[str, str], ...]:
    ordered = tuple(rows)
    pairs: list[tuple[str, str]] = []
    used: set[str] = set()
    for index, left in enumerate(ordered):
        if left.row_id in used or left.amount == 0:
            continue
        for right in ordered[index + 1:]:
            if right.row_id in used or right.amount != -left.amount or right.currency != left.currency:
                continue
            if _fold(right.counterparty) != _fold(left.counterparty):
                continue
            if abs((right.booking_date - left.booking_date).days) > 62:
                continue
            pairs.append((left.row_id, right.row_id))
            used.update((left.row_id, right.row_id))
            break
    return tuple(pairs)
