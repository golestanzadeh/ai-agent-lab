"""Fail-closed binding between Kernel task scope and durable case runs.

This adapter never dispatches work.  It permits durable lifecycle mutation only
when the existing Kernel already owns an exactly matching task context.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from agent_lab.case_persistence import SQLiteCasePersistence, VersionedRun
from agent_lab.case_state import RunStatus
from agent_lab.orchestrator_kernel import OrchestratorKernel


@dataclass(frozen=True, slots=True)
class DurableKernelRunLifecycle:
    kernel: OrchestratorKernel
    persistence: SQLiteCasePersistence

    def create_for_registered_task(
        self, *, task_id: str, owner_id: str, case_id: str, tax_year: int,
        run_id: str, request_id: str, expected_state_revision: int,
    ) -> VersionedRun:
        self._require_exact_context(task_id, case_id, tax_year, run_id)
        return self.persistence.create_run(
            owner_id=owner_id, case_id=case_id, tax_year=tax_year, run_id=run_id,
            request_id=self._kernel_request_id(task_id, request_id),
            expected_state_revision=expected_state_revision,
        )

    def transition_for_registered_task(
        self, *, task_id: str, owner_id: str, case_id: str, tax_year: int,
        run_id: str, request_id: str, expected_revision: int, status: RunStatus,
    ) -> VersionedRun:
        self._require_exact_context(task_id, case_id, tax_year, run_id)
        return self.persistence.transition_run(
            owner_id=owner_id, case_id=case_id, tax_year=tax_year, run_id=run_id,
            request_id=self._kernel_request_id(task_id, request_id),
            expected_revision=expected_revision, status=status,
        )

    @staticmethod
    def _kernel_request_id(task_id: str, request_id: str) -> str:
        if not task_id.strip() or not request_id.strip():
            raise ValueError("task_id and request_id are required")
        encoded = json.dumps(
            {"request_id": request_id, "task_id": task_id},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
        return "KERNEL-TASK:sha256:" + hashlib.sha256(encoded).hexdigest()

    def _require_exact_context(self, task_id: str, case_id: str, tax_year: int, run_id: str) -> None:
        actual = self.kernel.registered_case_context(task_id)
        expected = {"case_id": case_id, "tax_year": tax_year, "run_id": run_id}
        if actual != expected:
            raise PermissionError("Kernel task and durable run scope do not match")
