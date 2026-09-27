"""Composition boundary for a registered synthetic case and its workflow state."""
from __future__ import annotations
from .case_registry import CaseRegistry, LookupStatus
from .synthetic_workflow_store import SyntheticWorkflowStore, WorkflowScopeError, WorkflowSnapshot, WorkflowStage


class SyntheticProductService:
    def __init__(self, registry: CaseRegistry, store: SyntheticWorkflowStore) -> None:
        self.registry=registry; self.store=store

    def start(self, case_id: str, tax_year: int, run_id: str, artifact_identity: str, transition_id: str) -> WorkflowSnapshot:
        result=self.registry.resolve_by_case_id(case_id)
        record=self.registry.get(case_id) if result.status is LookupStatus.RESOLVED else None
        if record is None or record.tax_period.year!=tax_year or not case_id.startswith("SYNTHETIC-"):
            raise WorkflowScopeError("registered synthetic case scope is required")
        return self.store.create(case_id,tax_year,run_id,artifact_identity,transition_id)

    def advance(self, case_id: str, tax_year: int, run_id: str, expected: WorkflowStage, target: WorkflowStage, artifact_identity: str, transition_id: str) -> WorkflowSnapshot:
        if self.registry.resolve_by_case_id(case_id).status is not LookupStatus.RESOLVED: raise WorkflowScopeError("case is not registered")
        return self.store.advance(case_id,tax_year,run_id,expected,target,artifact_identity,transition_id)
