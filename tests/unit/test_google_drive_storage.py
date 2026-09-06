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
from agent_lab.case_scoped_drive import CaseScopedDriveResolver, OutOfScopeError
from agent_lab.google_drive_storage import GoogleDriveMetadataAdapter


class FakeRequest:
    def __init__(self, response):
        self._response = response

    def execute(self):
        return self._response


class FakeFiles:
    def __init__(self, objects):
        self.objects = objects
        self.calls = []

    def list(self, **kwargs):
        self.calls.append(("list", kwargs))
        parent = kwargs["q"].split("'")[1]
        children = [
            obj for obj in self.objects.values()
            if parent in obj.get("parents", ()) and not obj.get("trashed", False)
        ]
        return FakeRequest({"files": children})

    def get(self, **kwargs):
        self.calls.append(("get", kwargs))
        object_id = kwargs["fileId"]
        obj = self.objects.get(object_id)
        if obj is None:
            raise KeyError(object_id)
        fields = kwargs["fields"]
        result = {key: obj[key] for key in ("id", "name", "mimeType", "parents", "trashed") if key in obj}
        if fields == "id,parents,trashed":
            result = {key: result[key] for key in ("id", "parents", "trashed") if key in result}
        return FakeRequest(result)


class FakeDrive:
    def __init__(self, objects):
        self._files = FakeFiles(objects)

    def files(self):
        return self._files


def _adapter(objects):
    registry = CaseRegistry()
    now = datetime.now(timezone.utc)
    registry.register(
        CaseRecord(
            case_id="CASE-A-2024",
            owner_type=OwnerType.PERSON,
            owner_id="PERSON-1",
            tax_period=TaxPeriod("CALENDAR_YEAR", 2024),
            case_type=CaseType.INDIVIDUAL,
            assessment_mode=AssessmentMode.INDIVIDUAL_ASSESSMENT,
            lifecycle_status=LifecycleStatus.CREATED,
            storage_scope_reference=StorageScopeReference("google_drive", "ROOT-A"),
            schema_version=1,
            created_at=now,
            updated_at=now,
        )
    )
    return GoogleDriveMetadataAdapter(
        drive_service=FakeDrive(objects),
        resolver=CaseScopedDriveResolver(registry),
    )


def test_direct_child_is_accepted() -> None:
    adapter = _adapter({
        "DOC-A": {
            "id": "DOC-A", "name": "a.pdf", "mimeType": "application/pdf",
            "parents": ["ROOT-A"], "trashed": False,
        },
    })
    assert adapter.get_metadata("CASE-A-2024", "DOC-A").name == "a.pdf"


def test_nested_descendant_is_accepted() -> None:
    adapter = _adapter({
        "FOLDER-A": {
            "id": "FOLDER-A", "name": "nested", "mimeType": adapter_mime_folder(),
            "parents": ["ROOT-A"], "trashed": False,
        },
        "DOC-A": {
            "id": "DOC-A", "name": "a.pdf", "mimeType": "application/pdf",
            "parents": ["FOLDER-A"], "trashed": False,
        },
    })
    assert adapter.get_metadata("CASE-A-2024", "DOC-A").object_id == "DOC-A"


def test_sibling_or_unrelated_object_is_rejected() -> None:
    adapter = _adapter({
        "DOC-B": {
            "id": "DOC-B", "name": "b.pdf", "mimeType": "application/pdf",
            "parents": ["ROOT-B"], "trashed": False,
        },
        "ROOT-B": {
            "id": "ROOT-B", "name": "other", "mimeType": adapter_mime_folder(),
            "parents": ["OTHER-ROOT"], "trashed": False,
        },
    })
    with pytest.raises(OutOfScopeError):
        adapter.get_metadata("CASE-A-2024", "DOC-B")


def test_trashed_object_is_rejected() -> None:
    adapter = _adapter({
        "DOC-A": {
            "id": "DOC-A", "name": "a.pdf", "mimeType": "application/pdf",
            "parents": ["ROOT-A"], "trashed": True,
        },
    })
    with pytest.raises(Exception):
        adapter.get_metadata("CASE-A-2024", "DOC-A")


def adapter_mime_folder():
    return "application/vnd.google-apps.folder"
