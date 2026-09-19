from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from agent_lab.elster_dry_run import (
    ApprovalStatus,
    ContentReleaseApproval,
    DestinationTransmissionApproval,
    SyntheticSubmissionEnvelope,
    SyntheticTaxSummary,
)
from agent_lab.elster_preview import build_synthetic_elster_preview
from agent_lab.elster_submission_lifecycle import (
    ElsterSubmissionLifecycleError,
    LifecycleOutcome,
    RECEIPT_PLACEHOLDER_MARKER,
    SyntheticAttemptOutcome,
    SyntheticReceiptPlaceholder,
    SyntheticSubmissionAttemptResult,
    evaluate_synthetic_submission_lifecycle,
)
from agent_lab.eric_adapter_contract import EricAdapterContract, OfficialMaterialKind
from agent_lab.eric_material_process import (
    MaterialReviewStatus,
    SyntheticEricMaterialRecord,
    SyntheticMaterialReview,
    evaluate_synthetic_material_process,
)


NOW = datetime(2026, 9, 14, 22, 0, tzinfo=timezone.utc)


def artifacts(*, retry: bool = True):
    envelope = SyntheticSubmissionEnvelope(
        case_id="SYNTH-CASE-LIFECYCLE",
        run_id="SYNTH-RUN-LIFECYCLE",
        tax_year=2024,
        procedure_code="UFA10",
        eric_version="44.3.6.0",
        purpose="synthetic lifecycle",
        data_classification="SYNTHETIC",
        payload=SyntheticTaxSummary(50000, 8000, 2500),
    )
    contract = EricAdapterContract()
    records = tuple(
        SyntheticEricMaterialRecord(
            material_id=f"SYNTH-MATERIAL-LIFECYCLE-{index}",
            registrant_id="SYNTH-REGISTRANT-LIFECYCLE",
            kind=kind,
            artifact_reference="sha256:" + str(index) * 64,
            source_locator=f"synthetic://lifecycle/{index}",
            observed_at=NOW - timedelta(hours=2),
        )
        for index, kind in enumerate(OfficialMaterialKind, start=1)
    )
    reviews = tuple(
        SyntheticMaterialReview(
            review_id=f"SYNTH-REVIEW-LIFECYCLE-{index}",
            reviewer_id="SYNTH-REVIEWER-LIFECYCLE",
            material_id=record.material_id,
            material_reference=record.identity.reference,
            kind=record.kind,
            reviewed_at=NOW - timedelta(hours=1),
            status=MaterialReviewStatus.APPROVED,
        )
        for index, record in enumerate(records, start=1)
    )
    preview = build_synthetic_elster_preview(
        envelope,
        contract,
        evaluate_synthetic_material_process(contract, records, reviews),
    )
    content = ContentReleaseApproval(
        approval_id="SYNTH-CONTENT-LIFECYCLE",
        approver_id="SYNTH-HUMAN-CONTENT",
        case_id=envelope.case_id,
        run_id=envelope.run_id,
        artifact_reference=envelope.artifact_identity.reference,
        artifact_version=envelope.artifact_identity.version,
        data_classification=envelope.data_classification,
        purpose=envelope.purpose,
        issued_at=NOW - timedelta(minutes=30),
        expires_at=NOW + timedelta(hours=1),
        status=ApprovalStatus.APPROVED,
    )
    destination = DestinationTransmissionApproval(
        approval_id="SYNTH-DESTINATION-LIFECYCLE",
        approver_id="SYNTH-HUMAN-DESTINATION",
        content_release_approval_id=content.approval_id,
        case_id=envelope.case_id,
        run_id=envelope.run_id,
        artifact_reference=envelope.artifact_identity.reference,
        artifact_version=envelope.artifact_identity.version,
        destination_identity="SYNTH-ELSTER-ACCEPTANCE-SERVER",
        channel="SYNTH-ERIC",
        purpose=envelope.purpose,
        issued_at=NOW - timedelta(minutes=20),
        expires_at=NOW + timedelta(hours=1),
        single_retry_permitted=retry,
        status=ApprovalStatus.APPROVED,
    )
    return envelope, preview, content, destination


