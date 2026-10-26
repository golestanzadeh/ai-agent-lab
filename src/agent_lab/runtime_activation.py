"""Governed activation preparation. This evaluator never grants execution."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
from typing import Mapping


class ReadinessStatus(str,Enum):
    READY="READY"
    CONFIGURATION_MISSING="CONFIGURATION_MISSING"
    AUTHORITY_MISSING="AUTHORITY_MISSING"
    SECURITY_GATE_BLOCKED="SECURITY_GATE_BLOCKED"
    RECONCILIATION_REQUIRED="RECONCILIATION_REQUIRED"


@dataclass(frozen=True,slots=True)
class OperationGate:
    operation: str
    authority: str
    controls: tuple[str,...]
    evidence: tuple[str,...]
    configuration: tuple[str,...]
    independent_activation: bool


_IDENTITY=("C03","C04","C05","C06","C07","C08","C09","C10","C11","C12","C13")
_PROVIDER=("RUNTIME_BINDING","LEAST_PRIVILEGE","PRIVACY","RETENTION","CASE_ISOLATION")
GATES=(
    OperationGate("protected_case_creation","KERNEL_AND_OWNER_RUNTIME_APPROVAL",_IDENTITY+("OI-0003",),("independent-operational-identity-pass","case-creation-recovery-pass"),("identity_binding_ref","sqlite_binding_ref","audit_recovery_ref"),False),
    OperationGate("protected_identity_registration","KERNEL_IDENTITY_CREATE",_IDENTITY,("independent-operational-identity-pass","subject-declaration-binding"),("identity_binding_ref","sqlite_binding_ref","audit_recovery_ref"),True),
    OperationGate("drive_provisioning","KERNEL_AND_OWNER_PROVIDER_BINDING",_IDENTITY+_PROVIDER,("provider-binding-independent-pass","provisioning-reconciliation-pass"),("drive_credential_ref","drive_binding_ref","least_privilege_ref","privacy_ref","retention_ref","audit_recovery_ref"),False),
    OperationGate("document_ingestion","KERNEL_CASE_DOCUMENT_AUTHORITY",_IDENTITY+_PROVIDER,("document-isolation-version-lineage-pass",),("drive_binding_ref","provider_authorization_ref","privacy_ref","retention_ref"),False),
    OperationGate("gemini_extraction","KERNEL_AND_OWNER_PROVIDER_BINDING",_IDENTITY+_PROVIDER,("provider-privacy-retention-pass","document-attribution-pass"),("provider_authorization_ref","privacy_ref","retention_ref"),False),
    OperationGate("csv_ingestion","KERNEL_CASE_PROCESSING_AUTHORITY",_IDENTITY+("CASE_ISOLATION",),("case-run-ledger-lineage-pass",),("sqlite_binding_ref","provider_authorization_ref","audit_recovery_ref"),True),
    OperationGate("approval","HUMAN_PROJECT_OWNER",("CONTENT_RELEASE_APPROVAL",),("exact-immutable-artifact-release-approval",),("provider_authorization_ref",),False),
    OperationGate("submission","HUMAN_PROJECT_OWNER",("CONTENT_RELEASE_APPROVAL","DESTINATION_TRANSMISSION_APPROVAL"),("separate-artifact-and-destination-approvals",),("provider_authorization_ref",),False),
)
_REF=re.compile(r"sha256:[0-9a-f]{64}")
CONFIG_FIELDS=frozenset({"identity_binding_ref","sqlite_binding_ref","drive_credential_ref","drive_binding_ref","provider_authorization_ref","least_privilege_ref","privacy_ref","retention_ref","audit_recovery_ref"})


@dataclass(frozen=True,slots=True)
class RuntimeActivationConfiguration:
    deployment_id: str
    owner_id: str
    case_id: str
    tax_year: int
    run_id: str
    references: tuple[tuple[str,str|None],...]
    digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.references,tuple) or any(not isinstance(item,tuple) or len(item)!=2 for item in self.references):
            raise ValueError("immutable closed configuration references are required")
        refs=dict(self.references)
        if len(refs)!=len(self.references): raise ValueError("duplicate configuration reference")
        payload={"schema":"ai-tax-agent.runtime-activation-preparation/1.0",
                 "deployment_id":self.deployment_id,"owner_id":self.owner_id,
                 "case_id":self.case_id,"tax_year":self.tax_year,"run_id":self.run_id,
                 "references":refs}
        expected=self._validate_payload(payload)
        if self.digest!=expected: raise ValueError("activation configuration digest mismatch")

    @classmethod
    def parse(cls,payload: dict) -> "RuntimeActivationConfiguration":
        digest=cls._validate_payload(payload)
        return cls(payload["deployment_id"],payload["owner_id"],payload["case_id"],payload["tax_year"],payload["run_id"],tuple(sorted(payload["references"].items())),digest)

    @staticmethod
    def _validate_payload(payload: dict) -> str:
        fields={"schema","deployment_id","owner_id","case_id","tax_year","run_id","references"}
        if not isinstance(payload,dict) or set(payload)!=fields or payload["schema"]!="ai-tax-agent.runtime-activation-preparation/1.0":
            raise ValueError("activation configuration schema mismatch")
        for field in ("deployment_id","owner_id","case_id","run_id"):
            if not isinstance(payload[field],str) or not payload[field].strip() or len(payload[field].encode())>128:
                raise ValueError("invalid activation configuration identity")
        if type(payload["tax_year"]) is not int or not 1900<=payload["tax_year"]<=9998:
            raise ValueError("invalid activation configuration year")
        refs=payload["references"]
        if not isinstance(refs,dict) or set(refs)!=CONFIG_FIELDS:
            raise ValueError("closed non-secret configuration references are required")
        if any(value is not None and (not isinstance(value,str) or _REF.fullmatch(value) is None) for value in refs.values()):
            raise ValueError("configuration accepts immutable references only, never credentials")
        canonical=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
        return "sha256:"+hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True,slots=True)
class CapabilityReadiness:
    operation: str
    status: ReadinessStatus
    reasons: tuple[str,...]
    executable: bool=False


def assess_runtime_readiness(runtime, configuration: RuntimeActivationConfiguration|None,
                             *, case_id: str, tax_year: int, run_id: str,
                             authority_references: Mapping[str,str]|None=None) -> tuple[CapabilityReadiness,...]:
    """Read existing authorities only; references are claims, not acceptance proof.

    Operational service composition is absent in c09_service_host. Therefore
    no protected capability can become READY or executable in this version.
    """
    projection=runtime.read_case(case_id,tax_year)
    runtime.verify_run_reference(case_id,tax_year,run_id)
    if configuration is not None:
        if not isinstance(configuration,RuntimeActivationConfiguration):
            raise ValueError("validated runtime activation configuration is required")
        configuration.__post_init__()
        runtime.verify_activation_scope(configuration.owner_id,configuration.case_id,configuration.tax_year,configuration.run_id,case_id,tax_year,run_id)
    authorities=dict(authority_references or {})
    if set(authorities)-{gate.operation for gate in GATES}: raise ValueError("unknown authority operation")
    if any(not isinstance(value,str) or _REF.fullmatch(value) is None for value in authorities.values()): raise ValueError("authority references must be immutable references")
    results=[CapabilityReadiness("read_only_case_navigation",ReadinessStatus.READY,("VERIFIED_COMMITTED_CASE_RUN",),False)]
    refs=dict(configuration.references) if configuration is not None else {}
    reconciliation=runtime.storage_requires_reconciliation(case_id,tax_year)
    for gate in GATES:
        missing=tuple(field for field in gate.configuration if refs.get(field) is None)
        if reconciliation:
            status=ReadinessStatus.RECONCILIATION_REQUIRED; reasons=("PROVISIONING_RECONCILIATION_REQUIRED",)
        elif configuration is None or missing:
            status=ReadinessStatus.CONFIGURATION_MISSING; reasons=missing or ("EXACT_RUNTIME_CONFIGURATION",)
        elif gate.operation not in authorities:
            status=ReadinessStatus.AUTHORITY_MISSING; reasons=(gate.authority,)
        else:
            status=ReadinessStatus.SECURITY_GATE_BLOCKED
            reasons=("OPERATIONAL_SERVICE_CLIENT_NOT_IMPLEMENTED","INDEPENDENT_OPERATIONAL_ACCEPTANCE_REQUIRED")+gate.controls
        results.append(CapabilityReadiness(gate.operation,status,reasons,False))
    return tuple(results)
