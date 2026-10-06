from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from agent_lab.elster_dry_run import (
    ApprovalStatus,
    ContentReleaseApproval,
    DestinationTransmissionApproval,
    GateOutcome,
    SubmissionControlError,
    SyntheticSubmissionEnvelope,
    SyntheticTaxSummary,
    evaluate_synthetic_dry_run,
)


NOW = datetime(2026, 9, 14, 18, 0, tzinfo=timezone.utc)


def envelope() -> SyntheticSubmissionEnvelope:
    return SyntheticSubmissionEnvelope(
        case_id="SYNTH-CASE-0001",
        run_id="SYNTH-RUN-0001",
        tax_year=2024,
        procedure_code="UFA10",
        eric_version="44.3.6.0",
        purpose="synthetic Phase P1 control validation",
        data_classification="SYNTHETIC",
        payload=SyntheticTaxSummary(
            gross_wages_eur=50000,
            withheld_wage_tax_eur=8000,
            deductible_expenses_eur=2500,
        ),
    )


def content(item: SyntheticSubmissionEnvelope | None = None) -> ContentReleaseApproval:
    item = item or envelope()
    return ContentReleaseApproval(
        approval_id="SYNTH-CONTENT-0001",
        approver_id="SYNTH-HUMAN-0001",
        case_id=item.case_id,
        run_id=item.run_id,
        artifact_reference=item.artifact_identity.reference,
        artifact_version=item.artifact_identity.version,
        data_classification=item.data_classification,
        purpose=item.purpose,
        issued_at=NOW - timedelta(minutes=10),
        expires_at=NOW + timedelta(hours=1),
        status=ApprovalStatus.APPROVED,
    )


def destination(
    item: SyntheticSubmissionEnvelope | None = None,
    first: ContentReleaseApproval | None = None,
) -> DestinationTransmissionApproval:
    item = item or envelope()
    first = first or content(item)
    return DestinationTransmissionApproval(
        approval_id="SYNTH-DESTINATION-0001",
        approver_id="SYNTH-HUMAN-0001",
        content_release_approval_id=first.approval_id,
        case_id=item.case_id,
        run_id=item.run_id,
        artifact_reference=item.artifact_identity.reference,
        artifact_version=item.artifact_identity.version,
        destination_identity="SYNTH-ELSTER-ACCEPTANCE-SERVER",
        channel="SYNTH-ERIC",
        purpose=item.purpose,
        issued_at=NOW - timedelta(minutes=5),
        expires_at=NOW + timedelta(minutes=30),
        single_retry_permitted=False,
        status=ApprovalStatus.APPROVED,
    )


def test_envelope_has_stable_immutable_identity():
    item = envelope()
    assert item.artifact_identity == item.artifact_identity
    assert item.artifact_identity.reference.startswith("sha256:")
    with pytest.raises(Exception):
        item.tax_year = 2025


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("tax_year", 2025, "tax_year"),
        ("procedure_code", "UFA12", "procedure_code"),
        ("eric_version", "43.2", "ERiC version"),
        ("data_classification", "PRIVATE", "SYNTHETIC"),
        ("case_id", "CASE-001", "SYNTH-"),
        ("run_id", "RUN-001", "SYNTH-"),
    ],
)
def test_envelope_fails_closed_outside_exact_synthetic_route(field, value, message):
    with pytest.raises(SubmissionControlError, match=message):
        replace(envelope(), **{field: value})


def test_payload_rejects_negative_and_boolean_values():
    with pytest.raises(SubmissionControlError):
        SyntheticTaxSummary(-1, 0, 0)
    with pytest.raises(SubmissionControlError):
        SyntheticTaxSummary(True, 0, 0)


def test_first_human_gate_is_required_before_destination_gate():
    result = evaluate_synthetic_dry_run(envelope(), now=NOW)
    assert result.outcome is GateOutcome.HUMAN_REQUIRED
    assert result.required_gate == "CONTENT_RELEASE_APPROVAL"
    assert result.transmission_permitted is False


