"""Strictly read-only, synthetic-only Kernel status projection for UI25."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agent_lab.orchestrator_kernel import OrchestratorKernel


ALLOWED_TASK_STATUSES = frozenset({
    "REGISTERED", "HUMAN_REQUIRED", "REJECTED", "ACTIVE", "BLOCKED",
    "AWAITING_ACCEPTANCE", "COMPLETED", "FAILED", "CANCELLED", "EXPIRED", "REVOKED",
})


class KernelProjectionUnavailable(RuntimeError):
    """The requested projection cannot be proven from the Kernel."""


@dataclass(frozen=True, slots=True)
class KernelTaskProjection:
    task_id: str
    role_id: str
    status: str
    response_status: str | None = None
    result_summary: str | None = None


@dataclass(frozen=True, slots=True)
class KernelRunProjection:
    case_id: str
    tax_year: int
    run_id: str
    kill_switch: str
    tasks: tuple[KernelTaskProjection, ...]


class ReadOnlyKernelProjection:
    """Adapter over the existing Kernel's integrity-checked observation API."""

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path).resolve()

    def read(self, case_id: str, tax_year: int, run_id: str) -> KernelRunProjection:
        try:
            raw = OrchestratorKernel.inspect_case_run_read_only(
                self.database_path, case_id=case_id, tax_year=tax_year, run_id=run_id
            )
        except Exception as exc:
            raise KernelProjectionUnavailable(str(exc)) from exc
        if raw.get("audit_integrity") != "PASS":
            raise KernelProjectionUnavailable("Kernel audit integrity is not proven")
        tasks = tuple(
            KernelTaskProjection(
                item["task_id"], item["role_id"], item["status"],
                item.get("response_status"), item.get("result_summary"),
            )
            for item in raw.get("tasks", ())
        )
        if not tasks or len({task.task_id for task in tasks}) != len(tasks):
            raise KernelProjectionUnavailable("Kernel task projection is empty or ambiguous")
        if any(task.status not in ALLOWED_TASK_STATUSES for task in tasks):
            raise KernelProjectionUnavailable("Kernel task projection contains an unknown status")
        return KernelRunProjection(
            case_id=raw["case_id"], tax_year=raw["tax_year"], run_id=raw["run_id"],
            kill_switch=raw["kill_switch"], tasks=tasks,
        )
