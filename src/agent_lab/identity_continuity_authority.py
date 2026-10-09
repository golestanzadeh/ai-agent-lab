"""Synthetic identity continuity adapter backed by the real Orchestrator Kernel."""
from __future__ import annotations

from dataclasses import dataclass

from agent_lab.orchestrator_kernel import IntegrityError, OrchestratorKernel


IdentityContinuityError = IntegrityError


@dataclass(frozen=True, slots=True)
class IdentityContinuityContext:
    deployment_id: str
    case_id: str
    tax_year: int
    task_id: str
    manifest_id: str
    run_id: str
    operation: str


class IdentityContinuityAuthority:
    """Narrow adapter; all authoritative state and decisions remain in Kernel."""

    def __init__(self, kernel: OrchestratorKernel, context: IdentityContinuityContext) -> None:
        self._kernel = kernel
        self.context = context

    def initialize(self, head: str) -> None:
        self._kernel.initialize_identity_continuity(
            deployment_id=self.context.deployment_id, case_id=self.context.case_id,
            tax_year=self.context.tax_year, head=head,
        )

    def reserve(self, epoch: int, current_head: str, next_head: str) -> None:
        self._kernel.reserve_identity_continuity(
            **self._scope(), expected_epoch=epoch, expected_head=current_head, next_head=next_head,
        )

    def finalize(self, epoch: int, next_head: str) -> None:
        self._kernel.finalize_identity_continuity(
            **self._scope(), committed_epoch=epoch + 1, committed_head=next_head,
        )

    def reconcile(self, identity_epoch: int, identity_head: str) -> None:
        self._kernel.reconcile_identity_continuity(
            **self._scope(), identity_epoch=identity_epoch, identity_head=identity_head,
        )

    def verify(self, epoch: int, head: str) -> None:
        self._kernel.verify_identity_continuity(
            deployment_id=self.context.deployment_id, case_id=self.context.case_id,
            tax_year=self.context.tax_year, epoch=epoch, head=head,
        )

    def _scope(self) -> dict[str, object]:
        return {
            "deployment_id": self.context.deployment_id,
            "case_id": self.context.case_id,
            "tax_year": self.context.tax_year,
            "manifest_id": self.context.manifest_id,
            "task_id": self.context.task_id,
            "run_id": self.context.run_id,
            "operation": self.context.operation,
        }
