from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from agent_lab.elster_dry_run import SyntheticSubmissionEnvelope, SyntheticTaxSummary
from agent_lab.elster_preview import (
    ElsterPreviewError,
    PREVIEW_DISCLAIMER,
    PreviewOutcome,
    build_synthetic_elster_preview,
)
from agent_lab.eric_adapter_contract import EricAdapterContract, OfficialMaterialKind
from agent_lab.eric_material_process import (
    MaterialReviewStatus,
    SyntheticEricMaterialRecord,
    SyntheticMaterialReview,
    evaluate_synthetic_material_process,
)


NOW = datetime(2026, 9, 14, 20, 0, tzinfo=timezone.utc)


def envelope() -> SyntheticSubmissionEnvelope:
    return SyntheticSubmissionEnvelope(
        case_id="SYNTH-CASE-PREVIEW",
        run_id="SYNTH-RUN-PREVIEW",
        tax_year=2024,
        procedure_code="UFA10",
        eric_version="41.2",
        purpose="synthetic preview\nline-injection check",
        data_classification="SYNTHETIC",
        payload=SyntheticTaxSummary(50000, 8000, 2500),
    )


def material_decision(contract: EricAdapterContract):
    records = tuple(
        SyntheticEricMaterialRecord(
            material_id=f"SYNTH-MATERIAL-PREVIEW-{index}",
            registrant_id="SYNTH-REGISTRANT-PREVIEW",
            kind=kind,
            artifact_reference="sha256:" + str(index) * 64,
            source_locator=f"synthetic://preview/{index}",
            observed_at=NOW,
        )
        for index, kind in enumerate(OfficialMaterialKind, start=1)
    )
    reviews = tuple(
        SyntheticMaterialReview(
            review_id=f"SYNTH-REVIEW-PREVIEW-{index}",
            reviewer_id="SYNTH-REVIEWER-PREVIEW",
            material_id=item.material_id,
            material_reference=item.identity.reference,
            kind=item.kind,
            reviewed_at=NOW + timedelta(minutes=1),
            status=MaterialReviewStatus.APPROVED,
        )
        for index, item in enumerate(records, start=1)
    )
    return evaluate_synthetic_material_process(contract, records, reviews)


def preview():
    contract = EricAdapterContract()
    return build_synthetic_elster_preview(
        envelope(), contract, material_decision(contract)
    )


def test_preview_is_deterministic_complete_and_hash_bound():
    item = preview()
    assert item.artifact_identity == item.artifact_identity
    assert item.outcome is PreviewOutcome.SYNTHETIC_PREVIEW_READY_OFFICIAL_MAPPING_BLOCKED
    for expected in (
        "SYNTHETIC ELSTER PREVIEW",
        "SYNTH-CASE-PREVIEW",
        "SYNTH-RUN-PREVIEW",
        "ERiC 41.2 / UFA10 / tax year 2024",
        "Gross wages (EUR): 50000",
        "Withheld wage tax (EUR): 8000",
        "Deductible expenses (EUR): 2500",
        "Official material status: NOT_RECOVERED",
        PREVIEW_DISCLAIMER,
    ):
        assert expected in item.rendered_text


def test_purpose_cannot_inject_an_unlabelled_preview_line():
    text = preview().rendered_text
    assert 'Purpose: "synthetic preview\\nline-injection check"' in text
    assert "Purpose: synthetic preview\nline-injection check" not in text


def test_envelope_mutation_changes_preview_identity():
    original = envelope()
    changed = replace(
        original,
        payload=replace(original.payload, deductible_expenses_eur=2501),
    )
    contract = EricAdapterContract()
    decision = material_decision(contract)
    first = build_synthetic_elster_preview(original, contract, decision)
    second = build_synthetic_elster_preview(changed, contract, decision)
    assert first.artifact_identity != second.artifact_identity
    assert first.envelope_reference != second.envelope_reference


def test_material_process_must_bind_the_exact_contract():
    contract = EricAdapterContract()
    decision = material_decision(contract)
    with pytest.raises(ElsterPreviewError, match="binding mismatch"):
        build_synthetic_elster_preview(
            envelope(),
            contract,
            replace(decision, contract_reference="sha256:" + "0" * 64),
        )


def test_incomplete_material_process_blocks_preview():
    contract = EricAdapterContract()
    decision = replace(
        material_decision(contract),
        outcome="BLOCKED",
        blockers=("SYNTHETIC_TEST_BLOCKER",),
    )
    with pytest.raises(ElsterPreviewError, match="not complete"):
        build_synthetic_elster_preview(envelope(), contract, decision)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("transmission_permitted", True, "external capability"),
        ("credential_access", True, "external capability"),
        ("network_calls", ("https://example.invalid",), "network calls"),
        ("disclaimer", "safe", "cannot be weakened"),
        ("official_material_status", "VERIFIED", "NOT_RECOVERED"),
    ],
)
def test_preview_cannot_be_forged_or_weakened(field, value, message):
    with pytest.raises(ElsterPreviewError, match=message):
        replace(preview(), **{field: value})


def test_unknown_input_types_are_rejected():
    contract = EricAdapterContract()
    decision = material_decision(contract)
    with pytest.raises(ElsterPreviewError, match="SyntheticSubmissionEnvelope"):
        build_synthetic_elster_preview(object(), contract, decision)