def evaluate(*, retry=True, plans=(), results=(), now=NOW):
    envelope, preview, content, destination = artifacts(retry=retry)
    return evaluate_synthetic_submission_lifecycle(
        preview,
        envelope,
        content,
        destination,
        now=now,
        plans=plans,
        results=results,
    )


def result_for(plan, outcome, *, observed_at=None):
    observed_at = observed_at or NOW + timedelta(minutes=1)
    placeholder = None
    if outcome is SyntheticAttemptOutcome.SUCCESS_PLACEHOLDER:
        placeholder = SyntheticReceiptPlaceholder(
            receipt_id=f"SYNTH-RECEIPT-{plan.attempt_number}",
            plan_reference=plan.identity.reference,
            idempotency_key=plan.idempotency_key,
            recorded_at=observed_at,
        )
    return SyntheticSubmissionAttemptResult(
        result_id=f"SYNTH-RESULT-{plan.attempt_number}",
        plan_reference=plan.identity.reference,
        idempotency_key=plan.idempotency_key,
        attempt_number=plan.attempt_number,
        outcome=outcome,
        observed_at=observed_at,
        receipt_placeholder=placeholder,
    )


def test_initial_attempt_is_deterministic_inert_and_hash_bound():
    first = evaluate()
    second = evaluate()
    assert first == second
    assert first.outcome is LifecycleOutcome.ATTEMPT_PLANNED_NO_TRANSMITTER
    assert first.next_plan.attempt_number == 1
    assert first.next_plan.idempotency_key == first.idempotency_key
    assert first.next_plan.transmitter_available is False
    assert first.next_plan.transmission_permitted is False
    assert first.next_plan.credential_access is False
    assert first.next_plan.network_calls == ()


def test_open_plan_is_not_duplicated():
    first = evaluate()
    decision = evaluate(plans=(first.next_plan,))
    assert decision.next_plan is None
    assert decision.blockers == ("PLANNED_ATTEMPT_HAS_NO_SYNTHETIC_RESULT",)


def test_definite_failure_allows_exactly_one_retry_with_same_idempotency_key():
    first = evaluate()
    failed = result_for(first.next_plan, SyntheticAttemptOutcome.DEFINITE_FAILURE)
    retry = evaluate(plans=(first.next_plan,), results=(failed,), now=NOW + timedelta(minutes=2))
    assert retry.next_plan.attempt_number == 2
    assert retry.next_plan.idempotency_key == first.idempotency_key
    failed_again = result_for(
        retry.next_plan,
        SyntheticAttemptOutcome.DEFINITE_FAILURE,
        observed_at=NOW + timedelta(minutes=3),
    )
    exhausted = evaluate(
        plans=(first.next_plan, retry.next_plan),
        results=(failed, failed_again),
        now=NOW + timedelta(minutes=4),
    )
    assert exhausted.outcome is LifecycleOutcome.RETRY_EXHAUSTED
    assert exhausted.next_plan is None


def test_retry_requires_exact_destination_authorization():
    first = evaluate(retry=False)
    failed = result_for(first.next_plan, SyntheticAttemptOutcome.DEFINITE_FAILURE)
    decision = evaluate(
        retry=False,
        plans=(first.next_plan,),
        results=(failed,),
        now=NOW + timedelta(minutes=2),
    )
    assert decision.outcome is LifecycleOutcome.RETRY_NOT_AUTHORIZED
    assert decision.next_plan is None


def test_uncertain_outcome_never_retries():
    first = evaluate()
    uncertain = result_for(first.next_plan, SyntheticAttemptOutcome.UNCERTAIN)
    decision = evaluate(
        plans=(first.next_plan,),
        results=(uncertain,),
        now=NOW + timedelta(minutes=2),
    )
    assert decision.outcome is LifecycleOutcome.UNCERTAIN_BLOCKED
    assert decision.blockers == ("UNCERTAIN_OUTCOME_MUST_NEVER_AUTO_RETRY",)


