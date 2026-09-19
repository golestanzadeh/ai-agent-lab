"""Synthetic display-only submission-readiness presentation."""
from dataclasses import dataclass
from agent_lab.ui_state_contract import UIWorkspaceState

BLOCKERS=("OFFICIAL_ERIC_MAPPING_NOT_RECOVERED","OFFICIAL_MATERIAL_NOT_VERIFIED","CREDENTIALS_NOT_AUTHORIZED","TRANSMITTER_NOT_IMPLEMENTED","REAL_TRANSMISSION_NOT_AUTHORIZED")
class UISubmissionReadinessError(ValueError): pass

@dataclass(frozen=True,slots=True)
class SyntheticSubmissionReadiness:
    case_id:str; run_id:str; artifact_reference:str
    content_release_status:str="NOT_APPROVED"
    destination_transmission_status:str="NOT_APPROVED"
    blockers:tuple[str,...]=BLOCKERS
    ready:bool=False; submission_enabled:bool=False; receipt_reference:str|None=None
    data_classification:str="SYNTHETIC_DISPLAY_ONLY"; network_calls:tuple[str,...]=()
    def __post_init__(self):
        if not self.case_id.startswith("SYNTH-") or not self.run_id.startswith("SYNTH-"): raise UISubmissionReadinessError("scope must be synthetic")
        digest=self.artifact_reference[7:] if self.artifact_reference.startswith("sha256:") else ""
        if len(digest)!=64 or any(c not in "0123456789abcdef" for c in digest): raise UISubmissionReadinessError("artifact must be canonical")
        if self.content_release_status!="NOT_APPROVED" or self.destination_transmission_status!="NOT_APPROVED": raise UISubmissionReadinessError("Article 1 stages cannot be approved here")
        if self.blockers!=BLOCKERS: raise UISubmissionReadinessError("blocker set cannot change")
        if self.ready or self.submission_enabled or self.receipt_reference is not None or self.network_calls: raise UISubmissionReadinessError("operational submission state is forbidden")
        if self.data_classification!="SYNTHETIC_DISPLAY_ONLY": raise UISubmissionReadinessError("classification cannot change")

def build_synthetic_submission_readiness(workspace:UIWorkspaceState)->SyntheticSubmissionReadiness:
    if workspace.run_id is None or workspace.preview_reference is None: raise UISubmissionReadinessError("populated workspace required")
    return SyntheticSubmissionReadiness(workspace.case_id,workspace.run_id,workspace.preview_reference)
