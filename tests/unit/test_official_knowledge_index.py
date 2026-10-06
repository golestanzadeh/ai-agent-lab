import json
from pathlib import Path
import pytest
from agent_lab.official_knowledge_index import DEFAULT_INDEX, OfficialKnowledgeError, OfficialKnowledgeIndex, OfficialKnowledgeMismatch, OfficialKnowledgeMissing, OfficialKnowledgeUnresolved, OfficialKnowledgeReopenCompletion, _hash

SOURCE_HASH = "6379af3c83b8d8ea1f5b8e683d2cfc401cb1506a6018cd44d68452f8b67dacd5"
DR02 = "ELSTER.E10.2024.DR02.VORSORGEAUFWAND_V1"
DR04 = "ELSTER.E10.2024.DR04.SECTION_35A_V1"
DR03 = "ELSTER.E10.2024.DR03.CHILD_AND_SCHOOL_FEES_V1"

def resolve(index, stable_id=DR02, **overrides):
    args = {"tax_year": 2024, "release": "44.3.6.0", "source_sha256": SOURCE_HASH}; args.update(overrides)
    return index.resolve(stable_id, **args)

def custom_index(tmp_path: Path, mutate=lambda data: None):
    data = json.loads(DEFAULT_INDEX.read_text(encoding="utf-8")); mutate(data)
    path = tmp_path / "custom.json"; path.write_text(json.dumps(data), encoding="utf-8")
    return path, _hash(data)

def test_default_requires_and_verifies_trusted_manifest(tmp_path):
    manifest = tmp_path / "manifest.json"; manifest.write_text("{}", encoding="utf-8")
    with pytest.raises(OfficialKnowledgeError, match="manifest metadata mismatch"): OfficialKnowledgeIndex(manifest_path=manifest)
    with pytest.raises(OfficialKnowledgeError, match="default index trust"): OfficialKnowledgeIndex(trusted_canonical_sha256="0" * 64)

def test_custom_path_requires_explicit_trusted_hash(tmp_path):
    path, pin = custom_index(tmp_path)
    with pytest.raises(OfficialKnowledgeError, match="explicit trusted canonical hash"): OfficialKnowledgeIndex(path)
    assert OfficialKnowledgeIndex(path, trusted_canonical_sha256=pin).reference == "sha256:" + pin

def test_resolve_does_not_touch_protected_source(monkeypatch):
    import agent_lab.official_source_resolver as protected
    monkeypatch.setattr(protected.OfficialSourceResolver, "resolve", lambda *_: (_ for _ in ()).throw(AssertionError("protected source touched")))
    monkeypatch.delenv("AI_TAX_PROTECTED_SOURCE_ROOT", raising=False)
    entry = resolve(OfficialKnowledgeIndex())
    assert entry.status == "VERIFIED_ACCEPTED" and entry.authority == "ELSTER"
    assert entry.form == "Anlage Vorsorgeaufwand" and entry.dependencies == ("DR-01", "DEC-006", "DEC-007")

@pytest.mark.parametrize("key,value,fragment", [("tax_year", 2023, "tax year"), ("release", "45", "release"), ("source_sha256", "0"*64, "source hash")])
def test_wrong_provenance_fails_closed_with_versioned_audit(key, value, fragment):
    with pytest.raises(OfficialKnowledgeMismatch, match=fragment) as caught: resolve(OfficialKnowledgeIndex(), **{key: value})
    audit = caught.value.audit_record
    assert audit.schema_version == 1 and audit.state == "REOPEN_REQUIRED" and audit.stable_id == DR02
    assert audit.logical_source_id == "ELSTER_E10_2024_ANNUAL_DOCUMENTATION"
    assert audit.required_review_scope.startswith("only " + DR02)

def test_missing_and_unresolved_entries_are_not_resolvable():
    with pytest.raises(OfficialKnowledgeMissing): resolve(OfficialKnowledgeIndex(), "ELSTER.E10.2024.UNKNOWN_V1")
    with pytest.raises(OfficialKnowledgeUnresolved) as caught: resolve(OfficialKnowledgeIndex(), DR04)
    assert caught.value.audit_record.reason == "ENTRY_UNRESOLVED"
    assert caught.value.audit_record.source_locator == "HA_35a - Felder; HA_35a - Regeln"
    dr03 = resolve(OfficialKnowledgeIndex(), DR03)
    assert dr03.status == "VERIFIED_ACCEPTED" and dr03.independent_acceptance == "PASS"
    assert "E0500706" in dr03.field_ids and "501150" in dr03.rule_ids

def test_reopen_completion_requires_actual_section_change_and_acceptance():
    with pytest.raises(OfficialKnowledgeUnresolved) as caught: resolve(OfficialKnowledgeIndex(), DR04)
    request = caught.value.audit_record
    completed = OfficialKnowledgeReopenCompletion(1, request, "HA_35a - Regeln rows 2-11", "UNCHANGED", "FAIL")
    assert completed.section_inspected and completed.acceptance_result == "FAIL"
    with pytest.raises(ValueError, match="section"):
        OfficialKnowledgeReopenCompletion(1, request, "", "UNCHANGED", "PASS")
    with pytest.raises(ValueError, match="change"):
        OfficialKnowledgeReopenCompletion(1, request, "rows", "UNKNOWN", "PASS")
    with pytest.raises(ValueError, match="schema"):
        OfficialKnowledgeReopenCompletion(999, request, "rows", "UNCHANGED", "PASS")
    with pytest.raises(ValueError, match="audit record"):
        OfficialKnowledgeReopenCompletion(1, object(), "rows", "UNCHANGED", "PASS")

def test_pin_detects_canonical_drift(tmp_path):
    path, pin = custom_index(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8")); data["entries"][0]["topic"] += " drift"; path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(OfficialKnowledgeError, match="canonical hash"): OfficialKnowledgeIndex(path, trusted_canonical_sha256=pin)

def test_invalid_lifecycle_and_entry_provenance_fail_closed(tmp_path):
    path, pin = custom_index(tmp_path, lambda d: d["entries"][0].update(status="DRAFT"))
    with pytest.raises(OfficialKnowledgeError, match="lifecycle"): OfficialKnowledgeIndex(path, trusted_canonical_sha256=pin)
    path, pin = custom_index(tmp_path, lambda d: d["entries"][0].update(tax_year=2023))
    with pytest.raises(OfficialKnowledgeError, match="entry provenance"): OfficialKnowledgeIndex(path, trusted_canonical_sha256=pin)

def test_compare_reports_all_four_dispositions(tmp_path):
    def mutate(data):
        data["entries"][0]["topic"] += " changed"; data["entries"].pop(1)
        new = dict(data["entries"][2]); new["stable_id"] = "ELSTER.E10.2024.DR05.INTEGRATION_V1"; data["entries"].append(new)
    path, pin = custom_index(tmp_path, mutate)
    dispositions = {c.stable_id: c.disposition for c in OfficialKnowledgeIndex().compare(OfficialKnowledgeIndex(path, trusted_canonical_sha256=pin))}
    assert dispositions["ELSTER.E10.2024.DR01.FILING_AND_WAGE_V1"] == "CHANGED"
    assert dispositions[DR02] == "REMOVED"
    assert dispositions["ELSTER.E10.2024.DR03.CHILD_AND_SCHOOL_FEES_V1"] == "UNCHANGED"
    assert dispositions["ELSTER.E10.2024.DR05.INTEGRATION_V1"] == "NEW"
