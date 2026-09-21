"""Privacy-safe support and recovery state for the synthetic local UI."""

from __future__ import annotations

from dataclasses import dataclass

from agent_lab.ui_state_contract import UIWorkspaceState


SUPPORT_VERSION = "1"
SAFE_SUPPORT_CODES = (
    "READ_ONLY_RECOVERY_DIAGNOSTICS_AVAILABLE",
    "PAUSE_CONTROL_NOT_IMPLEMENTED",
    "RESUME_CONTROL_NOT_IMPLEMENTED",
    "STOP_CONTROL_NOT_IMPLEMENTED",
    "RECEIPT_NOT_AVAILABLE_NO_TRANSMISSION",
)


class UISupportError(ValueError):
    """Raised when support diagnostics are incomplete or operationally unsafe."""


@dataclass(frozen=True, slots=True)
class SyntheticUISupport:
    case_id: str
    run_id: str
    status_codes: tuple[str, ...]
    version: str = SUPPORT_VERSION
    data_classification: str = "SYNTHETIC"
    controls_enabled: bool = False
    receipt_present: bool = False
    network_calls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.case_id.startswith("SYNTH-") or not self.run_id.startswith("SYNTH-"):
            raise UISupportError("support scope must be synthetic")
        if self.version != SUPPORT_VERSION or self.data_classification != "SYNTHETIC":
            raise UISupportError("unsupported support version or classification")
        if self.status_codes != SAFE_SUPPORT_CODES:
            raise UISupportError("exact privacy-safe support codes are required")
        if self.controls_enabled is not False or self.receipt_present is not False:
            raise UISupportError("operational controls and receipts must remain unavailable")
        if self.network_calls != ():
            raise UISupportError("support diagnostics cannot make network calls")


def build_synthetic_ui_support(workspace: UIWorkspaceState) -> SyntheticUISupport:
    """Build display-only diagnostics for exactly one populated synthetic workspace."""
    if not isinstance(workspace, UIWorkspaceState) or workspace.run_id is None:
        raise UISupportError("a populated UIWorkspaceState is required")
    return SyntheticUISupport(
        case_id=workspace.case_id,
        run_id=workspace.run_id,
        status_codes=SAFE_SUPPORT_CODES,
    )
