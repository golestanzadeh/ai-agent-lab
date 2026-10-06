"""Current local E10/2024 readiness lineage with external execution blocked."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agent_lab.artifact_identity import ArtifactIdentity, build_artifact_identity
from agent_lab.eric_e10_2024_declaration import E10DeclarationResult
from agent_lab.eric_e10_2024_mapping import E10MappingResult
from agent_lab.eric_e10_2024_plausibility import (
    E10PlausibilityResult,
    PlausibilityOutcome,
)


READINESS_VERSION = "1"
RESIDUAL_BLOCKERS = (
    "OFFICIAL_ERIC_PLAUSIBILITY_ENGINE_NOT_EXECUTED",
    "REAL_PAYLOAD_NOT_AUTHORIZED",
    "ARTICLE_1_CONTENT_RELEASE_NOT_APPROVED",
    "ARTICLE_1_DESTINATION_TRANSMISSION_NOT_APPROVED",
    "TRANSMITTER_NOT_IMPLEMENTED",
)
DENIED_CAPABILITIES = (
    "ERIC_FFI",
    "OFFICIAL_ERIC_PLAUSIBILITY_ENGINE",
    "REAL_DATA",
    "SIGNING",
    "MANUFACTURER_ID_ACCESS",
    "CREDENTIAL_OR_CERTIFICATE_ACCESS",
    "NETWORK",
    "TRANSMISSION",
)


class E10ReadinessError(ValueError):
    """Raised when current E10 readiness lineage is incomplete or unsafe."""


class E10ReadinessOutcome(str, Enum):
    LOCAL_PIPELINE_READY_EXTERNAL_EXECUTION_BLOCKED = (
        "LOCAL_PIPELINE_READY_EXTERNAL_EXECUTION_BLOCKED"
    )


@dataclass(frozen=True, slots=True)
class E10LocalReadinessAssessment:
    mapping_reference: str
    declaration_reference: str
    plausibility_reference: str
    blockers: tuple[str, ...]
    denied_capabilities: tuple[str, ...]
    outcome: E10ReadinessOutcome = (
        E10ReadinessOutcome.LOCAL_PIPELINE_READY_EXTERNAL_EXECUTION_BLOCKED
    )
    readiness_version: str = READINESS_VERSION
    synthetic_only: bool = True
    official_xsd_validated: bool = True
    local_plausibility_subset_passed: bool = True
    official_eric_plausibility_executed: bool = False
    external_readiness: bool = False
    network_calls: tuple[str, ...] = ()
    transmission_permitted: bool = False

    def __post_init__(self) -> None:
        for name, value in (
            ("mapping_reference", self.mapping_reference),
            ("declaration_reference", self.declaration_reference),
            ("plausibility_reference", self.plausibility_reference),
        ):
            _reference(name, value)
        if len({self.mapping_reference, self.declaration_reference, self.plausibility_reference}) != 3:
            raise E10ReadinessError("readiness lineage references must be distinct")
        if self.blockers != RESIDUAL_BLOCKERS:
            raise E10ReadinessError("residual blockers cannot be weakened")
        if self.denied_capabilities != DENIED_CAPABILITIES:
            raise E10ReadinessError("readiness capability policy cannot be weakened")
        if self.outcome is not E10ReadinessOutcome.LOCAL_PIPELINE_READY_EXTERNAL_EXECUTION_BLOCKED:
            raise E10ReadinessError("unsupported readiness outcome")
        if self.readiness_version != READINESS_VERSION:
            raise E10ReadinessError("unsupported readiness version")
        if any(
            value is not True
            for value in (
                self.synthetic_only,
                self.official_xsd_validated,
                self.local_plausibility_subset_passed,
            )
        ):
            raise E10ReadinessError("local readiness evidence cannot be weakened")
        if any(
            value is not False
            for value in (
                self.official_eric_plausibility_executed,
                self.external_readiness,
                self.transmission_permitted,
            )
        ):
            raise E10ReadinessError("external readiness cannot be enabled")
        if self.network_calls != ():
            raise E10ReadinessError("local readiness cannot contain network calls")

    @property
    def artifact_identity(self) -> ArtifactIdentity:
        return build_artifact_identity(
            kind="ERIC_E10_2024_LOCAL_READINESS",
            version=self.readiness_version,
            payload=self,
        )


def _reference(name: str, value: str) -> None:
    digest = value.removeprefix("sha256:") if isinstance(value, str) else ""
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise E10ReadinessError(f"{name} must be a canonical sha256 reference")


def assess_local_e10_2024_readiness(
    mapping: E10MappingResult,
    declaration: E10DeclarationResult,
    plausibility: E10PlausibilityResult,
) -> E10LocalReadinessAssessment:
    """Bind completed local stages without claiming official/external readiness."""
    if not isinstance(mapping, E10MappingResult):
        raise E10ReadinessError("an E10MappingResult is required")
    if not isinstance(declaration, E10DeclarationResult):
        raise E10ReadinessError("an E10DeclarationResult is required")
    if not isinstance(plausibility, E10PlausibilityResult):
        raise E10ReadinessError("an E10PlausibilityResult is required")
    mapping_reference = mapping.artifact_identity.reference
    declaration_reference = declaration.artifact_identity.reference
    if declaration.mapping_reference != mapping_reference:
        raise E10ReadinessError("declaration does not bind the exact mapping")
    if plausibility.declaration_reference != declaration_reference:
        raise E10ReadinessError("plausibility does not bind the exact declaration")
    if (
        declaration.official_xsd_validated is not True
        or plausibility.outcome is not PlausibilityOutcome.LOCAL_SUBSET_PASS_OFFICIAL_ENGINE_BLOCKED
        or plausibility.findings != ()
    ):
        raise E10ReadinessError("local XSD and plausibility stages must pass")
    return E10LocalReadinessAssessment(
        mapping_reference=mapping_reference,
        declaration_reference=declaration_reference,
        plausibility_reference=plausibility.artifact_identity.reference,
        blockers=RESIDUAL_BLOCKERS,
        denied_capabilities=DENIED_CAPABILITIES,
    )
