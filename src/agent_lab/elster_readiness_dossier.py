"""Immutable synthetic Phase P1 readiness dossier with no execution capability."""

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
from agent_lab.elster_preview import SyntheticElsterPreview
from agent_lab.elster_submission_audit import (
    RecoveredLifecycleState,
    SyntheticLifecycleAuditSnapshot,
    SyntheticLifecycleRecovery,
)
from agent_lab.eric_adapter_contract import (
    DENIED_CAPABILITIES,
    MISSING_MATERIAL_BLOCKERS,
    EricAdapterContract,
)
from agent_lab.eric_material_process import (
    EricMaterialProcessDecision,
    MaterialProcessOutcome,
)


DOSSIER_VERSION = "1"
EVIDENCE_KINDS = (
    "SYNTHETIC_ENVELOPE",
    "ADAPTER_CONTRACT",
    "SYNTHETIC_MATERIAL_PROCESS",
    "SYNTHETIC_PREVIEW",
    "SYNTHETIC_LIFECYCLE_AUDIT",
    "SYNTHETIC_LIFECYCLE_RECOVERY",
)
EXTERNAL_READINESS_BLOCKERS = MISSING_MATERIAL_BLOCKERS + (
    "OFFICIAL_XML_MAPPING_NOT_IMPLEMENTED",
    "OFFICIAL_PLAUSIBILITY_VALIDATION_NOT_IMPLEMENTED",
    "CREDENTIALS_AND_CERTIFICATES_NOT_AUTHORIZED",
    "TRANSMITTER_NOT_IMPLEMENTED",
    "REAL_ELSTER_TRANSMISSION_NOT_AUTHORIZED",
)


class ElsterReadinessDossierError(ValueError):
    """Raised when a synthetic readiness dossier is incomplete or unsafe."""


class DossierOutcome(str, Enum):
    SYNTHETIC_DOSSIER_COMPLETE_EXTERNAL_READINESS_BLOCKED = (
        "SYNTHETIC_DOSSIER_COMPLETE_EXTERNAL_READINESS_BLOCKED"
    )


