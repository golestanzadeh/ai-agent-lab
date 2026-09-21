from dataclasses import replace
from xml.etree import ElementTree as ET

import pytest

from agent_lab.elster_dry_run import SyntheticSubmissionEnvelope, SyntheticTaxSummary
from agent_lab.eric_e10_2024_mapping import (
    DENIED_CAPABILITIES,
    E10_NAMESPACE,
    REMAINING_BLOCKERS,
    DeductibleExpenseSemantics,
    E10MappingError,
    E10MappingRequest,
    E10Person,
    MappingOutcome,
    OtherExpenseCategory,
    map_synthetic_summary_to_e10_2024,
)


def envelope(**payload_overrides: int) -> SyntheticSubmissionEnvelope:
    payload = {
        "gross_wages_eur": 67_554,
        "withheld_wage_tax_eur": 17_653,
        "deductible_expenses_eur": 1_234,
    }
    payload.update(payload_overrides)
    return SyntheticSubmissionEnvelope(
        case_id="SYNTH-CASE-E10-2024",
        run_id="SYNTH-RUN-E10-2024",
        tax_year=2024,
        procedure_code="UFA10",
        eric_version="44.3.6.0",
        purpose="synthetic E10/2024 mapping validation",
        data_classification="SYNTHETIC",
        payload=SyntheticTaxSummary(**payload),
    )


def request(*, tax_class: int = 1, **payload_overrides: int) -> E10MappingRequest:
    return E10MappingRequest(
        envelope=envelope(**payload_overrides),
        person=E10Person.PERSON_A,
        tax_class=tax_class,
        deductible_expense_semantics=(
            DeductibleExpenseSemantics.OTHER_EMPLOYMENT_EXPENSES
        ),
        other_expense_category=OtherExpenseCategory.WRITING_MATERIALS,
    )


def request_with_wage_taxes(*, tax_class: int = 1) -> E10MappingRequest:
    return replace(
        request(tax_class=tax_class),
        solidarity_surcharge_eur=3543,
        church_tax_eur=775,
    )


def local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def test_maps_tax_classes_one_to_five_to_official_sum_fields():
    result = map_synthetic_summary_to_e10_2024(request(tax_class=3))
    assert result.outcome is MappingOutcome.LOCAL_PROFILE_VALIDATED_EXTERNAL_EXECUTION_BLOCKED
    assert [(item.field_id, item.lexical_value) for item in result.field_bindings] == [
        ("E0200002", "3"),
        ("E0200201", "67554"),
        ("E0200301", "17653,00"),
        ("E0205405", "Schreibmaterial"),
        ("E0205406", "1234"),
        ("E0204803", "1234"),
    ]
    root = ET.fromstring(result.fragment_xml)
    assert root.tag == f"{{{E10_NAMESPACE}}}E10"
    assert root.attrib == {"version": "2024"}
    assert [
        local_name(item)
        for item in root.iter()
        if len(local_name(item)) == 8 and local_name(item).startswith("E")
    ] == [
        "E0200002",
        "E0200201",
        "E0200301",
        "E0205405",
        "E0205406",
        "E0204803",
    ]


def test_maps_tax_class_six_to_separate_official_sum_fields():
    result = map_synthetic_summary_to_e10_2024(request(tax_class=6))
    assert [(item.field_id, item.lexical_value) for item in result.field_bindings] == [
        ("E0200203", "67554"),
        ("E0200303", "17653,00"),
        ("E0205405", "Schreibmaterial"),
        ("E0205406", "1234"),
        ("E0204803", "1234"),
    ]
    assert "LStB_6_Sum" in result.fragment_xml
    assert "E0200002" not in result.fragment_xml


@pytest.mark.parametrize(
    ("tax_class", "expected"),
    [
        (1, [("E0200401", "3543,00"), ("E0200501", "775,00")]),
        (6, [("E0200403", "3543,00"), ("E0200503", "775,00")]),
    ],
)
def test_maps_explicit_solidarity_and_church_tax_to_official_sum_fields(tax_class, expected):
    result = map_synthetic_summary_to_e10_2024(request_with_wage_taxes(tax_class=tax_class))
    observed = [(item.field_id, item.lexical_value) for item in result.field_bindings]
    for binding in expected:
        assert binding in observed


@pytest.mark.parametrize("field", ["solidarity_surcharge_eur", "church_tax_eur"])
@pytest.mark.parametrize("value", [-1, True, 1_000_000_000_000])
def test_rejects_invalid_optional_wage_tax_amounts(field, value):
    with pytest.raises(E10MappingError, match=field):
        replace(request(), **{field: value})


