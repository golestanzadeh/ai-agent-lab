"""Source-evidenced local subset of E10/2024 Anlage N plausibility rules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from xml.etree import ElementTree as ET

from agent_lab.artifact_identity import ArtifactIdentity, build_artifact_identity
from agent_lab.eric_e10_2024_declaration import E10DeclarationResult
from agent_lab.eric_e10_2024_mapping import E10_NAMESPACE


PLAUSIBILITY_PROFILE_VERSION = "1"
SUPPORTED_OFFICIAL_RULES = (
    "241",
    "310010",
    "310070",
    "100200001",
    "100200112",
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


def evaluate_local_e10_2024_plausibility(
    declaration: E10DeclarationResult,
) -> E10PlausibilityResult:
    """Evaluate only the five reviewed presence rules; never invoke ERiC."""
    if not isinstance(declaration, E10DeclarationResult):
        raise E10PlausibilityError("an E10DeclarationResult is required")
    try:
        root = ET.fromstring(declaration.declaration_xml)
    except ET.ParseError as exc:
        raise E10PlausibilityError("declaration XML is not well formed") from exc

    findings: list[PlausibilityFinding] = []
    gross_1_5 = _present(root, "E0200201")
    wage_tax_1_5 = _present(root, "E0200301")
    tax_class = _present(root, "E0200002")
    gross_6 = _present(root, "E0200203")
    wage_tax_6 = _present(root, "E0200303")
    expense_item = _present(root, "E0205406") or _present(root, "E0204802")
    expense_sum = _present(root, "E0204803")

    if gross_1_5 and not tax_class:
        findings.append(PlausibilityFinding("241", ("E0200002", "E0200201"), "tax class is required for tax-class 1-5 wages"))
    if gross_1_5 and not wage_tax_1_5:
        findings.append(PlausibilityFinding("310010", ("E0200201", "E0200301"), "wage tax is required when tax-class 1-5 wages are present"))
    if gross_6 and not wage_tax_6:
        findings.append(PlausibilityFinding("310070", ("E0200203", "E0200303"), "wage tax is required when tax-class 6 wages are present"))
    if expense_item and not expense_sum:
        findings.append(PlausibilityFinding("100200001", ("E0205406", "E0204802", "E0204803"), "other-expense itemization requires its sum"))
    if expense_sum and not expense_item:
        findings.append(PlausibilityFinding("100200112", ("E0204803", "E0205406", "E0204802"), "other-expense sum requires itemization"))

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
        findings=frozen_findings,
        blockers=REMAINING_BLOCKERS,
        denied_capabilities=DENIED_CAPABILITIES,
    )
