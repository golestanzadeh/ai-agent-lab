from dataclasses import replace
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from agent_lab.case_declaration_dr03 import (
    ACCEPTED_FROZEN_CALCULATION_REFERENCE,
    ACCEPTED_DR02_ACCEPTANCE_REFERENCE,
    ACCEPTED_HUMAN_REGISTRATION_REFERENCE,
    ACCEPTED_OWNER_AUTHORIZATION_REFERENCE,
    ACCEPTED_SCHOOL_DESCRIPTION,
    ACCEPTED_SCHOOL_DOCUMENT_REFERENCES,
    ACCEPTED_SCHOOL_PAYMENT_ROW_IDS,
    DR03Error, DR03Request, _validate_calendar_date,
    compose_and_validate_dr03,
)
from agent_lab.human_declared_fact import FactConfirmationState, FactValidationStatus, HumanDeclaredFact, HumanFactValidationResult
from agent_lab.official_source_resolver import OfficialSourceResolver
from tests.unit.test_case_declaration_dr02 import prior as dr01_prior
from agent_lab.case_declaration_dr02 import DR02Request, compose_and_validate_dr02

ROOT = Path(r"C:\AI-Tax-Agent-Protected\Official-Sources")
REGISTRATION = Path("artifacts/case001/declaration-remediation-20261005/dr03-owner-declarations.json")
REF = "sha256:" + "1" * 64


def prior():
    return compose_and_validate_dr02(DR02Request("CASE-001",2024,"run",dr01_prior(),REF,REF,REF,"3391.74","3391.74","120.15","2954.09","620.00","474.11"),resolver=OfficialSourceResolver(protected_root=ROOT))


def registered_facts():
    payload=json.loads(REGISTRATION.read_text(encoding="utf-8"))
    return tuple(HumanDeclaredFact("CASE-001",2024,item["semantic_key"],item["value"],item["declaring_actor_reference"],FactConfirmationState(item["confirmation_state"]),__import__("datetime").datetime.fromisoformat(item["declared_at"]),HumanFactValidationResult(FactValidationStatus(item["validation"]["status"]),tuple(item["validation"]["checks"]),tuple(item["validation"]["errors"])),item["authorization_reference"],tuple(item["audit_references"])) for item in payload["facts"])


def req(*, run_id="run"):
    facts=registered_facts()
    dr02=prior()
    if run_id != "run": dr02=replace(dr02,run_id=run_id)
    return DR03Request("CASE-001",2024,run_id,dr02,ACCEPTED_DR02_ACCEPTANCE_REFERENCE,facts,REGISTRATION,ACCEPTED_HUMAN_REGISTRATION_REFERENCE,ACCEPTED_SCHOOL_DOCUMENT_REFERENCES,ACCEPTED_SCHOOL_PAYMENT_ROW_IDS,ACCEPTED_SCHOOL_DESCRIPTION,"480.00","144.00","3000.00",ACCEPTED_FROZEN_CALCULATION_REFERENCE)


@pytest.mark.skipif(not ROOT.exists() or not REGISTRATION.exists(), reason="protected sources unavailable")
def test_dr03_exact_fields_xsd_and_frozen_result():
    result=compose_and_validate_dr03(req(),resolver=OfficialSourceResolver(protected_root=ROOT))
    values=dict(result.declared_values)
    assert values["E0500702"]=="3000" and values["E0504405"]=="480" and values["E0505607"]=="480"
    assert values["E0500807"]==values["E0500808"]=="1"
    assert values["E0500703"]==values["E0500601"]==values["E0500805"]=="01.01-31.12"
    root = ET.fromstring(result.declaration_xml)
    ordered_sections = [node.tag.rsplit("}", 1)[-1] for node in root]
    assert ordered_sections.index("Kind") < ordered_sections.index("N")
    assert result.assessment_only_school_fee_deduction_eur=="144.00"
    assert result.local_plausibility_passed and len(result.local_plausibility_rules)==5
    assert result.frozen_refund_eur=="133.83" and not result.official_eric_executed and not result.transmission_permitted


@pytest.mark.skipif(not REGISTRATION.exists(), reason="protected registration unavailable")
def test_dr03_rejects_cross_case_missing_fact_and_changed_money():
    request=req()
    with pytest.raises(DR03Error): replace(request,case_id="CASE-002")
    with pytest.raises(DR03Error): replace(request,human_facts=request.human_facts[:-1])
    with pytest.raises(DR03Error): replace(request,school_fee_paid_eur="481.00")