def test_zero_values_preserve_official_lexical_shapes():
    result = map_synthetic_summary_to_e10_2024(
        request(gross_wages_eur=0, withheld_wage_tax_eur=0, deductible_expenses_eur=0)
    )
    values = {item.field_id: item.lexical_value for item in result.field_bindings}
    assert values == {
        "E0200002": "1",
        "E0200201": "0",
        "E0200301": "0,00",
        "E0205405": "Schreibmaterial",
        "E0205406": "0",
        "E0204803": "0",
    }


@pytest.mark.parametrize("tax_class", [0, 7, True, "1"])
def test_rejects_invalid_tax_class(tax_class):
    with pytest.raises(E10MappingError, match="tax_class"):
        request(tax_class=tax_class)


def test_rejects_ambiguous_deductible_expense_semantics():
    with pytest.raises(E10MappingError, match="semantic classification"):
        E10MappingRequest(
            envelope=envelope(),
            person=E10Person.PERSON_A,
            tax_class=1,
            deductible_expense_semantics="OTHER",
            other_expense_category=OtherExpenseCategory.WRITING_MATERIALS,
        )


def test_rejects_ambiguous_other_expense_category():
    with pytest.raises(E10MappingError, match="official category"):
        E10MappingRequest(
            envelope=envelope(),
            person=E10Person.PERSON_A,
            tax_class=1,
            deductible_expense_semantics=(
                DeductibleExpenseSemantics.OTHER_EMPLOYMENT_EXPENSES
            ),
            other_expense_category="miscellaneous",
        )


@pytest.mark.parametrize(
    "field_name",
    ["gross_wages_eur", "withheld_wage_tax_eur", "deductible_expenses_eur"],
)
def test_rejects_amount_above_official_twelve_digit_boundary(field_name):
    with pytest.raises(E10MappingError, match="amount boundary"):
        map_synthetic_summary_to_e10_2024(request(**{field_name: 1_000_000_000_000}))


def test_request_identity_changes_with_person_tax_class_or_payload():
    baseline = request()
    assert replace(baseline, person=E10Person.PERSON_B).artifact_identity != baseline.artifact_identity
    assert replace(baseline, tax_class=2).artifact_identity != baseline.artifact_identity
    assert request(gross_wages_eur=67_555).artifact_identity != baseline.artifact_identity
    assert replace(baseline, solidarity_surcharge_eur=1).artifact_identity != baseline.artifact_identity
    assert replace(baseline, church_tax_eur=1).artifact_identity != baseline.artifact_identity


def test_profile_v1_request_is_rejected_after_v2_expansion():
    with pytest.raises(E10MappingError, match="profile version"):
        replace(request(), profile_version="1")


def test_result_is_deterministic_and_hash_bound():
    first = map_synthetic_summary_to_e10_2024(request())
    second = map_synthetic_summary_to_e10_2024(request())
    assert first == second
    assert first.artifact_identity == second.artifact_identity
    changed = map_synthetic_summary_to_e10_2024(request(deductible_expenses_eur=1_235))
    assert changed.artifact_identity != first.artifact_identity


def test_result_preserves_all_external_capability_blocks():
    result = map_synthetic_summary_to_e10_2024(request())
    assert result.blockers == REMAINING_BLOCKERS
    assert result.denied_capabilities == DENIED_CAPABILITIES
    assert result.synthetic_only is True
    assert result.official_eric_plausibility_executed is False
    assert result.credential_access is False
    assert result.manufacturer_id_access is False
    assert result.network_calls == ()
    assert result.transmission_permitted is False


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("fragment_xml", "<E10/>", "root"),
        ("blockers", (), "blockers"),
        ("denied_capabilities", (), "capability"),
        ("synthetic_only", False, "synthetic-only"),
        ("official_eric_plausibility_executed", True, "capability"),
        ("credential_access", True, "capability"),
        ("manufacturer_id_access", True, "capability"),
        ("network_calls", ("https://example.invalid",), "network"),
        ("transmission_permitted", True, "capability"),
    ],
)
def test_result_tampering_fails_closed(field, value, message):
    result = map_synthetic_summary_to_e10_2024(request())
    with pytest.raises(E10MappingError, match=message):
        replace(result, **{field: value})


def test_fragment_binding_mutation_fails_closed():
    result = map_synthetic_summary_to_e10_2024(request())
    mutated = result.fragment_xml.replace("67554", "67555")
    with pytest.raises(E10MappingError, match="differ"):
        replace(result, fragment_xml=mutated)


def test_rejects_non_request_input():
    with pytest.raises(E10MappingError, match="E10MappingRequest"):
        map_synthetic_summary_to_e10_2024(envelope())
