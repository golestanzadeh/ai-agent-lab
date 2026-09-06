from datetime import datetime, timezone

import pytest

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
from agent_lab.case_scoped_drive import CaseScopedDriveResolver
from agent_lab.storage import (
    CaseScopedStorage,
    InMemoryCaseScopedStorageAdapter,
    StorageObjectMetadata,
)


def _case(case_id: str, owner_id: str, root_id: str) -> CaseRecord:
    now = datetime.now(timezone.utc)
    return CaseRecord(
        case_id=case_id,
        owner_type=OwnerType.PERSON,
        owner_id=owner_id,
        tax_period=TaxPeriod("CALENDAR_YEAR", int(case_id[-4:])),
        case_type=CaseType.INDIVIDUAL,
        assessment_mode=AssessmentMode.INDIVIDUAL_ASSESSMENT,
        lifecycle_status=LifecycleStatus.CREATED,
        storage_scope_reference=StorageScopeReference("google_drive", root_id),
        schema_version=1,
        created_at=now,
        updated_at=now,
    )


def _service() -> tuple[CaseRegistry, CaseScopedStorage]:
    registry = CaseRegistry()
    registry.register(_case("CASE-A-2024", "PERSON-1", "ROOT-A"))
    registry.register(_case("CASE-B-2025", "PERSON-1", "ROOT-B"))
    resolver = CaseScopedDriveResolver(registry)
    provider = InMemoryCaseScopedStorageAdapter(
        {
            "CASE-A-2024": StorageScopeReference("google_drive", "ROOT-A"),
            "CASE-B-2025": StorageScopeReference("google_drive", "ROOT-B"),
        }
    )
    provider.add_object(
        "CASE-A-2024",
        StorageObjectMetadata("DOC-A", "a.pdf", "application/pdf", ("ROOT-A",), False),
    )
    provider.add_object(
        "CASE-B-2025",
        StorageObjectMetadata("DOC-B", "b.pdf", "application/pdf", ("ROOT-B",), False),
    )
    return registry, CaseScopedStorage(resolver, provider)


def test_list_is_case_scoped() -> None:
    _, storage = _service()
    assert [item.object_id for item in storage.list_children("CASE-A-2024")] == ["DOC-A"]
    assert [item.object_id for item in storage.list_children("CASE-B-2025")] == ["DOC-B"]


def test_unknown_case_fails_closed() -> None:
    _, storage = _service()
    with pytest.raises(Exception):
        storage.list_children("CASE-UNKNOWN")


def test_object_lookup_is_bound_to_requested_case() -> None:
    _, storage = _service()
    assert storage.get_metadata("CASE-A-2024", "DOC-A").name == "a.pdf"
    with pytest.raises(Exception):
        storage.get_metadata("CASE-A-2024", "DOC-B")


def test_empty_object_id_fails_closed() -> None:
    _, storage = _service()
    with pytest.raises(Exception):
        storage.get_metadata("CASE-A-2024", "")
