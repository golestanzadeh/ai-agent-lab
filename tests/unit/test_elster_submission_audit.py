from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json

import pytest

from agent_lab.elster_dry_run import (
    ApprovalStatus,
    ContentReleaseApproval,
    DestinationTransmissionApproval,
    SyntheticSubmissionEnvelope,
    SyntheticTaxSummary,
)
from agent_lab.elster_preview import build_synthetic_elster_preview
from agent_lab.elster_submission_audit import (
    ElsterSubmissionAuditError,
    RecoveredLifecycleState,
    build_synthetic_lifecycle_audit,
    restore_synthetic_lifecycle_audit,
)
from agent_lab.elster_submission_lifecycle import (
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


NOW = datetime(2026, 9, 15, 0, 0, tzinfo=timezone.utc)


def context(case_suffix="AUDIT", *, retry=True):
    envelope = SyntheticSubmissionEnvelope(
        case_id=f"SYNTH-CASE-{case_suffix}",
        run_id=f"SYNTH-RUN-{case_suffix}",
        tax_year=2024,
        procedure_code="UFA10",
        eric_version="44.3.6.0",
        purpose="private synthetic purpose excluded from audit",
        data_classification="SYNTHETIC",
        payload=SyntheticTaxSummary(54321, 8765, 2345),
    )
    contract = EricAdapterContract()
    records = tuple(
        SyntheticEricMaterialRecord(
            material_id=f"SYNTH-MATERIAL-{case_suffix}-{index}",
            registrant_id=f"SYNTH-REGISTRANT-{case_suffix}",
            kind=kind,
            artifact_reference="sha256:" + str(index) * 64,
            source_locator=f"synthetic://audit/{case_suffix}/{index}",
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
    preview = build_synthetic_elster_preview(
        envelope, contract, evaluate_synthetic_material_process(contract, records, reviews)
    )
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
        single_retry_permitted=retry,
        status=ApprovalStatus.APPROVED,
    )
    return envelope, preview, content, destination


def first_plan(ctx):
    envelope, preview, content, destination = ctx
    return evaluate_synthetic_submission_lifecycle(
        preview, envelope, content, destination, now=NOW
    ).next_plan


def result(plan, outcome, *, at=None):
    at = at or plan.planned_at + timedelta(minutes=1)
    receipt = None
    if outcome is SyntheticAttemptOutcome.SUCCESS_PLACEHOLDER:
        receipt = SyntheticReceiptPlaceholder(
            receipt_id=f"SYNTH-RECEIPT-AUDIT-{plan.attempt_number}",
            plan_reference=plan.identity.reference,
            idempotency_key=plan.idempotency_key,
            recorded_at=at,
        )
    return SyntheticSubmissionAttemptResult(
        result_id=f"SYNTH-RESULT-AUDIT-{plan.attempt_number}",
        plan_reference=plan.identity.reference,
        idempotency_key=plan.idempotency_key,
        attempt_number=plan.attempt_number,
        outcome=outcome,
        observed_at=at,
        receipt_placeholder=receipt,
    )


def restore(snapshot):
    return restore_synthetic_lifecycle_audit(
        snapshot.to_json(),
        expected_case_id=snapshot.case_id,
        expected_run_id=snapshot.run_id,
        expected_idempotency_key=snapshot.idempotency_key,
    )


def test_open_attempt_round_trip_is_deterministic_and_privacy_minimized():
    ctx = context()
    plan = first_plan(ctx)
    snapshot = build_synthetic_lifecycle_audit(ctx[1], (plan,), ())
    recovered = restore(snapshot)
    assert recovered.state is RecoveredLifecycleState.AWAITING_SYNTHETIC_RESULT
    assert recovered.open_attempt_number == 1
    assert recovered.completed_attempts == 0
    assert snapshot == build_synthetic_lifecycle_audit(ctx[1], (plan,), ())
    serialized = snapshot.to_json()
    for excluded in ("54321", "8765", "2345", ctx[0].purpose, "gross_wages"):
        assert excluded not in serialized


@pytest.mark.parametrize(
    ("outcome", "state"),
    [
        (SyntheticAttemptOutcome.DEFINITE_FAILURE, RecoveredLifecycleState.DEFINITE_FAILURE_RECORDED),
        (SyntheticAttemptOutcome.UNCERTAIN, RecoveredLifecycleState.UNCERTAIN_BLOCKED),
        (SyntheticAttemptOutcome.SUCCESS_PLACEHOLDER, RecoveredLifecycleState.COMPLETE_WITH_PLACEHOLDER),
    ],
)
def test_restart_recovers_exact_first_attempt_result(outcome, state):
    ctx = context()
    plan = first_plan(ctx)
    attempt_result = result(plan, outcome)
    recovered = restore(build_synthetic_lifecycle_audit(ctx[1], (plan,), (attempt_result,)))
    assert recovered.state is state
    assert recovered.completed_attempts == 1
    assert recovered.open_attempt_number is None
    assert bool(recovered.receipt_placeholder_reference) is (
        outcome is SyntheticAttemptOutcome.SUCCESS_PLACEHOLDER
    )


def test_retry_open_and_exhausted_states_survive_restart():
    ctx = context()
    first = first_plan(ctx)
    failed = result(first, SyntheticAttemptOutcome.DEFINITE_FAILURE)
    envelope, preview, content, destination = ctx
    second = evaluate_synthetic_submission_lifecycle(
        preview,
        envelope,
        content,
        destination,
        now=NOW + timedelta(minutes=2),
        plans=(first,),
        results=(failed,),
    ).next_plan
    open_recovery = restore(build_synthetic_lifecycle_audit(preview, (first, second), (failed,)))
    assert open_recovery.state is RecoveredLifecycleState.AWAITING_SYNTHETIC_RESULT
    assert open_recovery.open_attempt_number == 2
    failed_again = result(second, SyntheticAttemptOutcome.DEFINITE_FAILURE)
    exhausted = restore(
        build_synthetic_lifecycle_audit(preview, (first, second), (failed, failed_again))
    )
    assert exhausted.state is RecoveredLifecycleState.RETRY_EXHAUSTED
    assert exhausted.completed_attempts == 2


def test_digest_mutation_reordering_and_truncation_fail_closed():
    ctx = context()
    plan = first_plan(ctx)
    success = result(plan, SyntheticAttemptOutcome.SUCCESS_PLACEHOLDER)
    snapshot = build_synthetic_lifecycle_audit(ctx[1], (plan,), (success,))
    payload = json.loads(snapshot.to_json())
    payload["events"][0]["artifact_reference"] = "sha256:" + "f" * 64
    with pytest.raises(ElsterSubmissionAuditError, match="digest mismatch"):
        restore_synthetic_lifecycle_audit(
            json.dumps(payload),
            expected_case_id=snapshot.case_id,
            expected_run_id=snapshot.run_id,
            expected_idempotency_key=snapshot.idempotency_key,
        )
    payload = json.loads(snapshot.to_json())
    payload["events"] = list(reversed(payload["events"]))
    with pytest.raises(ElsterSubmissionAuditError):
        restore_synthetic_lifecycle_audit(
            json.dumps(payload),
            expected_case_id=snapshot.case_id,
            expected_run_id=snapshot.run_id,
            expected_idempotency_key=snapshot.idempotency_key,
        )
    payload = json.loads(snapshot.to_json())
    payload["events"].pop()
    payload["head_digest"] = payload["events"][-1]["event_digest"]
    with pytest.raises(ElsterSubmissionAuditError, match="success and receipt"):
        restore_synthetic_lifecycle_audit(
            json.dumps(payload),
            expected_case_id=snapshot.case_id,
            expected_run_id=snapshot.run_id,
            expected_idempotency_key=snapshot.idempotency_key,
        )


def test_unknown_fields_and_cross_case_recovery_fail_closed():
    ctx = context()
    snapshot = build_synthetic_lifecycle_audit(ctx[1], (first_plan(ctx),), ())
    payload = json.loads(snapshot.to_json())
    payload["unexpected"] = True
    with pytest.raises(ElsterSubmissionAuditError, match="unexpected"):
        restore_synthetic_lifecycle_audit(
            json.dumps(payload),
            expected_case_id=snapshot.case_id,
            expected_run_id=snapshot.run_id,
            expected_idempotency_key=snapshot.idempotency_key,
        )
    with pytest.raises(ElsterSubmissionAuditError, match="scope mismatch"):
        restore_synthetic_lifecycle_audit(
            snapshot.to_json(),
            expected_case_id="SYNTH-CASE-OTHER",
            expected_run_id=snapshot.run_id,
            expected_idempotency_key=snapshot.idempotency_key,
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("contains_tax_values", True, "privacy boundary"),
        ("restart_recovery_only", False, "privacy boundary"),
        ("transmission_permitted", True, "external capability"),
        ("credential_access", True, "external capability"),
        ("network_calls", ("https://example.invalid",), "network calls"),
    ],
)
def test_snapshot_cannot_be_forged_beyond_local_recovery(field, value, message):
    ctx = context()
    snapshot = build_synthetic_lifecycle_audit(ctx[1], (first_plan(ctx),), ())
    with pytest.raises(ElsterSubmissionAuditError, match=message):
        replace(snapshot, **{field: value})
