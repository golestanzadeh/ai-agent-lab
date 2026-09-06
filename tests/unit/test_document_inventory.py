from agent_lab.case_registry import StorageScopeReference
from agent_lab.document_inventory import DocumentInventoryService
from agent_lab.storage import InMemoryCaseScopedStorageAdapter, StorageObjectMetadata


def _storage() -> InMemoryCaseScopedStorageAdapter:
    storage = InMemoryCaseScopedStorageAdapter(
        {"CASE-001": StorageScopeReference("test", "root-1")}
    )
    storage.add_object(
        "CASE-001",
        StorageObjectMetadata(
            object_id="folder-1",
            name="Z folder",
            mime_type="application/vnd.google-apps.folder",
            parent_ids=("root-1",),
            is_folder=True,
        ),
    )
    storage.add_object(
        "CASE-001",
        StorageObjectMetadata(
            object_id="file-2",
            name="b.pdf",
            mime_type="application/pdf",
            parent_ids=("root-1",),
            is_folder=False,
        ),
    )
    storage.add_object(
        "CASE-001",
        StorageObjectMetadata(
            object_id="file-1",
            name="A.pdf",
            mime_type="application/pdf",
            parent_ids=("root-1",),
            is_folder=False,
        ),
    )
    return storage


def test_inventory_is_metadata_only_and_deterministically_sorted() -> None:
    inventory = DocumentInventoryService(_storage()).build("CASE-001")

    assert inventory.case_id == "CASE-001"
    assert inventory.document_count == 2
    assert inventory.folder_count == 1
    assert [item.name for item in inventory.items] == ["A.pdf", "b.pdf", "Z folder"]
    assert all(item.object_id for item in inventory.items)


def test_inventory_rejects_empty_case_id() -> None:
    try:
        DocumentInventoryService(_storage()).build("  ")
    except ValueError as exc:
        assert str(exc) == "case_id is required"
    else:
        raise AssertionError("empty case_id must be rejected")
