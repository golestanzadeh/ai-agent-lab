"""Synthetic-only ERiC material registration and review-process design."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum

from agent_lab.artifact_identity import ArtifactIdentity, build_artifact_identity
from agent_lab.eric_adapter_contract import (
    ADAPTER_CONTRACT_VERSION,
    EricAdapterContract,
    OfficialMaterialKind,
    OfficialMaterialStatus,
    REQUIRED_OFFICIAL_MATERIALS,
)
from agent_lab.elster_dry_run import (
    SUPPORTED_ERIC_VERSION,
    SUPPORTED_PROCEDURE_CODE,
    SUPPORTED_TAX_YEAR,
)


MATERIAL_RECORD_VERSION = "1"
SYNTHETIC_CLASSIFICATION = "SYNTHETIC"


class EricMaterialProcessError(ValueError):
    """Raised when the package-3 synthetic process boundary is violated."""


class MaterialReviewStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class MaterialProcessOutcome(str, Enum):
    BLOCKED = "BLOCKED"
    SYNTHETIC_PROCESS_READY_OFFICIAL_STATUS_BLOCKED = (
        "SYNTHETIC_PROCESS_READY_OFFICIAL_STATUS_BLOCKED"
    )


def _required(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise EricMaterialProcessError(f"{name} is required")


def _synthetic(name: str, value: str) -> None:
    _required(name, value)
    if not value.startswith("SYNTH-"):
        raise EricMaterialProcessError(f"{name} must use the SYNTH- namespace")


def _aware(name: str, value: datetime) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise EricMaterialProcessError(f"{name} must be timezone-aware")


def _artifact_reference(name: str, value: str) -> None:
    _required(name, value)
    digest = value[7:] if value.startswith("sha256:") else ""
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise EricMaterialProcessError(f"{name} must be a canonical sha256 reference")


@dataclass(frozen=True, slots=True)
class SyntheticEricMaterialRecord:
    material_id: str
    registrant_id: str
    kind: OfficialMaterialKind
    artifact_reference: str
    source_locator: str
    observed_at: datetime
    eric_version: str = SUPPORTED_ERIC_VERSION
    procedure_code: str = SUPPORTED_PROCEDURE_CODE
    tax_year: int = SUPPORTED_TAX_YEAR
    data_classification: str = SYNTHETIC_CLASSIFICATION
    record_version: str = MATERIAL_RECORD_VERSION

    def __post_init__(self) -> None:
        _synthetic("material_id", self.material_id)
        _synthetic("registrant_id", self.registrant_id)
        if not isinstance(self.kind, OfficialMaterialKind):
            raise EricMaterialProcessError("unknown official material kind")
        _artifact_reference("artifact_reference", self.artifact_reference)
        _required("source_locator", self.source_locator)
        if not self.source_locator.startswith("synthetic://"):
            raise EricMaterialProcessError("source_locator must be synthetic and local-only")
        _aware("observed_at", self.observed_at)
        if (
            self.eric_version != SUPPORTED_ERIC_VERSION
            or self.procedure_code != SUPPORTED_PROCEDURE_CODE
            or self.tax_year != SUPPORTED_TAX_YEAR
        ):
            raise EricMaterialProcessError("material route binding mismatch")
        if self.data_classification != SYNTHETIC_CLASSIFICATION:
            raise EricMaterialProcessError("only SYNTHETIC material records are permitted")
        if self.record_version != MATERIAL_RECORD_VERSION:
            raise EricMaterialProcessError("unsupported material record_version")

    @property
    def identity(self) -> ArtifactIdentity:
        payload = asdict(self)
        payload["observed_at"] = self.observed_at.isoformat()
        return build_artifact_identity(
            kind="SYNTHETIC_ERIC_MATERIAL_RECORD",
            version=self.record_version,
            payload=payload,
        )


@dataclass(frozen=True, slots=True)
class SyntheticMaterialReview:
    review_id: str
    reviewer_id: str
    material_id: str
    material_reference: str
    kind: OfficialMaterialKind
    reviewed_at: datetime
    status: MaterialReviewStatus
    review_version: str = MATERIAL_RECORD_VERSION

    def __post_init__(self) -> None:
        _synthetic("review_id", self.review_id)
        _synthetic("reviewer_id", self.reviewer_id)
        _synthetic("material_id", self.material_id)
        _artifact_reference("material_reference", self.material_reference)
        if not isinstance(self.kind, OfficialMaterialKind):
            raise EricMaterialProcessError("unknown review material kind")
        _aware("reviewed_at", self.reviewed_at)
        if not isinstance(self.status, MaterialReviewStatus):
            raise EricMaterialProcessError("unknown material review status")
        if self.review_version != MATERIAL_RECORD_VERSION:
            raise EricMaterialProcessError("unsupported material review_version")

    @property
    def identity(self) -> ArtifactIdentity:
        payload = asdict(self)
        payload["reviewed_at"] = self.reviewed_at.isoformat()
        return build_artifact_identity(
            kind="SYNTHETIC_ERIC_MATERIAL_REVIEW",
            version=self.review_version,
            payload=payload,
        )


@dataclass(frozen=True, slots=True)
class EricMaterialProcessDecision:
    outcome: MaterialProcessOutcome
    contract_reference: str
    material_references: tuple[str, ...]
    review_references: tuple[str, ...]
    blockers: tuple[str, ...]
    official_status: OfficialMaterialStatus = (
        OfficialMaterialStatus.RECOVERED_LOCAL_MAPPING_UNVERIFIED
    )
    official_status_advancement_permitted: bool = False
    protected_material_retrieval_permitted: bool = False
    credential_access: bool = False
    network_calls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _artifact_reference("contract_reference", self.contract_reference)
        for reference in self.material_references:
            _artifact_reference("material_reference", reference)
        for reference in self.review_references:
            _artifact_reference("review_reference", reference)
        if self.official_status is not OfficialMaterialStatus.RECOVERED_LOCAL_MAPPING_UNVERIFIED:
            raise EricMaterialProcessError(
                "official material status must match governed local recovery"
            )
        flags = (
            self.official_status_advancement_permitted,
            self.protected_material_retrieval_permitted,
            self.credential_access,
        )
        if any(value is not False for value in flags):
            raise EricMaterialProcessError("package 3 cannot enable an external capability")
        if self.network_calls != ():
            raise EricMaterialProcessError("package 3 cannot contain network calls")


def evaluate_synthetic_material_process(
    contract: EricAdapterContract,
    records: tuple[SyntheticEricMaterialRecord, ...],
    reviews: tuple[SyntheticMaterialReview, ...],
) -> EricMaterialProcessDecision:
    """Evaluate the inert workflow without reading or retrieving any real material."""
    if not isinstance(contract, EricAdapterContract):
        raise EricMaterialProcessError("an EricAdapterContract is required")
    if contract.contract_version != ADAPTER_CONTRACT_VERSION:
        raise EricMaterialProcessError("adapter contract version mismatch")
    if not isinstance(records, tuple) or not all(
        isinstance(record, SyntheticEricMaterialRecord) for record in records
    ):
        raise EricMaterialProcessError("records must be synthetic material records")
    if not isinstance(reviews, tuple) or not all(
        isinstance(review, SyntheticMaterialReview) for review in reviews
    ):
        raise EricMaterialProcessError("reviews must be synthetic material reviews")

    blockers: list[str] = []
    if len({record.material_id for record in records}) != len(records):
        blockers.append("DUPLICATE_MATERIAL_ID")
    if len({record.kind for record in records}) != len(records):
        blockers.append("DUPLICATE_MATERIAL_KIND")
    if len({review.review_id for review in reviews}) != len(reviews):
        blockers.append("DUPLICATE_REVIEW_ID")

    ordered_records: list[SyntheticEricMaterialRecord] = []
    ordered_reviews: list[SyntheticMaterialReview] = []
    for kind in REQUIRED_OFFICIAL_MATERIALS:
        kind_records = [record for record in records if record.kind is kind]
        if len(kind_records) != 1:
            blockers.append(f"{kind.value}_RECORD_REQUIRED")
            continue
        record = kind_records[0]
        ordered_records.append(record)
        kind_reviews = [review for review in reviews if review.kind is kind]
        if len(kind_reviews) != 1:
            blockers.append(f"{kind.value}_INDEPENDENT_REVIEW_REQUIRED")
            continue
        review = kind_reviews[0]
        ordered_reviews.append(review)
        if review.reviewer_id == record.registrant_id:
            blockers.append(f"{kind.value}_REVIEWER_NOT_INDEPENDENT")
        if review.material_id != record.material_id:
            blockers.append(f"{kind.value}_REVIEW_MATERIAL_ID_MISMATCH")
        if review.material_reference != record.identity.reference:
            blockers.append(f"{kind.value}_REVIEW_BINDING_MISMATCH")
        if review.reviewed_at < record.observed_at:
            blockers.append(f"{kind.value}_REVIEW_PREDATES_REGISTRATION")
        if review.status is not MaterialReviewStatus.APPROVED:
            blockers.append(f"{kind.value}_REVIEW_NOT_APPROVED")

    if len(records) != len(REQUIRED_OFFICIAL_MATERIALS):
        blockers.append("EXACT_MATERIAL_SET_REQUIRED")
    if len(reviews) != len(REQUIRED_OFFICIAL_MATERIALS):
        blockers.append("EXACT_REVIEW_SET_REQUIRED")

    outcome = (
        MaterialProcessOutcome.BLOCKED
        if blockers
        else MaterialProcessOutcome.SYNTHETIC_PROCESS_READY_OFFICIAL_STATUS_BLOCKED
    )
    return EricMaterialProcessDecision(
        outcome=outcome,
        contract_reference=contract.artifact_identity.reference,
        material_references=tuple(record.identity.reference for record in ordered_records),
        review_references=tuple(review.identity.reference for review in ordered_reviews),
        blockers=tuple(blockers),
    )
