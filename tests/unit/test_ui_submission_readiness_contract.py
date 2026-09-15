from dataclasses import replace
import pytest
from agent_lab.ui_app import _populate_synthetic_state,build_synthetic_registry
from agent_lab.ui_state_contract import select_synthetic_workspace
from agent_lab.ui_submission_readiness_contract import BLOCKERS,UISubmissionReadinessError,build_synthetic_submission_readiness
def view():
 w=_populate_synthetic_state(select_synthetic_workspace(build_synthetic_registry(),case_id="SYNTH-CASE-001",tax_year=2024)); return w,build_synthetic_submission_readiness(w)
def test_readiness_is_bound_separate_and_blocked():
 w,v=view(); assert (v.case_id,v.run_id,v.artifact_reference)==(w.case_id,w.run_id,w.preview_reference); assert v.blockers==BLOCKERS; assert v.content_release_status==v.destination_transmission_status=="NOT_APPROVED"; assert not v.ready
@pytest.mark.parametrize("field,value",[("content_release_status","APPROVED"),("destination_transmission_status","APPROVED"),("ready",True),("submission_enabled",True),("receipt_reference","sha256:"+"a"*64),("network_calls",("x",)),("blockers",())])
def test_operational_or_weakened_state_is_denied(field,value):
 with pytest.raises(UISubmissionReadinessError): replace(view()[1],**{field:value})
