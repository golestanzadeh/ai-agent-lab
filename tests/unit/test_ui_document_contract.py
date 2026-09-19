from dataclasses import replace

import pytest

from agent_lab.ui_app import _populate_synthetic_state, build_synthetic_registry
from agent_lab.ui_document_contract import UIDocumentError, build_synthetic_document_inventory
from agent_lab.ui_state_contract import select_synthetic_workspace


def _inventory():
    registry = build_synthetic_registry()
    workspace = _populate_synthetic_state(select_synthetic_workspace(registry, case_id="SYNTH-CASE-001", tax_year=2024))
    return build_synthetic_document_inventory(workspace)


def test_inventory_is_metadata_only_and_case_run_bound() -> None:
    inventory = _inventory()
    assert inventory.case_id == "SYNTH-CASE-001"
    assert inventory.run_id == "SYNTH-RUN-001"
    assert [item.display_label for item in inventory.documents] == ["مدرک مصنوعی 1", "مدرک مصنوعی 2"]
    assert all(not item.contains_content and not item.external_source_access for item in inventory.documents)


def test_private_or_cross_case_metadata_fails_closed() -> None:
    inventory = _inventory()
    with pytest.raises(UIDocumentError, match="generic synthetic"):
        replace(inventory.documents[0], display_label="Gehaltsabrechnung Reza.pdf")
    with pytest.raises(UIDocumentError, match="match inventory"):
        replace(inventory, documents=(replace(inventory.documents[0], case_id="SYNTH-CASE-002"), inventory.documents[1]))


def test_upload_persistence_and_network_cannot_be_forged() -> None:
    inventory = _inventory()
    for change in ({"upload_enabled": True}, {"persistence_enabled": True}, {"network_calls": ("https://example.invalid",)}, {"data_classification": "REAL"}):
        with pytest.raises(UIDocumentError):
            replace(inventory, **change)


def test_provenance_is_distinct_and_canonical() -> None:
    inventory = _inventory()
    item = inventory.documents[0]
    assert item.provenance_reference != item.document_reference
    with pytest.raises(UIDocumentError, match="canonical"):
        replace(item, provenance_reference="source-object-id")
