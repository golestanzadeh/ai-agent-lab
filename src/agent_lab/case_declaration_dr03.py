"""DR-03 CASE-001 Anlage Kind composition with protected Human facts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET

import xmlschema

from agent_lab.artifact_identity import ArtifactIdentity, build_artifact_identity
from agent_lab.case_declaration_dr02 import DR02Result
from agent_lab.eric_e10_2024_mapping import E10_NAMESPACE
from agent_lab.human_declared_fact import HumanDeclaredFact
from agent_lab.official_source_resolver import OfficialSourceResolver

DR03_VERSION = "1"
SHA_REFERENCE = re.compile(r"^sha256:[0-9a-f]{64}$")
ACCEPTED_FROZEN_CALCULATION_REFERENCE = "sha256:56fcb1c476e87a8bed3e9821ff12f83c784a07efc3138e18bb30a9aca2b20540"
ACCEPTED_DR02_ACCEPTANCE_REFERENCE = "sha256:e910d4b47ee0ec61dd4cb11740bac48bd61d71b18adf138931c4853e03d2fc18"
ACCEPTED_OFFICIAL_DOCUMENTATION_REFERENCE = "sha256:6379af3c83b8d8ea1f5b8e683d2cfc401cb1506a6018cd44d68452f8b67dacd5"
ACCEPTED_OFFICIAL_SCHEMA_REFERENCE = "sha256:86c735c6a3070aad1ccd90e5bdc8a0999099f44ed76b5752e74d8dfa5cd7d272"
ACCEPTED_OWNER_AUTHORIZATION_REFERENCE = "sha256:e6e67eda06be64f2592136dcf4e51bf8f2d8a0d30d1be1ae8652c20f0383ee8c"
ACCEPTED_HUMAN_REGISTRATION_REFERENCE = "sha256:fc1fc151c14561b21b113d3a0e6e88f20faf27debae0ef695f485e73f9e035d4"
ACCEPTED_HUMAN_FACT_REFERENCES = (
    "sha256:0ea7f32a895e7dcf502d1397f891237e173abd2ba2e04d8d211a8f06e1fc8302",
    "sha256:3887bc3c62d9d908ab15c12e8e6512df121357e2f63902259509af4d58979bbd",
    "sha256:dfb2cb45046443f9a6246ae3e519540304468322f1c2551dcb33de901924f456",
    "sha256:fd505935a73f936b3e89ea8e49aad648623510fea60f8c5de79343cd6e147600",
    "sha256:c011aa05a399275eb7286ed0b3bd6a32e74cb571585c3d2e69bb58eca2cfb763",
    "sha256:57f1d4bd3503686a322b1b6d93ad48b80e6b2602f8c5b6aad5d4f76e970a3f30",
)
ACCEPTED_SCHOOL_DESCRIPTION = "Schulstiftung der Erzdiözese Freiburg"
ACCEPTED_SCHOOL_DOCUMENT_REFERENCES = (
    "sha256:88085bd1fb3e3c7cf18d6bea27668c57e5604a16db769a22ce1ac629526bb60a",
    "sha256:fe9847b44c269a0345ece933e50a4c94f093d68471d2a7460c36ebc73e7cff2a",
)
ACCEPTED_SCHOOL_PAYMENT_ROW_IDS = (
    "TX-6ab4508354f25e43fd19f212",
    "TX-de313fcd2268cdea5f78e0f8",
)
REQUIRED_FACTS = (
    "child_tax_id", "child_birth_date", "child_residence_2024",
    "child_relationship_person_a_2024", "child_relationship_person_b_2024",
    "responsible_familienkasse",
)


class DR03Error(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class DR03Request:
    case_id: str
    tax_year: int
    run_id: str
    dr02_result: DR02Result
    dr02_acceptance_reference: str
    human_facts: tuple[HumanDeclaredFact, ...] = field(repr=False)
    human_registration_path: Path
    human_registration_reference: str
    school_document_references: tuple[str, ...]
    school_payment_row_ids: tuple[str, ...]
    school_description: str
    school_fee_paid_eur: str
    accepted_school_fee_deduction_eur: str
    kindergeld_entitlement_eur: str
    frozen_calculation_reference: str
    version: str = DR03_VERSION

    def __post_init__(self) -> None:
        if self.version != DR03_VERSION:
            raise DR03Error("unsupported DR-03 contract version")
        if self.case_id != "CASE-001" or self.tax_year != 2024 or not self.run_id:
            raise DR03Error("DR-03 requires exact CASE-001/2024/run scope")
        if not isinstance(self.dr02_result, DR02Result) or not self.dr02_result.non_transmitting_preview:
            raise DR03Error("accepted non-transmitting DR-02 result is required")
        if (self.dr02_result.case_id, self.dr02_result.tax_year, self.dr02_result.run_id) != (
            self.case_id, self.tax_year, self.run_id
        ):
            raise DR03Error("DR-02 predecessor scope/run does not match DR-03")
        if self.dr02_acceptance_reference != ACCEPTED_DR02_ACCEPTANCE_REFERENCE:
            raise DR03Error("accepted DR-02 package identity is required")
        if (
            self.dr02_result.declared_values != (
                ("E2000401", "3392"), ("E2000801", "3391"),
                ("E2000601", "121"), ("E2001203", "2955"),
                ("E2001505", "620"), ("E2004403", "475"),
            )
            or self.dr02_result.source_documentation_reference != ACCEPTED_OFFICIAL_DOCUMENTATION_REFERENCE
            or self.dr02_result.source_schema_reference != ACCEPTED_OFFICIAL_SCHEMA_REFERENCE
            or self.dr02_result.version != "1"
            or not self.dr02_result.official_xsd_validated
            or self.dr02_result.frozen_refund_eur != "133.83"
            or self.dr02_result.official_eric_executed
            or self.dr02_result.transmission_permitted
        ):
            raise DR03Error("DR-02 predecessor does not match accepted invariants")
        _validate_dr02_predecessor_xml(self.dr02_result)
        facts = {fact.semantic_key: fact for fact in self.human_facts}
        if tuple(sorted(facts)) != tuple(sorted(REQUIRED_FACTS)) or len(facts) != len(self.human_facts):
            raise DR03Error("exactly six unique DR-03 Human Declarations are required")
        for fact in facts.values():
            fact.assert_consumable(case_id=self.case_id, tax_year=self.tax_year)
        if self.school_description != ACCEPTED_SCHOOL_DESCRIPTION:
            raise DR03Error("exact accepted school/provider description is required")
        _verify_human_registration(self.human_registration_path, self.human_registration_reference, facts)
        if tuple(sorted(self.school_document_references)) != tuple(sorted(ACCEPTED_SCHOOL_DOCUMENT_REFERENCES)):
            raise DR03Error("exact accepted school-document lineage is required")
        if len(set(self.school_document_references)) != len(self.school_document_references):
            raise DR03Error("duplicate school-document lineage is prohibited")
        if tuple(sorted(self.school_payment_row_ids)) != tuple(sorted(ACCEPTED_SCHOOL_PAYMENT_ROW_IDS)):
            raise DR03Error("exact accepted school-payment lineage is required")
        if len(set(self.school_payment_row_ids)) != len(self.school_payment_row_ids):
            raise DR03Error("duplicate school-payment lineage is prohibited")
        if self.frozen_calculation_reference != ACCEPTED_FROZEN_CALCULATION_REFERENCE:
            raise DR03Error("exact accepted frozen calculation reference is required")
        paid = _amount(self.school_fee_paid_eur)
        deduction = _amount(self.accepted_school_fee_deduction_eur)
        benefit = _amount(self.kindergeld_entitlement_eur)
        if paid != Decimal("480.00") or deduction != Decimal("144.00") or benefit != Decimal("3000.00"):
            raise DR03Error("DR-03 accepted monetary facts must remain frozen")
        if deduction != paid * Decimal("0.30"):
            raise DR03Error("school-fee deduction must equal 30 percent")

    @property
    def artifact_identity(self) -> ArtifactIdentity:
        payload = {
            "case_id": self.case_id,
            "tax_year": self.tax_year,
            "run_id": self.run_id,
            "dr02_result_reference": self.dr02_result.artifact_identity.reference,
            "dr02_acceptance_reference": self.dr02_acceptance_reference,
            "human_fact_references": tuple(
                fact.artifact_identity.reference for fact in self.human_facts
            ),
            "human_registration_reference": self.human_registration_reference,
            "school_document_references": self.school_document_references,
            "school_payment_row_ids": self.school_payment_row_ids,
            "school_description": self.school_description,
            "school_fee_paid_eur": self.school_fee_paid_eur,
            "accepted_school_fee_deduction_eur": self.accepted_school_fee_deduction_eur,
            "kindergeld_entitlement_eur": self.kindergeld_entitlement_eur,
            "frozen_calculation_reference": self.frozen_calculation_reference,
        }
        return build_artifact_identity(
            kind="CASE_DECLARATION_DR03_REQUEST", version=self.version, payload=payload
        )


@dataclass(frozen=True, slots=True)
class DR03Result:
    request_reference: str
    prior_result_reference: str
    declaration_xml: str
    declared_values: tuple[tuple[str, str], ...]
    human_fact_references: tuple[str, ...]
    human_registration_reference: str
    school_document_references: tuple[str, ...]
    school_payment_row_ids: tuple[str, ...]
    frozen_calculation_reference: str
    source_documentation_reference: str
    source_schema_reference: str
    official_xsd_validated: bool = True
    local_plausibility_rules: tuple[str, ...] = (
        "501130", "100500043", "501150", "501162", "100500044",
    )
    local_plausibility_passed: bool = True
    assessment_only_school_fee_deduction_eur: str = "144.00"
    frozen_refund_eur: str = "133.83"
    non_transmitting_preview: bool = True
    official_eric_executed: bool = False
    transmission_permitted: bool = False
    version: str = DR03_VERSION

    @property
    def artifact_identity(self) -> ArtifactIdentity:
        return build_artifact_identity(kind="CASE_DECLARATION_DR03_RESULT", version=self.version, payload=self)


def _amount(value: str) -> Decimal:
    try:
        result = Decimal(value)
    except (InvalidOperation, TypeError) as exc:
        raise DR03Error("amounts must be exact decimals") from exc
    if not result.is_finite() or result < 0:
        raise DR03Error("amounts must be finite and non-negative")
    return result


def _validate_dr02_predecessor_xml(result: DR02Result) -> None:
    if (
        not SHA_REFERENCE.fullmatch(result.request_reference)
        or not SHA_REFERENCE.fullmatch(result.prior_result_reference)
        or result.request_reference == result.prior_result_reference
    ):
        raise DR03Error("DR-02 predecessor request/prior lineage is invalid")
    try:
        root = ET.fromstring(result.declaration_xml)
    except ET.ParseError as exc:
        raise DR03Error("DR-02 predecessor XML is invalid") from exc
    vorsorge = root.findall(f"{{{E10_NAMESPACE}}}VOR")
    if len(vorsorge) != 1:
        raise DR03Error("DR-02 predecessor must contain exactly one Vorsorgeaufwand section")
    expected = dict(result.declared_values)
    for field_name, expected_value in expected.items():
        nodes = vorsorge[0].findall(f".//{{{E10_NAMESPACE}}}{field_name}")
        if len(nodes) != 1 or nodes[0].text != expected_value:
            raise DR03Error("DR-02 predecessor XML does not match accepted field bindings")
    ns = f"{{{E10_NAMESPACE}}}"
    avor = vorsorge[0].findall(f"{ns}AVor")
    if len(avor) != 2:
        raise DR03Error("DR-02 predecessor pension-person structure is invalid")
    if (
        avor[0].findtext(f"{ns}Person") != "PersonA"
        or avor[1].findtext(f"{ns}Person") != "PersonB"
        or avor[0].find(f"{ns}E2000401") is None
        or avor[0].find(f"{ns}E2000801") is None
        or avor[1].find(f"{ns}E2000601") is None
    ):
        raise DR03Error("DR-02 predecessor pension fields are assigned to the wrong person")
    kv = vorsorge[0].findall(f"{ns}Beitr_g_KV_PV_Inl")
    other = vorsorge[0].findall(f"{ns}Weit_Sons_VorAW")
    kv_an = kv[0].findall(f"{ns}AN") if len(kv) == 1 else []
    other_people = other[0].findall(f"{ns}Pers") if len(other) == 1 else []
    if (
        len(kv) != 1 or kv[0].findtext(f"{ns}Person") != "PersonA"
        or len(kv_an) != 1
        or kv_an[0].findtext(f"{ns}E2001203") != "2955"
        or kv_an[0].findtext(f"{ns}E2001505") != "620"
        or len(other) != 1 or len(other_people) != 1
        or other_people[0].findtext(f"{ns}Person") != "PersonA"
        or other_people[0].findtext(f"{ns}E2004403") != "475"
    ):
        raise DR03Error("DR-02 predecessor insurance fields are assigned to the wrong person")
    # Preserve the accepted DR-01 financial/filing semantics carried by DR-02.
    accepted_prior = {
        "E0100001": "X", "E0101201": "X", "E0200201": "36470",
        "E0200301": "776,00", "E0205406": "1234", "E0204803": "1234",
    }
    for field_name, expected_value in accepted_prior.items():
        nodes = root.findall(f".//{ns}{field_name}")
        if len(nodes) != 1 or nodes[0].text != expected_value:
            raise DR03Error("DR-02 predecessor lost accepted DR-01 semantics")


def _verify_human_registration(
    path: Path, reference: str, facts: dict[str, HumanDeclaredFact]
) -> None:
    if not isinstance(path, Path) or not path.is_file() or not SHA_REFERENCE.fullmatch(reference):
        raise DR03Error("protected Human Declaration registration is required")
    normalized = path.resolve().as_posix().casefold()
    required_suffix = "/artifacts/case001/declaration-remediation-20261005/dr03-owner-declarations.json"
    if not normalized.endswith(required_suffix):
        raise DR03Error("Human Declaration registration is outside the approved case boundary")
    if reference != ACCEPTED_HUMAN_REGISTRATION_REFERENCE:
        raise DR03Error("Human Declaration registration identity is not accepted")
    raw = path.read_bytes()
    if reference != "sha256:" + hashlib.sha256(raw).hexdigest():
        raise DR03Error("Human Declaration registration hash mismatch")
    try:
        registration = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DR03Error("Human Declaration registration is invalid") from exc
    if (
        registration.get("schema_version") != "1"
        or registration.get("case_id") != "CASE-001"
        or registration.get("tax_year") != 2024
        or registration.get("source_reference") != ACCEPTED_OWNER_AUTHORIZATION_REFERENCE
        or registration.get("fact_count") != 6
    ):
        raise DR03Error("Human Declaration registration provenance is not approved")
    registered = {
        item.get("semantic_key"): item for item in registration.get("facts", [])
        if isinstance(item, dict)
    }
    if set(registered) != set(REQUIRED_FACTS) or len(registration.get("facts", [])) != 6:
        raise DR03Error("Human Declaration registration is incomplete")
    registered_references = tuple(registered[key].get("artifact_reference") for key in REQUIRED_FACTS)
    if registered_references != ACCEPTED_HUMAN_FACT_REFERENCES:
        raise DR03Error("registered Human Declaration identities are not accepted")
    for key, fact in facts.items():
        item = registered[key]
        if (
            item.get("value") != fact.value
            or item.get("artifact_reference") != fact.artifact_identity.reference
            or item.get("confirmation_state") != "CONFIRMED"
            or item.get("validation", {}).get("status") != "PASS"
            or fact.authorization_reference != ACCEPTED_OWNER_AUTHORIZATION_REFERENCE
        ):
            raise DR03Error("Human Declaration does not match protected registration")


def _validate_calendar_date(value: str) -> None:
    try:
        datetime.strptime(value, "%d.%m.%Y")
    except ValueError as exc:
        raise DR03Error("child birth date is not a valid calendar date") from exc


def _execute_kind_plausibility(values: dict[str, str], root: ET.Element) -> tuple[str, ...]:
    # Closed translations of the five official Kind/Schulgeld rules pinned in
    # ELSTER.E10.2024.DR03.CHILD_AND_SCHOOL_FEES_V1.
    if not values["E0505606"] or not values["E0504405"] or not values["E0505607"]:
        raise DR03Error("plausibility 501130/100500043/501162 failed")
    if Decimal(values["E0505607"]) != Decimal(values["E0504405"]):
        raise DR03Error("plausibility 501150 failed")
    forbidden = ("E0504505", "E0504603")
    if values["E0500807"] == values["E0500808"] == "1" and any(
        root.find(f".//{{{E10_NAMESPACE}}}{field}") is not None for field in forbidden
    ):
        raise DR03Error("plausibility 100500044 failed")
    return ("501130", "100500043", "501150", "501162", "100500044")


def _child(parent: ET.Element, name: str, value: str | None = None) -> ET.Element:
    node = ET.SubElement(parent, f"{{{E10_NAMESPACE}}}{name}")
    node.text = value
    return node


def compose_and_validate_dr03(request: DR03Request, *, resolver: OfficialSourceResolver) -> DR03Result:
    annual = resolver.resolve("ELSTER_E10_2024_ANNUAL_DOCUMENTATION")
    schema = resolver.resolve("ELSTER_E10_2024_XSD")
    facts = {fact.semantic_key: fact for fact in request.human_facts}
    if not re.fullmatch(r"[0-9]{11}", facts["child_tax_id"].value):
        raise DR03Error("child tax ID must contain eleven digits")
    if not re.fullmatch(r"[0-9]{2}\.[0-9]{2}\.[0-9]{4}", facts["child_birth_date"].value):
        raise DR03Error("child birth date must use DD.MM.YYYY")
    _validate_calendar_date(facts["child_birth_date"].value)
    if facts["child_residence_2024"].value != "DE|01.01.2024-31.12.2024":
        raise DR03Error("full-year German child residence must be explicit")
    relationship = "BIOLOGICAL_CHILD|01.01.2024-31.12.2024"
    if facts["child_relationship_person_a_2024"].value != relationship or facts["child_relationship_person_b_2024"].value != relationship:
        raise DR03Error("full-year biological-child relationship must be explicit")

    root = ET.fromstring(request.dr02_result.declaration_xml)
    if root.find(f"{{{E10_NAMESPACE}}}Kind") is not None:
        raise DR03Error("duplicate Anlage Kind is prohibited")
    kind = ET.Element(f"{{{E10_NAMESPACE}}}Kind")
    ang = _child(kind, "Ang_Kind"); allg = _child(ang, "Allg")
    values = {
        "E0500406": facts["child_tax_id"].value,
        "E0500701": facts["child_birth_date"].value,
        "E0500702": "3000",
        "E0500706": facts["responsible_familienkasse"].value,
        "E0500703": "01.01-31.12",
        "E0500807": "1", "E0500601": "01.01-31.12",
        "E0500808": "1", "E0500805": "01.01-31.12",
        "E0505606": request.school_description,
        "E0504405": "480", "E0505607": "480",
    }
    for field in ("E0500406", "E0500701", "E0500702", "E0500706"):
        _child(allg, field, values[field])
    ws = _child(ang, "WS"); inland = _child(ws, "Inl"); _child(inland, "E0500703", values["E0500703"])
    relationships = _child(kind, "K_Verh")
    for node_name, kind_field, period_field in (("K_Verh_A","E0500807","E0500601"),("K_Verh_B","E0500808","E0500805")):
        node = _child(relationships, node_name); _child(node, kind_field, values[kind_field]); _child(node, period_field, values[period_field])
    school = _child(kind, "Schulgeld"); single = _child(school, "Einz")
    _child(single, "E0505606", values["E0505606"]); _child(single, "E0504405", values["E0504405"])
    total = _child(school, "Sum"); _child(total, "E0505607", values["E0505607"])
    # The official E10 root is an ordered sequence; Anlage Kind precedes
    # Anlage N and Vorsorgeaufwand.  Insert after Hauptvordruck (ESt1A).
    root.insert(1, kind)
    executed_rules = _execute_kind_plausibility(values, root)
    xml = ET.tostring(root, encoding="unicode")
    try:
        xmlschema.XMLSchema(Path(schema.path)).validate(xml)
    except xmlschema.XMLSchemaException as exc:
        raise DR03Error("DR-03 failed exact official XSD validation") from exc
    return DR03Result(
        request_reference=request.artifact_identity.reference,
        prior_result_reference=request.dr02_result.artifact_identity.reference,
        declaration_xml=xml,
        declared_values=tuple(values.items()),
        human_fact_references=tuple(facts[key].artifact_identity.reference for key in REQUIRED_FACTS),
        human_registration_reference=request.human_registration_reference,
        school_document_references=request.school_document_references,
        school_payment_row_ids=request.school_payment_row_ids,
        frozen_calculation_reference=request.frozen_calculation_reference,
        source_documentation_reference="sha256:" + annual.sha256,
        source_schema_reference="sha256:" + schema.sha256,
        local_plausibility_rules=executed_rules,
    )
