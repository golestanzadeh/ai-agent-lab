"""Source-evidenced local subset of E10/2024 Anlage N plausibility rules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from xml.etree import ElementTree as ET

from agent_lab.artifact_identity import ArtifactIdentity, build_artifact_identity
from agent_lab.eric_e10_2024_declaration import E10DeclarationResult
from agent_lab.eric_e10_2024_mapping import E10_NAMESPACE


PLAUSIBILITY_PROFILE_VERSION = "5"
OFFICIAL_RULE_SOURCE_FILENAME = "Jahresdokumentation_E10_2024.ods"
OFFICIAL_RULE_SOURCE_SHA256 = "6379af3c83b8d8ea1f5b8e683d2cfc401cb1506a6018cd44d68452f8b67dacd5"
SUPPORTED_OFFICIAL_RULES = (
    "241",
    "310010",
    "310030",
    "310050",
    "310060",
    "310070",
    "310090",
    "310110",
    "310120",
    "100200001",
    "100200112",
    "121355",
    "100200099",
    "100200109",
    "201010",
    "330121",
    "100200108",
    "330122",
    "100200100",
    "100200110",
    "122050",
    "121410",
)
DENIED_CAPABILITIES = (
    "ERIC_FFI",
    "OFFICIAL_ERIC_PLAUSIBILITY_ENGINE",
    "SIGNING",
    "MANUFACTURER_ID_ACCESS",
    "CREDENTIAL_OR_CERTIFICATE_ACCESS",
    "NETWORK",
    "TRANSMISSION",
)
REMAINING_BLOCKERS = ("OFFICIAL_ERIC_PLAUSIBILITY_ENGINE_NOT_EXECUTED",)


class E10PlausibilityError(ValueError):
    """Raised when local plausibility evaluation leaves its governed subset."""


class PlausibilityOutcome(str, Enum):
    LOCAL_SUBSET_PASS_OFFICIAL_ENGINE_BLOCKED = "LOCAL_SUBSET_PASS_OFFICIAL_ENGINE_BLOCKED"
    LOCAL_SUBSET_FAIL_OFFICIAL_ENGINE_BLOCKED = "LOCAL_SUBSET_FAIL_OFFICIAL_ENGINE_BLOCKED"


@dataclass(frozen=True, slots=True)
class PlausibilityFinding:
    official_rule_code: str
    field_ids: tuple[str, ...]
    message: str

    def __post_init__(self) -> None:
        if self.official_rule_code not in SUPPORTED_OFFICIAL_RULES:
            raise E10PlausibilityError("finding uses an unsupported official rule")
        if not self.field_ids or any(not value.startswith("E") for value in self.field_ids):
            raise E10PlausibilityError("finding requires explicit E10 field identifiers")
        if not self.message:
            raise E10PlausibilityError("finding message is required")


@dataclass(frozen=True, slots=True)
class E10PlausibilityResult:
    outcome: PlausibilityOutcome
    declaration_reference: str
    profile_version: str
    evaluated_rule_codes: tuple[str, ...]
    rule_source_filename: str
    rule_source_sha256: str
    findings: tuple[PlausibilityFinding, ...]
    blockers: tuple[str, ...]
    denied_capabilities: tuple[str, ...]
    synthetic_only: bool = True
    official_eric_plausibility_executed: bool = False
    network_calls: tuple[str, ...] = ()
    transmission_permitted: bool = False

    def __post_init__(self) -> None:
        _sha256_reference("declaration_reference", self.declaration_reference)
        if self.profile_version != PLAUSIBILITY_PROFILE_VERSION:
            raise E10PlausibilityError("plausibility profile mismatch")
        if self.evaluated_rule_codes != SUPPORTED_OFFICIAL_RULES:
            raise E10PlausibilityError("evaluated rule set cannot be changed")
        if self.rule_source_filename != OFFICIAL_RULE_SOURCE_FILENAME:
            raise E10PlausibilityError("official rule-source filename mismatch")
        if self.rule_source_sha256 != OFFICIAL_RULE_SOURCE_SHA256:
            raise E10PlausibilityError("official rule-source digest mismatch")
        if not isinstance(self.findings, tuple) or any(
            not isinstance(item, PlausibilityFinding) for item in self.findings
        ):
            raise E10PlausibilityError("findings must be immutable plausibility findings")
        expected = (
            PlausibilityOutcome.LOCAL_SUBSET_FAIL_OFFICIAL_ENGINE_BLOCKED
            if self.findings
            else PlausibilityOutcome.LOCAL_SUBSET_PASS_OFFICIAL_ENGINE_BLOCKED
        )
        if self.outcome is not expected:
            raise E10PlausibilityError("plausibility outcome and findings differ")
        if self.blockers != REMAINING_BLOCKERS:
            raise E10PlausibilityError("plausibility blockers cannot be weakened")
        if self.denied_capabilities != DENIED_CAPABILITIES:
            raise E10PlausibilityError("plausibility capability policy mismatch")
        if self.synthetic_only is not True or self.official_eric_plausibility_executed is not False:
            raise E10PlausibilityError("official execution or non-synthetic input is forbidden")
        if self.network_calls != () or self.transmission_permitted is not False:
            raise E10PlausibilityError("local plausibility cannot enable external activity")

    @property
    def artifact_identity(self) -> ArtifactIdentity:
        return build_artifact_identity(
            kind="ERIC_E10_2024_PLAUSIBILITY_RESULT",
            version=self.profile_version,
            payload=self,
        )


def _sha256_reference(name: str, value: str) -> None:
    digest = value.removeprefix("sha256:") if isinstance(value, str) else ""
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise E10PlausibilityError(f"{name} must be a canonical sha256 reference")


def _present(root: ET.Element, field_id: str) -> bool:
    return root.find(f".//{{{E10_NAMESPACE}}}{field_id}") is not None


def _integer_values(root: ET.Element, field_id: str) -> tuple[int, ...]:
    values = []
    for element in root.findall(f".//{{{E10_NAMESPACE}}}{field_id}"):
        try:
            values.append(int(element.text or ""))
        except ValueError as exc:
            raise E10PlausibilityError(f"{field_id} must contain an integer") from exc
    return tuple(values)


def evaluate_local_e10_2024_plausibility(
    declaration: E10DeclarationResult,
) -> E10PlausibilityResult:
    """Evaluate only the reviewed presence rules; never invoke ERiC."""
    if not isinstance(declaration, E10DeclarationResult):
        raise E10PlausibilityError("an E10DeclarationResult is required")
    try:
        root = ET.fromstring(declaration.declaration_xml)
    except ET.ParseError as exc:
        raise E10PlausibilityError("declaration XML is not well formed") from exc

    findings: list[PlausibilityFinding] = []
    gross_1_5 = _present(root, "E0200201")
    wage_tax_1_5 = _present(root, "E0200301")
    solidarity_1_5 = _present(root, "E0200401")
    church_tax_1_5 = _present(root, "E0200501")
    partner_church_tax_1_5 = _present(root, "E0200601")
    tax_class = _present(root, "E0200002")
    gross_6 = _present(root, "E0200203")
    wage_tax_6 = _present(root, "E0200303")
    solidarity_6 = _present(root, "E0200403")
    church_tax_6 = _present(root, "E0200503")
    partner_church_tax_6 = _present(root, "E0200603")
    expense_item = _present(root, "E0205406") or _present(root, "E0204802")
    other_expense_label = _present(root, "E0205405")
    other_expense_amount = _present(root, "E0205406")
    expense_sum = _present(root, "E0204803")
    association_label = _present(root, "E0204001")
    association_amounts = _integer_values(root, "E0204003")
    association_sums = _integer_values(root, "E0204002")
    work_equipment_type = _present(root, "E0204401")
    work_equipment_amounts = _integer_values(root, "E0204402")
    work_equipment_sums = _integer_values(root, "E0204403")

    if gross_1_5 and not tax_class:
        findings.append(PlausibilityFinding("241", ("E0200002", "E0200201"), "tax class is required for tax-class 1-5 wages"))
    if gross_1_5 and not wage_tax_1_5:
        findings.append(PlausibilityFinding("310010", ("E0200201", "E0200301"), "wage tax is required when tax-class 1-5 wages are present"))
    if (wage_tax_1_5 or solidarity_1_5 or church_tax_1_5 or partner_church_tax_1_5) and not gross_1_5:
        findings.append(PlausibilityFinding("310030", ("E0200201", "E0200301", "E0200401", "E0200501", "E0200601"), "tax-class 1-5 wage taxes require gross wages"))
    if solidarity_1_5 and not wage_tax_1_5:
        findings.append(PlausibilityFinding("310050", ("E0200301", "E0200401"), "tax-class 1-5 solidarity surcharge requires wage tax"))
    if church_tax_1_5 and not wage_tax_1_5:
        findings.append(PlausibilityFinding("310060", ("E0200301", "E0200501"), "tax-class 1-5 church tax requires wage tax"))
    if gross_6 and not wage_tax_6:
        findings.append(PlausibilityFinding("310070", ("E0200203", "E0200303"), "wage tax is required when tax-class 6 wages are present"))
    if (wage_tax_6 or solidarity_6 or church_tax_6 or partner_church_tax_6) and not gross_6:
        findings.append(PlausibilityFinding("310090", ("E0200203", "E0200303", "E0200403", "E0200503", "E0200603"), "tax-class 6 wage taxes require gross wages"))
    if solidarity_6 and not wage_tax_6:
        findings.append(PlausibilityFinding("310110", ("E0200303", "E0200403"), "tax-class 6 solidarity surcharge requires wage tax"))
    if church_tax_6 and not wage_tax_6:
        findings.append(PlausibilityFinding("310120", ("E0200303", "E0200503"), "tax-class 6 church tax requires wage tax"))
    if expense_item and not expense_sum:
        findings.append(PlausibilityFinding("100200001", ("E0205406", "E0204802", "E0204803"), "other-expense itemization requires its sum"))
    if expense_sum and not expense_item:
        findings.append(PlausibilityFinding("100200112", ("E0204803", "E0205406", "E0204802"), "other-expense sum requires itemization"))
    if other_expense_label is not other_expense_amount:
        findings.append(PlausibilityFinding("121355", ("E0205405", "E0205406"), "other-expense label and amount must be provided together"))
    if association_amounts and sum(association_amounts) < 0:
        findings.append(PlausibilityFinding("100200099", ("E0204003",), "professional-association item total cannot be negative"))
    if association_sums and not association_amounts:
        findings.append(PlausibilityFinding("100200109", ("E0204003", "E0204002"), "professional-association sum requires itemization"))
    if association_sums and association_amounts and sum(association_amounts) >= 0 and association_sums[0] != sum(association_amounts):
        findings.append(PlausibilityFinding("201010", ("E0204003", "E0204002"), "professional-association sum must match item total"))
    if association_amounts and not association_sums:
        findings.append(PlausibilityFinding("330121", ("E0204003", "E0204002"), "professional-association itemization requires its sum"))
    if association_label is not bool(association_amounts):
        findings.append(PlausibilityFinding("100200108", ("E0204001", "E0204003"), "professional-association description and amount must be provided together"))
    if work_equipment_amounts and not work_equipment_sums:
        findings.append(PlausibilityFinding("330122", ("E0204402", "E0204403"), "work-equipment itemization requires its sum"))
    if work_equipment_amounts and sum(work_equipment_amounts) < 0:
        findings.append(PlausibilityFinding("100200100", ("E0204402",), "work-equipment item total cannot be negative"))
    if work_equipment_sums and not work_equipment_amounts:
        findings.append(PlausibilityFinding("100200110", ("E0204402", "E0204403"), "work-equipment sum requires itemization"))
    if work_equipment_sums and work_equipment_amounts and abs(work_equipment_sums[0] - sum(work_equipment_amounts)) > 5:
        findings.append(PlausibilityFinding("122050", ("E0204402", "E0204403"), "work-equipment sum differs from item total beyond the official tolerance of five"))
    if work_equipment_type is not bool(work_equipment_amounts):
        findings.append(PlausibilityFinding("121410", ("E0204401", "E0204402"), "work-equipment type and amount must be provided together"))

    frozen_findings = tuple(findings)
    return E10PlausibilityResult(
        outcome=(
            PlausibilityOutcome.LOCAL_SUBSET_FAIL_OFFICIAL_ENGINE_BLOCKED
            if frozen_findings
            else PlausibilityOutcome.LOCAL_SUBSET_PASS_OFFICIAL_ENGINE_BLOCKED
        ),
        declaration_reference=declaration.artifact_identity.reference,
        profile_version=PLAUSIBILITY_PROFILE_VERSION,
        evaluated_rule_codes=SUPPORTED_OFFICIAL_RULES,
        rule_source_filename=OFFICIAL_RULE_SOURCE_FILENAME,
        rule_source_sha256=OFFICIAL_RULE_SOURCE_SHA256,
        findings=frozen_findings,
        blockers=REMAINING_BLOCKERS,
        denied_capabilities=DENIED_CAPABILITIES,
    )
