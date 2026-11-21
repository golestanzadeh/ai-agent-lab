"""Inactive, role-private protected source interface for the Identity transaction owner."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, date

from agent_lab.identity_evidence_authority import EvidenceScope
from agent_lab.identity_protected_revision import ProtectedReference, MaterializedRevision, verify_protected_revision


@dataclass(frozen=True)
class EvidenceArtifact:
    reference: str
    kind: str
    accepted: ProtectedReference
    observed: MaterializedRevision = field(repr=False)


@dataclass(frozen=True)
class MaterializedMutation:
    subject_id: str
    authorization_event_id: str
    artifacts: tuple[EvidenceArtifact, ...]


class ProtectedMutationSource(ABC):
    """Bound only by governed Identity startup, never by an IPC request.

    Implementations verify their accepted immutable source and reference authority.
    They may read protected bytes before the writer transaction. They must not
    open/write Identity SQLite or choose a new trust root. No live adapter is
    provided or enabled by this package.
    """
    @abstractmethod
    def resolve(self, request: dict, case, now: datetime) -> MaterializedMutation:
        raise NotImplementedError


def resolve(source, request, case, now):
    if not isinstance(source, ProtectedMutationSource):
        raise PermissionError("governed protected source binding unavailable")
    bundle = source.resolve(request, case, now)
    if not isinstance(bundle, MaterializedMutation) or not bundle.subject_id or not bundle.authorization_event_id:
        raise PermissionError("typed protected materialization required")
    if not 1 <= len(bundle.artifacts) <= 64:
        raise PermissionError("bounded protected sources required")
    references = {}
    for artifact in bundle.artifacts:
        if not isinstance(artifact, EvidenceArtifact) or artifact.reference in references:
            raise PermissionError("ambiguous protected reference")
        scope = artifact.accepted.scope
        expected = EvidenceScope(request["case_id"], int(request["tax_year"]), bundle.subject_id,
                                 scope.semantic_key, request["actor_instance_id"], request["run_id"],
                                 request["task_id"], request["manifest_id"], scope.valid_from, scope.valid_to_exclusive)
        if not date(int(request["tax_year"]),1,1)<=scope.valid_from<scope.valid_to_exclusive<=date(int(request["tax_year"])+1,1,1):
            raise PermissionError("evidence effective interval mismatch")
        verify_protected_revision(artifact.accepted, artifact.observed,
                                  committed_provider=case.storage_scope_reference.provider,
                                  committed_root=case.storage_scope_reference.root_id, expected_scope=expected,
                                  now=now, max_bytes=1024*1024)
        import re
        if not isinstance(artifact.reference, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", artifact.reference):
            raise PermissionError("canonical immutable authority reference required")
        references[artifact.reference] = artifact
    if "subject_id" in request["payload"] and bundle.subject_id != request["payload"]["subject_id"]:
        raise PermissionError("protected mutation subject mismatch")
    for key in ("identity_record_ref","prior_binding_ref","replacement_binding_ref","fact_envelope_ref"):
        if key in request["payload"] and request["payload"][key] not in references:
            raise PermissionError("protected domain content unavailable")
    authorization = request["authorization_references"]
    if len(authorization) != 1 or authorization[0] not in references or references[authorization[0]].kind != "IDENTITY_AUTHORIZATION":
        raise PermissionError("exact authorization evidence required")
    for ref in request["payload"].get("evidence_refs", []):
        if ref not in references:
            raise PermissionError("protected evidence unavailable")
    return bundle, references


@dataclass(frozen=True)
class MutationReferences:
    """Already authenticated reference metadata supplied by role-private startup."""
    subject_id: str
    authorization_event_id: str
    artifacts: tuple[tuple[str, str, ProtectedReference], ...]


@dataclass(frozen=True)
class InactiveSourceBinding:
    deployment_id: str
    store_id: str
    adapter_build_ref: str
    credential_custody_ref: str
    source_scope_digest: str
    configurations: tuple
    allowed_revisions: tuple
    mode: str = "INACTIVE"

    def validate(self):
        from agent_lab.runtime_activation import RuntimeActivationConfiguration
        from agent_lab.ipc_operational_read import digest,text
        from agent_lab.identity_protected_revision import ProtectedRevision
        text(self.deployment_id)
        text(self.store_id)
        for value in (self.adapter_build_ref,self.credential_custody_ref,self.source_scope_digest):
            digest(value)
        if self.mode!="INACTIVE" or type(self.configurations) is not tuple or not 1<=len(self.configurations)<=64:
            raise PermissionError("inactive complete source configuration required")
        scopes=set()
        for config in self.configurations:
            if not isinstance(config,RuntimeActivationConfiguration):
                raise PermissionError("existing typed activation configuration required")
            config.__post_init__()
            key=(config.case_id,config.tax_year,config.run_id)
            if config.deployment_id!=self.deployment_id or key in scopes:
                raise PermissionError("source configuration scope substitution")
            scopes.add(key)
            refs=dict(config.references)
            if any(refs[name] is None for name in ("identity_binding_ref","sqlite_binding_ref","drive_binding_ref",
                    "drive_credential_ref","least_privilege_ref","provider_authorization_ref","privacy_ref","retention_ref","audit_recovery_ref")):
                raise PermissionError("source/custody configuration missing")
            if refs["drive_credential_ref"]!=self.credential_custody_ref:
                raise PermissionError("credential custody substitution")
        if (type(self.allowed_revisions) is not tuple or not 1<=len(self.allowed_revisions)<=64
                or any(not isinstance(item,ProtectedRevision) for item in self.allowed_revisions)
                or len(set(self.allowed_revisions))!=len(self.allowed_revisions)):
            raise PermissionError("exact unique revision allowlist required")
        if self.source_scope_digest!=source_scope_digest(self.configurations,self.allowed_revisions):
            raise PermissionError("source allowlist configuration substitution")
        if self.adapter_build_ref!=adapter_build_digest():
            raise PermissionError("source adapter build substitution")


def adapter_build_digest():
    from pathlib import Path
    from agent_lab.c09_named_pipe import sha256_file
    from agent_lab.ipc_wire_primitives import canonical_sha256
    root=Path(__file__).parent
    return canonical_sha256({name:sha256_file(root/name) for name in ("identity_mutation_source.py","google_drive_storage.py")})


def source_scope_digest(configurations,revisions):
    from dataclasses import asdict
    from agent_lab.ipc_wire_primitives import canonical_sha256
    return canonical_sha256(dict(configurations=sorted(config.digest for config in configurations),
        revisions=sorted((asdict(item) for item in revisions),key=lambda item:(item["provider"],item["root_id"],item["object_id"],item["revision_id"]))))


class InactiveSourceDependencies(ABC):
    """Internal injected ports, never an acceptance grant or live trust root.

    Only synthetic implementations are exercised in Package 2C. A future live
    implementation needs the existing independently accepted binding/custody
    Human Gates. No interactive OAuth or ambient credentials are loaded here.
    """
    @abstractmethod
    def verify_binding(self,binding,configuration,now):
        """Verify current reference-authority and credential ownership/custody, or raise."""
        raise NotImplementedError

    @abstractmethod
    def references(self,request,case,configuration,now) -> MutationReferences:
        raise NotImplementedError

    @abstractmethod
    def drive_service(self,credential_custody_ref):
        """Load the exact noninteractive role-private service, or raise."""
        raise NotImplementedError


class InactiveGoogleDriveMutationSource(ProtectedMutationSource):
    """Concrete exact-revision materializer with no live authority selection."""
    def __init__(self,binding,dependencies):
        if not isinstance(binding,InactiveSourceBinding) or not isinstance(dependencies,InactiveSourceDependencies):
            raise PermissionError("typed inactive role-private dependencies required")
        binding.validate()
        self._binding=binding
        self._dependencies=dependencies
        self._cases=None

    def bind_authority(self,authority,service_configuration):
        from agent_lab.identity_persistence import IdentityPersistence
        from agent_lab.c09_service_host import ServiceRole,ROLE_BINDINGS
        from datetime import timezone
        if not isinstance(authority,IdentityPersistence) or authority._continuity_keys is None:
            raise PermissionError("existing keyed Identity authority required")
        config=service_configuration
        name,sid=ROLE_BINDINGS[ServiceRole.IDENTITY]
        if (config.schema!="ai-tax-agent.c09-service-config/1.0" or config.role is not ServiceRole.IDENTITY or config.principal_sid!=sid or config.service_name!=name
                or config.enabled is not True or config.deployment_id!=self._binding.deployment_id):
            raise PermissionError("exact Identity service binding required")
        logical=authority._logical_row()
        if logical is None or (logical["deployment_id"],logical["store_id"])!=(self._binding.deployment_id,self._binding.store_id):
            raise PermissionError("source deployment/store substitution")
        if authority._mutation_source is not None:
            raise PermissionError("existing source binding cannot be replaced")
        self._binding.validate()
        for configuration in self._binding.configurations:
            case=authority._cases.get(configuration.case_id)
            if case is None or (case.owner_id,case.tax_period.year)!=(configuration.owner_id,configuration.tax_year):
                raise PermissionError("source owner/case/year unavailable")
            self._verify_binding(configuration,datetime.now(timezone.utc))
        self._cases=authority._cases
        authority._mutation_source=self

    def _verify_binding(self,configuration,now):
        try:
            result=self._dependencies.verify_binding(self._binding,configuration,now)
        except Exception:
            raise PermissionError("source authority/custody unavailable") from None
        if result is not None:
            raise PermissionError("acceptance flags are not binding evidence")

    def resolve(self,request,case,now):
        from agent_lab.google_drive_storage import GoogleDriveMetadataAdapter
        from agent_lab.case_scoped_drive import CaseScopedDriveResolver
        if self._cases is None or self._cases.get(case.case_id)!=case:
            raise PermissionError("role-private source is not bound")
        self._binding.validate()
        if request["deployment_id"]!=self._binding.deployment_id:
            raise PermissionError("source deployment mismatch")
        matches=[config for config in self._binding.configurations if (config.owner_id,config.case_id,str(config.tax_year),config.run_id)==
                 (case.owner_id,request["case_id"],request["tax_year"],request["run_id"])]
        if len(matches)!=1:
            raise PermissionError("exact source configuration unavailable")
        configuration=matches[0]
        self._verify_binding(configuration,now)
        try:
            references=self._dependencies.references(request,case,configuration,now)
        except Exception:
            raise PermissionError("authenticated source references unavailable") from None
        if not isinstance(references,MutationReferences) or type(references.artifacts) is not tuple or not 1<=len(references.artifacts)<=64:
            raise PermissionError("closed bounded authenticated references required")
        from agent_lab.ipc_operational_read import digest,text
        text(references.subject_id)
        text(references.authorization_event_id)
        seen=set()
        for reference,kind,accepted in references.artifacts:
            digest(reference)
            if kind not in {"IDENTITY_AUTHORIZATION","IDENTITY_RECORD","ROLE_EVIDENCE","FACT_ENVELOPE","OWNER_DECLARATION","OWNER_CONFIRMATION","IDENTITY_AUDIT"}:
                raise PermissionError("unsupported evidence kind")
            if reference in seen or not isinstance(accepted,ProtectedReference) or accepted.revision not in self._binding.allowed_revisions:
                raise PermissionError("source reference/allowlist mismatch")
            seen.add(reference)
            expected=EvidenceScope(request["case_id"],int(request["tax_year"]),references.subject_id,accepted.scope.semantic_key,
                request["actor_instance_id"],request["run_id"],request["task_id"],request["manifest_id"],accepted.scope.valid_from,accepted.scope.valid_to_exclusive)
            if accepted.scope!=expected or accepted.revoked_at is not None or accepted.expires_at<=now:
                raise PermissionError("source reference scope/lease mismatch")
        by_reference={ref:kind for ref,kind,_ in references.artifacts}
        authorization=request["authorization_references"]
        if len(authorization)!=1 or by_reference.get(authorization[0])!="IDENTITY_AUTHORIZATION":
            raise PermissionError("exact source authorization required")
        if request["payload"].get("subject_id",references.subject_id)!=references.subject_id:
            raise PermissionError("source subject mismatch")
        required=list(request["payload"].get("evidence_refs",[]))
        required.extend(request["payload"][key] for key in ("identity_record_ref","prior_binding_ref","replacement_binding_ref","fact_envelope_ref") if key in request["payload"])
        if any(ref not in seen for ref in required):
            raise PermissionError("required immutable source unavailable")
        try:
            service=self._dependencies.drive_service(self._binding.credential_custody_ref)
        except Exception:
            raise PermissionError("role-private Drive credentials unavailable") from None
        if service is None:
            raise PermissionError("role-private Drive credentials unavailable")
        adapter=GoogleDriveMetadataAdapter(drive_service=service,resolver=CaseScopedDriveResolver(self._cases))
        from agent_lab.google_drive_storage import GoogleDriveStorageError
        from agent_lab.case_scoped_drive import CaseScopeError
        from agent_lab.identity_evidence_authority import IdentityEvidenceError
        from googleapiclient.errors import HttpError
        try:
            artifacts=tuple(EvidenceArtifact(reference,kind,accepted,
                adapter.read_protected_revision(request["case_id"],accepted,now=now)) for reference,kind,accepted in references.artifacts)
        except (GoogleDriveStorageError,CaseScopeError,IdentityEvidenceError,HttpError):
            raise PermissionError("protected source content unavailable or mismatched") from None
        return MaterializedMutation(references.subject_id,references.authorization_event_id,artifacts)
