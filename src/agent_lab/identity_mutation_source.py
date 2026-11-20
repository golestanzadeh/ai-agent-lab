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
