import copy
import pytest
from test_case_analysis_kernel_dispatch import make,REQ
from agent_lab.case_analysis_executor import AnalysisRequest
from agent_lab.case_analysis_projection import import_reviewed,read
from agent_lab.orchestrator_kernel import PermissionDenied


def payload():
    return {'case_id':REQ.case_id,'tax_year':REQ.tax_year,
            'csv':{'source_sha256':'a'*64,'row_count':2,'credits':'10.00','debits':'3.00','net':'7.00','status':'VERIFIED'},
            'subtotals':{'employment_income_component_using_allowance':'100.00'},'conditional':{'not_accepted':'1.00'},
            'links':[],'questions':['Missing annual evidence'],'spouse_payroll':None,
            'acceptance':'VERIFIED_SUBTOTALS_NOT_FINAL_TAX_ACCEPTANCE'}


def test_existing_kernel_projection_restart_idempotency_scope_and_tamper(tmp_path):
    d,e=make(tmp_path);p=payload();bindings=['sha256:'+'b'*64]
    with d._kernel() as k:k.set_kill_switch('RUNNING',actor_id='HUMAN_PROJECT_OWNER',authority_reference='owner://synthetic-start')
    first=import_reviewed(d,REQ,p,source_bindings=bindings,authority_reference='owner://synthetic-reviewed-import',verify_case=lambda *args:True)
    assert import_reviewed(d,REQ,p,source_bindings=bindings,authority_reference='owner://synthetic-reviewed-import',verify_case=lambda *args:True)==first
    reopened,_=make(tmp_path);assert read(reopened,REQ)==first and not e.calls
    assert read(reopened,AnalysisRequest('OTHER',2025,REQ.owner_id)) is None
    assert read(reopened,AnalysisRequest(REQ.case_id,2024,REQ.owner_id)) is None
    assert read(reopened,AnalysisRequest(REQ.case_id,2025,'OTHER')) is None
    with d._kernel() as k:
        k.verify_audit_chain()
        with k._connection:k._connection.execute("UPDATE responses SET payload_json=replace(payload_json,'100.00','900.00')")
    with pytest.raises(PermissionDenied):read(reopened,REQ)


def test_projection_rejects_final_tax_acceptance_and_bad_money(tmp_path):
    d,_=make(tmp_path)
    p=payload();p['acceptance']='FINAL_TAX_ACCEPTED'
    with pytest.raises(PermissionDenied):import_reviewed(d,REQ,p,source_bindings=['sha256:'+'a'*64],authority_reference='owner://test',verify_case=lambda *args:True)
    p=payload();p['csv']['net']='8.00'
    with pytest.raises(ValueError):import_reviewed(d,REQ,p,source_bindings=['sha256:'+'a'*64],authority_reference='owner://test',verify_case=lambda *args:True)
