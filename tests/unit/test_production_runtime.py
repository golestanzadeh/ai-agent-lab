from datetime import datetime, timezone
import sqlite3

import pytest
from fastapi.testclient import TestClient

from agent_lab.case_creation_workflow import CaseCreationWorkflow, InMemoryAuditSink
from agent_lab.case_identity_association import CaseIdentityAssociationService
from agent_lab.case_persistence import SQLiteCasePersistence,CasePersistenceError,StorageProvisioningUnavailable
from agent_lab.case_registry import AssessmentMode,CaseRecord,CaseType,LifecycleStatus,OwnerType,StorageScopeReference,TaxPeriod
from agent_lab.case_state import CaseState,RunStatus
from agent_lab.identity_persistence import IdentityPersistence
from agent_lab.orchestrator_kernel import OrchestratorKernel
from agent_lab.person_entity_registry import PersonEntityRegistry
from agent_lab.production_runtime import ProductionRuntime,ProtectedOperationDisabled
from agent_lab.storage_provisioning import DurableStorageProvisioningAdapter
from agent_lab.ui_product_app import create_runtime_product_dashboard_app
from test_orchestrator_kernel import CONTRACT_ROOT

KEY=b"production-runtime-synthetic-test-key-32-minimum"
OWNER="OWNER-A"
CASES=frozenset({"CASE-2023-A","CASE-2023-B","CASE-2028-A"})


class Creator:
    def create_case_scope(self,period,case_id):
        return StorageScopeReference("controlled-test",f"ROOT-{case_id}")


def seed(store):
    now=datetime.now(timezone.utc)
    provision=DurableStorageProvisioningAdapter(store,Creator())
    for case_id,owner,year in (("CASE-2023-A",OWNER,2023),("CASE-2023-B",OWNER,2023),("CASE-2028-A",OWNER,2028),("CASE-OTHER","OWNER-B",2026)):
        scope=provision.provision_case_scope(owner_id=owner,tax_period=TaxPeriod("CALENDAR_YEAR",year),case_id=case_id,request_id=f"CREATE-{case_id}")
        record=CaseRecord(case_id,OwnerType.PERSON,owner,TaxPeriod("CALENDAR_YEAR",year),CaseType.INDIVIDUAL,AssessmentMode.UNKNOWN_PENDING_VERIFICATION,LifecycleStatus.CREATED,scope,1,now,now)
        store.register_case(record,CaseState(case_id,1,"READY",now,now),ui_owner_id=owner)
    store.create_run(owner_id=OWNER,case_id="CASE-2023-A",tax_year=2023,run_id="RUN-REAL-PERSISTED",request_id="RUN-REQUEST",expected_state_revision=1)
    store.transition_run(owner_id=OWNER,case_id="CASE-2023-A",tax_year=2023,run_id="RUN-REAL-PERSISTED",request_id="RUN-START",expected_revision=1,status=RunStatus.RUNNING)


def compose(tmp_path,store,*,authorize=lambda *args:False):
    registry=store.load_runtime(owner_id=OWNER,allowed_case_ids=CASES).registry
    identities=PersonEntityRegistry()
    identity=IdentityPersistence(tmp_path/"identity.sqlite",cases=registry,authorize=authorize,evidence_resolver=lambda *args:None,integrity_key=KEY)
    workflow=CaseCreationWorkflow(identities,registry,CaseIdentityAssociationService(identities,registry),Creator(),InMemoryAuditSink(),durable_registrar=store)
    kernel=OrchestratorKernel(tmp_path/"kernel.sqlite",CONTRACT_ROOT)
    runtime=ProductionRuntime(persistence=store,identity=identity,creation_workflow=workflow,kernel=kernel,owner_id=OWNER,allowed_case_ids=CASES)
    return runtime,identity,kernel


