"""Closed local action adapter for the synthetic Milestone A workflow."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum

from .synthetic_product_service import SyntheticProductService
from .synthetic_workflow_store import WorkflowSnapshot, WorkflowStage, WorkflowTransitionError


class SyntheticAction(str, Enum):
    INTAKE = "INTAKE"
    PROCESS = "PROCESS"
    SPECIALIST_REVIEW = "SPECIALIST_REVIEW"
    CHIEF_REVIEW = "CHIEF_REVIEW"
    CALCULATE = "CALCULATE"
    PREPARE_DECLARATION = "PREPARE_DECLARATION"


class SyntheticRole(str, Enum):
    INTAKE_AGENT = "INTAKE_AGENT"
    PROCESSING_AGENT = "PROCESSING_AGENT"
    SPECIALIST_AGENT = "SPECIALIST_AGENT"
    CHIEF_AGENT = "CHIEF_AGENT"
    CALCULATION_AGENT = "CALCULATION_AGENT"
    DECLARATION_AGENT = "DECLARATION_AGENT"


@dataclass(frozen=True, slots=True)
class ActionRule:
    role: SyntheticRole
    expected: WorkflowStage
    target: WorkflowStage
    corrections_allowed: bool = False


RULES = {
    SyntheticAction.INTAKE: ActionRule(SyntheticRole.INTAKE_AGENT, WorkflowStage.CREATE_CASE, WorkflowStage.INTAKE),
    SyntheticAction.PROCESS: ActionRule(SyntheticRole.PROCESSING_AGENT, WorkflowStage.INTAKE, WorkflowStage.PROCESS),
    SyntheticAction.SPECIALIST_REVIEW: ActionRule(SyntheticRole.SPECIALIST_AGENT, WorkflowStage.PROCESS, WorkflowStage.SPECIALIST_REVIEW, True),
    SyntheticAction.CHIEF_REVIEW: ActionRule(SyntheticRole.CHIEF_AGENT, WorkflowStage.SPECIALIST_REVIEW, WorkflowStage.CHIEF_REVIEW, True),
    SyntheticAction.CALCULATE: ActionRule(SyntheticRole.CALCULATION_AGENT, WorkflowStage.CHIEF_REVIEW, WorkflowStage.CALCULATION),
    SyntheticAction.PREPARE_DECLARATION: ActionRule(SyntheticRole.DECLARATION_AGENT, WorkflowStage.CALCULATION, WorkflowStage.FORM_PREVIEW),
}


@dataclass(frozen=True, slots=True)
class SyntheticActionRequest:
    action: SyntheticAction
    role: SyntheticRole
    case_id: str
    tax_year: int
    run_id: str
    transition_id: str
    expected_prior_hash: str
    expected_prior_artifact_identity: str
    input_artifact_identities: tuple[str, ...]
    invalidated_artifact_identities: tuple[str, ...] = ()


class SyntheticWorkflowActionService:
    """Advance only the six approved local stages; it never executes supplied commands."""

    def __init__(self, product: SyntheticProductService) -> None:
        self.product = product

    def execute(self, request: SyntheticActionRequest) -> WorkflowSnapshot:
        current = self.product.store.get(request.case_id, request.tax_year, request.run_id)
        payload = {
            "schema_version": 1,
            "action": request.action.value if type(request.action) is SyntheticAction else str(request.action),
            "role": request.role.value if type(request.role) is SyntheticRole else str(request.role),
            "case_id": request.case_id,
            "tax_year": request.tax_year,
            "run_id": request.run_id,
            "prior_transition_hash": request.expected_prior_hash,
            "prior_artifact_identity": request.expected_prior_artifact_identity,
            "input_artifact_identities": request.input_artifact_identities,
            "invalidated_artifact_identities": request.invalidated_artifact_identities,
        }
        outcome=self.product.store.reserve_action_attempt(request.run_id,request.transition_id,payload)
        if outcome == "REJECTED": raise WorkflowTransitionError("action attempt was already rejected")
        try:
            if type(request.action) is not SyntheticAction or type(request.role) is not SyntheticRole:
                raise WorkflowTransitionError("action and role must be closed catalog members")
            rule = RULES[request.action]
            if request.role is not rule.role: raise WorkflowTransitionError("role is not authorized for action")
            if current.stage is rule.expected and (current.transition_hash != request.expected_prior_hash or current.artifact_identity != request.expected_prior_artifact_identity):
                raise WorkflowTransitionError("exact prior workflow state is required")
            inputs=self._identities(request.input_artifact_identities,"input")
            invalidated=self._identities(request.invalidated_artifact_identities,"invalidated")
            if invalidated and not rule.corrections_allowed: raise WorkflowTransitionError("correction invalidation is allowed only during review")
            if invalidated and invalidated != (request.expected_prior_artifact_identity,): raise WorkflowTransitionError("correction must invalidate the exact prior active artifact")
            if set(inputs)&set(invalidated): raise WorkflowTransitionError("an artifact cannot be both active and invalidated")
            payload["input_artifact_identities"]=inputs; payload["invalidated_artifact_identities"]=invalidated; payload["target_stage"]=rule.target.value
            artifact_identity="sha256:"+hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
            result=self.product.advance(request.case_id,request.tax_year,request.run_id,rule.expected,rule.target,artifact_identity,request.transition_id)
            if outcome == "PENDING": self.product.store.finalize_action_attempt(request.transition_id,"ACCEPTED")
            return result
        except Exception:
            if outcome == "PENDING": self.product.store.finalize_action_attempt(request.transition_id,"REJECTED")
            raise

    @staticmethod
    def _identities(values: tuple[str, ...], label: str) -> tuple[str, ...]:
        if not isinstance(values, tuple) or len(set(values)) != len(values):
            raise WorkflowTransitionError(f"non-empty unique {label} artifact identities are required")
        if label == "input" and not values:
            raise WorkflowTransitionError("non-empty unique input artifact identities are required")
        if any(not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71 for value in values):
            raise WorkflowTransitionError(f"valid {label} artifact identities are required")
        return tuple(sorted(values))
