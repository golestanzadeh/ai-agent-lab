"""Adapter to the accepted OrchestratorKernel Permission Matrix v1.

The manifest ID and run ID are supplied by the trusted caller, not inferred from
a user-provided authorization reference. An absent manifest fails closed.
"""
from __future__ import annotations

from agent_lab.case_registry import CaseRegistry
from agent_lab.orchestrator_kernel import OrchestratorKernel


def kernel_case_authorizer(
    *, kernel: OrchestratorKernel, cases: CaseRegistry,
    manifest_id: str, run_id: str,
):
    """Return a scoped callback for IdentityPersistence.

    Kernel permission_decision checks active manifest, kill switch, capability
    grant, and exact case/year/run. Case root is checked separately here.
    """
    if not manifest_id or not run_id:
        raise ValueError("manifest and run IDs are required")

    def authorize(action: str, case_id: str, root_id: str, reference: str) -> bool:
        case = cases.get(case_id)
        if case is None or case.storage_scope_reference.root_id != root_id:
            return False
        if not reference:
            return False
        capability = (
            "read_derived_case_artifact" if action in {"read_party", "read_identity", "read_fact"}
            else "write_derived_case_artifact"
            if action in {"register_identity", "update_identity", "bind_party", "bind_fact"}
            else None
        )
        if capability is None:
            return False
        try:
            decision = kernel.permission_decision(
                manifest_id, capability, case_id=case_id,
                tax_year=case.tax_period.year, run_id=run_id,
            )
            return decision.allowed is True and decision.outcome == "ALLOW"
        except Exception:
            return False

    return authorize
