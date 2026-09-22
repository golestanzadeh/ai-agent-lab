from dataclasses import replace
from pathlib import Path
from hashlib import sha256

import pytest

import agent_lab.eric_e10_2024_declaration as declaration_module

from agent_lab.elster_dry_run import SyntheticSubmissionEnvelope, SyntheticTaxSummary
from agent_lab.eric_e10_2024_declaration import (
    DENIED_CAPABILITIES,
    OFFICIAL_SCHEMA_SHA256,
    REMAINING_BLOCKERS,
    DeclarationOutcome,
    E10DeclarationError,
    assemble_and_validate_e10_2024_declaration,
)
from agent_lab.eric_e10_2024_mapping import (
    DeductibleExpenseSemantics,
    E10MappingRequest,
    E10Person,
    OtherExpenseCategory,
    map_synthetic_summary_to_e10_2024,
)


def mapping():
    envelope = SyntheticSubmissionEnvelope(
        case_id="SYNTH-CASE-E10-2024",
        run_id="SYNTH-RUN-E10-2024",
        tax_year=2024,
        procedure_code="UFA10",
        eric_version="44.3.6.0",
        purpose="synthetic E10/2024 declaration validation",
        data_classification="SYNTHETIC",
        payload=SyntheticTaxSummary(
            gross_wages_eur=67_554,
            withheld_wage_tax_eur=17_653,
            deductible_expenses_eur=1_234,
        ),
    )
    return map_synthetic_summary_to_e10_2024(
        E10MappingRequest(
            envelope=envelope,
            person=E10Person.PERSON_A,
            tax_class=1,
            deductible_expense_semantics=DeductibleExpenseSemantics.OTHER_EMPLOYMENT_EXPENSES,
            other_expense_category=OtherExpenseCategory.WRITING_MATERIALS,
        )
    )


@pytest.fixture
def schema_path(tmp_path, monkeypatch) -> Path:
    path = tmp_path / "E10-2024.xsd"
    path.write_text(
        """<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
 targetNamespace="http://finkonsens.de/elster/elstererklaerung/est/e10/v2024"
 xmlns:e10="http://finkonsens.de/elster/elstererklaerung/est/e10/v2024"
 elementFormDefault="qualified">
 <xs:element name="E10"><xs:complexType><xs:sequence>
  <xs:element name="N"><xs:complexType><xs:sequence>
   <xs:any minOccurs="1" maxOccurs="unbounded" processContents="skip"/>
  </xs:sequence></xs:complexType></xs:element>
 </xs:sequence><xs:attribute name="version" use="required" fixed="2024"/>
 </xs:complexType></xs:element>
</xs:schema>""",
        encoding="utf-8",
    )
    monkeypatch.setattr(declaration_module, "OFFICIAL_SCHEMA_SHA256", sha256(path.read_bytes()).hexdigest())
    return path


def test_validates_complete_synthetic_declaration_against_pinned_xsd(schema_path):
    result = assemble_and_validate_e10_2024_declaration(
        mapping(), schema_path=schema_path
    )
    assert result.outcome is DeclarationOutcome.OFFICIAL_XSD_VALIDATED_EXTERNAL_EXECUTION_BLOCKED
    assert result.schema_sha256 == declaration_module.OFFICIAL_SCHEMA_SHA256
    assert result.declaration_xml == mapping().fragment_xml
    assert result.blockers == REMAINING_BLOCKERS
    assert result.denied_capabilities == DENIED_CAPABILITIES


def test_result_is_deterministic_and_hash_bound(schema_path):
    first = assemble_and_validate_e10_2024_declaration(mapping(), schema_path=schema_path)
    second = assemble_and_validate_e10_2024_declaration(mapping(), schema_path=schema_path)
    assert first == second
    assert first.artifact_identity == second.artifact_identity


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("blockers", (), "blockers"),
        ("denied_capabilities", (), "capability"),
        ("synthetic_only", False, "synthetic"),
        ("official_xsd_validated", False, "XSD"),
        ("official_eric_plausibility_executed", True, "capability"),
        ("credential_access", True, "capability"),
        ("manufacturer_id_access", True, "capability"),
        ("network_calls", ("https://example.invalid",), "network"),
        ("transmission_permitted", True, "capability"),
    ],
)
def test_result_tampering_fails_closed(field, value, message, schema_path):
    result = assemble_and_validate_e10_2024_declaration(mapping(), schema_path=schema_path)
    with pytest.raises(E10DeclarationError, match=message):
        replace(result, **{field: value})


def test_rejects_missing_or_wrong_schema(tmp_path):
    with pytest.raises(E10DeclarationError, match="unavailable"):
        assemble_and_validate_e10_2024_declaration(mapping(), schema_path=tmp_path / "E10-2024.xsd")
    wrong = tmp_path / "E10-2024.xsd"
    wrong.write_text("<x/>", encoding="utf-8")
    with pytest.raises(E10DeclarationError, match="digest"):
        assemble_and_validate_e10_2024_declaration(mapping(), schema_path=wrong)


def test_rejects_schema_path_as_string(schema_path):
    with pytest.raises(E10DeclarationError, match="pathlib.Path"):
        assemble_and_validate_e10_2024_declaration(mapping(), schema_path=str(schema_path))


def test_rejects_non_mapping_input(schema_path):
    with pytest.raises(E10DeclarationError, match="E10MappingResult"):
        assemble_and_validate_e10_2024_declaration(object(), schema_path=schema_path)


def test_rejects_mapping_that_fails_xsd(schema_path):
    source = mapping()
    invalid = replace(
        source,
        fragment_xml=source.fragment_xml.replace(
            "</E10>",
            '<Bogus xmlns="http://finkonsens.de/elster/elstererklaerung/est/e10/v2024"></Bogus></E10>',
        ),
    )
    with pytest.raises(E10DeclarationError, match="failed official XSD"):
        assemble_and_validate_e10_2024_declaration(invalid, schema_path=schema_path)