def test_production_runtime_restart_multi_case_year_state_run_and_storage(tmp_path):
    path=tmp_path/"cases.sqlite"; store=SQLiteCasePersistence(path,integrity_key=KEY); seed(store)
    for attempt in range(2):
        runtime,identity,kernel=compose(tmp_path,store)
        client=TestClient(create_runtime_product_dashboard_app(runtime=runtime))
        for lang,direction in (("fa-IR","rtl"),("de-DE","ltr")):
            response=client.get(f"/?case_id=CASE-2023-A&lang={lang}")
            assert response.status_code==200 and f'dir="{direction}"' in response.text
            assert 'data-durable-run-status="RUNNING"' in response.text
            assert 'data-storage-state="COMPLETE"' in response.text
            assert 'data-persisted-state="READY"' in response.text
            assert "CASE-OTHER" not in response.text and "ROOT-" not in response.text
            assert client.get(f"/?case_id=CASE-OTHER&lang={lang}").status_code==404
        assert {case.tax_year for case in runtime.read_cases()}=={2023,2028}
        assert client.post("/test/cases").status_code==404
        assert client.post("/submit").status_code==404
        identity.close(); kernel.close(); store.close()
        if attempt==0: store=SQLiteCasePersistence(path,integrity_key=KEY)


def test_disabled_providers_are_audited_without_invocation_or_environment_activation(tmp_path,monkeypatch):
    store=SQLiteCasePersistence(tmp_path/"cases.sqlite",integrity_key=KEY); seed(store)
    runtime,identity,kernel=compose(tmp_path,store)
    monkeypatch.setenv("GEMINI_API_KEY","synthetic-ignored")
    for operation in runtime.OPERATIONS:
        with pytest.raises(ProtectedOperationDisabled,match="OPERATIONAL_ACCEPTANCE_REQUIRED"):
            runtime.request_operation(operation,case_id="CASE-2023-A",tax_year=2023)
    assert store._db.execute("SELECT count(*) FROM case_audit WHERE action='RUNTIME_OPERATION_DENIED'").fetchone()[0]==len(runtime.OPERATIONS)
    with pytest.raises(PermissionError): runtime.request_operation("gemini_extraction",case_id="CASE-OTHER",tax_year=2026)
    with pytest.raises(PermissionError): runtime.read_case("CASE-2023-A",2028)
    identity.close();kernel.close();store.close()


def test_missing_security_configuration_fails_startup(tmp_path):
    store=SQLiteCasePersistence(tmp_path/"cases.sqlite",integrity_key=KEY); seed(store)
    with pytest.raises(PermissionError,match="authorization configuration"):
        compose(tmp_path,store,authorize=None)
    store.close()


def test_identity_tamper_after_startup_fails_ui_closed(tmp_path):
    store=SQLiteCasePersistence(tmp_path/"cases.sqlite",integrity_key=KEY); seed(store)
    runtime,identity,kernel=compose(tmp_path,store)
    client=TestClient(create_runtime_product_dashboard_app(runtime=runtime))
    assert client.get("/?case_id=CASE-2023-A").status_code==200
    anchor=tmp_path/"identity.sqlite.audit-anchor"
    anchor.write_text('{}',encoding='utf-8')
    assert client.get("/?case_id=CASE-2023-A").status_code==503
    assert "CASE-2023-A" not in client.get("/").text
    identity._db.close();kernel.close();store.close()


def test_incomplete_storage_is_explicitly_unavailable_and_root_never_exposed(tmp_path):
    store=SQLiteCasePersistence(tmp_path/"cases.sqlite",integrity_key=KEY); seed(store)
    runtime,identity,kernel=compose(tmp_path,store)
    original=store.load_completed_storage_references
    def unavailable(**kwargs):
        raise StorageProvisioningUnavailable("controlled absent provisioning reference")
    store.load_completed_storage_references=unavailable
    projection=runtime.read_case("CASE-2023-A",2023)
    assert projection.storage_state=="UNAVAILABLE"
    store.load_completed_storage_references=original
    identity.close();kernel.close();store.close()


@pytest.mark.parametrize("failure",[
    CasePersistenceError("case audit anchor integrity failure"),
    PermissionError("storage scope is not authorized"),
    OSError("storage authority read failed"),
])
def test_storage_integrity_authorization_and_io_failures_propagate(tmp_path,failure):
    store=SQLiteCasePersistence(tmp_path/"cases.sqlite",integrity_key=KEY); seed(store)
    runtime,identity,kernel=compose(tmp_path,store)
    def corrupted(**kwargs): raise failure
    store.load_completed_storage_references=corrupted
    with pytest.raises(type(failure)):
        runtime.read_case("CASE-2023-A",2023)
    client=TestClient(create_runtime_product_dashboard_app(runtime=runtime))
    response=client.get("/?case_id=CASE-2023-A")
    assert 'data-persisted-state=' not in response.text
    assert 'data-storage-state="COMPLETE"' not in response.text
    identity.close();kernel.close();store.close()
