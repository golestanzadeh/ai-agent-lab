from dataclasses import replace
from pathlib import Path

import pytest

from agent_lab.case_declaration_dr01 import (
    DR01Error,
    DR01Request,
    HauptvordruckPersonA,
    HauptvordruckPersonB,
    compose_and_validate_dr01,
)
from agent_lab.official_source_resolver import OfficialSourceResolver
from tests.unit.test_eric_e10_2024_mapping import request as mapping_request
from agent_lab.eric_e10_2024_mapping import map_synthetic_summary_to_e10_2024


REF = "sha256:" + "1" * 64
ROOT = Path(r"C:\AI-Tax-Agent-Protected\Official-Sources")


def request():
    mapping = map_synthetic_summary_to_e10_2024(mapping_request(gross_wages_eur=36_470, withheld_wage_tax_eur=776))
    return DR01Request(
        case_id="CASE-TEST", tax_year=2024, run_id="RUN-TEST", case_registry_reference=REF,
        frozen_calculation_reference=REF, person_a_evidence_reference=REF,
        person_b_evidence_reference=REF, wage_evidence_reference=REF,
        source_gross_wage_eur="36470.23",
        person_a=HauptvordruckPersonA("12345678901", "01.01.1980", "Muster", "Max", "11", "Testweg", "1", "10115", "Berlin", "01.01.2010"),
        person_b=HauptvordruckPersonB("10987654321", "02.02.1982", "Muster", "Erika", "11"),
        anlage_n_mapping=mapping,
    )


@pytest.mark.skipif(not ROOT.exists(), reason="protected official source store unavailable")
def test_dr01_composes_joint_assessment_and_validates_exact_xsd():
    result = compose_and_validate_dr01(request(), resolver=OfficialSourceResolver(protected_root=ROOT))
    assert result.gross_wage_declared_eur == 36_470
    assert "<E0100001>X</E0100001>" in result.declaration_xml
    assert "<E0101201>X</E0101201>" in result.declaration_xml
    assert result.official_xsd_validated is True
    assert result.non_transmitting_preview is True
    assert result.official_eric_executed is False
    assert result.transmission_permitted is False


def test_taxpayer_favorable_rounding_must_match_anlage_n():
    with pytest.raises(DR01Error, match="gross wage does not match"):
        compose_and_validate_dr01(
            replace(request(), source_gross_wage_eur="36471.23"),
            resolver=OfficialSourceResolver(protected_root=ROOT),
        )


@pytest.mark.parametrize("value", ["", "NaN", "-1", "1000000000000"])
def test_rejects_invalid_source_wage(value):
    with pytest.raises(DR01Error, match="gross wage"):
        replace(request(), source_gross_wage_eur=value)


def test_rejects_wrong_case_year_or_ambiguous_lineage():
    with pytest.raises(DR01Error, match="2024"):
        replace(request(), tax_year=2023)
    with pytest.raises(DR01Error, match="lineage"):
        replace(request(), wage_evidence_reference="not-a-hash")


def test_request_and_result_identity_are_deterministic():
    first = request()
    second = request()
    assert first.artifact_identity == second.artifact_identity
    if ROOT.exists():
        resolver = OfficialSourceResolver(protected_root=ROOT)
        assert compose_and_validate_dr01(first, resolver=resolver).artifact_identity == compose_and_validate_dr01(second, resolver=resolver).artifact_identity


def test_case_run_and_evidence_identity_are_cryptographically_bound():
    baseline = request()
    assert replace(baseline, case_id="CASE-OTHER").artifact_identity != baseline.artifact_identity
    assert replace(baseline, run_id="RUN-OTHER").artifact_identity != baseline.artifact_identity
    assert replace(baseline, person_a_evidence_reference="sha256:" + "2" * 64).artifact_identity != baseline.artifact_identity
