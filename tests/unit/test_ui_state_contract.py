from dataclasses import replace
from datetime import datetime, timezone

import pytest

from agent_lab.case_registry import (
    AssessmentMode,
    CaseRecord,
    CaseRegistry,
    CaseType,
    LifecycleStatus,
    OwnerType,
    StorageScopeReference,
    TaxPeriod,
)
from agent_lab.ui_state_contract import (
    HumanGateStatus,
    HumanGateView,
    SUBMISSION_DISABLED_REASON,
    UIStateError,
    select_synthetic_workspace,
)


NOW = datetime(2026, 9, 15, tzinfo=timezone.utc)
REF_A = "sha256:" + "a" * 64
REF_B = "sha256:" + "b" * 64
REF_C = "sha256:" + "c" * 64


def _registry() -> CaseRegistry:
    registry = CaseRegistry()
    for suffix, year in (("001", 2024), ("002", 2025)):
        registry.register(
            CaseRecord(
                case_id=f"SYNTH-CASE-{suffix}",
                owner_type=OwnerType.PERSON,
                owner_id=f"SYNTH-PERSON-{suffix}",
                tax_period=TaxPeriod("CALENDAR_YEAR", year),
                case_type=CaseType.INDIVIDUAL,
                assessment_mode=AssessmentMode.INDIVIDUAL_ASSESSMENT,
                lifecycle_status=LifecycleStatus.REVIEW_REQUIRED,
                storage_scope_reference=StorageScopeReference("SYNTH", f"root-{suffix}"),
                schema_version=1,
                created_at=NOW,
                updated_at=NOW,
            )
        )
    return registry


def test_selection_requires_registry_resolved_case_and_exact_year() -> None:
    registry = _registry()
    state = select_synthetic_workspace(registry, case_id="SYNTH-CASE-001", tax_year=2024)
    assert state.owner_id == "SYNTH-PERSON-001"
    with pytest.raises(UIStateError, match="not resolved"):
        select_synthetic_workspace(registry, case_id="SYNTH-CASE-999", tax_year=2024)
    with pytest.raises(UIStateError, match="tax year"):
        select_synthetic_workspace(registry, case_id="SYNTH-CASE-001", tax_year=2025)


def test_non_synthetic_case_and_owner_fail_closed() -> None:
    registry = CaseRegistry()
    registry.register(
        CaseRecord(
            case_id="CASE-REAL",
            owner_type=OwnerType.PERSON,
            owner_id="PERSON-REAL",
            tax_period=TaxPeriod("CALENDAR_YEAR", 2024),
            case_type=CaseType.INDIVIDUAL,
            assessment_mode=AssessmentMode.INDIVIDUAL_ASSESSMENT,
            lifecycle_status=LifecycleStatus.ACTIVE,
            storage_scope_reference=StorageScopeReference("LOCAL", "real"),
            schema_version=1,
            created_at=NOW,
            updated_at=NOW,
        )
    )
    with pytest.raises(UIStateError, match="SYNTH"):
        select_synthetic_workspace(registry, case_id="CASE-REAL", tax_year=2024)


def test_case_content_is_bound_to_selected_case() -> None:
    state = select_synthetic_workspace(_registry(), case_id="SYNTH-CASE-001", tax_year=2024)
    with pytest.raises(UIStateError, match="does not match"):
        state.with_case_scoped_content(case_id="SYNTH-CASE-002", run_id="SYNTH-RUN-1")


def test_new_selection_clears_stale_case_content() -> None:
    registry = _registry()
    first = select_synthetic_workspace(registry, case_id="SYNTH-CASE-001", tax_year=2024)
    populated = first.with_case_scoped_content(
        case_id=first.case_id,
        run_id="SYNTH-RUN-1",
        document_references=(REF_A,),
        finding_references=(REF_B,),
        evidence_gap_codes=("MISSING_RECEIPT",),
        preview_reference=REF_C,
    )
    assert populated.document_references
    second = select_synthetic_workspace(registry, case_id="SYNTH-CASE-002", tax_year=2025)
    assert second.run_id is None
    assert second.document_references == ()
    assert second.finding_references == ()
    assert second.evidence_gap_codes == ()
    assert second.preview_reference is None


def test_human_gate_requires_exact_artifact_destination_and_expiry() -> None:
    gate = HumanGateView(
        HumanGateStatus.REQUIRED,
        action="REVIEW_SYNTHETIC_PREVIEW",
        artifact_reference=REF_A,
        destination="SYNTH-ELSTER-PREVIEW",
        expires_at=NOW,
    )
    state = select_synthetic_workspace(_registry(), case_id="SYNTH-CASE-001", tax_year=2024)
    bound = state.with_case_scoped_content(
        case_id=state.case_id, run_id="SYNTH-RUN-1", human_gate=gate
    )
    assert bound.human_gate == gate
    with pytest.raises(UIStateError, match="artifact_reference"):
        HumanGateView(HumanGateStatus.REQUIRED, action="REVIEW", destination="X", expires_at=NOW)


def test_submission_and_external_capabilities_cannot_be_forged() -> None:
    state = select_synthetic_workspace(_registry(), case_id="SYNTH-CASE-001", tax_year=2024)
    assert state.submission_enabled is False
    assert state.submission_disabled_reason == SUBMISSION_DISABLED_REASON
    for change in (
        {"submission_enabled": True},
        {"submission_disabled_reason": "READY"},
        {"official_receipt_reference": REF_A},
        {"network_calls": ("https://example.invalid",)},
        {"data_classification": "REAL"},
    ):
        with pytest.raises(UIStateError):
            replace(state, **change)


def test_references_are_unique_and_canonical() -> None:
    state = select_synthetic_workspace(_registry(), case_id="SYNTH-CASE-001", tax_year=2024)
    with pytest.raises(UIStateError, match="unique"):
        state.with_case_scoped_content(
            case_id=state.case_id,
            run_id="SYNTH-RUN-1",
            document_references=(REF_A, REF_A),
        )
    with pytest.raises(UIStateError, match="sha256"):
        state.with_case_scoped_content(
            case_id=state.case_id,
            run_id="SYNTH-RUN-1",
            finding_references=("not-a-reference",),
        )