def test_success_uses_only_an_explicit_placeholder_and_never_retries():
    first = evaluate()
    success = result_for(first.next_plan, SyntheticAttemptOutcome.SUCCESS_PLACEHOLDER)
    decision = evaluate(
        plans=(first.next_plan,),
        results=(success,),
        now=NOW + timedelta(minutes=2),
    )
    assert decision.outcome is LifecycleOutcome.COMPLETE_WITH_PLACEHOLDER
    assert decision.receipt_placeholder_reference == success.receipt_placeholder.identity.reference
    assert success.receipt_placeholder.marker == RECEIPT_PLACEHOLDER_MARKER
    assert success.receipt_placeholder.external_receipt_received is False


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("transmitter_available", True, "cannot enable transmission"),
        ("transmission_permitted", True, "cannot enable transmission"),
        ("credential_access", True, "cannot enable transmission"),
        ("network_calls", ("https://example.invalid",), "network calls"),
    ],
)
def test_attempt_plan_cannot_be_forged_to_enable_external_activity(field, value, message):
    plan = evaluate().next_plan
    with pytest.raises(ElsterSubmissionLifecycleError, match=message):
        replace(plan, **{field: value})


def test_receipt_placeholder_cannot_claim_external_receipt():
    plan = evaluate().next_plan
    receipt = result_for(plan, SyntheticAttemptOutcome.SUCCESS_PLACEHOLDER).receipt_placeholder
    with pytest.raises(ElsterSubmissionLifecycleError, match="external receipt"):
        replace(receipt, external_receipt_received=True)
    with pytest.raises(ElsterSubmissionLifecycleError, match="cannot be weakened"):
        replace(receipt, marker="REAL_RECEIPT")


def test_result_rejects_a_receipt_recorded_at_a_different_time():
    plan = evaluate().next_plan
    result = result_for(plan, SyntheticAttemptOutcome.SUCCESS_PLACEHOLDER)
    changed_receipt = replace(
        result.receipt_placeholder,
        recorded_at=result.observed_at + timedelta(seconds=1),
    )
    with pytest.raises(ElsterSubmissionLifecycleError, match="binding mismatch"):
        replace(result, receipt_placeholder=changed_receipt)


def test_lifecycle_decision_cannot_forge_outcome_or_receipt_binding():
    decision = evaluate()
    with pytest.raises(ElsterSubmissionLifecycleError, match="unknown lifecycle outcome"):
        replace(decision, outcome="COMPLETE")
    with pytest.raises(ElsterSubmissionLifecycleError, match="only complete lifecycle"):
        replace(decision, receipt_placeholder_reference="sha256:" + "0" * 64)
    with pytest.raises(ElsterSubmissionLifecycleError, match="idempotency binding mismatch"):
        replace(
            decision,
            next_plan=replace(decision.next_plan, idempotency_key="sha256:" + "0" * 64),
        )


def test_duplicate_reordered_and_mutated_history_fails_closed():
    first = evaluate().next_plan
    failed = result_for(first, SyntheticAttemptOutcome.DEFINITE_FAILURE)
    retry = evaluate(
        plans=(first,), results=(failed,), now=NOW + timedelta(minutes=2)
    ).next_plan
    with pytest.raises(ElsterSubmissionLifecycleError, match="unique and sequential"):
        evaluate(plans=(first, first), results=(failed, failed))
    with pytest.raises(ElsterSubmissionLifecycleError, match="binding mismatch"):
        evaluate(plans=(replace(first, preview_reference="sha256:" + "0" * 64),))
    with pytest.raises(ElsterSubmissionLifecycleError, match="binding mismatch"):
        evaluate(plans=(replace(first, plan_id="SYNTH-FORGED-PLAN"),))
    with pytest.raises(ElsterSubmissionLifecycleError, match="binding mismatch"):
        evaluate(
            plans=(first, retry),
            results=(failed, replace(failed, attempt_number=2)),
            now=NOW + timedelta(minutes=3),
        )


def test_expired_or_mismatched_approval_boundary_blocks_planning():
    envelope, preview, content, destination = artifacts()
    with pytest.raises(ElsterSubmissionLifecycleError, match="not ready"):
        evaluate_synthetic_submission_lifecycle(
            preview,
            envelope,
            content,
            destination,
            now=NOW + timedelta(hours=2),
        )
    with pytest.raises(ElsterSubmissionLifecycleError, match="binding mismatch"):
        evaluate_synthetic_submission_lifecycle(
            replace(preview, envelope_reference="sha256:" + "0" * 64),
            envelope,
            content,
            destination,
            now=NOW,
        )
