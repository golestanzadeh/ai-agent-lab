from dataclasses import replace
from datetime import datetime, timezone

import pytest

from agent_lab.human_declared_fact import (
    FactAssertionReference,
    FactConfirmationState,
    FactProvenanceKind,
    FactValidationStatus,
    FactValueType,
    HumanDeclaredFact,
    HumanDeclaredFactError,
    HumanFactValidationSpec,
    detect_fact_conflict,
    validate_human_fact,
)


REF = "sha256:" + "1" * 64


def fact(**changes):
    values = dict(
        case_id="CASE-001",
        tax_year=2024,
        semantic_key="CHILD.RESIDENCE_START",
        value="2024-01-01",
        declaring_actor_reference="OWNER:primary",
        confirmation_state=FactConfirmationState.CONFIRMED,
        declared_at=datetime(2026, 10, 4, tzinfo=timezone.utc),
        validation=validate_human_fact(
            "2024-01-01",
            HumanFactValidationSpec(FactValueType.DATE, date_must_be_within_tax_year=True),
            tax_year=2024,
        ),
        authorization_reference="OWNER-DIRECTIVE:DR03",
        audit_references=("AUDIT-00000001",),
        consuming_references=("RULE:DR03-RESIDENCE", "DECLARATION:ANLAGE-KIND"),
    )
    values.update(changes)
    return HumanDeclaredFact(**values)


def test_confirmed_valid_fact_is_consumable_and_identity_binds_lineage():
    item = fact()
    item.assert_consumable(case_id="CASE-001", tax_year=2024)
    assert item.source_type is FactProvenanceKind.HUMAN_DECLARATION
    assert item.validation.status is FactValidationStatus.PASS
    assert item.artifact_identity.reference.startswith("sha256:")
    assert replace(item, audit_references=("AUDIT-00000002",)).artifact_identity != item.artifact_identity
    assert replace(item, consuming_references=("RULE:OTHER",)).artifact_identity != item.artifact_identity


@pytest.mark.parametrize("state", [FactConfirmationState.PENDING, FactConfirmationState.REJECTED])
def test_unconfirmed_fact_cannot_be_consumed(state):
    with pytest.raises(HumanDeclaredFactError, match="not owner-confirmed"):
        replace(fact(), confirmation_state=state).assert_consumable(
            case_id="CASE-001", tax_year=2024
        )


def test_invalid_and_cross_case_facts_fail_closed():
    invalid = validate_human_fact(
        "2023-12-31",
        HumanFactValidationSpec(FactValueType.DATE, date_must_be_within_tax_year=True),
        tax_year=2024,
    )
    assert invalid.status is FactValidationStatus.FAIL
    assert invalid.errors == ("DATE_OUTSIDE_TAX_YEAR",)
    with pytest.raises(HumanDeclaredFactError, match="failed deterministic validation"):
        replace(fact(), validation=invalid).assert_consumable(case_id="CASE-001", tax_year=2024)
    with pytest.raises(HumanDeclaredFactError, match="outside"):
        fact().assert_consumable(case_id="CASE-OTHER", tax_year=2024)


def test_deterministic_allowed_value_range_and_format_validation():
    assert validate_human_fact(
        "PARENT_A",
        HumanFactValidationSpec(FactValueType.STRING, allowed_values=("PARENT_A", "PARENT_B")),
        tax_year=2024,
    ).status is FactValidationStatus.PASS
    failed = validate_human_fact(
        "1001",
        HumanFactValidationSpec(FactValueType.INTEGER, minimum="0", maximum="1000", pattern=r"\d+"),
        tax_year=2024,
    )
    assert failed.errors == ("ABOVE_MAXIMUM",)


def test_conflict_preserves_both_provenance_chains_without_overwrite():
    item = fact(value="2024-01-01")
    existing = FactAssertionReference(
        case_id="CASE-001",
        tax_year=2024,
        semantic_key=item.semantic_key,
        value="2024-02-01",
        provenance_kind=FactProvenanceKind.DOCUMENT,
        artifact_reference=REF,
        lineage_references=("DOCUMENT:doc-1", "EXTRACTION:extract-1"),
    )
    conflict = detect_fact_conflict(item, existing)
    assert conflict is not None and conflict.status == "FACT_CONFLICT"
    assert conflict.existing == existing
    assert conflict.human_declaration_reference == item.artifact_identity.reference
    assert conflict.human_declaration_lineage == ("OWNER-DIRECTIVE:DR03", "AUDIT-00000001")
    assert detect_fact_conflict(item, replace(existing, value=item.value)) is None


def test_conflict_comparison_rejects_cross_scope_and_fact_requires_audit_lineage():
    existing = FactAssertionReference(
        "CASE-OTHER", 2024, fact().semantic_key, "2024-02-01",
        FactProvenanceKind.FINANCIAL_SOURCE, REF, ("TX:1",),
    )
    with pytest.raises(HumanDeclaredFactError, match="identical fact scope"):
        detect_fact_conflict(fact(), existing)
    with pytest.raises(HumanDeclaredFactError, match="audit lineage"):
        replace(fact(), audit_references=())


def test_human_fact_cannot_masquerade_as_document_evidence():
    with pytest.raises(HumanDeclaredFactError, match="HUMAN_DECLARATION"):
        replace(fact(), source_type=FactProvenanceKind.DOCUMENT)


def test_validation_contract_rejects_malformed_spec_and_non_string_input():
    with pytest.raises(HumanDeclaredFactError, match="numeric bounds"):
        HumanFactValidationSpec(FactValueType.STRING, minimum="1")
    with pytest.raises(HumanDeclaredFactError, match="fact value must be a string"):
        validate_human_fact(None, HumanFactValidationSpec(FactValueType.STRING), tax_year=2024)  # type: ignore[arg-type]
