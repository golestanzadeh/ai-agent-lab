"""Deterministic runtime for creating isolated tax cases."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Protocol

from agent_lab.case_identity_association import CaseIdentityAssociationService
from agent_lab.case_registry import (
    AssessmentMode,
    CaseRecord,
    CaseRegistry,
    CaseType,
    LifecycleStatus,
    OwnerType,
    StorageScopeReference,
    TaxPeriod,
)
from agent_lab.person_entity_registry import PersonEntityRegistry


class CreationStatus(str, Enum):
    CREATED = "CREATED"
    IDEMPOTENT = "IDEMPOTENT"


@dataclass(frozen=True, slots=True)
class CaseCreationRequest:
    request_id: str
    owner_type: OwnerType
    owner_reference: str
    tax_period: TaxPeriod
    case_type: CaseType
    assessment_mode: AssessmentMode
    requested_by: str
    requested_at: datetime
    schema_version: int = 1

    def __post_init__(self) -> None:
        for name, value in (("request_id", self.request_id), ("owner_reference", self.owner_reference), ("requested_by", self.requested_by)):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if self.schema_version < 1:
            raise ValueError("schema_version must be >= 1")
        if self.requested_at.tzinfo is None:
            raise ValueError("requested_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class IdentityResolution:
    owner_id: str
    owner_type: OwnerType
    created: bool = False


@dataclass(frozen=True, slots=True)
class CreationResult:
    status: CreationStatus
    case_id: str
    creation_run_id: str
    storage_scope_reference: StorageScopeReference


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_type: str
    creation_run_id: str
    request_id: str
    case_id: str
    owner_type: OwnerType
    owner_id: str
    tax_period: TaxPeriod
    case_type: CaseType
    outcome: str
    created_at: datetime
    schema_version: int


class StorageScopeCreator(Protocol):
    def create_case_scope(self, tax_period: TaxPeriod, case_id: str) -> StorageScopeReference:
        ...


class AuditSink(Protocol):
    def record(self, event: AuditEvent) -> None:
        ...


class InMemoryStorageScopeCreator:
    REQUIRED_SUBFOLDERS = ("Documents", "Evidence", "Tax_Categories", "Calculations", "Reports", "Audit")

    def __init__(self, provider: str = "memory") -> None:
        self.provider = provider
        self.scopes: dict[str, tuple[str, ...]] = {}

    def create_case_scope(self, tax_period: TaxPeriod, case_id: str) -> StorageScopeReference:
        if case_id in self.scopes:
            raise ValueError(f"storage scope already exists: {case_id}")
        self.scopes[case_id] = self.REQUIRED_SUBFOLDERS
        return StorageScopeReference(self.provider, f"{tax_period.year}/Cases/{case_id}")


class InMemoryAuditSink:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def record(self, event: AuditEvent) -> None:
        self.events.append(event)


class CaseCreationWorkflow:
    """Create a case only after deterministic identity and parameter checks."""

    def __init__(
        self,
        identity_registry: PersonEntityRegistry,
        case_registry: CaseRegistry,
        association_service: CaseIdentityAssociationService,
        storage: StorageScopeCreator,
        audit: AuditSink,
        *,
        identity_resolver: Callable[[CaseCreationRequest], IdentityResolution] | None = None,
    ) -> None:
        self._identity_registry = identity_registry
        self._case_registry = case_registry
        self._association_service = association_service
        self._storage = storage
        self._audit = audit
        self._identity_resolver = identity_resolver or self._resolve_existing_identity

    def create(self, request: CaseCreationRequest) -> CreationResult:
        existing = self._find_idempotent_result(request.request_id)
        if existing is not None:
            return existing

        resolution = self._identity_resolver(request)
        if resolution.owner_type is not request.owner_type:
            raise ValueError("resolved identity type does not match request owner_type")
        self._validate_case_parameters(request)

        existing_case = self._find_existing_case(request, resolution.owner_id)
        if existing_case is not None:
            raise ValueError(f"case already exists for owner and tax period: {existing_case.case_id}")

        case_id = self._generate_case_id(request.tax_period.year)
        run_id = f"CREATE-RUN-{request.request_id}"
        storage_scope = self._storage.create_case_scope(request.tax_period, case_id)
        record = CaseRecord(
            case_id=case_id,
            owner_type=resolution.owner_type,
            owner_id=resolution.owner_id,
            tax_period=request.tax_period,
            case_type=request.case_type,
            assessment_mode=request.assessment_mode,
            lifecycle_status=LifecycleStatus.CREATED,
            storage_scope_reference=storage_scope,
            schema_version=request.schema_version,
            created_at=request.requested_at,
            updated_at=request.requested_at,
            last_run_id=run_id,
        )

        self._case_registry.register(record, request_id=request.request_id)
        try:
            self._association_service.associate(resolution.owner_id, case_id)
            self._audit.record(AuditEvent(
                event_type="CASE_CREATED",
                creation_run_id=run_id,
                request_id=request.request_id,
                case_id=case_id,
                owner_type=resolution.owner_type,
                owner_id=resolution.owner_id,
                tax_period=request.tax_period,
                case_type=request.case_type,
                outcome="SUCCESS",
                created_at=request.requested_at,
                schema_version=request.schema_version,
            ))
        except Exception:
            raise

        return CreationResult(CreationStatus.CREATED, case_id, run_id, storage_scope)

    def _resolve_existing_identity(self, request: CaseCreationRequest) -> IdentityResolution:
        if request.owner_type is OwnerType.PERSON:
            if self._identity_registry.get_person(request.owner_reference) is None:
                raise KeyError(f"unknown person_id: {request.owner_reference}")
        else:
            if self._identity_registry.get_entity(request.owner_reference) is None:
                raise KeyError(f"unknown entity_id: {request.owner_reference}")
        return IdentityResolution(request.owner_reference, request.owner_type)

    def _validate_case_parameters(self, request: CaseCreationRequest) -> None:
        if request.case_type is CaseType.INDIVIDUAL and request.owner_type is not OwnerType.PERSON:
            raise ValueError("INDIVIDUAL case_type requires PERSON owner")
        if request.case_type is CaseType.LEGAL_ENTITY and request.owner_type is not OwnerType.ENTITY:
            raise ValueError("LEGAL_ENTITY case_type requires ENTITY owner")
        if request.owner_type is OwnerType.ENTITY and request.assessment_mode is not AssessmentMode.NOT_APPLICABLE:
            raise ValueError("ENTITY cases require NOT_APPLICABLE assessment_mode")

    def _find_existing_case(self, request: CaseCreationRequest, owner_id: str) -> CaseRecord | None:
        result = self._case_registry.resolve_by_owner_type_and_period(request.owner_type, owner_id, request.tax_period)
        if len(result.case_ids) > 1:
            raise ValueError("multiple cases already exist for owner and tax period")
        return self._case_registry.get(result.case_id) if result.case_ids else None

    def _find_idempotent_result(self, request_id: str) -> CreationResult | None:
        run_id = f"CREATE-RUN-{request_id}"
        for record in self._case_registry.all_records():
            if record.last_run_id == run_id:
                return CreationResult(CreationStatus.IDEMPOTENT, record.case_id, run_id, record.storage_scope_reference)
        return None

    def _generate_case_id(self, year: int) -> str:
        prefix = f"CASE-{year}-"
        numbers = [
            int(record.case_id.rsplit("-", 1)[1])
            for record in self._case_registry.all_records()
            if record.case_id.startswith(prefix) and record.case_id.rsplit("-", 1)[1].isdigit()
        ]
        return f"{prefix}{max(numbers) + 1 if numbers else 1:04d}"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
