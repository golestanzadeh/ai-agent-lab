from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pytest

from agent_lab.case_creation_workflow import (
    CaseCreationRequest, CaseCreationWorkflow, InMemoryAuditSink,
)
from agent_lab.case_identity_association import CaseIdentityAssociationService
from agent_lab.case_persistence import CasePersistenceError, SQLiteCasePersistence
from agent_lab.case_registry import (
    AssessmentMode, CaseRecord, CaseRegistry, CaseType, LifecycleStatus,
    OwnerType, StorageScopeReference, TaxPeriod,
)
from agent_lab.case_state import CaseState
from agent_lab.person_entity_registry import PersonEntityRegistry, PersonRecord, RegistryStatus
from agent_lab.storage_provisioning import DurableStorageProvisioningAdapter


KEY = b"storage-provisioning-test-key-32-bytes-minimum"


class ControlledCreator:
    def __init__(self):
        self.scopes = {}
        self.calls = []
        self.fail_cases = set()

    def create_case_scope(self, tax_period, case_id):
        key = (tax_period.year, case_id); self.calls.append(key)
        if case_id in self.fail_cases:
            raise RuntimeError("controlled provider failure")
        return self.scopes.setdefault(
            key, StorageScopeReference("synthetic_controlled", f"ROOT-{tax_period.year}-{case_id}"),
        )


def test_success_duplicate_restart_and_multi_year_isolation(tmp_path):
    path = tmp_path / "cases.sqlite3"; creator = ControlledCreator()
    store = SQLiteCasePersistence(path, integrity_key=KEY)
    adapter = DurableStorageProvisioningAdapter(store, creator)
    first = adapter.provision_case_scope(owner_id="OWNER-A", tax_period=TaxPeriod("CALENDAR_YEAR", 2024),
                                         case_id="CASE-2024-A", request_id="REQ-A")
    assert adapter.provision_case_scope(owner_id="OWNER-A", tax_period=TaxPeriod("CALENDAR_YEAR", 2024),
                                        case_id="CASE-2024-A", request_id="REQ-A") == first
    second = adapter.provision_case_scope(owner_id="OWNER-A", tax_period=TaxPeriod("CALENDAR_YEAR", 2025),
                                          case_id="CASE-2025-A", request_id="REQ-B")
    assert first != second and creator.calls.count((2024, "CASE-2024-A")) == 1
    store.close()
    reopened = SQLiteCasePersistence(path, integrity_key=KEY)
    replay = DurableStorageProvisioningAdapter(reopened, creator).provision_case_scope(
        owner_id="OWNER-A", tax_period=TaxPeriod("CALENDAR_YEAR", 2024),
        case_id="CASE-2024-A", request_id="REQ-A",
    )
    assert replay == first and creator.calls.count((2024, "CASE-2024-A")) == 1
    reopened.close()


def test_interruption_after_provider_recovers_without_duplicate(tmp_path):
    store = SQLiteCasePersistence(tmp_path / "cases.sqlite3", integrity_key=KEY)
    creator = ControlledCreator(); interrupted = True
    def crash(_scope):
        nonlocal interrupted
        if interrupted:
            interrupted = False
            raise SystemExit("simulated process loss")
    adapter = DurableStorageProvisioningAdapter(store, creator, after_provider=crash)
    with pytest.raises(SystemExit):
        adapter.provision_case_scope(owner_id="OWNER-A", tax_period=TaxPeriod("CALENDAR_YEAR", 2026),
                                     case_id="CASE-2026-A", request_id="REQ-A")
    operation = adapter.operation_id(request_id="REQ-A", owner_id="OWNER-A", case_id="CASE-2026-A", tax_year=2026)
    assert store.get_storage_provisioning(operation_id=operation).status == "IN_PROGRESS"
    result = adapter.provision_case_scope(owner_id="OWNER-A", tax_period=TaxPeriod("CALENDAR_YEAR", 2026),
                                          case_id="CASE-2026-A", request_id="REQ-A")
    assert result.root_id == "ROOT-2026-CASE-2026-A"
    assert len(creator.scopes) == 1
    store.close()


