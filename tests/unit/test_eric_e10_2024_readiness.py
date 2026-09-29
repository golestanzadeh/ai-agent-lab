from dataclasses import replace

import pytest

from agent_lab.eric_e10_2024_plausibility import evaluate_local_e10_2024_plausibility
from agent_lab.eric_e10_2024_readiness import (
    DENIED_CAPABILITIES,
    RESIDUAL_BLOCKERS,
    E10ReadinessError,
    E10ReadinessOutcome,
    assess_local_e10_2024_readiness,
)
from tests.unit.test_eric_e10_2024_declaration import mapping
from tests.unit.test_eric_e10_2024_mapping import request_with_wage_taxes
from tests.unit.test_eric_e10_2024_plausibility import declaration, without
from agent_lab.eric_e10_2024_mapping import map_synthetic_summary_to_e10_2024


def pipeline():
    mapped = mapping()
    declared = declaration()
    assert declared.mapping_reference == mapped.artifact_identity.reference
    plausible = evaluate_local_e10_2024_plausibility(declared)
    return mapped, declared, plausible


def test_assessment_binds_current_local_pipeline_and_stays_blocked():
    mapped, declared, plausible = pipeline()
    result = assess_local_e10_2024_readiness(mapped, declared, plausible)
    assert result.outcome is E10ReadinessOutcome.LOCAL_PIPELINE_READY_EXTERNAL_EXECUTION_BLOCKED
    assert result.mapping_reference == mapped.artifact_identity.reference
    assert result.declaration_reference == declared.artifact_identity.reference
    assert result.plausibility_reference == plausible.artifact_identity.reference
    assert result.blockers == RESIDUAL_BLOCKERS
    assert result.denied_capabilities == DENIED_CAPABILITIES
    assert result.external_readiness is False
    assert result.transmission_permitted is False


def test_assessment_is_deterministic_and_hash_bound():
    first = assess_local_e10_2024_readiness(*pipeline())
    second = assess_local_e10_2024_readiness(*pipeline())
    assert first == second
    assert first.artifact_identity == second.artifact_identity


@pytest.mark.parametrize("tax_class", [1, 6])
def test_optional_wage_tax_mapping_preserves_complete_local_lineage(tax_class):
    mapped = map_synthetic_summary_to_e10_2024(
        request_with_wage_taxes(tax_class=tax_class)
    )
    declared = replace(
        declaration(),
        mapping_reference=mapped.artifact_identity.reference,
        declaration_xml=mapped.fragment_xml,
    )
    plausible = evaluate_local_e10_2024_plausibility(declared)
    result = assess_local_e10_2024_readiness(mapped, declared, plausible)
    assert plausible.findings == ()
    assert result.mapping_reference == mapped.artifact_identity.reference
    assert result.external_readiness is False


def test_rejects_cross_lineage_mapping_or_declaration():
    mapped, declared, plausible = pipeline()
    other_mapping = replace(mapped, request_reference="sha256:" + "0" * 64)
    with pytest.raises(E10ReadinessError, match="exact mapping"):
        assess_local_e10_2024_readiness(other_mapping, declared, plausible)
    other_declaration = replace(declared, mapping_reference="sha256:" + "0" * 64)
    with pytest.raises(E10ReadinessError, match="exact mapping"):
        assess_local_e10_2024_readiness(mapped, other_declaration, plausible)


def test_rejects_failed_local_plausibility():
    mapped, declared, _ = pipeline()
    invalid = replace(declared, declaration_xml=without(declared.declaration_xml, "E0200002"))
    failed = evaluate_local_e10_2024_plausibility(invalid)
    with pytest.raises(E10ReadinessError, match="plausibility stages must pass"):
        assess_local_e10_2024_readiness(mapped, invalid, failed)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("blockers", (), "blockers"),
        ("denied_capabilities", (), "capability"),
        ("synthetic_only", False, "evidence"),
        ("official_xsd_validated", False, "evidence"),
        ("local_plausibility_subset_passed", False, "evidence"),
        ("official_eric_plausibility_executed", True, "external readiness"),
        ("external_readiness", True, "external readiness"),
        ("network_calls", ("https://example.invalid",), "network"),
        ("transmission_permitted", True, "external readiness"),
    ],
)
def test_assessment_cannot_be_forged_past_boundary(field, value, message):
    result = assess_local_e10_2024_readiness(*pipeline())
    with pytest.raises(E10ReadinessError, match=message):
        replace(result, **{field: value})


@pytest.mark.parametrize("index", [0, 1, 2])
def test_rejects_wrong_input_type(index):
    items = list(pipeline())
    items[index] = object()
    with pytest.raises(E10ReadinessError, match="required"):
        assess_local_e10_2024_readiness(*items)
