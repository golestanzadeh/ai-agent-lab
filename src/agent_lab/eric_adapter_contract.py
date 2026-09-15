"""Versioned, non-production ERiC adapter boundary with no external capability."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agent_lab.artifact_identity import ArtifactIdentity, build_artifact_identity
from agent_lab.elster_dry_run import (
    SUPPORTED_ERIC_VERSION,
    SUPPORTED_PROCEDURE_CODE,
    SUPPORTED_TAX_YEAR,
    SyntheticSubmissionEnvelope,
)


ADAPTER_CONTRACT_VERSION = "1"
ADAPTER_ENVIRONMENT = "NON_PRODUCTION_DESIGN"
SUPPORTED_ENVELOPE_SCHEMA_VERSION = 1


class EricAdapterContractError(ValueError):
    """Raised when an adapter design escapes the authorized package-2 boundary."""


class AdapterDesignOutcome(str, Enum):
    BOUNDARY_READY_MAPPING_BLOCKED = "BOUNDARY_READY_MAPPING_BLOCKED"


class OfficialMaterialStatus(str, Enum):
    NOT_RECOVERED = "NOT_RECOVERED"


class OfficialMaterialKind(str, Enum):
    INTERFACE_SPECIFICATION = "ERIC_INTERFACE_SPECIFICATION"
    XML_SCHEMA = "UFA10_2024_XML_SCHEMA"
    PLAUSIBILITY_RULES = "UFA10_2024_PLAUSIBILITY_RULES"


REQUIRED_OFFICIAL_MATERIALS = (
    OfficialMaterialKind.INTERFACE_SPECIFICATION,
    OfficialMaterialKind.XML_SCHEMA,
    OfficialMaterialKind.PLAUSIBILITY_RULES,
)
DENIED_CAPABILITIES = (
    "ERIC_FFI",
    "XML_MAPPING",
    "PLAUSIBILITY_VALIDATION",
    "SIGNING",
    "CREDENTIAL_OR_CERTIFICATE_ACCESS",
    "NETWORK",
    "TRANSMISSION",
)
MISSING_MATERIAL_BLOCKERS = (
    "OFFICIAL_ERIC_INTERFACE_SPECIFICATION_NOT_RECOVERED",
    "OFFICIAL_UFA10_2024_XML_SCHEMA_NOT_RECOVERED",
    "OFFICIAL_UFA10_2024_PLAUSIBILITY_RULES_NOT_RECOVERED",
)


def _required(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise EricAdapterContractError(f"{name} is required")


def _artifact_reference(name: str, value: str) -> None:
    _required(name, value)
    prefix = "sha256:"
    digest = value[len(prefix) :] if value.startswith(prefix) else ""
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise EricAdapterContractError(f"{name} must be a canonical sha256 reference")


@dataclass(frozen=True, slots=True)
class EricAdapterContract:
    """Exact design contract; it deliberately exposes no callable ERiC API."""

    contract_version: str = ADAPTER_CONTRACT_VERSION
    environment: str = ADAPTER_ENVIRONMENT
    eric_version: str = SUPPORTED_ERIC_VERSION
    procedure_code: str = SUPPORTED_PROCEDURE_CODE
    tax_year: int = SUPPORTED_TAX_YEAR
    envelope_schema_version: int = SUPPORTED_ENVELOPE_SCHEMA_VERSION
    material_status: OfficialMaterialStatus = OfficialMaterialStatus.NOT_RECOVERED
    required_official_materials: tuple[OfficialMaterialKind, ...] = (
        REQUIRED_OFFICIAL_MATERIALS
    )
    denied_capabilities: tuple[str, ...] = DENIED_CAPABILITIES

    def __post_init__(self) -> None:
        _required("contract_version", self.contract_version)
        if self.contract_version != ADAPTER_CONTRACT_VERSION:
            raise EricAdapterContractError("unsupported adapter contract_version")
        if self.environment != ADAPTER_ENVIRONMENT:
            raise EricAdapterContractError("only NON_PRODUCTION_DESIGN is permitted")
        if self.eric_version != SUPPORTED_ERIC_VERSION:
            raise EricAdapterContractError("unsupported ERiC version")
        if self.procedure_code != SUPPORTED_PROCEDURE_CODE:
            raise EricAdapterContractError("unsupported ELSTER procedure_code")
        if self.tax_year != SUPPORTED_TAX_YEAR:
            raise EricAdapterContractError("unsupported tax_year")
        if self.envelope_schema_version != SUPPORTED_ENVELOPE_SCHEMA_VERSION:
            raise EricAdapterContractError("unsupported envelope schema_version")
        if self.material_status is not OfficialMaterialStatus.NOT_RECOVERED:
            raise EricAdapterContractError(
                "official material status cannot advance without a governed review"
            )
        if self.required_official_materials != REQUIRED_OFFICIAL_MATERIALS:
            raise EricAdapterContractError(
                "required official materials cannot change without a contract version change"
            )
        if self.denied_capabilities != DENIED_CAPABILITIES:
            raise EricAdapterContractError(
                "denied capabilities cannot change without a contract version change"
            )

    @property
    def artifact_identity(self) -> ArtifactIdentity:
        return build_artifact_identity(
            kind="ERIC_ADAPTER_CONTRACT",
            version=self.contract_version,
            payload=self,
        )


@dataclass(frozen=True, slots=True)
class EricAdapterDesignPlan:
    outcome: AdapterDesignOutcome
    contract_reference: str
    contract_version: str
    envelope_reference: str
    required_official_materials: tuple[OfficialMaterialKind, ...]
    material_status: OfficialMaterialStatus
    blockers: tuple[str, ...]
    denied_capabilities: tuple[str, ...]
    mapping_permitted: bool = False
    validation_permitted: bool = False
    signing_permitted: bool = False
    transmission_permitted: bool = False
    credential_access: bool = False
    network_calls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.outcome is not AdapterDesignOutcome.BOUNDARY_READY_MAPPING_BLOCKED:
            raise EricAdapterContractError("unsupported adapter design outcome")
        _artifact_reference("contract_reference", self.contract_reference)
        _artifact_reference("envelope_reference", self.envelope_reference)
        if self.contract_version != ADAPTER_CONTRACT_VERSION:
            raise EricAdapterContractError("plan contract_version mismatch")
        if self.required_official_materials != REQUIRED_OFFICIAL_MATERIALS:
            raise EricAdapterContractError("plan official-material policy mismatch")
        if self.material_status is not OfficialMaterialStatus.NOT_RECOVERED:
            raise EricAdapterContractError("plan official-material status mismatch")
        if self.blockers != MISSING_MATERIAL_BLOCKERS:
            raise EricAdapterContractError("plan blockers must remain fail-closed")
        if self.denied_capabilities != DENIED_CAPABILITIES:
            raise EricAdapterContractError("plan capability policy mismatch")
        capability_flags = (
            self.mapping_permitted,
            self.validation_permitted,
            self.signing_permitted,
            self.transmission_permitted,
            self.credential_access,
        )
        if any(value is not False for value in capability_flags):
            raise EricAdapterContractError(
                "non-production adapter plan cannot enable execution capabilities"
            )
        if self.network_calls != ():
            raise EricAdapterContractError(
                "non-production adapter plan cannot contain network calls"
            )


def design_eric_adapter(
    envelope: SyntheticSubmissionEnvelope,
    *,
    contract: EricAdapterContract | None = None,
) -> EricAdapterDesignPlan:
    """Bind an exact synthetic envelope to the inert versioned adapter contract."""
    if not isinstance(envelope, SyntheticSubmissionEnvelope):
        raise EricAdapterContractError("a SyntheticSubmissionEnvelope is required")
    active_contract = contract or EricAdapterContract()
    if not isinstance(active_contract, EricAdapterContract):
        raise EricAdapterContractError("an EricAdapterContract is required")
    if (
        envelope.eric_version != active_contract.eric_version
        or envelope.procedure_code != active_contract.procedure_code
        or envelope.tax_year != active_contract.tax_year
        or envelope.schema_version != active_contract.envelope_schema_version
    ):
        raise EricAdapterContractError("envelope and adapter route binding mismatch")

    return EricAdapterDesignPlan(
        outcome=AdapterDesignOutcome.BOUNDARY_READY_MAPPING_BLOCKED,
        contract_reference=active_contract.artifact_identity.reference,
        contract_version=active_contract.contract_version,
        envelope_reference=envelope.artifact_identity.reference,
        required_official_materials=active_contract.required_official_materials,
        material_status=active_contract.material_status,
        blockers=MISSING_MATERIAL_BLOCKERS,
        denied_capabilities=active_contract.denied_capabilities,
    )
