"""Read-only production composition; the existing Kernel owns all execution."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from agent_lab.case_creation_workflow import CaseCreationWorkflow
from agent_lab.case_persistence import SQLiteCasePersistence, StorageProvisioningUnavailable
from agent_lab.identity_persistence import IdentityPersistence
from agent_lab.orchestrator_kernel import OrchestratorKernel
from agent_lab.ui_dashboard import DashboardCase, DashboardUnavailable


class ProtectedOperationDisabled(PermissionError):
    pass


@dataclass(frozen=True, slots=True)
class RuntimeCaseProjection:
    case_id: str
    tax_year: int
    state_status: str
    state_revision: int
    runs: tuple[tuple[str,str,int], ...]
    storage_state: str
    providers_state: str = "OPERATIONAL_ACCEPTANCE_REQUIRED"


class ProductionRuntime:
    """Borrow existing authorities; never own a second registry or dispatcher."""

    OPERATIONS=frozenset({"case_creation","document_ingestion","gemini_extraction","csv_processing","drive_mutation","approval","submission","provider_activation"})

    def __init__(self, *, persistence: SQLiteCasePersistence, identity: IdentityPersistence,
                 creation_workflow: CaseCreationWorkflow, kernel: OrchestratorKernel,
                 owner_id: str, allowed_case_ids: frozenset[str],
                 provider_interfaces: Mapping[str,object] | None = None) -> None:
        if not isinstance(persistence,SQLiteCasePersistence) or not isinstance(identity,IdentityPersistence):
            raise ValueError("accepted persistence and Identity authority are required")
        if not isinstance(creation_workflow,CaseCreationWorkflow) or not isinstance(kernel,OrchestratorKernel):
            raise ValueError("existing workflow and Kernel are required")
        if not owner_id.strip() or not allowed_case_ids or any(not isinstance(c,str) or not c.strip() for c in allowed_case_ids):
            raise ValueError("exact owner and case allowlist are required")
        interfaces=dict(provider_interfaces or {})
        if set(interfaces)-self.OPERATIONS: raise ValueError("unknown provider interface")
        self._persistence=persistence; self._identity=identity; self._workflow=creation_workflow
        self._kernel=kernel; self._owner=owner_id; self._allowed=frozenset(allowed_case_ids)
        self._interfaces=interfaces
        self._runtime()

    def _runtime(self):
        runtime=self._persistence.load_runtime(owner_id=self._owner,allowed_case_ids=self._allowed)
        records=runtime.registry.all_records()
        self._identity.verify_runtime_cases(records)
        self._workflow.verify_runtime_cases(records)
        return runtime

    def read_cases(self) -> tuple[DashboardCase,...]:
        try:
            runtime=self._runtime()
            return tuple(DashboardCase(r.case_id,r.tax_period.year,r.lifecycle_status.value) for r in runtime.registry.all_records())
        except Exception as exc:
            raise DashboardUnavailable("verified runtime unavailable") from exc

    def read_case(self, case_id: str, tax_year: int) -> RuntimeCaseProjection:
        if case_id not in self._allowed or isinstance(tax_year,bool) or not isinstance(tax_year,int):
            raise PermissionError("case/year is outside runtime scope")
        runtime=self._runtime(); record=runtime.registry.get(case_id)
        if record is None or record.tax_period.year!=tax_year: raise PermissionError("case/year mismatch")
        state=self._persistence.get_state(owner_id=self._owner,case_id=case_id,tax_year=tax_year)
        storage="UNAVAILABLE"
        try:
            self._persistence.load_completed_storage_references(owner_id=self._owner,allowed_case_ids=frozenset({case_id}))
            storage="COMPLETE"
        except StorageProvisioningUnavailable:
            # A valid case may predate provisioning. No provider/folder inference.
            storage="UNAVAILABLE"
        return RuntimeCaseProjection(case_id,tax_year,state.state.lifecycle_status,state.revision,
            tuple((r.run.run_id,r.run.status.value,r.revision) for r in runtime.case_runs(case_id)),storage)

    def request_operation(self, operation: str, *, case_id: str, tax_year: int) -> None:
        if operation not in self.OPERATIONS: raise ValueError("unknown protected operation")
        self.read_case(case_id,tax_year)
        self._persistence.record_runtime_denial(owner_id=self._owner,case_id=case_id,tax_year=tax_year,operation=operation)
        raise ProtectedOperationDisabled("OPERATIONAL_ACCEPTANCE_REQUIRED")

    def request_activation(self, *, case_id: str, tax_year: int) -> None:
        """Credentials/configuration alone can never grant operational authority."""
        self.request_operation("provider_activation",case_id=case_id,tax_year=tax_year)

    def verify_run_reference(self, case_id: str, tax_year: int, run_id: str) -> None:
        projection=self.read_case(case_id,tax_year)
        if not isinstance(run_id,str) or not run_id.strip() or run_id not in {run[0] for run in projection.runs}:
            raise PermissionError("run is outside the committed case/year scope")

    def verify_activation_scope(self, owner_id: str, configured_case: str, configured_year: int,
                                configured_run: str, case_id: str, tax_year: int, run_id: str) -> None:
        self.verify_run_reference(case_id,tax_year,run_id)
        if (owner_id,configured_case,configured_year,configured_run)!=(self._owner,case_id,tax_year,run_id):
            raise PermissionError("activation configuration scope mismatch")

    def storage_requires_reconciliation(self, case_id: str, tax_year: int) -> bool:
        self.read_case(case_id,tax_year)
        status=self._persistence.read_provisioning_status(owner_id=self._owner,case_id=case_id,tax_year=tax_year)
        return status in {"IN_PROGRESS","RECONCILIATION_REQUIRED"}

    def assess_readiness(self, configuration=None, *, case_id: str, tax_year: int,
                         run_id: str, authority_references=None):
        from agent_lab.runtime_activation import assess_runtime_readiness
        return assess_runtime_readiness(self,configuration,case_id=case_id,tax_year=tax_year,
            run_id=run_id,authority_references=authority_references)
