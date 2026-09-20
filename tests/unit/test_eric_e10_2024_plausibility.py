from dataclasses import replace
from pathlib import Path

import pytest

from agent_lab.eric_e10_2024_declaration import DeclarationOutcome, E10DeclarationResult
from agent_lab.eric_e10_2024_plausibility import (
    DENIED_CAPABILITIES,
    REMAINING_BLOCKERS,
    SUPPORTED_OFFICIAL_RULES,
    E10PlausibilityError,
    PlausibilityOutcome,
    evaluate_local_e10_2024_plausibility,
)
from tests.unit.test_eric_e10_2024_declaration import mapping


def declaration() -> E10DeclarationResult:
    source = mapping()
    return E10DeclarationResult(
        outcome=DeclarationOutcome.OFFICIAL_XSD_VALIDATED_EXTERNAL_EXECUTION_BLOCKED,
        mapping_reference=source.artifact_identity.reference,
        profile_version="1",
        namespace="http://finkonsens.de/elster/elstererklaerung/est/e10/v2024",
        schema_version="2024",
        declaration_xml=source.fragment_xml,
        schema_filename="E10-2024.xsd",
        schema_sha256="86c735c6a3070aad1ccd90e5bdc8a0999099f44ed76b5752e74d8dfa5cd7d272",
        blockers=("OFFICIAL_ERIC_PLAUSIBILITY_ENGINE_NOT_EXECUTED",),
        denied_capabilities=(
            "ERIC_FFI",
            "OFFICIAL_ERIC_PLAUSIBILITY_ENGINE",
            "SIGNING",
            "MANUFACTURER_ID_ACCESS",
            "CREDENTIAL_OR_CERTIFICATE_ACCESS",
            "NETWORK",
            "TRANSMISSION",
        ),
    )


def without(xml: str, field_id: str) -> str:
    import re

    return re.sub(rf"<[^>]*{field_id}>.*?</[^>]*{field_id}>", "", xml)


def test_mapped_declaration_passes_reviewed_local_rule_subset():
    result = evaluate_local_e10_2024_plausibility(declaration())
    assert result.outcome is PlausibilityOutcome.LOCAL_SUBSET_PASS_OFFICIAL_ENGINE_BLOCKED
    assert result.evaluated_rule_codes == SUPPORTED_OFFICIAL_RULES
    assert result.findings == ()
    assert result.blockers == REMAINING_BLOCKERS
    assert result.denied_capabilities == DENIED_CAPABILITIES
    assert result.official_eric_plausibility_executed is False


def test_result_is_deterministic_and_hash_bound():
    first = evaluate_local_e10_2024_plausibility(declaration())
    second = evaluate_local_e10_2024_plausibility(declaration())
    assert first == second
    assert first.artifact_identity == second.artifact_identity


@pytest.mark.parametrize(
    ("removed", "rule_code"),
    [
        ("E0200002", "241"),
        ("E0200301", "310010"),
        ("E0204803", "100200001"),
        ("E0205406", "100200112"),
        ("E0205405", "121355"),
    ],
)
def test_reports_reviewed_official_presence_rules(removed, rule_code):
    source = declaration()
    changed = replace(source, declaration_xml=without(source.declaration_xml, removed))
    result = evaluate_local_e10_2024_plausibility(changed)
    assert result.outcome is PlausibilityOutcome.LOCAL_SUBSET_FAIL_OFFICIAL_ENGINE_BLOCKED
    assert rule_code in {finding.official_rule_code for finding in result.findings}


def test_reports_tax_class_six_withholding_rule():
    source = declaration()
    xml = source.declaration_xml.replace("LStB_1_5_Sum", "LStB_6_Sum")
    xml = without(xml, "E0200002").replace("E0200201", "E0200203").replace("E0200301", "E0200303")
    changed = replace(source, declaration_xml=without(xml, "E0200303"))
    result = evaluate_local_e10_2024_plausibility(changed)
    assert [item.official_rule_code for item in result.findings] == ["310070"]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("evaluated_rule_codes", (), "rule set"),
        ("blockers", (), "blockers"),
        ("denied_capabilities", (), "capability"),
        ("synthetic_only", False, "non-synthetic"),
        ("official_eric_plausibility_executed", True, "official execution"),
        ("network_calls", ("https://example.invalid",), "external"),
        ("transmission_permitted", True, "external"),
    ],
)
def test_result_tampering_fails_closed(field, value, message):
    result = evaluate_local_e10_2024_plausibility(declaration())
    with pytest.raises(E10PlausibilityError, match=message):
        replace(result, **{field: value})


def test_rejects_non_declaration_input():
    with pytest.raises(E10PlausibilityError, match="E10DeclarationResult"):
        evaluate_local_e10_2024_plausibility(Path("synthetic.xml"))
