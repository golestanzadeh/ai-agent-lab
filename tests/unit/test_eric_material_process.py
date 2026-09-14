from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from agent_lab.eric_adapter_contract import EricAdapterContract, OfficialMaterialKind
from agent_lab.eric_material_process import (
    EricMaterialProcessError,
    MaterialProcessOutcome,
    MaterialReviewStatus,
    SyntheticEricMaterialRecord,
    SyntheticMaterialReview,
    evaluate_synthetic_material_process,
)


NOW = datetime(2026, 9, 14, 19, 0, tzinfo=timezone.utc)


def record(kind: OfficialMaterialKind, suffix: str) -> SyntheticEricMaterialRecord:
    return SyntheticEricMaterialRecord(
        material_id=f"SYNTH-MATERIAL-{suffix}",
        registrant_id="SYNTH-REGISTRANT-001",
        kind=kind,
        artifact_reference="sha256:" + suffix.lower() * 64,
        source_locator=f"synthetic://eric/{suffix}",
        observed_at=NOW,
    )


def review(item: SyntheticEricMaterialRecord, suffix: str) -> SyntheticMaterialReview:
    return SyntheticMaterialReview(
        review_id=f"SYNTH-REVIEW-{suffix}",
        reviewer_id="SYNTH-REVIEWER-001",
        material_id=item.material_id,
        material_reference=item.identity.reference,
        kind=item.kind,
        reviewed_at=NOW + timedelta(minutes=1),
        status=MaterialReviewStatus.APPROVED,
    )


def complete_set():
    records = tuple(
        record(kind, str(index))
        for index, kind in enumerate(OfficialMaterialKind, start=1)
    )
    reviews = tuple(review(item, str(index)) for index, item in enumerate(records, start=1))
    return records, reviews


def test_complete_synthetic_process_keeps_official_status_blocked():
    records, reviews = complete_set()
    decision = evaluate_synthetic_material_process(
        EricAdapterContract(), records, reviews
    )
    assert (
        decision.outcome
        is MaterialProcessOutcome.SYNTHETIC_PROCESS_READY_OFFICIAL_STATUS_BLOCKED
    )
    assert decision.blockers == ()
    assert decision.official_status.value == "NOT_RECOVERED"
    assert decision.official_status_advancement_permitted is False
    assert decision.protected_material_retrieval_permitted is False
    assert decision.credential_access is False
    assert decision.network_calls == ()


def test_each_material_and_review_is_hash_bound_in_required_order():
    records, reviews = complete_set()
    decision = evaluate_synthetic_material_process(
        EricAdapterContract(), tuple(reversed(records)), tuple(reversed(reviews))
    )
    assert decision.material_references == tuple(item.identity.reference for item in records)
    assert decision.review_references == tuple(item.identity.reference for item in reviews)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("material_id", "REAL-MATERIAL", "SYNTH-"),
        ("registrant_id", "REAL-REGISTRANT", "SYNTH-"),
        ("source_locator", "https://www.elster.de/material", "synthetic"),
        ("data_classification", "PUBLIC", "SYNTHETIC"),
        ("eric_version", "43.2", "route binding"),
        ("procedure_code", "UFA12", "route binding"),
        ("tax_year", 2025, "route binding"),
    ],
)
def test_material_record_fails_closed_outside_synthetic_route(field, value, message):
    item = record(OfficialMaterialKind.INTERFACE_SPECIFICATION, "1")
    with pytest.raises(EricMaterialProcessError, match=message):
        replace(item, **{field: value})


def test_missing_or_duplicate_materials_block():
    records, reviews = complete_set()
    missing = evaluate_synthetic_material_process(
        EricAdapterContract(), records[:-1], reviews[:-1]
    )
    assert missing.outcome is MaterialProcessOutcome.BLOCKED
    duplicate = evaluate_synthetic_material_process(
        EricAdapterContract(), records + (records[0],), reviews
    )
    assert duplicate.outcome is MaterialProcessOutcome.BLOCKED
    assert "DUPLICATE_MATERIAL_ID" in duplicate.blockers


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"reviewer_id": "SYNTH-REGISTRANT-001"}, "NOT_INDEPENDENT"),
        ({"material_id": "SYNTH-MATERIAL-OTHER"}, "ID_MISMATCH"),
        ({"material_reference": "sha256:" + "0" * 64}, "BINDING_MISMATCH"),
        ({"reviewed_at": NOW - timedelta(seconds=1)}, "PREDATES"),
        ({"status": MaterialReviewStatus.REJECTED}, "NOT_APPROVED"),
    ],
)
def test_review_must_be_independent_ordered_approved_and_bound(mutation, message):
    records, reviews = complete_set()
    changed = (replace(reviews[0], **mutation),) + reviews[1:]
    decision = evaluate_synthetic_material_process(
        EricAdapterContract(), records, changed
    )
    assert decision.outcome is MaterialProcessOutcome.BLOCKED
    assert any(message in blocker for blocker in decision.blockers)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("official_status_advancement_permitted", True, "external capability"),
        ("protected_material_retrieval_permitted", True, "external capability"),
        ("credential_access", True, "external capability"),
        ("network_calls", ("https://example.invalid",), "network calls"),
    ],
)
def test_decision_cannot_be_forged_to_enable_external_capability(field, value, message):
    records, reviews = complete_set()
    decision = evaluate_synthetic_material_process(
        EricAdapterContract(), records, reviews
    )
    with pytest.raises(EricMaterialProcessError, match=message):
        replace(decision, **{field: value})


def test_record_mutation_invalidates_review_binding():
    records, reviews = complete_set()
    changed_records = (replace(records[0], source_locator="synthetic://eric/changed"),) + records[1:]
    decision = evaluate_synthetic_material_process(
        EricAdapterContract(), changed_records, reviews
    )
    assert decision.outcome is MaterialProcessOutcome.BLOCKED
    assert any("BINDING_MISMATCH" in blocker for blocker in decision.blockers)


def test_naive_timestamps_are_rejected():
    with pytest.raises(EricMaterialProcessError, match="timezone-aware"):
        replace(
            record(OfficialMaterialKind.INTERFACE_SPECIFICATION, "1"),
            observed_at=datetime(2026, 9, 14),
        )
