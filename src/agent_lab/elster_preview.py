"""Immutable Human-readable preview for the synthetic Phase P1 path."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json

from agent_lab.artifact_identity import ArtifactIdentity, build_artifact_identity
from agent_lab.eric_adapter_contract import EricAdapterContract, OfficialMaterialStatus
from agent_lab.eric_material_process import (
    EricMaterialProcessDecision,
    MaterialProcessOutcome,
)
from agent_lab.elster_dry_run import (
    SUPPORTED_ERIC_VERSION,
    SUPPORTED_PROCEDURE_CODE,
    SUPPORTED_TAX_YEAR,
    SyntheticSubmissionEnvelope,
)


PREVIEW_VERSION = "1"
PREVIEW_DISCLAIMER = (
    "SYNTHETIC NON-PRODUCTION PREVIEW; NOT AN OFFICIAL TAX FORM; TRANSMISSION FORBIDDEN"
)


class ElsterPreviewError(ValueError):
    """Raised when a preview escapes its synthetic non-production boundary."""


class PreviewOutcome(str, Enum):
    SYNTHETIC_PREVIEW_READY_OFFICIAL_MAPPING_BLOCKED = (
        "SYNTHETIC_PREVIEW_READY_OFFICIAL_MAPPING_BLOCKED"
    )


def _required(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ElsterPreviewError(f"{name} is required")


def _synthetic(name: str, value: str) -> None:
    _required(name, value)
    if not value.startswith("SYNTH-"):
        raise ElsterPreviewError(f"{name} must use the SYNTH- namespace")


def _artifact_reference(name: str, value: str) -> None:
    _required(name, value)
    digest = value[7:] if value.startswith("sha256:") else ""
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ElsterPreviewError(f"{name} must be a canonical sha256 reference")


@dataclass(frozen=True, slots=True)
class SyntheticElsterPreview:
    case_id: str
    run_id: str
    purpose: str
    envelope_reference: str
    adapter_contract_reference: str
    material_process_contract_reference: str
    tax_year: int
    procedure_code: str
    eric_version: str
    gross_wages_eur: int
    withheld_wage_tax_eur: int
    deductible_expenses_eur: int
    official_material_status: OfficialMaterialStatus
    outcome: PreviewOutcome = (
        PreviewOutcome.SYNTHETIC_PREVIEW_READY_OFFICIAL_MAPPING_BLOCKED
    )
    preview_version: str = PREVIEW_VERSION
    disclaimer: str = PREVIEW_DISCLAIMER
    transmission_permitted: bool = False
    credential_access: bool = False
    network_calls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _synthetic("case_id", self.case_id)
        _synthetic("run_id", self.run_id)
        _required("purpose", self.purpose)
        for name, reference in (
            ("envelope_reference", self.envelope_reference),
            ("adapter_contract_reference", self.adapter_contract_reference),
            ("material_process_contract_reference", self.material_process_contract_reference),
        ):
            _artifact_reference(name, reference)
        if (
            self.tax_year != SUPPORTED_TAX_YEAR
            or self.procedure_code != SUPPORTED_PROCEDURE_CODE
            or self.eric_version != SUPPORTED_ERIC_VERSION
        ):
            raise ElsterPreviewError("preview route binding mismatch")
        for name, value in (
            ("gross_wages_eur", self.gross_wages_eur),
            ("withheld_wage_tax_eur", self.withheld_wage_tax_eur),
            ("deductible_expenses_eur", self.deductible_expenses_eur),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ElsterPreviewError(f"{name} must be a non-negative integer")
        if self.official_material_status is not OfficialMaterialStatus.NOT_RECOVERED:
            raise ElsterPreviewError("official material status must remain NOT_RECOVERED")
        if self.outcome is not PreviewOutcome.SYNTHETIC_PREVIEW_READY_OFFICIAL_MAPPING_BLOCKED:
            raise ElsterPreviewError("unsupported preview outcome")
        if self.preview_version != PREVIEW_VERSION:
            raise ElsterPreviewError("unsupported preview_version")
        if self.disclaimer != PREVIEW_DISCLAIMER:
            raise ElsterPreviewError("preview disclaimer cannot be weakened")
        if self.transmission_permitted is not False or self.credential_access is not False:
            raise ElsterPreviewError("preview cannot enable an external capability")
        if self.network_calls != ():
            raise ElsterPreviewError("preview cannot contain network calls")

    @property
    def artifact_identity(self) -> ArtifactIdentity:
        return build_artifact_identity(
            kind="SYNTHETIC_ELSTER_HUMAN_PREVIEW",
            version=self.preview_version,
            payload=self,
        )

    @property
    def rendered_text(self) -> str:
        purpose = json.dumps(self.purpose, ensure_ascii=False)
        return "\n".join(
            (
                "SYNTHETIC ELSTER PREVIEW",
                f"Case: {self.case_id}",
                f"Run: {self.run_id}",
                f"Purpose: {purpose}",
                f"Route: ERiC {self.eric_version} / {self.procedure_code} / tax year {self.tax_year}",
                f"Gross wages (EUR): {self.gross_wages_eur}",
                f"Withheld wage tax (EUR): {self.withheld_wage_tax_eur}",
                f"Deductible expenses (EUR): {self.deductible_expenses_eur}",
                f"Official material status: {self.official_material_status.value}",
                f"Envelope: {self.envelope_reference}",
                f"Adapter contract: {self.adapter_contract_reference}",
                self.disclaimer,
            )
        )


def build_synthetic_elster_preview(
    envelope: SyntheticSubmissionEnvelope,
    contract: EricAdapterContract,
    material_decision: EricMaterialProcessDecision,
) -> SyntheticElsterPreview:
    """Build a local preview only after the synthetic material process is complete."""
    if not isinstance(envelope, SyntheticSubmissionEnvelope):
        raise ElsterPreviewError("a SyntheticSubmissionEnvelope is required")
    if not isinstance(contract, EricAdapterContract):
        raise ElsterPreviewError("an EricAdapterContract is required")
    if not isinstance(material_decision, EricMaterialProcessDecision):
        raise ElsterPreviewError("an EricMaterialProcessDecision is required")
    if material_decision.contract_reference != contract.artifact_identity.reference:
        raise ElsterPreviewError("material process and adapter contract binding mismatch")
    if (
        material_decision.outcome
        is not MaterialProcessOutcome.SYNTHETIC_PROCESS_READY_OFFICIAL_STATUS_BLOCKED
        or material_decision.blockers
    ):
        raise ElsterPreviewError("synthetic material process is not complete")
    payload = envelope.payload
    return SyntheticElsterPreview(
        case_id=envelope.case_id,
        run_id=envelope.run_id,
        purpose=envelope.purpose,
        envelope_reference=envelope.artifact_identity.reference,
        adapter_contract_reference=contract.artifact_identity.reference,
        material_process_contract_reference=material_decision.contract_reference,
        tax_year=envelope.tax_year,
        procedure_code=envelope.procedure_code,
        eric_version=envelope.eric_version,
        gross_wages_eur=payload.gross_wages_eur,
        withheld_wage_tax_eur=payload.withheld_wage_tax_eur,
        deductible_expenses_eur=payload.deductible_expenses_eur,
        official_material_status=material_decision.official_status,
    )
