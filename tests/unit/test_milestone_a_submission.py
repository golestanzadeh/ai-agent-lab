from datetime import datetime, timedelta, timezone
import hashlib
import json
import sqlite3
from types import SimpleNamespace

import pytest

from agent_lab.approval import InvalidApprovalError
from agent_lab.case_registry import AssessmentMode, CaseRecord, CaseRegistry, CaseType, LifecycleStatus, OwnerType, StorageScopeReference, TaxPeriod
from agent_lab.durable_approval import DurableApprovalError, DurableApprovalIntegrityError, DurableApprovalStore
from agent_lab.elster_dry_run import ApprovalStatus, ContentReleaseApproval, DestinationTransmissionApproval
from agent_lab.milestone_a_submission import MilestoneASubmissionCoordinator
from agent_lab.synthetic_product_service import SyntheticProductService
from agent_lab.synthetic_workflow_store import SyntheticWorkflowStore, WorkflowStage

NOW=datetime(2026,9,28,12,tzinfo=timezone.utc); CASE="SYNTHETIC-MA04"; RUN="RUN-SYNTHETIC-MA04"; YEAR=2024; REF="sha256:"+"a"*64

class ScopedRuns:
    def __init__(self, case_id, run_id): self.runs={(case_id,run_id)}
    def add(self, case_id, run_id): self.runs.add((case_id,run_id))
    def get_run(self, case_id, run_id):
        if (case_id,run_id) not in self.runs: raise KeyError(run_id)
        return SimpleNamespace(case_id=case_id,run_id=run_id)

def registry(case=CASE):
    r=CaseRegistry(); r.register(CaseRecord(case,OwnerType.PERSON,"SYNTHETIC-PERSON",TaxPeriod("CALENDAR_YEAR",YEAR),CaseType.INDIVIDUAL,AssessmentMode.NOT_APPLICABLE,LifecycleStatus.CREATED,StorageScopeReference("synthetic_local","ma04"),1,NOW,NOW)); return r

def setup(tmp_path, case=CASE, run=RUN):
    r=registry(case); state=ScopedRuns(case,run)
    approvals=DurableApprovalStore(tmp_path/"approvals.sqlite3",case_registry=r,case_state=state)
    workflow=SyntheticWorkflowStore(tmp_path/"workflow.sqlite3"); product=SyntheticProductService(r,workflow)
    current=product.start(case,YEAR,run,REF,"CREATE")
    stages=(WorkflowStage.INTAKE,WorkflowStage.PROCESS,WorkflowStage.SPECIALIST_REVIEW,WorkflowStage.CHIEF_REVIEW,WorkflowStage.CALCULATION,WorkflowStage.FORM_PREVIEW)
    for n,target in enumerate(stages,1): current=product.advance(case,YEAR,run,current.stage,target,REF,f"PRE-{n}")
    content=ContentReleaseApproval("SYNTH-CONTENT-MA04","SYNTH-HUMAN-1",case,run,REF,"1","SYNTHETIC","test",NOW,NOW+timedelta(hours=2),ApprovalStatus.APPROVED)
    destination=DestinationTransmissionApproval("SYNTH-DEST-MA04","SYNTH-HUMAN-2",content.approval_id,case,run,REF,"1","SYNTH-ELSTER-ACCEPTANCE-SERVER","SYNTH-ERIC","test",NOW+timedelta(minutes=1),NOW+timedelta(hours=2),False,ApprovalStatus.APPROVED)
    approvals.register_submission_approval(content); approvals.register_submission_approval(destination)
    intent={"operation_id":"SYNTH-OP-MA04","case_id":case,"tax_year":YEAR,"run_id":run,"artifact_reference":REF,"artifact_version":"1","content_approval_id":content.approval_id,"destination_approval_id":destination.approval_id,"destination_identity":"SYNTH-ELSTER-ACCEPTANCE-SERVER","channel":"SYNTH-ERIC","purpose":"test","requested_at":NOW.isoformat(timespec="microseconds").replace("+00:00","Z")}
    return approvals,workflow,intent

