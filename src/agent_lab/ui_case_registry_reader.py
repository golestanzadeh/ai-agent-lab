"""Fail-closed, read-only Case Registry projection for the product dashboard."""

from __future__ import annotations

from dataclasses import dataclass

from agent_lab.case_registry import CaseRegistry
from agent_lab.ui_dashboard import DashboardCase, DashboardUnavailable


@dataclass(frozen=True, slots=True)
class CaseRegistryDashboardReader:
    """Project explicitly authorized case metadata into the dashboard.

    The owner scope prevents an unscoped registry scan.  The independent case
    allowlist is deliberate: possession of an owner identifier alone is not UI
    authorization.  No storage reference, person data, or document data crosses
    this boundary.
    """

    registry: CaseRegistry
    owner_id: str
    allowed_case_ids: frozenset[str]

    def __post_init__(self) -> None:
        if not isinstance(self.registry, CaseRegistry):
            raise TypeError("CaseRegistry is required")
        if not self.owner_id.strip():
            raise ValueError("owner_id is required")
        if not self.allowed_case_ids or any(
            not isinstance(case_id, str) or not case_id.strip()
            for case_id in self.allowed_case_ids
        ):
            raise ValueError("a non-empty case allowlist is required")

    def __call__(self) -> tuple[DashboardCase, ...]:
        owner_records = self.registry.list_by_owner(self.owner_id)
        owner_case_ids = {record.case_id for record in owner_records}
        if not self.allowed_case_ids.issubset(owner_case_ids):
            raise DashboardUnavailable("authorized case scope is not resolved")

        return tuple(
            DashboardCase(
                case_id=record.case_id,
                tax_year=record.tax_period.year,
                status=record.lifecycle_status.value,
            )
            for record in owner_records
            if record.case_id in self.allowed_case_ids
        )
