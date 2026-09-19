from dataclasses import replace
import pytest
from agent_lab.ui_app import _populate_synthetic_state, build_synthetic_registry
from agent_lab.ui_decision_contract import UIDecisionError, build_synthetic_decision_queue
from agent_lab.ui_state_contract import select_synthetic_workspace

def ws(case="SYNTH-CASE-001",year=2024): return _populate_synthetic_state(select_synthetic_workspace(build_synthetic_registry(),case_id=case,tax_year=year))
def test_queue_is_exact_non_operational_gate_binding():
    w=ws(); q=build_synthetic_decision_queue(w); i=q.items[0]
    assert (q.case_id,q.run_id,i.artifact_reference)==(w.case_id,w.run_id,w.preview_reference)
    assert not q.mutation_enabled and not q.persistence_enabled and q.network_calls==()
def test_case_switch_clears_gate_identity(): assert build_synthetic_decision_queue(ws()).items[0].gate_id != build_synthetic_decision_queue(ws("SYNTH-CASE-002",2025)).items[0].gate_id
@pytest.mark.parametrize("field,value",[("mutation_enabled",True),("persistence_enabled",True),("network_calls",("x",))])
def test_queue_denies_capabilities(field,value):
    with pytest.raises(UIDecisionError): replace(build_synthetic_decision_queue(ws()),**{field:value})
def test_missing_gate_fails_closed():
    from agent_lab.ui_state_contract import HumanGateView,HumanGateStatus
    with pytest.raises(UIDecisionError): build_synthetic_decision_queue(replace(ws(),human_gate=HumanGateView(HumanGateStatus.NOT_REQUIRED)))
