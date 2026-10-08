"""DR-04 CASE-001 section-35a non-transmitting declaration composition."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_HALF_UP
from pathlib import Path
import re
from xml.etree import ElementTree as ET

import xmlschema

from agent_lab.artifact_identity import ArtifactIdentity, build_artifact_identity
from agent_lab.case_declaration_dr02 import DR02Result
from agent_lab.eric_e10_2024_mapping import E10_NAMESPACE
from agent_lab.official_source_resolver import OfficialSourceResolver


DR04_VERSION = "2"
SHA_REFERENCE = re.compile(r"^sha256:[0-9a-f]{64}$")
ANNUAL_SOURCE_ID = "ELSTER_E10_2024_ANNUAL_DOCUMENTATION"
XSD_SOURCE_ID = "ELSTER_E10_2024_XSD"
MAX_WHOLE_EUROS = Decimal("999999999999")


class DR04Error(ValueError):
    """Fail-closed DR-04 composition error."""


@dataclass(frozen=True, slots=True)
class DR04Request:
    case_id: str
    tax_year: int
    run_id: str
    dr02_result: DR02Result
    frozen_calculation_reference: str
    craftsman_document_reference: str
    craftsman_payment_reference: str
    tenant_document_reference: str
    tenant_payment_relationship_reference: str
    craftsman_invoice_eur: str
    craftsman_eligible_basis_eur: str
    tenant_eligible_basis_eur: str
    accepted_section_35a_credit_eur: str
    version: str = DR04_VERSION

    def __post_init__(self) -> None:
        if self.case_id != "CASE-001" or self.tax_year != 2024 or not self.run_id:
            raise DR04Error("DR-04 requires exact CASE-001/2024/run scope")
        if self.version != DR04_VERSION:
            raise DR04Error("unsupported DR-04 contract version")
        if not isinstance(self.dr02_result, DR02Result):
            raise DR04Error("an accepted DR-02 result is required")
        if (
            not self.dr02_result.non_transmitting_preview
            or self.dr02_result.official_eric_executed
            or self.dr02_result.transmission_permitted
            or self.dr02_result.frozen_refund_eur != "133.83"
        ):
            raise DR04Error("the accepted non-transmitting frozen DR-02 boundary is required")
        for reference in (
            self.frozen_calculation_reference,
            self.craftsman_document_reference,
            self.craftsman_payment_reference,
            self.tenant_document_reference,
            self.tenant_payment_relationship_reference,
        ):
            if not isinstance(reference, str) or not SHA_REFERENCE.fullmatch(reference):
                raise DR04Error("canonical evidence references are required")
        invoice = _amount(self.craftsman_invoice_eur, "craftsman invoice")
        craftsman = _amount(self.craftsman_eligible_basis_eur, "craftsman eligible basis")
        tenant = _amount(self.tenant_eligible_basis_eur, "tenant eligible basis")
        credit = _amount(self.accepted_section_35a_credit_eur, "accepted section-35a credit")
        if craftsman > invoice:
            raise DR04Error("craftsman eligible basis cannot exceed the source invoice")
        declared_craftsman = craftsman.to_integral_value(rounding=ROUND_CEILING)
        declared_tenant = tenant.to_integral_value(rounding=ROUND_CEILING)
        expected_credit = ((declared_craftsman + declared_tenant) * Decimal("0.20")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if credit != expected_credit:
            raise DR04Error("accepted section-35a credit does not match the whole-euro declaration bases")

    @property
    def artifact_identity(self) -> ArtifactIdentity:
        return build_artifact_identity(kind="CASE_DECLARATION_DR04_REQUEST", version=self.version, payload=self)


@dataclass(frozen=True, slots=True)
class DR04Result:
    request_reference: str
    prior_result_reference: str
    declaration_xml: str
    exact_source_values: tuple[tuple[str, str], ...]
    declared_values: tuple[tuple[str, str], ...]
    calculated_section_35a_credit_eur: str
    source_documentation_reference: str
    source_schema_reference: str
    historical_section_35a_credit_eur: str = "31.83"
    historical_refund_eur: str = "133.83"
    successor_refund_eur: str = "134.00"
    official_xsd_validated: bool = True
    local_plausibility_rules: tuple[str, ...] = (
        "101100088", "101100089", "101100090", "101100091", "10817", "12204",
        "101100079", "101170002", "10821", "101170007",
    )
    local_plausibility_passed: bool = False
    non_transmitting_preview: bool = True
    official_eric_executed: bool = False
    transmission_permitted: bool = False
    version: str = DR04_VERSION

    @property
    def artifact_identity(self) -> ArtifactIdentity:
        return build_artifact_identity(kind="CASE_DECLARATION_DR04_RESULT", version=self.version, payload=self)


def _amount(value: str, label: str) -> Decimal:
    if not isinstance(value, str) or not re.fullmatch(r"(?:0|[1-9][0-9]{0,11})(?:\.[0-9]{1,2})?", value):
        raise DR04Error(f"{label} must be a bounded exact decimal string")
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError) as exc:
        raise DR04Error(f"{label} must be an exact decimal string") from exc
    if not amount.is_finite() or amount <= 0 or amount > MAX_WHOLE_EUROS:
        raise DR04Error(f"{label} is outside the supported positive boundary")
    return amount


def _whole_euros(value: str) -> str:
    return str(int(_amount(value, "declaration amount").to_integral_value(rounding=ROUND_CEILING)))


def _child(parent: ET.Element, name: str, value: str | None = None) -> ET.Element:
    node = ET.SubElement(parent, f"{{{E10_NAMESPACE}}}{name}")
    node.text = value
    return node


def _insert_ha_35a_in_official_order(root: ET.Element, section: ET.Element) -> None:
    later_sections = {
        "EM_35c", "Sonst", "WA_ESt", "ESt1A_U", "Kind", "L", "Anl_34b", "G", "Zins", "S",
        "Corona", "N_GRE", "N", "N_DHH", "N_AUS", "KAP", "KAP_BET", "KAP_I", "AUS", "R",
        "RAV_bAV", "R_AUS", "SO", "V", "V_FeWo", "V_Sonstige", "FW", "VOR", "AV", "Mob",
        "Vorsatz",
    }
    for index, child in enumerate(root):
        if child.tag.rsplit("}", 1)[-1] in later_sections:
            root.insert(index, section)
            return
    root.append(section)


def compose_and_validate_dr04(request: DR04Request, *, resolver: OfficialSourceResolver) -> DR04Result:
    """Add the bounded section-35a facts and validate against the exact protected XSD."""

    if not isinstance(request, DR04Request) or not isinstance(resolver, OfficialSourceResolver):
        raise DR04Error("exact DR-04 request and official-source resolver are required")
    annual = resolver.resolve(ANNUAL_SOURCE_ID)
    schema_source = resolver.resolve(XSD_SOURCE_ID)
    root = ET.fromstring(request.dr02_result.declaration_xml)
    if root.find(f"{{{E10_NAMESPACE}}}HA_35a") is not None:
        raise DR04Error("duplicate HA_35a is prohibited")

    invoice = _whole_euros(request.craftsman_invoice_eur)
    craftsman = _whole_euros(request.craftsman_eligible_basis_eur)
    tenant = _whole_euros(request.tenant_eligible_basis_eur)

    ha = ET.Element(f"{{{E10_NAMESPACE}}}HA_35a")
    reductions = _child(ha, "St_Erm")
    household = _child(reductions, "Hhn_BV_DL")
    household_item = _child(household, "Einz")
    _child(household_item, "E0107206", "Betriebskostenabrechnung: haushaltsnahe Dienstleistungen")
    _child(household_item, "E0107207", tenant)
    household_sum = _child(household, "Sum")
    _child(household_sum, "E0107208", tenant)
    crafts = _child(reductions, "Handw_L")
    crafts_item = _child(crafts, "Einz")
    _child(crafts_item, "E0111217", "Handwerkerleistung")
    _child(crafts_item, "E0170601", invoice)
    _child(crafts_item, "E0111214", craftsman)
    crafts_sum = _child(crafts, "Sum")
    _child(crafts_sum, "E0111215", craftsman)
    _insert_ha_35a_in_official_order(root, ha)

    xml = ET.tostring(root, encoding="unicode")
    try:
        xmlschema.XMLSchema(Path(schema_source.path)).validate(xml)
    except xmlschema.XMLSchemaException as exc:
        raise DR04Error("DR-04 failed exact official XSD validation") from exc

    return DR04Result(
        request_reference=request.artifact_identity.reference,
        prior_result_reference=request.dr02_result.artifact_identity.reference,
        declaration_xml=xml,
        exact_source_values=(
            ("craftsman_invoice_eur", request.craftsman_invoice_eur),
            ("craftsman_eligible_basis_eur", request.craftsman_eligible_basis_eur),
            ("tenant_eligible_basis_eur", request.tenant_eligible_basis_eur),
            ("accepted_section_35a_credit_eur", request.accepted_section_35a_credit_eur),
        ),
        declared_values=(
            ("E0107207", tenant), ("E0107208", tenant), ("E0170601", invoice),
            ("E0111214", craftsman), ("E0111215", craftsman),
        ),
        calculated_section_35a_credit_eur=request.accepted_section_35a_credit_eur,
        source_documentation_reference="sha256:" + annual.sha256,
        source_schema_reference="sha256:" + schema_source.sha256,
    )
