from dataclasses import replace
from pathlib import Path
import pytest
from agent_lab.case_declaration_dr01 import DR01Result
from agent_lab.case_declaration_dr02 import DR02Error, DR02Request, compose_and_validate_dr02
from agent_lab.official_source_resolver import OfficialSourceResolver
from tests.unit.test_case_declaration_dr01 import request as dr01_request
from agent_lab.case_declaration_dr01 import compose_and_validate_dr01

ROOT = Path(r"C:\AI-Tax-Agent-Protected\Official-Sources")
REF = "sha256:" + "1" * 64

def prior():
    return compose_and_validate_dr01(dr01_request(), resolver=OfficialSourceResolver(protected_root=ROOT))

def req():
    return DR02Request("CASE-001", 2024, "run", prior(), REF, REF, REF, "3391.74", "3391.74", "120.15", "2954.09", "620.00", "474.11")

@pytest.mark.skipif(not ROOT.exists(), reason="protected official sources unavailable")
def test_dr02_exact_values_xsd_and_boundary():
    out = compose_and_validate_dr02(req(), resolver=OfficialSourceResolver(protected_root=ROOT))
    assert dict(out.declared_values) == {"E2000401":"3392","E2000801":"3391","E2000601":"121","E2001203":"2955","E2001505":"620","E2004403":"475"}
    assert "E2001405" not in out.declaration_xml
    assert out.frozen_refund_eur == "133.83" and not out.official_eric_executed and not out.transmission_permitted

def test_dr02_isolation_and_bad_amount_fail_closed():
    with pytest.raises(DR02Error): replace(req(), case_id="CASE-002")
    with pytest.raises(DR02Error): replace(req(), health_eur="NaN")

def test_dr02_identity_binds_evidence():
    assert req().artifact_identity.reference != replace(req(), pension_evidence_reference="sha256:"+"2"*64).artifact_identity.reference