def test_failure_retry_and_other_case_are_isolated(tmp_path):
    store = SQLiteCasePersistence(tmp_path / "cases.sqlite3", integrity_key=KEY)
    creator = ControlledCreator(); creator.fail_cases.add("CASE-2025-FAIL")
    adapter = DurableStorageProvisioningAdapter(store, creator)
    with pytest.raises(RuntimeError, match="controlled"):
        adapter.provision_case_scope(owner_id="OWNER-A", tax_period=TaxPeriod("CALENDAR_YEAR", 2025),
                                     case_id="CASE-2025-FAIL", request_id="REQ-FAIL")
    good = adapter.provision_case_scope(owner_id="OWNER-A", tax_period=TaxPeriod("CALENDAR_YEAR", 2025),
                                        case_id="CASE-2025-GOOD", request_id="REQ-GOOD")
    creator.fail_cases.clear()
    recovered = adapter.provision_case_scope(owner_id="OWNER-A", tax_period=TaxPeriod("CALENDAR_YEAR", 2025),
                                             case_id="CASE-2025-FAIL", request_id="REQ-FAIL")
    assert good != recovered
    store.close()


def test_scope_substitution_and_incorrect_case_registration_are_rejected(tmp_path):
    store = SQLiteCasePersistence(tmp_path / "cases.sqlite3", integrity_key=KEY)
    creator = ControlledCreator(); adapter = DurableStorageProvisioningAdapter(store, creator)
    scope = adapter.provision_case_scope(owner_id="OWNER-A", tax_period=TaxPeriod("CALENDAR_YEAR", 2025),
                                         case_id="CASE-2025-A", request_id="REQ-A")
    with pytest.raises(CasePersistenceError, match="different scope"):
        adapter.provision_case_scope(owner_id="OWNER-B", tax_period=TaxPeriod("CALENDAR_YEAR", 2025),
                                     case_id="CASE-2025-A", request_id="REQ-A")
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    record = CaseRecord(
        "CASE-2025-A", OwnerType.PERSON, "OWNER-A", TaxPeriod("CALENDAR_YEAR", 2025),
        CaseType.INDIVIDUAL, AssessmentMode.UNKNOWN_PENDING_VERIFICATION,
        LifecycleStatus.CREATED, StorageScopeReference(scope.provider, "WRONG"), 1, now, now,
    )
    with pytest.raises(CasePersistenceError, match="does not match"):
        store.register_case(record, CaseState("CASE-2025-A", 1, "READY", now, now), ui_owner_id="OWNER-A")
    store.close()


def test_concurrent_independent_cases_and_audit_consistency(tmp_path):
    store = SQLiteCasePersistence(tmp_path / "cases.sqlite3", integrity_key=KEY)
    creator = ControlledCreator(); adapter = DurableStorageProvisioningAdapter(store, creator)
    def provision(number):
        return adapter.provision_case_scope(
            owner_id="OWNER-A", tax_period=TaxPeriod("CALENDAR_YEAR", 2027),
            case_id=f"CASE-2027-{number}", request_id=f"REQ-{number}",
        )
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = tuple(pool.map(provision, range(1, 5)))
    assert len({scope.root_id for scope in results}) == 4
    actions = [row[0] for row in store._db.execute(
        "SELECT action FROM case_audit WHERE action LIKE 'STORAGE_PROVISIONING_%'"
    )]
    assert actions.count("STORAGE_PROVISIONING_INTENT") == 4
    assert actions.count("STORAGE_PROVISIONING_COMPLETE") == 4
    store.close()


def test_case_creation_workflow_commits_completed_scope_and_recovers(tmp_path):
    identities = PersonEntityRegistry(); now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    identities.register_person(PersonRecord("PERSON-A", RegistryStatus.ACTIVE, "Synthetic", now, now, 1))
    cases = CaseRegistry(); store = SQLiteCasePersistence(tmp_path / "cases.sqlite3", integrity_key=KEY)
    creator = ControlledCreator(); adapter = DurableStorageProvisioningAdapter(store, creator)
    workflow = CaseCreationWorkflow(
        identities, cases, CaseIdentityAssociationService(identities, cases), adapter,
        InMemoryAuditSink(), durable_registrar=store, allow_multiple_cases_per_period=True,
    )
    def request(request_id, year):
        return CaseCreationRequest(
            request_id, OwnerType.PERSON, "PERSON-A", TaxPeriod("CALENDAR_YEAR", year),
            CaseType.INDIVIDUAL, AssessmentMode.UNKNOWN_PENDING_VERIFICATION,
            "synthetic-owner", now,
        )
    first = workflow.create(request("REQ-A", 2025)); second = workflow.create(request("REQ-B", 2025))
    third = workflow.create(request("REQ-C", 2026))
    store.close()
    reopened = SQLiteCasePersistence(tmp_path / "cases.sqlite3", integrity_key=KEY)
    runtime = reopened.load_runtime(
        owner_id="PERSON-A", allowed_case_ids=frozenset({first.case_id, second.case_id, third.case_id}),
    )
    assert len(runtime.registry.all_records()) == 3
    assert len({record.storage_scope_reference.root_id for record in runtime.registry.all_records()}) == 3
    reopened.close()
