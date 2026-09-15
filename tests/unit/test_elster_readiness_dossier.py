from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from agent_lab.artifact_identity import canonical_json
from agent_lab.elster_dry_run import (
    ApprovalStatus,
    ContentReleaseApproval,
    DestinationTransmissionApproval,
    SyntheticSubmissionEnvelope,
    SyntheticTaxSummary,
)
from agent_lab.elster_preview import build_synthetic_elster_preview
from agent_lab.elster_readiness_dossier import (
    DossierOutcome,
    EVIDENCE_KINDS,
    EXTERNAL_READINESS_BLOCKERS,
    ElsterReadinessDossierError,
    build_synthetic_elster_readiness_dossier,
)
from agent_lab.elster_submission_audit import (
    build_synthetic_lifecycle_audit,
    restore_synthetic_lifecycle_audit,
)
from agent_lab.elster_submission_lifecycle import (
    SyntheticAttemptOutcome,
    SyntheticReceiptPlaceholder,
    SyntheticSubmissionAttemptResult,
    evaluate_synthetic_submission_lifecycle,
)
from agent_lab.eric_adapter_contract import (
    DENIED_CAPABILITIES,
    EricAdapterContract,
    OfficialMaterialKind,
)
from agent_lab.eric_material_process import (
    MaterialReviewStatus,
    SyntheticEricMaterialRecord,
    SyntheticMaterialReview,
    evaluate_synthetic_material_process,
)


NOW = datetime(2026, 9, 15, 1, 0, tzinfo=timezone.utc)


def upstream(case_suffix="DOSSIER"):
    envelope = SyntheticSubmissionEnvelope(
        case_id=f"SYNTH-CASE-{case_suffix}",
        run_id=f"SYNTH-RUN-{case_suffix}",
        tax_year=2024,
        procedure_code="UFA10",
        eric_version="41.2",
        purpose="synthetic dossier purpose excluded from output",
        data_classification="SYNTHETIC",
        payload=SyntheticTaxSummary(65432, 7654, 3456),
    )
    contract = EricAdapterContract()
    records = tuple(
        SyntheticEricMaterialRecord(
            material_id=f"SYNTH-MATERIAL-{case_suffix}-{index}",
            registrant_id=f"SYNTH-REGISTRANT-{case_suffix}",
            kind=kind,
            artifact_reference="sha256:" + str(index) * 64,
            source_locator=f"synthetic://dossier/{case_suffix}/{index}",
            observed_at=NOW - timedelta(hours=2),
        )
        for index, kind in enumerate(OfficialMaterialKind, start=1)
    )
    reviews = tuple(
        SyntheticMaterialReview(
            review_id=f"SYNTH-REVIEW-{case_suffix}-{index}",
            reviewer_id=f"SYNTH-REVIEWER-{case_suffix}",
            material_id=record.material_id,
            material_reference=record.identity.reference,
            kind=record.kind,
            reviewed_at=NOW - timedelta(hours=1),
            status=MaterialReviewStatus.APPROVED,
        )
        for index, record in enumerate(records, start=1)
    )
    material_decision = evaluate_synthetic_material_process(contract, records, reviews)
    preview = build_synthetic_elster_preview(envelope, contract, material_decision)
    content = ContentReleaseApproval(
        approval_id=f"SYNTH-CONTENT-{case_suffix}",
        approver_id="SYNTH-CONTENT-APPROVER",
        case_id=envelope.case_id,
        run_id=envelope.run_id,
        artifact_reference=envelope.artifact_identity.reference,
        artifact_version=envelope.artifact_identity.version,
        data_classification="SYNTHETIC",
        purpose=envelope.purpose,
        issued_at=NOW - timedelta(minutes=30),
        expires_at=NOW + timedelta(hours=2),
        status=ApprovalStatus.APPROVED,
    )
    destination = DestinationTransmissionApproval(
        approval_id=f"SYNTH-DESTINATION-{case_suffix}",
        approver_id="SYNTH-DESTINATION-APPROVER",
        content_release_approval_id=content.approval_id,
        case_id=envelope.case_id,
        run_id=envelope.run_id,
        artifact_reference=envelope.artifact_identity.reference,
        artifact_version=envelope.artifact_identity.version,
        destination_identity="SYNTH-ELSTER-ACCEPTANCE-SERVER",
        channel="SYNTH-ERIC",
        purpose=envelope.purpose,
        issued_at=NOW - timedelta(minutes=20),
        expires_at=NOW + timedelta(hours=2),
        single_retry_permitted=True,
        status=ApprovalStatus.APPROVED,
    )
    plan = evaluate_synthetic_submission_lifecycle(
        preview, envelope, content, destination, now=NOW
    ).next_plan
    audit = build_synthetic_lifecycle_audit(preview, (plan,), ())
    recovery = restore_synthetic_lifecycle_audit(
        audit.to_json(),
        expected_case_id=audit.case_id,
        expected_run_id=audit.run_id,
        expected_idempotency_key=audit.idempotency_key,
    )
    return envelope, contract, material_decision, preview, plan, audit, recovery


def dossier(items=None):
    items = items or upstream()
    envelope, contract, material_decision, preview, _, audit, recovery = items
    return build_synthetic_elster_readiness_dossier(
        envelope, contract, material_decision, preview, audit, recovery
    )


