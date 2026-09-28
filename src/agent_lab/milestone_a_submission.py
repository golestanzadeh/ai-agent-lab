"""MA-04 durable coordinator over the existing approval and workflow stores."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from .durable_approval import DurableApprovalStore
from .synthetic_workflow_store import SyntheticWorkflowStore, WorkflowStage, WorkflowTransitionError


def _digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()


class MilestoneASubmissionCoordinator:
    """Replay a synthetic saga; no network, credential, or transmitter exists here."""

    STEPS = (
        ("APPROVAL_STAGE_1", WorkflowStage.FORM_PREVIEW, WorkflowStage.APPROVAL_STAGE_1),
        ("APPROVAL_STAGE_2", WorkflowStage.APPROVAL_STAGE_1, WorkflowStage.APPROVAL_STAGE_2),
        ("SYNTHETIC_SUBMISSION", WorkflowStage.APPROVAL_STAGE_2, WorkflowStage.SYNTHETIC_SUBMISSION),
        ("RECEIPT", WorkflowStage.SYNTHETIC_SUBMISSION, WorkflowStage.RECEIPT),
        ("RECOVERY", WorkflowStage.RECEIPT, WorkflowStage.RECOVERY),
    )

    def __init__(self, approvals: DurableApprovalStore, workflow: SyntheticWorkflowStore) -> None:
        self.approvals = approvals
        self.workflow = workflow

    def execute(self, intent: dict[str, object], *, now: datetime, crash_after: str | None = None) -> dict[str, object]:
        state = self.approvals.begin_submission_coordinator(intent)
        if crash_after == "INTENT_RECORDED":
            raise RuntimeError("injected crash after intent commit")
        if state["state"] == "INTENT_RECORDED":
            current = self.workflow.get(
                str(intent["case_id"]), int(intent["tax_year"]), str(intent["run_id"])
            )
            if (
                current.stage is not WorkflowStage.FORM_PREVIEW
                or current.artifact_identity != intent["artifact_reference"]
            ):
                raise WorkflowTransitionError(
                    "approval intent does not match the active form-preview artifact"
                )
        state = self.approvals.consume_coordinator_approvals(str(intent["operation_id"]), now=now)
        if crash_after == "APPROVALS_CONSUMED":
            raise RuntimeError("injected crash after approval consumption")
        operation_id = str(intent["operation_id"])
        artifacts = {
            "APPROVAL_STAGE_1": _digest(operation_id + ":content"),
            "APPROVAL_STAGE_2": _digest(operation_id + ":destination"),
            "SYNTHETIC_SUBMISSION": _digest(operation_id + ":result"),
            "RECEIPT": _digest(operation_id + ":receipt"),
            "RECOVERY": _digest(operation_id + ":recovery"),
        }
        result = {
            "schema_version": 1, "result_id": "SYNTH-RESULT-" + operation_id.removeprefix("SYNTH-"),
            "operation_id": operation_id, "case_id": intent["case_id"], "run_id": intent["run_id"],
            "outcome": "SYNTHETIC_SUCCESS_PLACEHOLDER", "artifact_reference": artifacts["SYNTHETIC_SUBMISSION"],
            "network_calls": [], "credential_access": False,
        }
        receipt = {
            "schema_version": 1, "receipt_id": "SYNTH-RECEIPT-" + operation_id.removeprefix("SYNTH-"),
            "operation_id": operation_id, "case_id": intent["case_id"], "run_id": intent["run_id"],
            "result_reference": artifacts["SYNTHETIC_SUBMISSION"], "artifact_reference": artifacts["RECEIPT"],
            "marker": "SYNTHETIC_PLACEHOLDER_NO_EXTERNAL_RECEIPT", "external_receipt_received": False,
            "network_calls": [],
        }
        for marker, expected, target in self.STEPS:
            state = self.approvals.get_submission_coordinator(operation_id)
            if marker in state["markers"]:
                continue
            transition_id = operation_id + ":" + marker
            try:
                self.workflow.advance(str(intent["case_id"]), int(intent["tax_year"]), str(intent["run_id"]), expected, target, artifacts[marker], transition_id)
            except WorkflowTransitionError:
                # An exact idempotent replay succeeds in advance(); any other state is ambiguous.
                raise
            if crash_after == marker:
                raise RuntimeError("injected crash after workflow commit: " + marker)
            state = self.approvals.commit_submission_coordinator(
                operation_id, marker,
                result=result if marker == "SYNTHETIC_SUBMISSION" else None,
                receipt=receipt if marker == "RECEIPT" else None,
            )
            if crash_after == "MARKER_" + marker:
                raise RuntimeError("injected crash after coordinator marker: " + marker)
        final = self.workflow.get(str(intent["case_id"]), int(intent["tax_year"]), str(intent["run_id"]))
        if final.stage is not WorkflowStage.RECOVERY or final.artifact_identity != artifacts["RECOVERY"]:
            raise WorkflowTransitionError("completed coordinator does not match durable workflow state")
        return state
