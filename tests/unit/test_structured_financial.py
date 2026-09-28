from decimal import Decimal

import pytest

from agent_lab.structured_financial import (
    SPARKASSE_HEADERS,
    StructuredFinancialIngestionError,
    ingest_sparkasse_csv,
)


def _csv(*rows: tuple[str, ...]) -> bytes:
    def line(values):
        return ";".join('"' + value.replace('"', '""') + '"' for value in values)
    return (line(SPARKASSE_HEADERS) + "\r\n" + "\r\n".join(line(row) for row in rows) + "\r\n").encode("cp1252")


def _row(*, booking="02.04.24", value="02.04.24", counterparty="School", iban="DE02", amount="-240,00", purpose="Fee"):
    values = {name: "" for name in SPARKASSE_HEADERS}
    values.update({"Auftragskonto": "DE01", "Buchungstag": booking, "Valutadatum": value, "Buchungstext": "FOLGELASTSCHRIFT", "Verwendungszweck": purpose, "Beguenstigter/Zahlungspflichtiger": counterparty, "Kontonummer/IBAN": iban, "Betrag": amount, "Waehrung": "EUR", "Kategorie": "Bildung"})
    return tuple(values[name] for name in SPARKASSE_HEADERS)


def test_ingests_without_destroying_originals_and_binds_case_source():
    result = ingest_sparkasse_csv(_csv(_row()), case_id="CASE-X", tax_year=2024, source_id="SFS-1")
    tx = result.transactions[0]
    assert result.case_id == "CASE-X"
    assert tx.source_id == "SFS-1"
    assert tx.booking_date.isoformat() == "2024-04-02"
    assert tx.amount == Decimal("-240.00")
    assert tx.direction == "DEBIT"
    assert dict(tx.originals)["Betrag"] == "-240,00"
    assert result.summary()["parsed_row_count"] == 1


def test_reports_exact_duplicates_without_deleting_them():
    row = _row()
    result = ingest_sparkasse_csv(_csv(row, row), case_id="CASE-X", tax_year=2024, source_id="SFS-1")
    assert len(result.transactions) == 2
    assert len(result.exact_duplicate_groups) == 1
    assert result.summary()["exact_duplicate_extra_row_count"] == 1


def test_reports_invalid_rows_and_keeps_valid_rows():
    result = ingest_sparkasse_csv(_csv(_row(), _row(booking="bad")), case_id="CASE-X", tax_year=2024, source_id="SFS-1")
    assert len(result.transactions) == 1
    assert result.invalid_rows == ({"source_row_number": 3, "errors": ["BOOKING_DATE_INVALID"]},)


def test_detects_reversal_and_own_account_transfer():
    debit = _row(counterparty="Vendor", iban="DE01", amount="-10,00")
    credit = _row(booking="03.04.24", value="03.04.24", counterparty="Vendor", iban="DE01", amount="10,00")
    result = ingest_sparkasse_csv(_csv(debit, credit), case_id="CASE-X", tax_year=2024, source_id="SFS-1")
    assert len(result.reversal_pairs) == 1
    assert len(result.own_account_transfer_rows) == 2


def test_rejects_schema_and_scope_ambiguity():
    with pytest.raises(StructuredFinancialIngestionError, match="case_id"):
        ingest_sparkasse_csv(_csv(_row()), case_id="", tax_year=2024, source_id="SFS-1")
    malformed = _csv(_row()).replace(b'"Kategorie"', b'"Other"', 1)
    with pytest.raises(StructuredFinancialIngestionError, match="schema"):
        ingest_sparkasse_csv(malformed, case_id="CASE-X", tax_year=2024, source_id="SFS-1")