@pytest.mark.skipif(not REGISTRATION.exists(), reason="protected registration unavailable")
def test_dr03_identity_binds_human_and_source_lineage():
    request=req()
    changed=tuple(replace(f,value="SUBSTITUTED") if f.semantic_key=="responsible_familienkasse" else f for f in request.human_facts)
    with pytest.raises(DR03Error): replace(request,human_facts=changed)
    with pytest.raises(DR03Error): replace(request,school_description="SUBSTITUTED")


@pytest.mark.skipif(not REGISTRATION.exists(), reason="protected registration unavailable")
def test_dr03_rejects_unconfirmed_or_wrong_scope_fact():
    request=req()
    facts=list(request.human_facts)
    facts[0]=replace(facts[0],confirmation_state=FactConfirmationState.PENDING)
    with pytest.raises(Exception): replace(request,human_facts=tuple(facts))
    facts=list(request.human_facts); facts[0]=replace(facts[0],case_id="CASE-002")
    with pytest.raises(Exception): replace(request,human_facts=tuple(facts))


@pytest.mark.skipif(not REGISTRATION.exists(), reason="protected registration unavailable")
def test_dr03_rejects_substituted_lineage_duplicate_and_cross_run(tmp_path):
    request=req()
    with pytest.raises(DR03Error): replace(request,frozen_calculation_reference=REF)
    with pytest.raises(DR03Error): replace(request,school_document_references=(REF,REF))
    with pytest.raises(DR03Error): replace(request,school_payment_row_ids=("TX-other",)*2)
    with pytest.raises(DR03Error): replace(request,run_id="other-run")
    with pytest.raises(DR03Error): replace(request,human_registration_reference=REF)
    with pytest.raises(DR03Error): replace(request,dr02_acceptance_reference=REF)
    with pytest.raises(DR03Error): replace(request,dr02_result=replace(request.dr02_result,frozen_refund_eur="0.00"))
    with pytest.raises(DR03Error): replace(request,dr02_result=replace(request.dr02_result,transmission_permitted=True))
    with pytest.raises(DR03Error): replace(request,dr02_result=replace(request.dr02_result,declared_values=()))
    with pytest.raises(DR03Error): replace(request,dr02_result=replace(request.dr02_result,version="2"))
    with pytest.raises(DR03Error): replace(request,version="2")
    predecessor_root=ET.fromstring(request.dr02_result.declaration_xml)
    vor=next(node for node in predecessor_root if node.tag.rsplit("}",1)[-1]=="VOR")
    predecessor_root.remove(vor)
    altered=replace(request.dr02_result,declaration_xml=ET.tostring(predecessor_root,encoding="unicode"))
    with pytest.raises(DR03Error): replace(request,dr02_result=altered)
    predecessor_root=ET.fromstring(request.dr02_result.declaration_xml)
    other=next(node for node in predecessor_root.iter() if node.tag.rsplit("}",1)[-1]=="Weit_Sons_VorAW")
    existing=next(node for node in other if node.tag.rsplit("}",1)[-1]=="Pers")
    existing_person=next(node for node in existing if node.tag.rsplit("}",1)[-1]=="Person")
    existing_person.text="PersonB"
    namespace=existing.tag.split("}",1)[0]+"}"
    injected=ET.Element(namespace+"Pers")
    ET.SubElement(injected,namespace+"Person").text="PersonA"
    other.insert(0,injected)
    altered=replace(request.dr02_result,declaration_xml=ET.tostring(predecessor_root,encoding="unicode"))
    with pytest.raises(DR03Error): replace(request,dr02_result=altered)
    predecessor_root=ET.fromstring(request.dr02_result.declaration_xml)
    vor=next(node for node in predecessor_root if node.tag.rsplit("}",1)[-1]=="VOR")
    person=next(node for node in vor.iter() if node.tag.rsplit("}",1)[-1]=="Person")
    person.text="PersonB"
    altered=replace(request.dr02_result,declaration_xml=ET.tostring(predecessor_root,encoding="unicode"))
    with pytest.raises(DR03Error): replace(request,dr02_result=altered)
    predecessor_root=ET.fromstring(request.dr02_result.declaration_xml)
    wage=next(node for node in predecessor_root.iter() if node.tag.rsplit("}",1)[-1]=="E0200201")
    wage.text="36469"
    altered=replace(request.dr02_result,declaration_xml=ET.tostring(predecessor_root,encoding="unicode"))
    with pytest.raises(DR03Error): replace(request,dr02_result=altered)
    forged=tmp_path/"dr03-owner-declarations.json"
    forged.write_bytes(REGISTRATION.read_bytes())
    with pytest.raises(DR03Error): replace(request,human_registration_path=forged)


def test_dr03_rejects_invalid_calendar_birth_date():
    with pytest.raises(DR03Error): _validate_calendar_date("31.02.2015")
