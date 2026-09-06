"""Deterministic in-memory Case Registry model.

The registry is the identity and lookup boundary for tax cases. It does not
read Drive or document contents. Storage references are opaque values owned by
a later case-scoped storage layer.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from typing import Iterable


class OwnerType(str, Enum):
    PERSON = "PERSON"
    ENTITY = "ENTITY"


class CaseType(str, Enum):
    INDIVIDUAL = "INDIVIDUAL"
    LEGAL_ENTITY = "LEGAL_ENTITY"


class AssessmentMode(str, Enum):
    JOINT_ASSESSMENT = "JOINT_ASSESSMENT"
    INDIVIDUAL_ASSESSMENT = "INDIVIDUAL_ASSESSMENT"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN_PENDING_VERIFICATION = "UNKNOWN_PENDING_VERIFICATION"


class LifecycleStatus(str, Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    PROCESSING = "PROCESSING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"
    BLOCKED = "BLOCKED"


class LookupStatus(str, Enum):
    NOT_FOUND = "NOT_FOUND"
    RESOLVED = "RESOLVED"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True, slots=True)
class TaxPeriod:
    """Structured tax period; calendar year is the first supported variant."""

    type: str
    year: int

    def __post_init__(self) -> None:
        if self.type != "CALENDAR_YEAR":
            raise ValueError("unsupported tax period type")
        if not isinstance(self.year, int) or isinstance(self.year, bool):
            raise TypeError("tax period year must be an integer")
        if not 1900 <= self.year <= 9999:
            raise ValueError("tax period year must be between 1900 and 9999")


@dataclass(frozen=True, slots=True)
class StorageScopeReference:
    """Opaque exact case-root reference, independent of the storage provider."""

    provider: str
    root_id: str

    def __post_init__(self) -> None:
        if not self.provider.strip() or not self.root_id.strip():
            raise ValueError("storage scope provider and root_id are required")


@dataclass(frozen=True, slots=True)
class CaseRecord:
    case_id: str
    owner_type: OwnerType
    owner_id: str
    tax_period: TaxPeriod
    case_type: CaseType
    assessment_mode: AssessmentMode
    lifecycle_status: LifecycleStatus
    storage_scope_reference: StorageScopeReference
    schema_version: int
    created_at: datetime
    updated_at: datetime
    last_run_id: str | None = None

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id is required")
        if not self.owner_id.strip():
            raise ValueError("owner_id is required")
        if self.schema_version < 1:
            raise ValueError("schema_version must be >= 1")
        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot precede created_at")


@dataclass(frozen=True, slots=True)
class LookupResult:
    status: LookupStatus
    case_ids: tuple[str, ...]

    @property
    def case_id(self) -> str:
        if self.status is not LookupStatus.RESOLVED:
            raise LookupError(f"lookup is {self.status.value.lower()}")
        return self.case_ids[0]


class CaseRegistry:
    """Deterministic registry with explicit ambiguity and no unscoped access."""

    def __init__(self, *, schema_version: int = 1) -> None:
        if schema_version < 1:
            raise ValueError("schema_version must be >= 1")
        self._schema_version = schema_version
        self._records: dict[str, CaseRecord] = {}
        self._request_index: dict[str, str] = {}
        self._lock = RLock()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def register(self, record: CaseRecord, *, request_id: str | None = None) -> CaseRecord:
        """Add a case, enforcing uniqueness and optional idempotency."""
        with self._lock:
            existing = self._records.get(record.case_id)
            if existing is not None:
                if request_id and self._request_index.get(request_id) == record.case_id:
                    return existing
                raise ValueError(f"case_id already exists: {record.case_id}")

            if request_id:
                if not request_id.strip():
                    raise ValueError("request_id cannot be empty")
                existing_case_id = self._request_index.get(request_id)
                if existing_case_id is not None:
                    return self._records[existing_case_id]
                self._request_index[request_id] = record.case_id

            self._records[record.case_id] = record
            return record

    def get(self, case_id: str) -> CaseRecord | None:
        with self._lock:
            return self._records.get(case_id)

    def resolve_by_case_id(self, case_id: str) -> LookupResult:
        with self._lock:
            return LookupResult(
                LookupStatus.RESOLVED if case_id in self._records else LookupStatus.NOT_FOUND,
                (case_id,) if case_id in self._records else (),
            )

    def resolve_by_owner_and_period(
        self, owner_id: str, tax_period: TaxPeriod
    ) -> LookupResult:
        with self._lock:
            matches = tuple(
                sorted(
                    record.case_id
                    for record in self._records.values()
                    if record.owner_id == owner_id and record.tax_period == tax_period
                )
            )
        return self._result_for(matches)

    def resolve_by_owner_type_and_period(
        self, owner_type: OwnerType, owner_id: str, tax_period: TaxPeriod
    ) -> LookupResult:
        with self._lock:
            matches = tuple(
                sorted(
                    record.case_id
                    for record in self._records.values()
                    if record.owner_type == owner_type
                    and record.owner_id == owner_id
                    and record.tax_period == tax_period
                )
            )
        return self._result_for(matches)

    def list_by_owner(self, owner_id: str) -> tuple[CaseRecord, ...]:
        with self._lock:
            return tuple(
                sorted(
                    (record for record in self._records.values() if record.owner_id == owner_id),
                    key=lambda record: (record.tax_period.year, record.case_id),
                )
            )

    def update_lifecycle(self, case_id: str, status: LifecycleStatus) -> CaseRecord:
        with self._lock:
            record = self._require(case_id)
            updated = replace(record, lifecycle_status=status, updated_at=self._now())
            self._records[case_id] = updated
            return updated

    def update_storage_scope(
        self, case_id: str, storage_scope_reference: StorageScopeReference
    ) -> CaseRecord:
        """Move the physical scope without changing case identity."""
        with self._lock:
            record = self._require(case_id)
            updated = replace(
                record,
                storage_scope_reference=storage_scope_reference,
                updated_at=self._now(),
            )
            self._records[case_id] = updated
            return updated

    def update_last_run(self, case_id: str, run_id: str) -> CaseRecord:
        if not run_id.strip():
            raise ValueError("run_id is required")
        with self._lock:
            record = self._require(case_id)
            updated = replace(record, last_run_id=run_id, updated_at=self._now())
            self._records[case_id] = updated
            return updated

    def all_records(self) -> tuple[CaseRecord, ...]:
        with self._lock:
            return tuple(sorted(self._records.values(), key=lambda r: r.case_id))

    def validate(self) -> None:
        """Validate durable registry invariants represented by this model."""
        with self._lock:
            seen_roots: dict[tuple[str, str], str] = {}
            for record in self._records.values():
                if record.schema_version < 1:
                    raise ValueError(f"invalid schema version: {record.case_id}")
                root = (
                    record.storage_scope_reference.provider,
                    record.storage_scope_reference.root_id,
                )
                previous = seen_roots.get(root)
                if previous is not None and previous != record.case_id:
                    raise ValueError(
                        f"storage root mapped to multiple cases: {root[1]}"
                    )
                seen_roots[root] = record.case_id

    @staticmethod
    def _result_for(case_ids: Iterable[str]) -> LookupResult:
        ids = tuple(case_ids)
        if not ids:
            return LookupResult(LookupStatus.NOT_FOUND, ())
        if len(ids) > 1:
            return LookupResult(LookupStatus.AMBIGUOUS, ids)
        return LookupResult(LookupStatus.RESOLVED, ids)

    def _require(self, case_id: str) -> CaseRecord:
        record = self._records.get(case_id)
        if record is None:
            raise KeyError(f"unknown case_id: {case_id}")
        return record
