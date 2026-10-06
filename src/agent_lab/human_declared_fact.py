"""Small immutable contract for owner-declared, case-scoped facts.

This module records provenance and deterministic validation.  It deliberately
does not decide whether a rule permits human declaration instead of documentary
evidence; the consuming rule remains responsible for that legal distinction.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
import re

from agent_lab.artifact_identity import ArtifactIdentity, build_artifact_identity


HUMAN_DECLARED_FACT_VERSION = "1"
SHA_REFERENCE = re.compile(r"^sha256:[0-9a-f]{64}$")


class HumanDeclaredFactError(ValueError):
    """Raised when a fact contract is malformed or cannot be consumed."""


class FactProvenanceKind(str, Enum):
    DOCUMENT = "DOCUMENT"
    FINANCIAL_SOURCE = "FINANCIAL_SOURCE"
    OFFICIAL_SOURCE = "OFFICIAL_SOURCE"
    DERIVED = "DERIVED"
    HUMAN_DECLARATION = "HUMAN_DECLARATION"


class FactConfirmationState(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"


class FactValidationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class FactValueType(str, Enum):
    STRING = "STRING"
    INTEGER = "INTEGER"
    DECIMAL = "DECIMAL"
    DATE = "DATE"
    BOOLEAN = "BOOLEAN"


@dataclass(frozen=True, slots=True)
class HumanFactValidationSpec:
    """Closed deterministic validation instructions for one semantic fact."""

    value_type: FactValueType
    allowed_values: tuple[str, ...] = ()
    pattern: str | None = None
    minimum: str | None = None
    maximum: str | None = None
    date_must_be_within_tax_year: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.value_type, FactValueType):
            raise HumanDeclaredFactError("a supported value type is required")
        if len(set(self.allowed_values)) != len(self.allowed_values):
            raise HumanDeclaredFactError("allowed values must be unique")
        if any(not isinstance(item, str) or not item for item in self.allowed_values):
            raise HumanDeclaredFactError("allowed values must be non-empty strings")
        if self.pattern is not None:
            try:
                re.compile(self.pattern)
            except re.error as exc:
                raise HumanDeclaredFactError("validation pattern is invalid") from exc
        if self.date_must_be_within_tax_year and self.value_type is not FactValueType.DATE:
            raise HumanDeclaredFactError("tax-year consistency is valid only for dates")
        if (self.minimum is not None or self.maximum is not None) and self.value_type not in (
            FactValueType.INTEGER, FactValueType.DECIMAL
        ):
            raise HumanDeclaredFactError("numeric bounds require a numeric value type")
        try:
            lower = Decimal(self.minimum) if self.minimum is not None else None
            upper = Decimal(self.maximum) if self.maximum is not None else None
        except InvalidOperation as exc:
            raise HumanDeclaredFactError("numeric bounds must be exact decimals") from exc
        if ((lower is not None and not lower.is_finite()) or
                (upper is not None and not upper.is_finite())):
            raise HumanDeclaredFactError("numeric bounds must be finite")
        if lower is not None and upper is not None and lower > upper:
            raise HumanDeclaredFactError("minimum cannot exceed maximum")


@dataclass(frozen=True, slots=True)
class HumanFactValidationResult:
    status: FactValidationStatus
    checks: tuple[str, ...]
    errors: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.checks:
            raise HumanDeclaredFactError("at least one validation check is required")
        if self.status is FactValidationStatus.PASS and self.errors:
            raise HumanDeclaredFactError("passing validation cannot contain errors")
        if self.status is FactValidationStatus.FAIL and not self.errors:
            raise HumanDeclaredFactError("failed validation must identify errors")


@dataclass(frozen=True, slots=True)
class HumanDeclaredFact:
    case_id: str
    tax_year: int
    semantic_key: str
    value: str
    declaring_actor_reference: str
    confirmation_state: FactConfirmationState
    declared_at: datetime
    validation: HumanFactValidationResult
    authorization_reference: str
    audit_references: tuple[str, ...]
    consuming_references: tuple[str, ...] = ()
    source_type: FactProvenanceKind = FactProvenanceKind.HUMAN_DECLARATION
    version: str = HUMAN_DECLARED_FACT_VERSION

    def __post_init__(self) -> None:
        for name in ("case_id", "semantic_key", "value", "declaring_actor_reference",
                     "authorization_reference", "version"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise HumanDeclaredFactError(f"{name} is required")
        if self.tax_year < 1900 or self.tax_year > 9999:
            raise HumanDeclaredFactError("tax_year is invalid")
        if self.source_type is not FactProvenanceKind.HUMAN_DECLARATION:
            raise HumanDeclaredFactError("human-declared facts require HUMAN_DECLARATION provenance")
        if not isinstance(self.confirmation_state, FactConfirmationState):
            raise HumanDeclaredFactError("confirmation state is invalid")
        if not isinstance(self.validation, HumanFactValidationResult):
            raise HumanDeclaredFactError("deterministic validation result is required")
        if self.declared_at.tzinfo is None:
            raise HumanDeclaredFactError("declared_at must be timezone-aware")
        if not self.audit_references or any(not ref.strip() for ref in self.audit_references):
            raise HumanDeclaredFactError("audit lineage is required")
        if any(not ref.strip() for ref in self.consuming_references):
            raise HumanDeclaredFactError("consuming references must be non-empty")
        if len(set(self.audit_references)) != len(self.audit_references):
            raise HumanDeclaredFactError("audit references must be unique")
        if len(set(self.consuming_references)) != len(self.consuming_references):
            raise HumanDeclaredFactError("consuming references must be unique")
        if self.version != HUMAN_DECLARED_FACT_VERSION:
            raise HumanDeclaredFactError("unsupported human-declared fact version")

    @property
    def artifact_identity(self) -> ArtifactIdentity:
        return build_artifact_identity(
            kind="HUMAN_DECLARED_CASE_FACT",
            version=self.version,
            payload={
                "case_id": self.case_id,
                "tax_year": self.tax_year,
                "semantic_key": self.semantic_key,
                "value": self.value,
                "declaring_actor_reference": self.declaring_actor_reference,
                "confirmation_state": self.confirmation_state,
                "declared_at": self.declared_at.isoformat(),
                "validation": self.validation,
                "authorization_reference": self.authorization_reference,
                "audit_references": self.audit_references,
                "consuming_references": self.consuming_references,
                "source_type": self.source_type,
                "version": self.version,
            },
        )

    def assert_consumable(self, *, case_id: str, tax_year: int) -> None:
        if self.case_id != case_id or self.tax_year != tax_year:
            raise HumanDeclaredFactError("fact is outside the consuming case/tax-year scope")
        if self.confirmation_state is not FactConfirmationState.CONFIRMED:
            raise HumanDeclaredFactError("fact is not owner-confirmed")
        if self.validation.status is not FactValidationStatus.PASS:
            raise HumanDeclaredFactError("fact failed deterministic validation")


@dataclass(frozen=True, slots=True)
class FactAssertionReference:
    """Minimal immutable reference to an existing fact provenance chain."""

    case_id: str
    tax_year: int
    semantic_key: str
    value: str
    provenance_kind: FactProvenanceKind
    artifact_reference: str
    lineage_references: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.case_id.strip() or not self.semantic_key.strip() or not self.value.strip():
            raise HumanDeclaredFactError("fact assertion scope, key, and value are required")
        if self.tax_year < 1900 or self.tax_year > 9999:
            raise HumanDeclaredFactError("tax_year is invalid")
        if not isinstance(self.provenance_kind, FactProvenanceKind):
            raise HumanDeclaredFactError("fact provenance kind is invalid")
        if not SHA_REFERENCE.fullmatch(self.artifact_reference):
            raise HumanDeclaredFactError("canonical fact artifact reference is required")
        if not self.lineage_references or any(not ref.strip() for ref in self.lineage_references):
            raise HumanDeclaredFactError("fact assertion lineage is required")


@dataclass(frozen=True, slots=True)
class FactConflict:
    case_id: str
    tax_year: int
    semantic_key: str
    existing: FactAssertionReference
    human_declaration_reference: str
    human_declaration_lineage: tuple[str, ...]
    status: str = "FACT_CONFLICT"
    version: str = HUMAN_DECLARED_FACT_VERSION

    def __post_init__(self) -> None:
        if self.status != "FACT_CONFLICT" or self.version != HUMAN_DECLARED_FACT_VERSION:
            raise HumanDeclaredFactError("invalid fact-conflict contract")
        if (self.case_id, self.tax_year, self.semantic_key) != (
            self.existing.case_id, self.existing.tax_year, self.existing.semantic_key
        ):
            raise HumanDeclaredFactError("conflict provenance scope mismatch")
        if not SHA_REFERENCE.fullmatch(self.human_declaration_reference):
            raise HumanDeclaredFactError("canonical human-declaration reference is required")
        if not self.human_declaration_lineage:
            raise HumanDeclaredFactError("human-declaration lineage is required")

    @property
    def artifact_identity(self) -> ArtifactIdentity:
        return build_artifact_identity(kind="CASE_FACT_CONFLICT", version=self.version, payload=self)


def validate_human_fact(value: str, spec: HumanFactValidationSpec, *, tax_year: int) -> HumanFactValidationResult:
    """Validate an assertion without assigning probabilistic confidence."""

    if not isinstance(value, str):
        raise HumanDeclaredFactError("fact value must be a string")
    if not isinstance(spec, HumanFactValidationSpec):
        raise HumanDeclaredFactError("validation spec is required")
    if tax_year < 1900 or tax_year > 9999:
        raise HumanDeclaredFactError("tax_year is invalid")
    errors: list[str] = []
    checks = [f"TYPE:{spec.value_type.value}"]
    parsed: object = value
    try:
        if spec.value_type is FactValueType.STRING:
            if not value.strip():
                raise ValueError
        elif spec.value_type is FactValueType.INTEGER:
            parsed = int(value)
            if str(parsed) != value:
                raise ValueError
        elif spec.value_type is FactValueType.DECIMAL:
            parsed = Decimal(value)
            if not parsed.is_finite():
                raise ValueError
        elif spec.value_type is FactValueType.DATE:
            parsed = date.fromisoformat(value)
        elif spec.value_type is FactValueType.BOOLEAN:
            if value not in ("true", "false"):
                raise ValueError
    except (ValueError, InvalidOperation):
        errors.append("INVALID_TYPE_OR_FORMAT")

    if spec.allowed_values:
        checks.append("ALLOWED_VALUES")
        if value not in spec.allowed_values:
            errors.append("VALUE_NOT_ALLOWED")
    if spec.pattern is not None:
        checks.append("PATTERN")
        if re.fullmatch(spec.pattern, value) is None:
            errors.append("PATTERN_MISMATCH")
    if not errors and spec.value_type in (FactValueType.INTEGER, FactValueType.DECIMAL):
        numeric = Decimal(str(parsed))
        if spec.minimum is not None:
            checks.append("MINIMUM")
            if numeric < Decimal(spec.minimum):
                errors.append("BELOW_MINIMUM")
        if spec.maximum is not None:
            checks.append("MAXIMUM")
            if numeric > Decimal(spec.maximum):
                errors.append("ABOVE_MAXIMUM")
    if not errors and spec.date_must_be_within_tax_year:
        checks.append("TAX_YEAR")
        if not isinstance(parsed, date) or parsed.year != tax_year:
            errors.append("DATE_OUTSIDE_TAX_YEAR")
    return HumanFactValidationResult(
        status=FactValidationStatus.FAIL if errors else FactValidationStatus.PASS,
        checks=tuple(checks), errors=tuple(errors),
    )


def detect_fact_conflict(
    human_fact: HumanDeclaredFact, existing: FactAssertionReference
) -> FactConflict | None:
    """Expose a material value conflict without choosing either provenance."""

    if (human_fact.case_id, human_fact.tax_year, human_fact.semantic_key) != (
        existing.case_id, existing.tax_year, existing.semantic_key
    ):
        raise HumanDeclaredFactError("conflict comparison requires identical fact scope")
    if human_fact.value == existing.value:
        return None
    return FactConflict(
        case_id=human_fact.case_id,
        tax_year=human_fact.tax_year,
        semantic_key=human_fact.semantic_key,
        existing=existing,
        human_declaration_reference=human_fact.artifact_identity.reference,
        human_declaration_lineage=(
            human_fact.authorization_reference,
            *human_fact.audit_references,
        ),
    )
