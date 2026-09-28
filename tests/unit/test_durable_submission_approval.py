from dataclasses import replace
from datetime import datetime,timedelta,timezone
import sqlite3
import pytest
from agent_lab.approval import ApprovalAlreadyConsumedError
from agent_lab.durable_approval import DurableApprovalError,DurableApprovalIntegrityError
from agent_lab.elster_dry_run import ApprovalStatus,ContentReleaseApproval,DestinationTransmissionApproval
from test_durable_approval import make_store,reopen

NOW=datetime(2026,9,28,tzinfo=timezone.utc); REF="sha256:"+"a"*64
def pair():
    content=ContentReleaseApproval("SYNTH-CONTENT","SYNTH-HUMAN-1","CASE-2024-0001","RUN-00000001",REF,"1","SYNTHETIC","test",NOW,NOW+timedelta(hours=1),ApprovalStatus.APPROVED)
    destination=DestinationTransmissionApproval("SYNTH-DEST","SYNTH-HUMAN-2",content.approval_id,content.case_id,content.run_id,REF,"1","SYNTH-ELSTER-ACCEPTANCE-SERVER","SYNTH-ERIC","test",NOW+timedelta(minutes=1),NOW+timedelta(hours=1),True,ApprovalStatus.APPROVED)
    return content,destination
def test_pair_reloads_and_consumes_exactly_once(tmp_path):
    db=tmp_path/"a.sqlite3"; _,_,store=make_store(db); content,destination=pair()
    store.register_submission_approval(content); store.register_submission_approval(destination); store.close()
    with reopen(db) as loaded:
        assert loaded.get_submission_approval(content.approval_id)==content
        assert loaded.consume_submission_pair(content.approval_id,destination.approval_id,"SYNTH-CONSUME-1")==pair()
        assert loaded.consume_submission_pair(content.approval_id,destination.approval_id,"SYNTH-CONSUME-1")==pair()
        with pytest.raises(ApprovalAlreadyConsumedError): loaded.consume_submission_pair(content.approval_id,destination.approval_id,"SYNTH-CONSUME-2")
def test_changed_duplicate_wrong_order_and_corruption_fail_closed(tmp_path):
    db=tmp_path/"a.sqlite3"; _,_,store=make_store(db); content,destination=pair(); store.register_submission_approval(content); store.register_submission_approval(destination)
    with pytest.raises(DurableApprovalError): store.register_submission_approval(replace(content,purpose="changed"))
    with pytest.raises(DurableApprovalError): store.consume_submission_pair(destination.approval_id,content.approval_id,"SYNTH-C")
    store.close(); conn=sqlite3.connect(db); conn.execute("UPDATE durable_submission_approvals SET payload_json='{}' WHERE approval_id=?",(content.approval_id,)); conn.commit(); conn.close()
    with reopen(db) as loaded:
        with pytest.raises(DurableApprovalIntegrityError): loaded.get_submission_approval(content.approval_id)
