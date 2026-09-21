from dataclasses import replace
from pathlib import Path

import pytest

from agent_lab.eric_e10_2024_declaration import DeclarationOutcome, E10DeclarationResult
from agent_lab.eric_e10_2024_plausibility import (
    DENIED_CAPABILITIES,
    REMAINING_BLOCKERS,
    OFFICIAL_RULE_SOURCE_FILENAME,
    OFFICIAL_RULE_SOURCE_SHA256,
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
    assert result.rule_source_filename == OFFICIAL_RULE_SOURCE_FILENAME
    assert result.rule_source_sha256 == OFFICIAL_RULE_SOURCE_SHA256
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


def test_other_expense_negative_item_total_is_rejected():
    source = declaration()
    xml = source.declaration_xml.replace("<E0205406>1234</E0205406>", "<E0205406>-1</E0205406>")
    result = evaluate_local_e10_2024_plausibility(replace(source, declaration_xml=xml))
    assert "100200103" in {item.official_rule_code for item in result.findings}


@pytest.mark.parametrize(
    ("difference", "fails"),
    [(5, False), (-5, False), (6, True), (-6, True)],
)
def test_other_expense_official_tolerance_boundary_is_absolute_and_exclusive(
    difference, fails
):
    source = declaration()
    item_amount = 1_234
    declared_sum = item_amount + difference
    xml = source.declaration_xml.replace(
        f"<E0204803>{item_amount}</E0204803>",
        f"<E0204803>{declared_sum}</E0204803>",
    )
    result = evaluate_local_e10_2024_plausibility(replace(source, declaration_xml=xml))
    codes = {item.official_rule_code for item in result.findings}
    assert ("100200002" in codes) is fails


@pytest.mark.parametrize("removed", ["E0204801", "E0204802"])
def test_ferry_or_flight_description_and_amount_must_be_provided_together(removed):
    source = declaration()
    xml = source.declaration_xml.replace(
        "<Sonst>",
        "<Flug><E0204801>Synthetic ferry ticket</E0204801><E0204802>321</E0204802></Flug><Sonst>",
    )
    changed = replace(source, declaration_xml=without(xml, removed))
    result = evaluate_local_e10_2024_plausibility(changed)
    assert "121361" in {item.official_rule_code for item in result.findings}


@pytest.mark.parametrize(
    ("declared_sum", "fails"),
    [(1560, False), (1561, True)],
)
def test_other_expense_tolerance_uses_combined_sonst_and_ferry_or_flight_total(
    declared_sum, fails
):
    source = declaration()
    xml = source.declaration_xml.replace(
        "<Sonst>",
        "<Flug><E0204801>Synthetic ferry ticket</E0204801><E0204802>321</E0204802></Flug><Sonst>",
    ).replace("<E0204803>1234</E0204803>", f"<E0204803>{declared_sum}</E0204803>")
    result = evaluate_local_e10_2024_plausibility(replace(source, declaration_xml=xml))
    codes = {item.official_rule_code for item in result.findings}
    assert ("100200002" in codes) is fails


def test_reports_tax_class_six_withholding_rule():
    source = declaration()
    xml = source.declaration_xml.replace("LStB_1_5_Sum", "LStB_6_Sum")
    xml = without(xml, "E0200002").replace("E0200201", "E0200203").replace("E0200301", "E0200303")
    changed = replace(source, declaration_xml=without(xml, "E0200303"))
    result = evaluate_local_e10_2024_plausibility(changed)
    assert [item.official_rule_code for item in result.findings] == ["310070"]


@pytest.mark.parametrize(
    ("tax_class", "optional_field", "removed_field", "rule_code"),
    [
        (1, "solidarity_surcharge_eur", "E0200301", "310050"),
        (1, "church_tax_eur", "E0200301", "310060"),
        (6, "solidarity_surcharge_eur", "E0200303", "310110"),
        (6, "church_tax_eur", "E0200303", "310120"),
    ],
)
def test_optional_wage_taxes_require_wage_tax(tax_class, optional_field, removed_field, rule_code):
    source_mapping = mapping()
    # Rebuild from the fixture request through its public input is covered by mapping tests;
    # here inject exact official fields to isolate the reviewed presence rules.
    field_id = {("solidarity_surcharge_eur", 1): "E0200401", ("church_tax_eur", 1): "E0200501", ("solidarity_surcharge_eur", 6): "E0200403", ("church_tax_eur", 6): "E0200503"}[(optional_field, tax_class)]
    xml = source_mapping.fragment_xml
    if tax_class == 6:
        xml = xml.replace("LStB_1_5_Sum", "LStB_6_Sum").replace("E0200201", "E0200203").replace("E0200301", "E0200303")
        xml = without(xml, "E0200002")
    xml = xml.replace(f"</{removed_field}>", f"</{removed_field}><{field_id}>1,00</{field_id}>")
    changed = replace(declaration(), declaration_xml=without(xml, removed_field))
    result = evaluate_local_e10_2024_plausibility(changed)
    assert rule_code in {item.official_rule_code for item in result.findings}


@pytest.mark.parametrize(
    ("tax_class", "gross_field", "rule_code"),
    [(1, "E0200201", "310030"), (6, "E0200203", "310090")],
)
def test_wage_tax_group_requires_gross_wages(tax_class, gross_field, rule_code):
    source = declaration()
    xml = source.declaration_xml
    if tax_class == 6:
        xml = xml.replace("LStB_1_5_Sum", "LStB_6_Sum")
        xml = xml.replace("E0200201", "E0200203").replace("E0200301", "E0200303")
        xml = without(xml, "E0200002")
    changed = replace(source, declaration_xml=without(xml, gross_field))
    result = evaluate_local_e10_2024_plausibility(changed)
    assert rule_code in {item.official_rule_code for item in result.findings}


@pytest.mark.parametrize(
    ("tax_class", "gross_field", "partner_field", "rule_code"),
    [
        (1, "E0200201", "E0200601", "310030"),
        (6, "E0200203", "E0200603", "310090"),
    ],
)
def test_partner_church_tax_requires_gross_wages(
    tax_class, gross_field, partner_field, rule_code
):
    source = declaration()
    xml = source.declaration_xml
    if tax_class == 6:
        xml = xml.replace("LStB_1_5_Sum", "LStB_6_Sum")
        xml = xml.replace("E0200201", "E0200203").replace("E0200301", "E0200303")
        xml = without(xml, "E0200002")
    xml = xml.replace(
        f"</{gross_field}>",
        f"</{gross_field}><{partner_field}>1,00</{partner_field}>",
    )
    changed = replace(source, declaration_xml=without(xml, gross_field))
    result = evaluate_local_e10_2024_plausibility(changed)
    finding = next(item for item in result.findings if item.official_rule_code == rule_code)
    assert partner_field in finding.field_ids


@pytest.mark.parametrize(
    ("tax_class", "wage_tax_field", "partner_field", "required_rule", "excluded_rule"),
    [
        (1, "E0200301", "E0200601", "310010", "310060"),
        (6, "E0200303", "E0200603", "310070", "310120"),
    ],
)
def test_partner_church_tax_does_not_infer_employee_church_tax_dependency(
    tax_class, wage_tax_field, partner_field, required_rule, excluded_rule
):
    source = declaration()
    xml = source.declaration_xml
    if tax_class == 6:
        xml = xml.replace("LStB_1_5_Sum", "LStB_6_Sum")
        xml = xml.replace("E0200201", "E0200203").replace("E0200301", "E0200303")
        xml = without(xml, "E0200002")
    xml = xml.replace(
        f"</{wage_tax_field}>",
        f"</{wage_tax_field}><{partner_field}>1,00</{partner_field}>",
    )
    changed = replace(source, declaration_xml=without(xml, wage_tax_field))
    result = evaluate_local_e10_2024_plausibility(changed)
    codes = {item.official_rule_code for item in result.findings}
    assert required_rule in codes
    assert excluded_rule not in codes


@pytest.mark.parametrize(
    ("xml_changes", "rule_code"),
    [
        (("<E0204002>10</E0204002>",), "100200109"),
        (("<E0204003>10</E0204003>",), "330121"),
        (("<E0204001>Synthetic</E0204001>",), "100200108"),
        (("<E0204003>-1</E0204003>",), "100200099"),
        (("<E0204001>Synthetic</E0204001><E0204003>10</E0204003><E0204002>11</E0204002>",), "201010"),
    ],
)
def test_professional_association_rules(xml_changes, rule_code):
    source = declaration()
    payload = xml_changes[0]
    xml = source.declaration_xml.replace("</Wk>", f"<Berufsverb><Einz>{payload}</Einz></Berufsverb></Wk>")
    result = evaluate_local_e10_2024_plausibility(replace(source, declaration_xml=xml))
    assert rule_code in {item.official_rule_code for item in result.findings}


@pytest.mark.parametrize(
    ("payload", "rule_code"),
    [
        ("<E0204402>10</E0204402>", "330122"),
        ("<E0204402>-1</E0204402><E0204403>0</E0204403>", "100200100"),
        ("<E0204403>10</E0204403>", "100200110"),
        ("<E0204401>Computer</E0204401>", "121410"),
    ],
)
def test_work_equipment_presence_and_nonnegative_rules(payload, rule_code):
    source = declaration()
    xml = source.declaration_xml.replace(
        "</Wk>", f"<Arbeitsmittel><Einz>{payload}</Einz></Arbeitsmittel></Wk>"
    )
    result = evaluate_local_e10_2024_plausibility(replace(source, declaration_xml=xml))
    assert rule_code in {item.official_rule_code for item in result.findings}


@pytest.mark.parametrize(
    ("difference", "fails"),
    [(5, False), (-5, False), (6, True), (-6, True)],
)
def test_work_equipment_official_tolerance_boundary_is_absolute_and_exclusive(
    difference, fails
):
    source = declaration()
    item_amount = 100
    equipment_sum = item_amount + difference
    payload = (
        f"<E0204401>Computer</E0204401><E0204402>{item_amount}</E0204402>"
        f"<E0204403>{equipment_sum}</E0204403>"
    )
    xml = source.declaration_xml.replace(
        "</Wk>", f"<Arbeitsmittel><Einz>{payload}</Einz></Arbeitsmittel></Wk>"
    )
    result = evaluate_local_e10_2024_plausibility(replace(source, declaration_xml=xml))
    codes = {item.official_rule_code for item in result.findings}
    assert ("122050" in codes) is fails


@pytest.mark.parametrize(
    ("payload", "rule_code"),
    [
        ("<E0204505>10</E0204505>", "330123"),
        ("<E0204505>-1</E0204505><E0204504>0</E0204504>", "100200101"),
        ("<E0204504>10</E0204504>", "100200111"),
        ("<E0204503>anteilige Miete</E0204503>", "121432"),
    ],
)
def test_home_office_presence_and_nonnegative_rules(payload, rule_code):
    source = declaration()
    xml = source.declaration_xml.replace(
        "</Wk>", f"<Arb_Zim><Einz>{payload}</Einz></Arb_Zim></Wk>"
    )
    result = evaluate_local_e10_2024_plausibility(replace(source, declaration_xml=xml))
    assert rule_code in {item.official_rule_code for item in result.findings}


@pytest.mark.parametrize(
    ("difference", "fails"),
    [(5, False), (-5, False), (6, True), (-6, True)],
)
def test_home_office_official_tolerance_boundary_is_absolute_and_exclusive(
    difference, fails
):
    source = declaration()
    item_amount = 100
    declared_sum = item_amount + difference
    payload = (
        f"<E0204503>anteilige Miete</E0204503><E0204505>{item_amount}</E0204505>"
        f"<E0204504>{declared_sum}</E0204504>"
    )
    xml = source.declaration_xml.replace(
        "</Wk>", f"<Arb_Zim><Einz>{payload}</Einz></Arb_Zim></Wk>"
    )
    result = evaluate_local_e10_2024_plausibility(replace(source, declaration_xml=xml))
    codes = {item.official_rule_code for item in result.findings}
    assert ("122056" in codes) is fails


@pytest.mark.parametrize(
    ("payload", "rule_code"),
    [
        ("<E0204808>10</E0204808>", "100200003"),
        ("<E0204812>10</E0204812>", "100200009"),
        ("<E0204808>-1</E0204808><E0204812>0</E0204812>", "100200102"),
        ("<E0204804>Kursgebühren</E0204804>", "121352"),
    ],
)
def test_training_presence_and_nonnegative_rules(payload, rule_code):
    source = declaration()
    xml = source.declaration_xml.replace(
        "</Wk>", f"<Fortb><Einz>{payload}</Einz></Fortb></Wk>"
    )
    result = evaluate_local_e10_2024_plausibility(replace(source, declaration_xml=xml))
    assert rule_code in {item.official_rule_code for item in result.findings}


@pytest.mark.parametrize(
    ("difference", "fails"),
    [(5, False), (-5, False), (6, True), (-6, True)],
)
def test_training_official_tolerance_boundary_is_absolute_and_exclusive(
    difference, fails
):
    source = declaration()
    item_amount = 100
    declared_sum = item_amount + difference
    payload = (
        f"<E0204804>Kursgebühren</E0204804><E0204808>{item_amount}</E0204808>"
        f"<E0204812>{declared_sum}</E0204812>"
    )
    xml = source.declaration_xml.replace(
        "</Wk>", f"<Fortb><Einz>{payload}</Einz></Fortb></Wk>"
    )
    result = evaluate_local_e10_2024_plausibility(replace(source, declaration_xml=xml))
    codes = {item.official_rule_code for item in result.findings}
    assert ("100200007" in codes) is fails


@pytest.mark.parametrize(
    ("first_days", "second_days", "fails"),
    [(1, 365, False), (183, 183, False), (1, 366, True), (200, 167, True)],
)
def test_combined_home_office_days_cannot_exceed_leap_year_maximum(
    first_days, second_days, fails
):
    source = declaration()
    payload = f"<Homeoffice><E0204507>{first_days}</E0204507><E0206206>{second_days}</E0206206></Homeoffice>"
    xml = source.declaration_xml.replace("</Wk>", f"{payload}</Wk>")
    result = evaluate_local_e10_2024_plausibility(replace(source, declaration_xml=xml))
    codes = {item.official_rule_code for item in result.findings}
    assert ("100200127" in codes) is fails


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("evaluated_rule_codes", (), "rule set"),
        ("rule_source_filename", "other.ods", "filename"),
        ("rule_source_sha256", "0" * 64, "digest"),
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
