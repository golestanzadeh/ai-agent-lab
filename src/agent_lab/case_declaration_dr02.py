"""DR-02 CASE-001 Anlage Vorsorgeaufwand non-transmitting composition."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR
from pathlib import Path
import re
from xml.etree import ElementTree as ET

import xmlschema

from agent_lab.artifact_identity import ArtifactIdentity, build_artifact_identity
from agent_lab.case_declaration_dr01 import DR01Result
from agent_lab.eric_e10_2024_mapping import E10_NAMESPACE
from agent_lab.official_source_resolver import OfficialSourceResolver

DR02_VERSION = "1"
SHA_REFERENCE = re.compile(r"^sha256:[0-9a-f]{64}$")


class DR02Error(ValueError):
    """Fail-closed DR-02 error."""


@dataclass(frozen=True, slots=True)
class DR02Request:
    case_id: str
    tax_year: int
    run_id: str
    dr01_result: DR01Result
    frozen_calculation_reference: str
    pension_evidence_reference: str
    insurance_evidence_reference: str
    employee_rv_eur: str
    employer_rv_eur: str
    spouse_rv_eur: str
    health_eur: str
    care_eur: str
    unemployment_eur: str
    version: str = DR02_VERSION

    def __post_init__(self) -> None:
        if self.case_id != "CASE-001" or self.tax_year != 2024 or not self.run_id:
            raise DR02Error("DR-02 requires exact CASE-001/2024/run scope")
        if not isinstance(self.dr01_result, DR01Result) or not self.dr01_result.non_transmitting_preview:
            raise DR02Error("an accepted non-transmitting DR-01 result is required")
        for ref in (self.frozen_calculation_reference, self.pension_evidence_reference, self.insurance_evidence_reference):
            if not SHA_REFERENCE.fullmatch(ref):
                raise DR02Error("canonical evidence references are required")
        for value in (self.employee_rv_eur, self.employer_rv_eur, self.spouse_rv_eur,
                      self.health_eur, self.care_eur, self.unemployment_eur):
            _amount(value)

    @property
    def artifact_identity(self) -> ArtifactIdentity:
        return build_artifact_identity(kind="CASE_DECLARATION_DR02_REQUEST", version=self.version, payload=self)


@dataclass(frozen=True, slots=True)
class DR02Result:
    case_id: str
    tax_year: int
    run_id: str
    request_reference: str
    prior_result_reference: str
    declaration_xml: str
    declared_values: tuple[tuple[str, str], ...]
    source_documentation_reference: str
    source_schema_reference: str
    official_xsd_validated: bool = True
    frozen_refund_eur: str = "133.83"
    non_transmitting_preview: bool = True
    official_eric_executed: bool = False
    transmission_permitted: bool = False
    version: str = DR02_VERSION

    @property
    def artifact_identity(self) -> ArtifactIdentity:
        return build_artifact_identity(kind="CASE_DECLARATION_DR02_RESULT", version=self.version, payload=self)


def _amount(value: str) -> Decimal:
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError) as exc:
        raise DR02Error("amounts must be exact decimal strings") from exc
    if not amount.is_finite() or amount < 0:
        raise DR02Error("amounts must be finite and non-negative")
    return amount


def _whole(value: str, *, reducing: bool = False) -> str:
    rounding = ROUND_FLOOR if reducing else ROUND_CEILING
    return str(int(_amount(value).to_integral_value(rounding=rounding)))


def _child(parent: ET.Element, name: str, value: str | None = None) -> ET.Element:
    node = ET.SubElement(parent, f"{{{E10_NAMESPACE}}}{name}")
    node.text = value
    return node


def compose_and_validate_dr02(request: DR02Request, *, resolver: OfficialSourceResolver) -> DR02Result:
    annual = resolver.resolve("ELSTER_E10_2024_ANNUAL_DOCUMENTATION")
    schema = resolver.resolve("ELSTER_E10_2024_XSD")
    root = ET.fromstring(request.dr01_result.declaration_xml)
    if root.find(f"{{{E10_NAMESPACE}}}VOR") is not None:
        raise DR02Error("duplicate VOR is prohibited")
    values = {
        "E2000401": _whole(request.employee_rv_eur),
        "E2000801": _whole(request.employer_rv_eur, reducing=True),
        "E2000601": _whole(request.spouse_rv_eur),
        "E2001203": _whole(request.health_eur),
        "E2001505": _whole(request.care_eur),
        "E2004403": _whole(request.unemployment_eur),
    }
    vor = ET.Element(f"{{{E10_NAMESPACE}}}VOR")
    for person, fields in (("PersonA", ("E2000401", "E2000801")), ("PersonB", ("E2000601",))):
        node = _child(vor, "AVor"); _child(node, "Person", person)
        for field in fields: _child(node, field, values[field])
    kv = _child(vor, "Beitr_g_KV_PV_Inl"); _child(kv, "Person", "PersonA"); an = _child(kv, "AN")
    _child(an, "E2001203", values["E2001203"]); _child(an, "E2001505", values["E2001505"])
    other = _child(vor, "Weit_Sons_VorAW"); pers = _child(other, "Pers"); _child(pers, "Person", "PersonA")
    _child(pers, "E2004403", values["E2004403"])
    root.append(vor)
    xml = ET.tostring(root, encoding="unicode")
    try:
        xmlschema.XMLSchema(Path(schema.path)).validate(xml)
    except xmlschema.XMLSchemaException as exc:
        raise DR02Error("DR-02 failed exact official XSD validation") from exc
    return DR02Result(
        case_id=request.case_id,
        tax_year=request.tax_year,
        run_id=request.run_id,
        request_reference=request.artifact_identity.reference,
        prior_result_reference=request.dr01_result.artifact_identity.reference,
        declaration_xml=xml,
        declared_values=tuple(values.items()),
        source_documentation_reference="sha256:" + annual.sha256,
        source_schema_reference="sha256:" + schema.sha256,
    )
