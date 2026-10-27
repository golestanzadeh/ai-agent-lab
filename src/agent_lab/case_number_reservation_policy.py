"""Pure fail-closed Stage 3 reservation-release policy; no storage mutations."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ReservationEvidence:
    case_active: bool
    restorable_backup_count: int
    protected_hold: bool
    pending_operation: bool
    inventory_verified: bool
    original_identity_verified: bool


def may_release_number(evidence: ReservationEvidence) -> bool:
    """Permit release only when every authoritative safety condition is proven."""
    if not isinstance(evidence, ReservationEvidence):
        return False
    if type(evidence.case_active) is not bool:
        return False
    if type(evidence.restorable_backup_count) is not int or evidence.restorable_backup_count < 0:
        return False
    if any(type(x) is not bool for x in (
        evidence.protected_hold, evidence.pending_operation,
        evidence.inventory_verified, evidence.original_identity_verified
    )):
        return False
    return (
        not evidence.case_active
        and evidence.restorable_backup_count == 0
        and not evidence.protected_hold
        and not evidence.pending_operation
        and evidence.inventory_verified
        and evidence.original_identity_verified
    )
