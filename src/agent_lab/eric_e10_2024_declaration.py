"""Local synthetic E10/2024 declaration assembly and official-XSD validation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from pathlib import Path
from xml.etree import ElementTree as ET

import xmlschema

from agent_lab.artifact_identity import ArtifactIdentity, build_artifact_identity
from agent_lab.eric_e10_2024_mapping import (
    E10_NAMESPACE,
    E10_VERSION,
    E10MappingResult,
)


DECLARATION_PROFILE_VERSION = "1"
OFFICIAL_SCHEMA_FILENAME = "E10-2024.xsd"
OFFICIAL_SCHEMA_SHA256 = "86c735c6a3070aad1ccd90e5bdc8a0999099f44ed76b5752e74d8dfa5cd7d272"
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


class E10DeclarationError(ValueError):
    """Raised when declaration assembly or validation fails closed."""


class DeclarationOutcome(str, Enum):
    OFFICIAL_XSD_VALIDATED_EXTERNAL_EXECUTION_BLOCKED = (
        "OFFICIAL_XSD_VALIDATED_EXTERNAL_EXECUTION_BLOCKED"
    )


@dataclass(frozen=True, slots=True)
class E10DeclarationResult:
    outcome: DeclarationOutcome
    mapping_reference: str
    profile_version: str
    namespace: str
    schema_version: str
    declaration_xml: str
    schema_filename: str
    schema_sha256: str
    blockers: tuple[str, ...]
    denied_capabilities: tuple[str, ...]
    synthetic_only: bool = True
    official_xsd_validated: bool = True
    official_eric_plausibility_executed: bool = False
    credential_access: bool = False
    manufacturer_id_access: bool = False
    network_calls: tuple[str, ...] = ()
    transmission_permitted: bool = False

    def __post_init__(self) -> None:
        if self.outcome is not DeclarationOutcome.OFFICIAL_XSD_VALIDATED_EXTERNAL_EXECUTION_BLOCKED:
            raise E10DeclarationError("unsupported declaration outcome")
        _sha256_reference("mapping_reference", self.mapping_reference)
        if self.profile_version != DECLARATION_PROFILE_VERSION:
            raise E10DeclarationError("declaration profile mismatch")
        if self.namespace != E10_NAMESPACE or self.schema_version != E10_VERSION:
            raise E10DeclarationError("declaration E10/2024 identity mismatch")
        if self.schema_filename != OFFICIAL_SCHEMA_FILENAME:
            raise E10DeclarationError("official schema filename mismatch")
        if self.schema_sha256 != OFFICIAL_SCHEMA_SHA256:
            raise E10DeclarationError("official schema digest mismatch")
        if self.blockers != REMAINING_BLOCKERS:
            raise E10DeclarationError("declaration blockers cannot be weakened")
        if self.denied_capabilities != DENIED_CAPABILITIES:
            raise E10DeclarationError("declaration denied-capability policy mismatch")
        if self.synthetic_only is not True or self.official_xsd_validated is not True:
            raise E10DeclarationError("declaration must be synthetic and XSD-validated")
        if any(
            value is not False
            for value in (
                self.official_eric_plausibility_executed,
                self.credential_access,
                self.manufacturer_id_access,
                self.transmission_permitted,
            )
        ):
            raise E10DeclarationError("external or protected capability cannot be enabled")
        if self.network_calls != ():
            raise E10DeclarationError("local declaration cannot contain network calls")
        _validate_root(self.declaration_xml)

    @property
    def artifact_identity(self) -> ArtifactIdentity:
        return build_artifact_identity(
            kind="ERIC_E10_2024_DECLARATION_RESULT",
            version=self.profile_version,
            payload=self,
        )


def _sha256_reference(name: str, value: str) -> None:
    digest = value.removeprefix("sha256:") if isinstance(value, str) else ""
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise E10DeclarationError(f"{name} must be a canonical sha256 reference")


def _validate_root(declaration_xml: str) -> None:
    if not isinstance(declaration_xml, str) or not declaration_xml:
        raise E10DeclarationError("declaration XML is required")
    try:
        root = ET.fromstring(declaration_xml)
    except ET.ParseError as exc:
        raise E10DeclarationError("declaration is not well-formed XML") from exc
    if root.tag != f"{{{E10_NAMESPACE}}}E10" or root.attrib != {"version": E10_VERSION}:
        raise E10DeclarationError("declaration root must be exact E10/2024")
    if root.find(f"{{{E10_NAMESPACE}}}N") is None:
        raise E10DeclarationError("declaration requires the verified Anlage N subset")


def _official_schema(schema_path: Path) -> xmlschema.XMLSchema:
    if not isinstance(schema_path, Path):
        raise E10DeclarationError("schema_path must be an explicit pathlib.Path")
    try:
        resolved = schema_path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise E10DeclarationError("official schema path is unavailable") from exc
    if not resolved.is_file() or resolved.name != OFFICIAL_SCHEMA_FILENAME:
        raise E10DeclarationError("exact official E10-2024.xsd path is required")
    try:
        digest = sha256(resolved.read_bytes()).hexdigest()
    except OSError as exc:
        raise E10DeclarationError("official schema cannot be read") from exc
    if digest != OFFICIAL_SCHEMA_SHA256:
        raise E10DeclarationError("official E10-2024.xsd digest is not recognized")
    try:
        return xmlschema.XMLSchema(resolved)
    except (OSError, xmlschema.XMLSchemaException) as exc:
        raise E10DeclarationError("official schema could not be loaded") from exc


def assemble_and_validate_e10_2024_declaration(
    mapping: E10MappingResult, *, schema_path: Path
) -> E10DeclarationResult:
    """Validate the mapped synthetic declaration locally; never invoke ERiC."""
    if not isinstance(mapping, E10MappingResult):
        raise E10DeclarationError("an E10MappingResult is required")
    declaration_xml = mapping.fragment_xml
    _validate_root(declaration_xml)
    schema = _official_schema(schema_path)
    try:
        schema.validate(declaration_xml)
    except xmlschema.XMLSchemaValidationError as exc:
        raise E10DeclarationError("synthetic declaration failed official XSD validation") from exc
    return E10DeclarationResult(
        outcome=DeclarationOutcome.OFFICIAL_XSD_VALIDATED_EXTERNAL_EXECUTION_BLOCKED,
        mapping_reference=mapping.artifact_identity.reference,
        profile_version=DECLARATION_PROFILE_VERSION,
        namespace=E10_NAMESPACE,
        schema_version=E10_VERSION,
        declaration_xml=declaration_xml,
        schema_filename=OFFICIAL_SCHEMA_FILENAME,
        schema_sha256=OFFICIAL_SCHEMA_SHA256,
        blockers=REMAINING_BLOCKERS,
        denied_capabilities=DENIED_CAPABILITIES,
    )
