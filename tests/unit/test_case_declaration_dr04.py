from dataclasses import replace
from pathlib import Path

import pytest

from agent_lab.case_declaration_dr01 import compose_and_validate_dr01
from agent_lab.case_declaration_dr02 import DR02Request, compose_and_validate_dr02
from agent_lab.case_declaration_dr04 import DR04Error, DR04Request, compose_and_validate_dr04
from agent_lab.official_source_resolver import OfficialSourceResolver
from tests.unit.test_case_declaration_dr01 import request as dr01_request


ROOT = Path(r"C:\AI-Tax-Agent-Protected\Official-Sources")
REF = "sha256:" + "1" * 64


def prior():
    dr01 = compose_and_validate_dr01(dr01_request(), resolver=OfficialSourceResolver(protected_root=ROOT))
    return compose_and_validate_dr02(
        DR02Request(
            "CASE-001", 2024, "run", dr01, REF, REF, REF,
            "3391.74", "3391.74", "120.15", "2954.09", "620.00", "474.11",
        ),
        resolver=OfficialSourceResolver(protected_root=ROOT),
    )


def request():
    return DR04Request(
        case_id="CASE-001",
        tax_year=2024,
        run_id="RUN-CASE001-DR04-20261004-001",
        dr02_result=prior(),
        frozen_calculation_reference=REF,
        craftsman_document_reference="sha256:" + "2" * 64,
        craftsman_payment_reference="sha256:" + "3" * 64,
        tenant_document_reference="sha256:" + "4" * 64,
        tenant_payment_relationship_reference="sha256:" + "5" * 64,
        craftsman_invoice_eur="90.00",
        craftsman_eligible_basis_eur="90.00",
        tenant_eligible_basis_eur="69.13",
        accepted_section_35a_credit_eur="32.00",
    )


@pytest.mark.skipif(not ROOT.exists(), reason="protected official sources unavailable")
def test_dr04_exact_values_xsd_order_and_external_boundary():
    result = compose_and_validate_dr04(request(), resolver=OfficialSourceResolver(protected_root=ROOT))
    assert dict(result.exact_source_values) == {
        "craftsman_invoice_eur": "90.00",
        "craftsman_eligible_basis_eur": "90.00",
        "tenant_eligible_basis_eur": "69.13",
        "accepted_section_35a_credit_eur": "32.00",
    }
    assert dict(result.declared_values) == {
        "E0107207": "70", "E0107208": "70", "E0170601": "90",
        "E0111214": "90", "E0111215": "90",
    }
    assert result.calculated_section_35a_credit_eur == "32.00"
    assert result.historical_section_35a_credit_eur == "31.83"
    assert result.historical_refund_eur == "133.83"
    assert result.successor_refund_eur == "134.00"
    assert result.version == "2"
    assert result.official_xsd_validated and result.non_transmitting_preview
    assert not result.local_plausibility_passed
    assert "101170007" in result.local_plausibility_rules
    assert not result.official_eric_executed and not result.transmission_permitted
    assert result.declaration_xml.index("HA_35a") < result.declaration_xml.index("<N>")
    assert result.declaration_xml.index("<N>") < result.declaration_xml.index("<VOR>")


def test_dr04_case_isolation_credit_and_amounts_fail_closed():
    with pytest.raises(DR04Error, match="exact CASE-001"):
        replace(request(), case_id="CASE-002")
    with pytest.raises(DR04Error, match="credit does not match"):
        replace(request(), accepted_section_35a_credit_eur="31.83")
    with pytest.raises(DR04Error, match="bounded exact decimal"):
        replace(request(), tenant_eligible_basis_eur="69.123")
    with pytest.raises(DR04Error, match="cannot exceed"):
        replace(request(), craftsman_eligible_basis_eur="91.00")


def test_dr04_identity_binds_each_evidence_chain_and_exact_cent_amount():
    original = request().artifact_identity.reference
    assert original != replace(request(), craftsman_payment_reference="sha256:" + "6" * 64).artifact_identity.reference
    assert original != replace(request(), tenant_payment_relationship_reference="sha256:" + "7" * 64).artifact_identity.reference
    assert original != replace(request(), tenant_eligible_basis_eur="69.14").artifact_identity.reference
    with pytest.raises(DR04Error, match="unsupported DR-04 contract version"):
        replace(request(), version="1")


@pytest.mark.skipif(not ROOT.exists(), reason="protected official sources unavailable")
def test_dr04_duplicate_section_is_rejected():
    result = compose_and_validate_dr04(request(), resolver=OfficialSourceResolver(protected_root=ROOT))
    duplicate_request = replace(request(), dr02_result=replace(prior(), declaration_xml=result.declaration_xml))
    with pytest.raises(DR04Error, match="duplicate HA_35a"):
        compose_and_validate_dr04(duplicate_request, resolver=OfficialSourceResolver(protected_root=ROOT))


def test_dr04_rejects_prior_result_that_opens_external_boundary():
    with pytest.raises(DR04Error, match="non-transmitting frozen DR-02"):
        replace(request(), dr02_result=replace(prior(), transmission_permitted=True))