@pytest.mark.parametrize("boundary",["INTENT_RECORDED","APPROVALS_CONSUMED","APPROVAL_STAGE_1","APPROVAL_STAGE_2","SYNTHETIC_SUBMISSION","RECEIPT","RECOVERY","MARKER_APPROVAL_STAGE_1","MARKER_APPROVAL_STAGE_2","MARKER_SYNTHETIC_SUBMISSION","MARKER_RECEIPT","MARKER_RECOVERY"])
def test_crash_restart_replay_at_every_commit_boundary(tmp_path,boundary):
    approvals,workflow,intent=setup(tmp_path)
    with pytest.raises(RuntimeError): MilestoneASubmissionCoordinator(approvals,workflow).execute(intent,now=NOW+timedelta(minutes=2),crash_after=boundary)
    approvals.close(); workflow.close()
    # Reopen both independent databases and deterministically replay the exact transition.
    r=registry(); state=ScopedRuns(CASE,RUN)
    with DurableApprovalStore(tmp_path/"approvals.sqlite3",case_registry=r,case_state=state) as a, SyntheticWorkflowStore(tmp_path/"workflow.sqlite3") as w:
        result=MilestoneASubmissionCoordinator(a,w).execute(intent,now=NOW+timedelta(minutes=3))
        assert result["state"]=="COMPLETE"; assert w.get(CASE,YEAR,RUN).stage is WorkflowStage.RECOVERY
        assert result["result"]["network_calls"]==[] and result["receipt"]["external_receipt_received"] is False
        assert MilestoneASubmissionCoordinator(a,w).execute(intent,now=NOW+timedelta(minutes=4))==result
        row=a._connection.execute("SELECT COUNT(*) result_count,COUNT(receipt_json) receipt_count FROM durable_submission_coordinators WHERE operation_id=? AND result_json IS NOT NULL",(intent["operation_id"],)).fetchone()
        assert (row["result_count"],row["receipt_count"])==(1,1)

def test_expired_revoked_rebound_and_cross_case_fail_closed(tmp_path):
    approvals,workflow,intent=setup(tmp_path)
    with pytest.raises(DurableApprovalError): MilestoneASubmissionCoordinator(approvals,workflow).execute(intent,now=NOW+timedelta(hours=3))
    with pytest.raises(DurableApprovalError): approvals.begin_submission_coordinator({**intent,"purpose":"changed"})
    cross={**intent,"operation_id":"SYNTH-OP-CROSS","case_id":"SYNTHETIC-OTHER"}
    with pytest.raises(InvalidApprovalError): MilestoneASubmissionCoordinator(approvals,workflow).execute(cross,now=NOW+timedelta(minutes=2))
    approvals.close(); workflow.close()

def test_corrupt_or_ambiguous_coordinator_fails_closed(tmp_path):
    approvals,workflow,intent=setup(tmp_path); approvals.begin_submission_coordinator(intent); approvals.close(); workflow.close()
    db=sqlite3.connect(tmp_path/"approvals.sqlite3"); db.execute("UPDATE durable_submission_coordinators SET markers_json='{}',state='COMPLETE'"); db.commit(); db.close()
    r=registry(); state=ScopedRuns(CASE,RUN)
    with DurableApprovalStore(tmp_path/"approvals.sqlite3",case_registry=r,case_state=state) as reopened:
        with pytest.raises(DurableApprovalIntegrityError): reopened.get_submission_coordinator(intent["operation_id"])

def test_consumption_corruption_and_second_operation_reuse_fail_closed(tmp_path):
    approvals,workflow,intent=setup(tmp_path)
    with pytest.raises(RuntimeError): MilestoneASubmissionCoordinator(approvals,workflow).execute(intent,now=NOW+timedelta(minutes=2),crash_after="APPROVALS_CONSUMED")
    approvals._connection.execute("UPDATE durable_submission_approvals SET consumed_by=NULL WHERE approval_id=?",(intent["content_approval_id"],))
    with pytest.raises(DurableApprovalIntegrityError): MilestoneASubmissionCoordinator(approvals,workflow).execute(intent,now=NOW+timedelta(minutes=3))
    approvals._connection.execute("UPDATE durable_submission_approvals SET consumed_by=? WHERE approval_id=?",(intent["operation_id"],intent["content_approval_id"]))
    second={**intent,"operation_id":"SYNTH-OP-MA04-SECOND"}
    with pytest.raises(Exception,match="APPROVAL_ALREADY_CONSUMED"):
        MilestoneASubmissionCoordinator(approvals,workflow).execute(second,now=NOW+timedelta(minutes=3))
    approvals.close(); workflow.close()