def _required(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ElsterReadinessDossierError(f"{name} is required")


def _synthetic(name: str, value: str) -> None:
    _required(name, value)
    if not value.startswith("SYNTH-"):
        raise ElsterReadinessDossierError(f"{name} must use the SYNTH- namespace")


def _reference(name: str, value: str) -> None:
    _required(name, value)
    digest = value[7:] if value.startswith("sha256:") else ""
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ElsterReadinessDossierError(f"{name} must be a canonical sha256 reference")


@dataclass(frozen=True, slots=True)
class SyntheticDossierEvidence:
    kind: str
    artifact_reference: str

    def __post_init__(self) -> None:
        if self.kind not in EVIDENCE_KINDS:
            raise ElsterReadinessDossierError("unknown dossier evidence kind")
        _reference("artifact_reference", self.artifact_reference)


@dataclass(frozen=True, slots=True)
class SyntheticElsterReadinessDossier:
    case_id: str
    run_id: str
    tax_year: int
    procedure_code: str
    eric_version: str
    lifecycle_state: str
    evidence: tuple[SyntheticDossierEvidence, ...]
    blockers: tuple[str, ...] = EXTERNAL_READINESS_BLOCKERS
    denied_capabilities: tuple[str, ...] = DENIED_CAPABILITIES
    outcome: DossierOutcome = (
        DossierOutcome.SYNTHETIC_DOSSIER_COMPLETE_EXTERNAL_READINESS_BLOCKED
    )
    dossier_version: str = DOSSIER_VERSION
    data_classification: str = "SYNTHETIC"
    contains_tax_values: bool = False
    external_readiness: bool = False
    mapping_permitted: bool = False
    validation_permitted: bool = False
    signing_permitted: bool = False
    transmission_permitted: bool = False
    credential_access: bool = False
    network_calls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _synthetic("case_id", self.case_id)
        _synthetic("run_id", self.run_id)
        if (
            self.tax_year != SUPPORTED_TAX_YEAR
            or self.procedure_code != SUPPORTED_PROCEDURE_CODE
            or self.eric_version != SUPPORTED_ERIC_VERSION
        ):
            raise ElsterReadinessDossierError("dossier route binding mismatch")
        if self.lifecycle_state not in tuple(item.value for item in RecoveredLifecycleState):
            raise ElsterReadinessDossierError("unknown recovered lifecycle state")
        if (
            not isinstance(self.evidence, tuple)
            or not all(isinstance(item, SyntheticDossierEvidence) for item in self.evidence)
            or tuple(item.kind for item in self.evidence) != EVIDENCE_KINDS
        ):
            raise ElsterReadinessDossierError("exact ordered dossier evidence is required")
        if len({item.artifact_reference for item in self.evidence}) != len(self.evidence):
            raise ElsterReadinessDossierError("dossier evidence references must be unique")
        if self.blockers != EXTERNAL_READINESS_BLOCKERS:
            raise ElsterReadinessDossierError("external readiness blockers cannot be weakened")
        if self.denied_capabilities != DENIED_CAPABILITIES:
            raise ElsterReadinessDossierError("denied capability policy cannot be weakened")
        if self.outcome is not DossierOutcome.SYNTHETIC_DOSSIER_COMPLETE_EXTERNAL_READINESS_BLOCKED:
            raise ElsterReadinessDossierError("unsupported dossier outcome")
        if self.dossier_version != DOSSIER_VERSION:
            raise ElsterReadinessDossierError("unsupported dossier_version")
        if self.data_classification != "SYNTHETIC" or self.contains_tax_values is not False:
            raise ElsterReadinessDossierError("dossier privacy boundary cannot be weakened")
        flags = (
            self.external_readiness,
            self.mapping_permitted,
            self.validation_permitted,
            self.signing_permitted,
            self.transmission_permitted,
            self.credential_access,
        )
        if any(value is not False for value in flags):
            raise ElsterReadinessDossierError("dossier cannot enable an external capability")
        if self.network_calls != ():
            raise ElsterReadinessDossierError("dossier cannot contain network calls")

    @property
    def artifact_identity(self) -> ArtifactIdentity:
        return build_artifact_identity(
            kind="SYNTHETIC_ELSTER_READINESS_DOSSIER",
            version=self.dossier_version,
            payload=self,
        )


def _material_process_reference(decision: EricMaterialProcessDecision) -> str:
    return build_artifact_identity(
        kind="SYNTHETIC_ERIC_MATERIAL_PROCESS_DECISION",
        version=DOSSIER_VERSION,
        payload={
            "outcome": decision.outcome.value,
            "contract_reference": decision.contract_reference,
            "material_references": decision.material_references,
            "review_references": decision.review_references,
            "blockers": decision.blockers,
            "official_status": decision.official_status.value,
        },
    ).reference


def _recovery_reference(recovery: SyntheticLifecycleRecovery) -> str:
    return build_artifact_identity(
        kind="SYNTHETIC_ELSTER_LIFECYCLE_RECOVERY",
        version=DOSSIER_VERSION,
        payload={
            "snapshot_reference": recovery.snapshot_reference,
            "case_id": recovery.case_id,
            "run_id": recovery.run_id,
            "idempotency_key": recovery.idempotency_key,
            "state": recovery.state.value,
            "completed_attempts": recovery.completed_attempts,
            "open_attempt_number": recovery.open_attempt_number,
            "receipt_placeholder_reference": recovery.receipt_placeholder_reference,
        },
    ).reference


def build_synthetic_elster_readiness_dossier(
    envelope: SyntheticSubmissionEnvelope,
    contract: EricAdapterContract,
    material_decision: EricMaterialProcessDecision,
    preview: SyntheticElsterPreview,
    audit_snapshot: SyntheticLifecycleAuditSnapshot,
    recovery: SyntheticLifecycleRecovery,
) -> SyntheticElsterReadinessDossier:
    """Aggregate exact synthetic P1 lineage while keeping external readiness blocked."""
    if not isinstance(envelope, SyntheticSubmissionEnvelope):
        raise ElsterReadinessDossierError("a SyntheticSubmissionEnvelope is required")
    if not isinstance(contract, EricAdapterContract):
        raise ElsterReadinessDossierError("an EricAdapterContract is required")
    if not isinstance(material_decision, EricMaterialProcessDecision):
        raise ElsterReadinessDossierError("an EricMaterialProcessDecision is required")
    if not isinstance(preview, SyntheticElsterPreview):
        raise ElsterReadinessDossierError("a SyntheticElsterPreview is required")
    if not isinstance(audit_snapshot, SyntheticLifecycleAuditSnapshot):
        raise ElsterReadinessDossierError("a SyntheticLifecycleAuditSnapshot is required")
    if not isinstance(recovery, SyntheticLifecycleRecovery):
        raise ElsterReadinessDossierError("a SyntheticLifecycleRecovery is required")
    if (
        preview.envelope_reference != envelope.artifact_identity.reference
        or preview.adapter_contract_reference != contract.artifact_identity.reference
        or material_decision.contract_reference != contract.artifact_identity.reference
        or material_decision.outcome
        is not MaterialProcessOutcome.SYNTHETIC_PROCESS_READY_OFFICIAL_STATUS_BLOCKED
        or material_decision.blockers
    ):
        raise ElsterReadinessDossierError("upstream P1 evidence binding mismatch")
    if len(material_decision.material_references) != 3 or len(material_decision.review_references) != 3:
        raise ElsterReadinessDossierError("complete synthetic material evidence is required")
    if (
        audit_snapshot.preview_reference != preview.artifact_identity.reference
        or recovery.snapshot_reference != audit_snapshot.identity.reference
        or (audit_snapshot.case_id, audit_snapshot.run_id)
        != (preview.case_id, preview.run_id)
        or (recovery.case_id, recovery.run_id)
        != (preview.case_id, preview.run_id)
        or recovery.idempotency_key != audit_snapshot.idempotency_key
    ):
        raise ElsterReadinessDossierError("lifecycle evidence binding mismatch")
    evidence = (
        SyntheticDossierEvidence("SYNTHETIC_ENVELOPE", envelope.artifact_identity.reference),
        SyntheticDossierEvidence("ADAPTER_CONTRACT", contract.artifact_identity.reference),
        SyntheticDossierEvidence("SYNTHETIC_MATERIAL_PROCESS", _material_process_reference(material_decision)),
        SyntheticDossierEvidence("SYNTHETIC_PREVIEW", preview.artifact_identity.reference),
        SyntheticDossierEvidence("SYNTHETIC_LIFECYCLE_AUDIT", audit_snapshot.identity.reference),
        SyntheticDossierEvidence("SYNTHETIC_LIFECYCLE_RECOVERY", _recovery_reference(recovery)),
    )
    return SyntheticElsterReadinessDossier(
        case_id=preview.case_id,
        run_id=preview.run_id,
        tax_year=preview.tax_year,
        procedure_code=preview.procedure_code,
        eric_version=preview.eric_version,
        lifecycle_state=recovery.state.value,
        evidence=evidence,
    )