def test_destination_gate_is_separately_required():
    item = envelope()
    result = evaluate_synthetic_dry_run(item, now=NOW, content_approval=content(item))
    assert result.outcome is GateOutcome.HUMAN_REQUIRED
    assert result.required_gate == "DESTINATION_TRANSMISSION_APPROVAL"


def test_valid_synthetic_approvals_still_never_permit_transmission():
    item = envelope()
    first = content(item)
    result = evaluate_synthetic_dry_run(
        item,
        now=NOW,
        content_approval=first,
        destination_approval=destination(item, first),
    )
    assert result.outcome is GateOutcome.DRY_RUN_READY
    assert result.transmission_permitted is False
    assert result.network_calls == ()
    assert result.credential_access is False
    assert result.blockers == ()
    assert "TRANSMITTER_NOT_IMPLEMENTED" in result.limitations


def test_two_approval_events_cannot_be_collapsed():
    item = envelope()
    first = content(item)
    second = replace(destination(item, first), approval_id=first.approval_id)
    result = evaluate_synthetic_dry_run(
        item, now=NOW, content_approval=first, destination_approval=second
    )
    assert result.outcome is GateOutcome.BLOCKED
    assert any("distinct" in blocker for blocker in result.blockers)


def test_destination_approval_must_follow_and_bind_content_approval():
    item = envelope()
    first = content(item)
    second = replace(
        destination(item, first),
        content_release_approval_id="SYNTH-CONTENT-OTHER",
        issued_at=first.issued_at - timedelta(seconds=1),
    )
    result = evaluate_synthetic_dry_run(
        item, now=NOW, content_approval=first, destination_approval=second
    )
    assert result.outcome is GateOutcome.BLOCKED
    assert any("not bound" in blocker for blocker in result.blockers)
    assert any("predates" in blocker for blocker in result.blockers)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("case_id", "SYNTH-CASE-OTHER"),
        ("run_id", "SYNTH-RUN-OTHER"),
        ("artifact_reference", "sha256:" + "0" * 64),
        ("artifact_version", "2"),
        ("purpose", "different purpose"),
        ("destination_identity", "SYNTH-OTHER-DESTINATION"),
        ("channel", "SYNTH-OTHER-CHANNEL"),
    ],
)
def test_destination_binding_mismatch_blocks(field, value):
    item = envelope()
    first = content(item)
    second = replace(destination(item, first), **{field: value})
    result = evaluate_synthetic_dry_run(
        item, now=NOW, content_approval=first, destination_approval=second
    )
    assert result.outcome is GateOutcome.BLOCKED


def test_expired_or_revoked_approvals_block():
    item = envelope()
    expired = replace(content(item), expires_at=NOW)
    result = evaluate_synthetic_dry_run(item, now=NOW, content_approval=expired)
    assert result.outcome is GateOutcome.BLOCKED

    first = content(item)
    revoked = replace(destination(item, first), status=ApprovalStatus.REVOKED)
    result = evaluate_synthetic_dry_run(
        item, now=NOW, content_approval=first, destination_approval=revoked
    )
    assert result.outcome is GateOutcome.BLOCKED


def test_artifact_mutation_invalidates_both_approval_bindings():
    item = envelope()
    first = content(item)
    second = destination(item, first)
    changed = replace(
        item,
        payload=replace(item.payload, deductible_expenses_eur=2501),
    )
    result = evaluate_synthetic_dry_run(
        changed, now=NOW, content_approval=first, destination_approval=second
    )
    assert result.outcome is GateOutcome.BLOCKED
    assert any("artifact binding mismatch" in blocker for blocker in result.blockers)


def test_timestamps_must_be_timezone_aware():
    with pytest.raises(SubmissionControlError, match="timezone-aware"):
        evaluate_synthetic_dry_run(envelope(), now=datetime(2026, 9, 14))
