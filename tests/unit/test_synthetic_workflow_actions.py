import hashlib
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from agent_lab.case_registry import AssessmentMode, CaseRecord, CaseRegistry, CaseType, LifecycleStatus, OwnerType, StorageScopeReference, TaxPeriod
from agent_lab.synthetic_product_service import SyntheticProductService
from agent_lab.synthetic_workflow_actions import SyntheticAction, SyntheticActionRequest, SyntheticRole, SyntheticWorkflowActionService
from agent_lab.synthetic_workflow_store import SyntheticWorkflowStore, WorkflowStage, WorkflowTransitionError, WorkflowScopeError


CASE="SYNTHETIC-MA03"; YEAR=2024; RUN="RUN-SYNTHETIC-MA03"
def h(value: str) -> str: return "sha256:"+hashlib.sha256(value.encode()).hexdigest()
def registry():
    now=datetime.now(timezone.utc); result=CaseRegistry()
    result.register(CaseRecord(CASE,OwnerType.PERSON,"SYNTHETIC-PERSON",TaxPeriod("CALENDAR_YEAR",YEAR),CaseType.INDIVIDUAL,AssessmentMode.NOT_APPLICABLE,LifecycleStatus.CREATED,StorageScopeReference("synthetic_local","scope-ma03"),1,now,now))
    return result


def setup(tmp_path):
    store=SyntheticWorkflowStore(tmp_path/"ma03.sqlite3")
    product=SyntheticProductService(registry(),store)
    initial=product.start(CASE,YEAR,RUN,h("create"),"MA03-0")
    return store,SyntheticWorkflowActionService(product),initial


def req(action,role,prior,n,invalidated=()):
    return SyntheticActionRequest(action,role,CASE,YEAR,RUN,f"MA03-{n}",prior.transition_hash,prior.artifact_identity,(h(f"input-{n}"),),invalidated)


def test_closed_six_action_sequence_is_deterministic_and_reopens(tmp_path):
    store,service,current=setup(tmp_path)
    sequence=((SyntheticAction.INTAKE,SyntheticRole.INTAKE_AGENT),(SyntheticAction.PROCESS,SyntheticRole.PROCESSING_AGENT),(SyntheticAction.SPECIALIST_REVIEW,SyntheticRole.SPECIALIST_AGENT),(SyntheticAction.CHIEF_REVIEW,SyntheticRole.CHIEF_AGENT),(SyntheticAction.CALCULATE,SyntheticRole.CALCULATION_AGENT),(SyntheticAction.PREPARE_DECLARATION,SyntheticRole.DECLARATION_AGENT))
    for n,(action,role) in enumerate(sequence,1): current=service.execute(req(action,role,current,n))
    assert current.stage is WorkflowStage.FORM_PREVIEW and current.sequence==7
    final=current; store.close()
    with SyntheticWorkflowStore(tmp_path/"ma03.sqlite3") as reopened:
        assert reopened.get(CASE,YEAR,RUN)==final


def test_exact_retry_is_idempotent_but_changed_transition_fails(tmp_path):
    store,service,current=setup(tmp_path)
    request=req(SyntheticAction.INTAKE,SyntheticRole.INTAKE_AGENT,current,1)
    first=service.execute(request); assert service.execute(request)==first
    with pytest.raises(WorkflowTransitionError): service.execute(replace(request,input_artifact_identities=(h("changed"),)))
    store.close()


@pytest.mark.parametrize("change",["role","action","prior"])
def test_role_catalog_sequence_and_prior_state_fail_closed(tmp_path,change):
    store,service,current=setup(tmp_path); request=req(SyntheticAction.INTAKE,SyntheticRole.INTAKE_AGENT,current,1)
    if change=="role": request=replace(request,role=SyntheticRole.CHIEF_AGENT)
    elif change=="action": request=replace(request,action="powershell -Command whoami")
    else: request=replace(request,expected_prior_hash=h("stale"))
    with pytest.raises(WorkflowTransitionError): service.execute(request)
    store.close()


def test_review_correction_invalidates_prior_identity_in_lineage(tmp_path):
    store,service,current=setup(tmp_path)
    current=service.execute(req(SyntheticAction.INTAKE,SyntheticRole.INTAKE_AGENT,current,1))
    current=service.execute(req(SyntheticAction.PROCESS,SyntheticRole.PROCESSING_AGENT,current,2))
    invalid=current.artifact_identity
    corrected=service.execute(req(SyntheticAction.SPECIALIST_REVIEW,SyntheticRole.SPECIALIST_AGENT,current,3,(invalid,)))
    store2,service2,current2=setup(tmp_path/"other")
    current2=service2.execute(req(SyntheticAction.INTAKE,SyntheticRole.INTAKE_AGENT,current2,1))
    current2=service2.execute(req(SyntheticAction.PROCESS,SyntheticRole.PROCESSING_AGENT,current2,2))
    without=service2.execute(req(SyntheticAction.SPECIALIST_REVIEW,SyntheticRole.SPECIALIST_AGENT,current2,3))
    assert corrected.artifact_identity != without.artifact_identity
    attempt=store.action_attempt("MA03-3")
    assert attempt["request"]["invalidated_artifact_identities"] == [invalid]
    store.close(); store2.close()


def test_correction_rejected_outside_review_and_cross_case_denied(tmp_path):
    store,service,current=setup(tmp_path)
    with pytest.raises(WorkflowTransitionError): service.execute(req(SyntheticAction.INTAKE,SyntheticRole.INTAKE_AGENT,current,1,(h("old"),)))
    cross=replace(req(SyntheticAction.INTAKE,SyntheticRole.INTAKE_AGENT,current,1),case_id="SYNTHETIC-OTHER")
    with pytest.raises(WorkflowScopeError): service.execute(cross)
    store.close()


def test_invalid_or_duplicate_artifact_identities_fail_closed(tmp_path):
    store,service,current=setup(tmp_path)
    base=req(SyntheticAction.INTAKE,SyntheticRole.INTAKE_AGENT,current,1)
    for values in ((),("command",),(h("same"),h("same"))):
        with pytest.raises(WorkflowTransitionError): service.execute(replace(base,input_artifact_identities=values))
    store.close()


def test_rejected_attempt_consumes_transition_identity_durably(tmp_path):
    store,service,current=setup(tmp_path)
    wrong=replace(req(SyntheticAction.INTAKE,SyntheticRole.INTAKE_AGENT,current,1),role=SyntheticRole.CHIEF_AGENT)
    with pytest.raises(WorkflowTransitionError): service.execute(wrong)
    assert store.action_attempt("MA03-1")["outcome"]=="REJECTED"
    with pytest.raises(WorkflowTransitionError): service.execute(req(SyntheticAction.INTAKE,SyntheticRole.INTAKE_AGENT,current,1))
    store.close()
