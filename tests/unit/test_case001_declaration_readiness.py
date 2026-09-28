import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs" / "case001-declaration-readiness-2024.json"


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_frozen_result_and_primary_state_are_exact() -> None:
    data = _manifest()
    assert data["state"] == "CASE_CLOSED_REMEDIATION_REQUIRED"
    assert data["frozen_case"]["refund_eur"] == "133.83"
    assert data["frozen_case"]["source_pdf_count"] == 16
    assert data["frozen_case"]["ledger_row_count"] == 946


def test_every_item_has_one_closed_classification_and_counts_match() -> None:
    data = _manifest()
    allowed = set(data["coverage_counts"]) - {"total"}
    observed = {name: 0 for name in allowed}
    assert len(data["items"]) == data["coverage_counts"]["total"] == 18
    for item in data["items"]:
        assert item["classification"] in allowed
        observed[item["classification"]] += 1
    assert observed == {key: data["coverage_counts"][key] for key in allowed}


def test_all_affirmative_calculation_items_are_visible() -> None:
    data = _manifest()
    affirmative = [item for item in data["items"] if item["classification"] not in {"IRRELEVANT_FOR_CASE", "EXCLUDED_BY_ACCEPTED_CASE_DECISION"}]
    assert len(affirmative) == data["coverage"]["affirmative_declaration_requirements"] == 9
    assert {item["id"] for item in affirmative} == {f"DEC-{number:03d}" for number in (1, 2, 3, 6, 7, 8, 9, 10, 18)}


def test_owner_closures_and_donation_exclusion_are_explicit() -> None:
    items = {item["id"]: item for item in _manifest()["items"]}
    assert items["DEC-011"]["tax_treatment"] == "DONATION_EVIDENCE_INCOMPLETE / EXCLUDED"
    assert items["DEC-012"]["tax_treatment"] == "OWNER_DECLINED / EXCLUDED"
    assert items["DEC-013"]["tax_treatment"] == "OWNER_DECLINED / EXCLUDED"


def test_preview_cannot_claim_complete_or_external_execution() -> None:
    data = _manifest()
    assert data["preview"]["type"] == "NON_TRANSMITTING_PREVIEW"
    assert data["preview"]["status"] == "DECLARATION_CONTENT_INCOMPLETE"
    assert data["coverage"]["complete_non_transmitting_declaration_possible"] is False
    assert not any(data["external_actions"].values())
    assert all(field["field_id"] != "E0200201" for field in data["preview"]["supported_portion"])


def test_vorsorge_components_and_tenant_lineage_are_exact() -> None:
    items = {item["id"]: item for item in _manifest()["items"]}
    assert items["DEC-006"]["accepted_tax_fact"]["spouse_employee_rv_eur"] == "120.15"
    assert items["DEC-007"]["accepted_tax_fact"]["health_after_4_percent_krankengeld_reduction_eur"] == "2835.93"
    assert len([ref for ref in items["DEC-010"]["source_evidence"] if ref.startswith("TX-")]) == 12
    assert items["DEC-010"]["relationship_artifact_sha256"] == _manifest()["frozen_case"]["evidence_reconciliation_sha256"]


def test_queue_is_dependency_ordered_and_uses_existing_scheduler() -> None:
    queue = {item["package_id"]: item for item in _manifest()["remediation_queue"]}
    assert list(queue) == ["DR-01", "DR-02", "DR-03", "DR-04", "DR-05"]
    assert queue["DR-01"]["dependencies"] == []
    assert queue["DR-05"]["dependencies"] == ["DR-02", "DR-03", "DR-04"]
    assert "all nine affirmative requirements" in queue["DR-05"]["definition_of_done"]
    assert _manifest()["coverage"]["affirmative_declaration_requirements"] == 9
    assert all(item["scheduler_disposition"] == "EXISTING_SCHEDULER_ONLY_AFTER_RECOVERY_GATE" for item in queue.values())
    assert "DEC-018" in queue["DR-03"]["definition_of_done"]
    assert "section 31 Günstigerprüfung input preservation" in queue["DR-03"]["required_tests"]