def test_revoked_approval_and_unsafe_receipt_payload_fail_closed(tmp_path):
    approvals,workflow,intent=setup(tmp_path)
    row=approvals._connection.execute("SELECT payload_json FROM durable_submission_approvals WHERE approval_id=?",(intent["content_approval_id"],)).fetchone()
    payload=json.loads(row["payload_json"]); payload["status"]="REVOKED"; encoded=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False); digest="sha256:"+hashlib.sha256(encoded.encode()).hexdigest()
    approvals._connection.execute("UPDATE durable_submission_approvals SET payload_json=?,integrity_digest=? WHERE approval_id=?",(encoded,digest,intent["content_approval_id"]))
    with pytest.raises(DurableApprovalError,match="not approved"): MilestoneASubmissionCoordinator(approvals,workflow).execute(intent,now=NOW+timedelta(minutes=2))
    approvals.close(); workflow.close()

def test_public_commit_api_rejects_early_or_external_receipt(tmp_path):
    approvals,workflow,intent=setup(tmp_path); approvals.begin_submission_coordinator(intent); approvals.consume_coordinator_approvals(intent["operation_id"],now=NOW+timedelta(minutes=2))
    with pytest.raises(DurableApprovalError): approvals.commit_submission_coordinator(intent["operation_id"],"APPROVAL_STAGE_1",receipt={"external_receipt_received":True})
    approvals.close(); workflow.close()

def test_fully_registered_cross_case_collision_fails_closed(tmp_path):
    approvals,workflow,intent=setup(tmp_path); other_case="SYNTHETIC-MA04-OTHER"; other_run="RUN-SYNTHETIC-MA04-OTHER"
    approvals._case_registry.register(CaseRecord(other_case,OwnerType.PERSON,"SYNTHETIC-PERSON-2",TaxPeriod("CALENDAR_YEAR",YEAR),CaseType.INDIVIDUAL,AssessmentMode.NOT_APPLICABLE,LifecycleStatus.CREATED,StorageScopeReference("synthetic_local","ma04-other"),1,NOW,NOW)); approvals._case_state.add(other_case,other_run)
    product=SyntheticProductService(approvals._case_registry,workflow); current=product.start(other_case,YEAR,other_run,REF,"OTHER-CREATE")
    for n,target in enumerate((WorkflowStage.INTAKE,WorkflowStage.PROCESS,WorkflowStage.SPECIALIST_REVIEW,WorkflowStage.CHIEF_REVIEW,WorkflowStage.CALCULATION,WorkflowStage.FORM_PREVIEW),1): current=product.advance(other_case,YEAR,other_run,current.stage,target,REF,f"OTHER-{n}")
    cross={**intent,"operation_id":"SYNTH-OP-MA04-CROSS","case_id":other_case,"run_id":other_run}
    with pytest.raises(DurableApprovalError,match="does not match coordinator intent"):
        MilestoneASubmissionCoordinator(approvals,workflow).execute(cross,now=NOW+timedelta(minutes=2))
    assert workflow.get(other_case,YEAR,other_run).stage is WorkflowStage.FORM_PREVIEW
    approvals.close(); workflow.close()

def test_unregistered_but_internally_consistent_scope_is_denied(tmp_path):
    approvals,workflow,intent=setup(tmp_path); unknown_case="SYNTHETIC-UNKNOWN"; unknown_run="RUN-SYNTHETIC-UNKNOWN"
    workflow.create(unknown_case,YEAR,unknown_run,REF,"UNKNOWN-CREATE")
    unknown_content=ContentReleaseApproval("SYNTH-CONTENT-UNKNOWN","SYNTH-HUMAN-1",unknown_case,unknown_run,REF,"1","SYNTHETIC","test",NOW,NOW+timedelta(hours=1),ApprovalStatus.APPROVED)
    with pytest.raises(InvalidApprovalError,match="unknown case_id"):
        approvals.register_submission_approval(unknown_content)
    unknown_intent={**intent,"operation_id":"SYNTH-OP-UNKNOWN","case_id":unknown_case,"run_id":unknown_run,"content_approval_id":unknown_content.approval_id}
    with pytest.raises(InvalidApprovalError,match="unknown case_id"):
        approvals.begin_submission_coordinator(unknown_intent)
    approvals.close(); workflow.close()