def test_dossier_is_deterministic_complete_and_explicitly_blocked():
    first = dossier()
    second = dossier()
    assert first == second
    assert first.artifact_identity == second.artifact_identity
    assert first.outcome is DossierOutcome.SYNTHETIC_DOSSIER_COMPLETE_EXTERNAL_READINESS_BLOCKED
    assert tuple(item.kind for item in first.evidence) == EVIDENCE_KINDS
    assert first.blockers == EXTERNAL_READINESS_BLOCKERS
    assert first.denied_capabilities == DENIED_CAPABILITIES
    assert first.external_readiness is False
    assert first.transmission_permitted is False
    assert first.network_calls == ()


def test_dossier_excludes_tax_values_and_purpose_text():
    items = upstream()
    rendered = canonical_json(dossier(items))
    for excluded in ("65432", "7654", "3456", items[0].purpose, "gross_wages"):
        assert excluded not in rendered


def test_envelope_or_contract_mutation_breaks_lineage():
    items = upstream()
    with pytest.raises(ElsterReadinessDossierError, match="upstream P1 evidence"):
        build_synthetic_elster_readiness_dossier(
            replace(items[0], payload=replace(items[0].payload, deductible_expenses_eur=3457)),
            items[1], items[2], items[3], items[5], items[6],
        )
    with pytest.raises(ElsterReadinessDossierError, match="upstream P1 evidence"):
        build_synthetic_elster_readiness_dossier(
            items[0], items[1],
            replace(items[2], contract_reference="sha256:" + "0" * 64),
            items[3], items[5], items[6],
        )


def test_incomplete_material_evidence_is_rejected():
    items = upstream()
    incomplete = replace(items[2], material_references=items[2].material_references[:2])
    with pytest.raises(ElsterReadinessDossierError, match="complete synthetic material"):
        build_synthetic_elster_readiness_dossier(
            items[0], items[1], incomplete, items[3], items[5], items[6]
        )


def test_audit_and_recovery_must_bind_exact_preview_and_snapshot():
    items = upstream()
    with pytest.raises(ElsterReadinessDossierError, match="lifecycle evidence"):
        build_synthetic_elster_readiness_dossier(
            items[0], items[1], items[2], items[3], items[5],
            replace(items[6], snapshot_reference="sha256:" + "0" * 64),
        )
    other = upstream("OTHER")
    with pytest.raises(ElsterReadinessDossierError, match="lifecycle evidence"):
        build_synthetic_elster_readiness_dossier(
            items[0], items[1], items[2], items[3], other[5], other[6]
        )


def test_completed_lifecycle_state_is_preserved_without_external_claim():
    items = upstream()
    plan = items[4]
    observed = NOW + timedelta(minutes=1)
    receipt = SyntheticReceiptPlaceholder(
        receipt_id="SYNTH-RECEIPT-DOSSIER",
        plan_reference=plan.identity.reference,
        idempotency_key=plan.idempotency_key,
        recorded_at=observed,
    )
    result = SyntheticSubmissionAttemptResult(
        result_id="SYNTH-RESULT-DOSSIER",
        plan_reference=plan.identity.reference,
        idempotency_key=plan.idempotency_key,
        attempt_number=1,
        outcome=SyntheticAttemptOutcome.SUCCESS_PLACEHOLDER,
        observed_at=observed,
        receipt_placeholder=receipt,
    )
    audit = build_synthetic_lifecycle_audit(items[3], (plan,), (result,))
    recovery = restore_synthetic_lifecycle_audit(
        audit.to_json(),
        expected_case_id=audit.case_id,
        expected_run_id=audit.run_id,
        expected_idempotency_key=audit.idempotency_key,
    )
    completed = build_synthetic_elster_readiness_dossier(
        items[0], items[1], items[2], items[3], audit, recovery
    )
    assert completed.lifecycle_state == "COMPLETE_WITH_PLACEHOLDER"
    assert completed.external_readiness is False


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("blockers", (), "blockers cannot be weakened"),
        ("denied_capabilities", (), "capability policy"),
        ("data_classification", "REAL", "privacy boundary"),
        ("contains_tax_values", True, "privacy boundary"),
        ("external_readiness", True, "external capability"),
        ("mapping_permitted", True, "external capability"),
        ("validation_permitted", True, "external capability"),
        ("signing_permitted", True, "external capability"),
        ("transmission_permitted", True, "external capability"),
        ("credential_access", True, "external capability"),
        ("network_calls", ("https://example.invalid",), "network calls"),
    ],
)
def test_dossier_cannot_be_forged_past_the_external_boundary(field, value, message):
    with pytest.raises(ElsterReadinessDossierError, match=message):
        replace(dossier(), **{field: value})


def test_evidence_order_removal_and_duplicate_are_rejected():
    item = dossier()
    with pytest.raises(ElsterReadinessDossierError, match="exact ordered"):
        replace(item, evidence=tuple(reversed(item.evidence)))
    with pytest.raises(ElsterReadinessDossierError, match="exact ordered"):
        replace(item, evidence=item.evidence[:-1])
    duplicate = replace(item.evidence[-1], artifact_reference=item.evidence[0].artifact_reference)
    with pytest.raises(ElsterReadinessDossierError, match="unique"):
        replace(item, evidence=item.evidence[:-1] + (duplicate,))


def test_route_lifecycle_and_evidence_types_cannot_be_forged():
    item = dossier()
    with pytest.raises(ElsterReadinessDossierError, match="route binding"):
        replace(item, tax_year=2025)
    with pytest.raises(ElsterReadinessDossierError, match="unknown recovered"):
        replace(item, lifecycle_state="TRANSMITTED")
    with pytest.raises(ElsterReadinessDossierError, match="exact ordered"):
        replace(item, evidence=(object(),) + item.evidence[1:])
