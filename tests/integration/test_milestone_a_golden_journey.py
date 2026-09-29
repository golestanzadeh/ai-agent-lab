"""Complete local synthetic Milestone A journey; no external capability."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

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
from agent_lab.durable_approval import DurableApprovalStore
from agent_lab.elster_dry_run import (
    ApprovalStatus,
    ContentReleaseApproval,
    DestinationTransmissionApproval,
)
from agent_lab.milestone_a_submission import MilestoneASubmissionCoordinator
from agent_lab.synthetic_product_service import SyntheticProductService
from agent_lab.synthetic_workflow_actions import (
    SyntheticAction,
    SyntheticActionRequest,
    SyntheticRole,
    SyntheticWorkflowActionService,
)
from agent_lab.synthetic_workflow_store import SyntheticWorkflowStore, WorkflowStage


NOW = datetime(2026, 9, 28, 14, tzinfo=timezone.utc)
CASE_ID = "SYNTHETIC-MA05-GOLDEN"
RUN_ID = "RUN-SYNTHETIC-MA05-GOLDEN"
YEAR = 2024
GENESIS = "sha256:" + "1" * 64


class ExactRunScope:
    def get_run(self, case_id: str, run_id: str):
        if (case_id, run_id) != (CASE_ID, RUN_ID):
            raise KeyError(run_id)
        return SimpleNamespace(case_id=case_id, run_id=run_id)


def _registry() -> CaseRegistry:
    registry = CaseRegistry()
    registry.register(
        CaseRecord(
            CASE_ID,
            OwnerType.PERSON,
            "SYNTHETIC-PERSON-MA05",
            TaxPeriod("CALENDAR_YEAR", YEAR),
            CaseType.INDIVIDUAL,
            AssessmentMode.NOT_APPLICABLE,
            LifecycleStatus.CREATED,
            StorageScopeReference("synthetic_local", "ma05-golden"),
            1,
            NOW,
            NOW,
        )
    )
    return registry


def test_complete_golden_journey_reopens_with_one_result_and_receipt(tmp_path):
    workflow_path = tmp_path / "workflow.sqlite3"
    approval_path = tmp_path / "approvals.sqlite3"
    registry = _registry()
    with SyntheticWorkflowStore(workflow_path) as workflow, DurableApprovalStore(
        approval_path, case_registry=registry, case_state=ExactRunScope()
    ) as approvals:
        product = SyntheticProductService(registry, workflow)
        current = product.start(CASE_ID, YEAR, RUN_ID, GENESIS, "MA05-CREATE")
        actions = SyntheticWorkflowActionService(product)
        sequence = (
            (SyntheticAction.INTAKE, SyntheticRole.INTAKE_AGENT),
            (SyntheticAction.PROCESS, SyntheticRole.PROCESSING_AGENT),
            (SyntheticAction.SPECIALIST_REVIEW, SyntheticRole.SPECIALIST_AGENT),
            (SyntheticAction.CHIEF_REVIEW, SyntheticRole.CHIEF_AGENT),
            (SyntheticAction.CALCULATE, SyntheticRole.CALCULATION_AGENT),
            (SyntheticAction.PREPARE_DECLARATION, SyntheticRole.DECLARATION_AGENT),
        )
        for index, (action, role) in enumerate(sequence, 1):
            # Canonical synthetic identities carry no tax data.
            request = SyntheticActionRequest(
                action,
                role,
                CASE_ID,
                YEAR,
                RUN_ID,
                f"MA05-ACTION-{index}",
                current.transition_hash,
                current.artifact_identity,
                ("sha256:" + format(index, "064x"),),
            )
            current = actions.execute(request)
        assert current.stage is WorkflowStage.FORM_PREVIEW

        content = ContentReleaseApproval(
            "SYNTH-CONTENT-MA05", "SYNTH-HUMAN-1", CASE_ID, RUN_ID,
            current.artifact_identity, "1", "SYNTHETIC", "milestone-a-proof",
            NOW, NOW + timedelta(hours=2), ApprovalStatus.APPROVED,
        )
        destination = DestinationTransmissionApproval(
            "SYNTH-DEST-MA05", "SYNTH-HUMAN-2", content.approval_id,
            CASE_ID, RUN_ID, current.artifact_identity, "1",
            "SYNTH-ELSTER-ACCEPTANCE-SERVER", "SYNTH-ERIC",
            "milestone-a-proof", NOW + timedelta(minutes=1),
            NOW + timedelta(hours=2), False, ApprovalStatus.APPROVED,
        )
        approvals.register_submission_approval(content)
        approvals.register_submission_approval(destination)
        intent = {
            "operation_id": "SYNTH-OP-MA05-GOLDEN",
            "case_id": CASE_ID,
            "tax_year": YEAR,
            "run_id": RUN_ID,
            "artifact_reference": current.artifact_identity,
            "artifact_version": "1",
            "content_approval_id": content.approval_id,
            "destination_approval_id": destination.approval_id,
            "destination_identity": "SYNTH-ELSTER-ACCEPTANCE-SERVER",
            "channel": "SYNTH-ERIC",
            "purpose": "milestone-a-proof",
            "requested_at": NOW.isoformat(timespec="microseconds").replace("+00:00", "Z"),
        }
        completed = MilestoneASubmissionCoordinator(approvals, workflow).execute(
            intent, now=NOW + timedelta(minutes=2)
        )
        assert completed["state"] == "COMPLETE"
        assert completed["result"]["credential_access"] is False
        assert completed["receipt"]["external_receipt_received"] is False

    with SyntheticWorkflowStore(workflow_path) as workflow, DurableApprovalStore(
        approval_path, case_registry=_registry(), case_state=ExactRunScope()
    ) as approvals:
        recovered = approvals.get_submission_coordinator("SYNTH-OP-MA05-GOLDEN")
        assert recovered == completed
        assert workflow.get(CASE_ID, YEAR, RUN_ID).stage is WorkflowStage.RECOVERY
        row = approvals._connection.execute(
            "SELECT COUNT(*) AS operations, COUNT(result_json) AS results, "
            "COUNT(receipt_json) AS receipts FROM durable_submission_coordinators"
        ).fetchone()
        assert (row["operations"], row["results"], row["receipts"]) == (1, 1, 1)
