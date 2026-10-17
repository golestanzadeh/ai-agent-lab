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
    extraction_fields: tuple[tuple[str, str], ...] = ()


_EXTRACTION_KEYS = (
    "DOCUMENT_REFERENCE", "DOCUMENT_DIGEST", "PARSER_SCHEMA", "EXTRACTION_DIGEST",
    "DOCUMENT_TYPE", "TAX_YEAR", "EMPLOYER_ID", "GROSS_EMPLOYMENT_INCOME",
    "WITHHELD_WAGE_TAX", "CURRENCY",
)


def _extraction_fields(summary: str | None) -> tuple[tuple[str, str], ...]:
    if summary is None or not summary.startswith("SYNTHETIC_CONTENT_EXTRACTION=VALID; "):
        return ()
    parts: dict[str, str] = {}
    for item in summary.split("; "):
        if "=" in item:
            key, value = item.split("=", 1)
            if key in parts:
                raise KernelProjectionUnavailable("duplicate extraction result field")
            parts[key] = value
    if any(not parts.get(key) for key in _EXTRACTION_KEYS):
        raise KernelProjectionUnavailable("incomplete extraction result")
    if "NOT_TAX_ANALYSIS" not in summary.split("; "):
        raise KernelProjectionUnavailable("extraction boundary marker is missing")
    return tuple((key, parts[key]) for key in _EXTRACTION_KEYS)


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
                _extraction_fields(item.get("result_summary")),
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
