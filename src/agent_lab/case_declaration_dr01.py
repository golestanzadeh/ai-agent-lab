"""DR-01 case-scoped Hauptvordruck composition for a non-transmitting preview."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from pathlib import Path
import re
from xml.etree import ElementTree as ET

import xmlschema

from agent_lab.artifact_identity import ArtifactIdentity, build_artifact_identity
from agent_lab.eric_e10_2024_mapping import E10_NAMESPACE, E10MappingResult
from agent_lab.official_source_resolver import OfficialSourceResolver


DR01_VERSION = "1"
ANNUAL_SOURCE_ID = "ELSTER_E10_2024_ANNUAL_DOCUMENTATION"
XSD_SOURCE_ID = "ELSTER_E10_2024_XSD"
SHA_REFERENCE = re.compile(r"^sha256:[0-9a-f]{64}$")


class DR01Error(ValueError):
    """Fail-closed DR-01 composition error."""


@dataclass(frozen=True, slots=True)
class HauptvordruckPersonA:
    tax_id: str
    birth_date: str
    last_name: str
    first_name: str
    religion_code: str
    street: str
    house_number: str
    postal_code: str
    city: str
    marriage_date: str


@dataclass(frozen=True, slots=True)
class HauptvordruckPersonB:
    tax_id: str
    birth_date: str
    last_name: str
    first_name: str
    religion_code: str


@dataclass(frozen=True, slots=True)
class DR01Request:
    case_id: str
    tax_year: int
    run_id: str
    case_registry_reference: str
    frozen_calculation_reference: str
    person_a_evidence_reference: str
    person_b_evidence_reference: str
    wage_evidence_reference: str
    source_gross_wage_eur: str
    person_a: HauptvordruckPersonA
    person_b: HauptvordruckPersonB
    anlage_n_mapping: E10MappingResult
    version: str = DR01_VERSION

    def __post_init__(self) -> None:
        if not self.case_id or not self.run_id:
            raise DR01Error("case_id and run_id are required")
        if self.tax_year != 2024 or self.version != DR01_VERSION:
            raise DR01Error("DR-01 supports only the versioned 2024 contract")
        for value in (
            self.case_registry_reference,
            self.frozen_calculation_reference,
            self.person_a_evidence_reference,
            self.person_b_evidence_reference,
            self.wage_evidence_reference,
        ):
            if not isinstance(value, str) or not SHA_REFERENCE.fullmatch(value):
                raise DR01Error("all lineage references must be canonical SHA-256 references")
        if not isinstance(self.person_a, HauptvordruckPersonA) or not isinstance(self.person_b, HauptvordruckPersonB):
            raise DR01Error("exact Person A and Person B declaration facts are required")
        if not isinstance(self.anlage_n_mapping, E10MappingResult):
            raise DR01Error("an exact Anlage N mapping is required")
        _validate_person(self.person_a, person_a=True)
        _validate_person(self.person_b, person_a=False)
        _gross_wage_whole_euros(self.source_gross_wage_eur)

    @property
    def artifact_identity(self) -> ArtifactIdentity:
        return build_artifact_identity(kind="CASE_DECLARATION_DR01_REQUEST", version=self.version, payload=self)


@dataclass(frozen=True, slots=True)
class DR01Result:
    request_reference: str
    declaration_xml: str
    gross_wage_source_eur: str
    gross_wage_declared_eur: int
    source_documentation_reference: str
    source_schema_reference: str
    official_xsd_validated: bool = True
    non_transmitting_preview: bool = True
    official_eric_executed: bool = False
    transmission_permitted: bool = False
    version: str = DR01_VERSION

    @property
    def artifact_identity(self) -> ArtifactIdentity:
        return build_artifact_identity(kind="CASE_DECLARATION_DR01_RESULT", version=self.version, payload=self)


def _validate_person(person: HauptvordruckPersonA | HauptvordruckPersonB, *, person_a: bool) -> None:
    if not re.fullmatch(r"[0-9]{11}", person.tax_id):
        raise DR01Error("tax ID must contain exactly eleven digits")
    if not re.fullmatch(r"[0-9]{2}\.[0-9]{2}\.[0-9]{4}", person.birth_date):
        raise DR01Error("birth date must use DD.MM.YYYY")
    if not person.last_name or not person.first_name or len(person.last_name) > 25 or len(person.first_name) > 25:
        raise DR01Error("official name boundaries are required")
    if not re.fullmatch(r"[0-9]{2}", person.religion_code):
        raise DR01Error("an explicit official religion code is required")
    if person_a:
        assert isinstance(person, HauptvordruckPersonA)
        if not person.street or not person.city or not re.fullmatch(r"[0-9]{5}", person.postal_code):
            raise DR01Error("complete Person A domestic address is required")
        if not re.fullmatch(r"[0-9]{1,4}", person.house_number):
            raise DR01Error("Person A house number must contain one to four digits")
        if not re.fullmatch(r"[0-9]{2}\.[0-9]{2}\.[0-9]{4}", person.marriage_date):
            raise DR01Error("marriage date is required for joint assessment")


def _gross_wage_whole_euros(value: str) -> int:
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError) as exc:
        raise DR01Error("source gross wage must be an exact decimal string") from exc
    if not amount.is_finite() or amount < 0 or amount > Decimal("999999999999.99"):
        raise DR01Error("source gross wage is outside the supported boundary")
    return int(amount.to_integral_value(rounding=ROUND_FLOOR))


def _child(parent: ET.Element, name: str, value: str | None = None) -> ET.Element:
    node = ET.SubElement(parent, f"{{{E10_NAMESPACE}}}{name}")
    node.text = value
    return node


def compose_and_validate_dr01(request: DR01Request, *, resolver: OfficialSourceResolver) -> DR01Result:
    if not isinstance(request, DR01Request) or not isinstance(resolver, OfficialSourceResolver):
        raise DR01Error("exact request and official-source resolver are required")
    annual = resolver.resolve(ANNUAL_SOURCE_ID)
    schema_source = resolver.resolve(XSD_SOURCE_ID)
    declared_wage = _gross_wage_whole_euros(request.source_gross_wage_eur)
    mapped_wages = [b.lexical_value for b in request.anlage_n_mapping.field_bindings if b.field_id == "E0200201"]
    if mapped_wages != [str(declared_wage)]:
        raise DR01Error("Anlage N gross wage does not match the authoritative taxpayer-favorable transformation")

    root = ET.fromstring(request.anlage_n_mapping.fragment_xml)
    est1a = ET.Element(f"{{{E10_NAMESPACE}}}ESt1A")
    art = _child(est1a, "Art_Erkl")
    _child(art, "E0100001", "X")
    allg = _child(est1a, "Allg")
    a = _child(allg, "A")
    for field, value in (
        ("E0100081", request.person_a.tax_id), ("E0100401", request.person_a.birth_date),
        ("E0100201", request.person_a.last_name), ("E0100301", request.person_a.first_name),
        ("E0100402", request.person_a.religion_code), ("E0101104", request.person_a.street),
        ("E0101206", request.person_a.house_number), ("E0100601", request.person_a.postal_code),
        ("E0100602", request.person_a.city), ("E0100701", request.person_a.marriage_date),
    ):
        _child(a, field, value)
    vlg = _child(allg, "Vlg_Art")
    _child(vlg, "E0101201", "X")
    b = _child(allg, "B")
    for field, value in (
        ("E0100082", request.person_b.tax_id), ("E0101001", request.person_b.birth_date),
        ("E0100901", request.person_b.last_name), ("E0100801", request.person_b.first_name),
        ("E0101002", request.person_b.religion_code),
    ):
        _child(b, field, value)
    root.insert(0, est1a)
    xml = ET.tostring(root, encoding="unicode")
    try:
        xmlschema.XMLSchema(Path(schema_source.path)).validate(xml)
    except xmlschema.XMLSchemaException as exc:
        raise DR01Error("DR-01 declaration failed exact official XSD validation") from exc
    return DR01Result(
        request_reference=request.artifact_identity.reference,
        declaration_xml=xml,
        gross_wage_source_eur=request.source_gross_wage_eur,
        gross_wage_declared_eur=declared_wage,
        source_documentation_reference="sha256:" + annual.sha256,
        source_schema_reference="sha256:" + schema_source.sha256,
    )
