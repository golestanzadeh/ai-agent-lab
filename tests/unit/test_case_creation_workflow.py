from datetime import datetime, timezone

import pytest

from agent_lab.case_creation_workflow import (
    AuditEvent,
    CaseCreationRequest,
    CaseCreationWorkflow,
    CreationStatus,
    InMemoryAuditSink,
    InMemoryStorageScopeCreator,
)
from agent_lab.case_identity_association import CaseIdentityAssociationService
from agent_lab.case_registry import (
    AssessmentMode,
    CaseRegistry,
    CaseType,
    OwnerType,
    TaxPeriod,
)
from agent_lab.person_entity_registry import PersonEntityRegistry, PersonRecord, RegistryStatus


def ts() -> datetime:
    return datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_person(registry: PersonEntityRegistry, person_id: str = "PERSON-0001") -> None:
    registry.register_person(PersonRecord(person_id, RegistryStatus.ACTIVE, "Test Person", ts(), ts(), 1))


def make_workflow() -> tuple[CaseCreationWorkflow, CaseRegistry, InMemoryStorageScopeCreator, InMemoryAuditSink]:
    identities = PersonEntityRegistry()
    make_person(identities)
    cases = CaseRegistry()
    associations = CaseIdentityAssociationService(identities, cases)
    storage = InMemoryStorageScopeCreator()
    audit = InMemoryAuditSink()
    workflow = CaseCreationWorkflow(identities, cases, associations, storage, audit)
    return workflow, cases, storage, audit


def request(request_id: str = "REQ-001", year: int = 2025) -> CaseCreationRequest:
    return CaseCreationRequest(
        request_id=request_id,
        owner_type=OwnerType.PERSON,
        owner_reference="PERSON-0001",
        tax_period=TaxPeriod("CALENDAR_YEAR", year),
        case_type=CaseType.INDIVIDUAL,
        assessment_mode=AssessmentMode.UNKNOWN_PENDING_VERIFICATION,
        requested_by="test-user",
        requested_at=ts(),
    )


def test_valid_request_creates_case_and_initializes_registry() -> None:
    workflow, cases, storage, audit = make_workflow()

    result = workflow.create(request())

    assert result.status is CreationStatus.CREATED
    assert result.case_id == "CASE-2025-0001"
    record = cases.get(result.case_id)
    assert record is not None
    assert record.owner_id == "PERSON-0001"
    assert record.lifecycle_status.value == "CREATED"
    assert record.last_run_id == "CREATE-RUN-REQ-001"
    assert storage.scopes[result.case_id] == InMemoryStorageScopeCreator.REQUIRED_SUBFOLDERS
    assert len(audit.events) == 1
    assert isinstance(audit.events[0], AuditEvent)


def test_repeated_request_is_idempotent() -> None:
    workflow, cases, storage, audit = make_workflow()

    first = workflow.create(request())
    second = workflow.create(request())

    assert first.case_id == second.case_id
    assert second.status is CreationStatus.IDEMPOTENT
    assert len(cases.all_records()) == 1
    assert len(storage.scopes) == 1
    assert len(audit.events) == 1


def test_existing_case_for_owner_and_period_is_rejected() -> None:
    workflow, _, _, _ = make_workflow()
    workflow.create(request("REQ-001"))

    with pytest.raises(ValueError, match="case already exists"):
        workflow.create(request("REQ-002"))


def test_unknown_identity_is_rejected_before_storage_creation() -> None:
    workflow, cases, storage, audit = make_workflow()
    bad = CaseCreationRequest(
        request_id="REQ-002",
        owner_type=OwnerType.PERSON,
        owner_reference="PERSON-404",
        tax_period=TaxPeriod("CALENDAR_YEAR", 2025),
        case_type=CaseType.INDIVIDUAL,
        assessment_mode=AssessmentMode.UNKNOWN_PENDING_VERIFICATION,
        requested_by="test-user",
        requested_at=ts(),
    )

    with pytest.raises(KeyError, match="unknown person_id"):
        workflow.create(bad)

    assert cases.all_records() == ()
    assert storage.scopes == {}
    assert audit.events == []


def test_case_type_must_match_owner_type() -> None:
    workflow, _, _, _ = make_workflow()
    bad = request()
    bad = CaseCreationRequest(
        bad.request_id, OwnerType.PERSON, bad.owner_reference, bad.tax_period,
        CaseType.LEGAL_ENTITY, bad.assessment_mode, bad.requested_by, bad.requested_at
    )

    with pytest.raises(ValueError, match="LEGAL_ENTITY case_type requires ENTITY"):
        workflow.create(bad)


def test_entity_case_requires_not_applicable_assessment_mode() -> None:
    identities = PersonEntityRegistry()
    from agent_lab.person_entity_registry import EntityRecord
    identities.register_entity(EntityRecord("ENTITY-0001", RegistryStatus.ACTIVE, "Example GmbH", ts(), ts(), 1))
    cases = CaseRegistry()
    associations = CaseIdentityAssociationService(identities, cases)
    workflow = CaseCreationWorkflow(identities, cases, associations, InMemoryStorageScopeCreator(), InMemoryAuditSink())
    bad = CaseCreationRequest(
        "REQ-ENTITY", OwnerType.ENTITY, "ENTITY-0001", TaxPeriod("CALENDAR_YEAR", 2025),
        CaseType.LEGAL_ENTITY, AssessmentMode.JOINT_ASSESSMENT, "test-user", ts()
    )

    with pytest.raises(ValueError, match="NOT_APPLICABLE"):
        workflow.create(bad)


def test_case_ids_increment_per_year() -> None:
    workflow, _, _, _ = make_workflow()

    first = workflow.create(request("REQ-001", 2025))
    second = workflow.create(request("REQ-002", 2026))

    assert first.case_id == "CASE-2025-0001"
    assert second.case_id == "CASE-2026-0001"


def test_association_is_created() -> None:
    workflow, _, _, _ = make_workflow()

    result = workflow.create(request())

    assert result.case_id in workflow._association_service.list_cases("PERSON-0001")


def test_storage_failure_prevents_registry_success() -> None:
    class FailingStorage:
        def create_case_scope(self, tax_period, case_id):
            raise RuntimeError("storage unavailable")

    identities = PersonEntityRegistry()
    make_person(identities)
    cases = CaseRegistry()
    associations = CaseIdentityAssociationService(identities, cases)
    audit = InMemoryAuditSink()
    workflow = CaseCreationWorkflow(identities, cases, associations, FailingStorage(), audit)

    with pytest.raises(RuntimeError, match="storage unavailable"):
        workflow.create(request())

    assert cases.all_records() == ()
    assert audit.events == []
