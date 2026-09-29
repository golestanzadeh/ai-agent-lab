from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import pytest
from agent_lab.case_registry import AssessmentMode, CaseRecord, CaseRegistry, CaseType, LifecycleStatus, OwnerType, StorageScopeReference, TaxPeriod
from agent_lab.synthetic_product_service import SyntheticProductService
from agent_lab.synthetic_workflow_store import SyntheticWorkflowStore, WorkflowIntegrityError, WorkflowScopeError, WorkflowStage, WorkflowTransitionError

CASE="SYNTHETIC-CASE-001"; RUN="RUN-SYNTHETIC-001"; A="sha256:"+"a"*64; B="sha256:"+"b"*64
def registry():
    r=CaseRegistry(); now=datetime.now(timezone.utc)
    r.register(CaseRecord(CASE,OwnerType.PERSON,"SYNTHETIC-PERSON",TaxPeriod("CALENDAR_YEAR",2024),CaseType.INDIVIDUAL,AssessmentMode.NOT_APPLICABLE,LifecycleStatus.CREATED,StorageScopeReference("synthetic_local","scope-1"),1,now,now)); return r

def test_atomic_ordered_idempotent_restart(tmp_path: Path):
    db=tmp_path/"workflow.sqlite3"
    with SyntheticWorkflowStore(db) as store:
        service=SyntheticProductService(registry(),store); first=service.start(CASE,2024,RUN,A,"T-1")
        assert first.stage is WorkflowStage.CREATE_CASE
        second=service.advance(CASE,2024,RUN,WorkflowStage.CREATE_CASE,WorkflowStage.INTAKE,B,"T-2")
        assert second.sequence==2
        assert service.advance(CASE,2024,RUN,WorkflowStage.CREATE_CASE,WorkflowStage.INTAKE,B,"T-2")==second
    with SyntheticWorkflowStore(db) as reopened: assert reopened.get(CASE,2024,RUN)==second

def test_cross_case_and_stale_transition_fail_closed(tmp_path: Path):
    with SyntheticWorkflowStore(tmp_path/"w.sqlite3") as store:
        service=SyntheticProductService(registry(),store); service.start(CASE,2024,RUN,A,"T-1")
        with pytest.raises(WorkflowScopeError): store.get("SYNTHETIC-OTHER",2024,RUN)
        with pytest.raises(WorkflowTransitionError): service.advance(CASE,2024,RUN,WorkflowStage.INTAKE,WorkflowStage.PROCESS,B,"T-2")
        with pytest.raises(WorkflowScopeError): service.start("CASE-001",2024,"RUN-SYNTHETIC-X",A,"T-X")

def test_transition_identity_cannot_be_rebound(tmp_path: Path):
    with SyntheticWorkflowStore(tmp_path/"w.sqlite3") as store:
        s=SyntheticProductService(registry(),store); s.start(CASE,2024,RUN,A,"T-1")
        s.advance(CASE,2024,RUN,WorkflowStage.CREATE_CASE,WorkflowStage.INTAKE,B,"T-2")
        with pytest.raises(WorkflowTransitionError): s.advance(CASE,2024,RUN,WorkflowStage.INTAKE,WorkflowStage.PROCESS,A,"T-2")
        with pytest.raises(WorkflowTransitionError): s.start(CASE,2024,RUN,A,"DIFFERENT-CREATE-ID")

def test_idempotent_replay_returns_original_transition_after_later_progress(tmp_path: Path):
    with SyntheticWorkflowStore(tmp_path/"w.sqlite3") as store:
        s=SyntheticProductService(registry(),store); s.start(CASE,2024,RUN,A,"T-1")
        intake=s.advance(CASE,2024,RUN,WorkflowStage.CREATE_CASE,WorkflowStage.INTAKE,B,"T-2")
        s.advance(CASE,2024,RUN,WorkflowStage.INTAKE,WorkflowStage.PROCESS,A,"T-3")
        assert s.advance(CASE,2024,RUN,WorkflowStage.CREATE_CASE,WorkflowStage.INTAKE,B,"T-2")==intake

def test_corrupt_journal_is_rejected_on_reopen(tmp_path: Path):
    db=tmp_path/"w.sqlite3"
    with SyntheticWorkflowStore(db) as store: SyntheticProductService(registry(),store).start(CASE,2024,RUN,A,"T-1")
    con=sqlite3.connect(db); con.execute("UPDATE transitions SET payload_json='{}'"); con.commit(); con.close()
    with pytest.raises(WorkflowIntegrityError): SyntheticWorkflowStore(db)

def test_unknown_schema_is_rejected(tmp_path: Path):
    db=tmp_path/"w.sqlite3"; con=sqlite3.connect(db); con.execute("CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL)"); con.execute("INSERT INTO metadata VALUES('schema_version','99')"); con.commit(); con.close()
    with pytest.raises(WorkflowIntegrityError): SyntheticWorkflowStore(db)

def test_failed_journal_insert_rolls_back_head_and_reopens_cleanly(tmp_path: Path):
    db=tmp_path/"w.sqlite3"
    with SyntheticWorkflowStore(db) as store:
        s=SyntheticProductService(registry(),store); original=s.start(CASE,2024,RUN,A,"T-1")
        store._db.execute("CREATE TRIGGER fail_transition BEFORE INSERT ON transitions BEGIN SELECT RAISE(ABORT,'simulated crash'); END")
        with pytest.raises(sqlite3.IntegrityError): s.advance(CASE,2024,RUN,WorkflowStage.CREATE_CASE,WorkflowStage.INTAKE,B,"T-2")
        store._db.execute("DROP TRIGGER fail_transition")
        assert store.get(CASE,2024,RUN)==original
    with SyntheticWorkflowStore(db) as reopened: assert reopened.get(CASE,2024,RUN)==original
