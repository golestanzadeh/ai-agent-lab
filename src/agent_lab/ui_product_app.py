"""Composition root for the local product Dashboard.

The command-line launcher uses the fail-closed no-source application.  An
accepted runtime host may inject the existing CaseRegistry plus exact owner and
case authorization; this module never reconstructs or persists a parallel
registry.
"""

from __future__ import annotations

from collections.abc import Iterable

from fastapi import FastAPI

from agent_lab.case_registry import CaseRegistry
from agent_lab.ui_case_registry_reader import CaseRegistryDashboardReader
from agent_lab.ui_dashboard import ReadKernelProjection, create_dashboard_app


def create_product_dashboard_app(
    *,
    registry: CaseRegistry | None = None,
    owner_id: str | None = None,
    allowed_case_ids: Iterable[str] | None = None,
    read_kernel_projection: ReadKernelProjection | None = None,
) -> FastAPI:
    """Build the production UI with an optional authorized read-only source.

    All three source arguments form one configuration unit.  Partial
    configuration is rejected at startup.  With no source, the Dashboard still
    starts on loopback and truthfully reports that protected case data is
    unavailable.
    """

    configured = (registry is not None, owner_id is not None, allowed_case_ids is not None)
    if any(configured) and not all(configured):
        raise ValueError("registry, owner_id and allowed_case_ids must be configured together")

    reader = None
    if all(configured):
        assert registry is not None and owner_id is not None and allowed_case_ids is not None
        reader = CaseRegistryDashboardReader(
            registry=registry,
            owner_id=owner_id,
            allowed_case_ids=frozenset(allowed_case_ids),
        )
    if read_kernel_projection is not None and reader is None:
        raise ValueError("Kernel projection requires the configured case source")
    app = create_dashboard_app(
        read_cases=reader,
        read_kernel_projection=read_kernel_projection,
    )
    app.state.product_case_source = "configured" if reader is not None else "unavailable"
    return app


app = create_product_dashboard_app()
