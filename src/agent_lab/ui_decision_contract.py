"""Display-only synthetic Human Decision Queue contract."""
from dataclasses import dataclass
from datetime import datetime
import hashlib
from agent_lab.ui_state_contract import HumanGateStatus, UIWorkspaceState

class UIDecisionError(ValueError): pass

@dataclass(frozen=True, slots=True)
class SyntheticDecisionItem:
    gate_id: str; case_id: str; run_id: str; status: HumanGateStatus; action: str
    artifact_reference: str; destination: str; expires_at: datetime
    operational: bool = False
    def __post_init__(self):
        if not self.gate_id.startswith("SYNTH-GATE-") or not self.case_id.startswith("SYNTH-") or not self.run_id.startswith("SYNTH-"): raise UIDecisionError("decision identity/scope must be synthetic")
        digest=self.artifact_reference[7:] if self.artifact_reference.startswith("sha256:") else ""
        if len(digest)!=64 or any(c not in "0123456789abcdef" for c in digest): raise UIDecisionError("artifact reference must be canonical")
        if self.action!="REVIEW_SYNTHETIC_PREVIEW" or self.destination!="LOCAL_SYNTHETIC_PREVIEW": raise UIDecisionError("decision fields are not allowlisted")
        if self.expires_at.tzinfo is None or self.operational is not False: raise UIDecisionError("decision must be aware and non-operational")

@dataclass(frozen=True, slots=True)
class SyntheticDecisionQueue:
    case_id: str; run_id: str; items: tuple[SyntheticDecisionItem, ...]
    data_classification: str="SYNTHETIC_DISPLAY_ONLY"; mutation_enabled: bool=False
    persistence_enabled: bool=False; network_calls: tuple[str,...]=()
    def __post_init__(self):
        if len(self.items)!=1 or any(x.case_id!=self.case_id or x.run_id!=self.run_id for x in self.items): raise UIDecisionError("queue scope mismatch")
        if self.data_classification!="SYNTHETIC_DISPLAY_ONLY" or self.mutation_enabled or self.persistence_enabled or self.network_calls: raise UIDecisionError("queue cannot gain operational capability")

def build_synthetic_decision_queue(workspace: UIWorkspaceState)->SyntheticDecisionQueue:
    gate=workspace.human_gate
    if workspace.run_id is None or gate.status is HumanGateStatus.NOT_REQUIRED or None in (gate.action,gate.artifact_reference,gate.destination,gate.expires_at): raise UIDecisionError("exact populated Human Gate required")
    raw=f"{workspace.case_id}|{workspace.run_id}|{gate.artifact_reference}"
    item=SyntheticDecisionItem("SYNTH-GATE-"+hashlib.sha256(raw.encode()).hexdigest()[:16],workspace.case_id,workspace.run_id,gate.status,gate.action,gate.artifact_reference,gate.destination,gate.expires_at)
    return SyntheticDecisionQueue(workspace.case_id,workspace.run_id,(item,))
