"""Synthetic, privacy-safe workflow state for the local UI prototype."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agent_lab.case_registry import LifecycleStatus
from agent_lab.ui_state_contract import UIWorkspaceState


WORKFLOW_VERSION = "1"
STAGE_CODES = ("CASE_SCOPE", "DOCUMENT_INTAKE", "PROCESSING", "SPECIALIST_REVIEW", "CHIEF_REVIEW", "CALCULATION", "FORM_PREVIEW", "HUMAN_APPROVAL", "SUBMISSION", "RECEIPT")
SAFE_DIAGNOSTIC_CODES = ("LOCAL_SYNTHETIC_RUNTIME_READY", "OFFICIAL_ERIC_MAPPING_NOT_RECOVERED", "PRODUCTION_SUBMISSION_PATH_NOT_AUTHORIZED")


class UIWorkflowError(ValueError):
    """Raised when workflow presentation state is incomplete or unsafe."""


class StageStatus(str, Enum):
    COMPLETE = "COMPLETE"
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    LOCKED = "LOCKED"


class RecoveryStatus(str, Enum):
    READY = "READY"
    NOT_REQUIRED = "NOT_REQUIRED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class UIWorkflowStage:
    code: str
    status: StageStatus

    def __post_init__(self) -> None:
        if self.code not in STAGE_CODES:
            raise UIWorkflowError("unknown workflow stage")


@dataclass(frozen=True, slots=True)
class SyntheticUIWorkflow:
    case_id: str
    run_id: str
    stages: tuple[UIWorkflowStage, ...]
    recovery_status: RecoveryStatus
    diagnostic_codes: tuple[str, ...]
    version: str = WORKFLOW_VERSION
    data_classification: str = "SYNTHETIC"
    contains_private_content: bool = False
    control_actions_enabled: bool = False
    submission_enabled: bool = False
    network_calls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.case_id.startswith("SYNTH-") or not self.run_id.startswith("SYNTH-"):
            raise UIWorkflowError("workflow scope must be synthetic")
        if tuple(stage.code for stage in self.stages) != STAGE_CODES:
            raise UIWorkflowError("exact ordered workflow stages are required")
        boundaries = tuple(stage for stage in self.stages if stage.status in (StageStatus.ACTIVE, StageStatus.BLOCKED))
        if len(boundaries) != 1:
            raise UIWorkflowError("workflow must expose exactly one current boundary")
        boundary_index = self.stages.index(boundaries[0])
        if any(stage.status is not StageStatus.COMPLETE for stage in self.stages[:boundary_index]):
            raise UIWorkflowError("stages before the current boundary must be complete")
        if any(stage.status is not StageStatus.LOCKED for stage in self.stages[boundary_index + 1 :]):
            raise UIWorkflowError("stages after the current boundary must be locked")
        if not isinstance(self.diagnostic_codes, tuple) or not self.diagnostic_codes or any(code not in SAFE_DIAGNOSTIC_CODES for code in self.diagnostic_codes):
            raise UIWorkflowError("only allowlisted privacy-safe diagnostics are permitted")
        if len(set(self.diagnostic_codes)) != len(self.diagnostic_codes):
            raise UIWorkflowError("diagnostic codes must be unique")
        if self.version != WORKFLOW_VERSION or self.data_classification != "SYNTHETIC":
            raise UIWorkflowError("unsupported workflow version or classification")
        if self.contains_private_content is not False:
            raise UIWorkflowError("workflow cannot contain private content")
        if self.control_actions_enabled is not False or self.submission_enabled is not False:
            raise UIWorkflowError("workflow cannot enable operational controls")
        if self.network_calls != ():
            raise UIWorkflowError("workflow cannot contain network calls")


def build_synthetic_ui_workflow(workspace: UIWorkspaceState) -> SyntheticUIWorkflow:
    """Derive an exact, non-operational workflow view from one selected workspace."""
    if not isinstance(workspace, UIWorkspaceState) or workspace.run_id is None:
        raise UIWorkflowError("a populated UIWorkspaceState is required")
    boundary = {LifecycleStatus.CREATED: 1, LifecycleStatus.ACTIVE: 1, LifecycleStatus.PROCESSING: 2, LifecycleStatus.REVIEW_REQUIRED: 3, LifecycleStatus.COMPLETED: 7, LifecycleStatus.ARCHIVED: 7, LifecycleStatus.BLOCKED: 2}[workspace.lifecycle_status]
    boundary_status = StageStatus.BLOCKED if workspace.lifecycle_status in (LifecycleStatus.BLOCKED, LifecycleStatus.COMPLETED, LifecycleStatus.ARCHIVED) else StageStatus.ACTIVE
    stages = tuple(UIWorkflowStage(code=code, status=StageStatus.COMPLETE if index < boundary else boundary_status if index == boundary else StageStatus.LOCKED) for index, code in enumerate(STAGE_CODES))
    return SyntheticUIWorkflow(case_id=workspace.case_id, run_id=workspace.run_id, stages=stages, recovery_status=RecoveryStatus.NOT_REQUIRED, diagnostic_codes=SAFE_DIAGNOSTIC_CODES)
