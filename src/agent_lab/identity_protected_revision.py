"""Check bytes and exact scope for an authenticated protected-source revision.

The Identity transaction owner must load the accepted reference and current
revocation state. This module neither selects a provider nor grants authority.
"""
from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from hmac import compare_digest
import re

from agent_lab.identity_evidence_authority import EvidenceScope, IdentityEvidenceError


@dataclass(frozen=True, slots=True)
class ProtectedRevision:
    provider: str
    root_id: str
    object_id: str
    revision_id: str


@dataclass(frozen=True, slots=True)
class ProtectedReference:
    revision: ProtectedRevision
    scope: EvidenceScope
    content_digest: str
    expires_at: datetime
    revoked_at: datetime | None


@dataclass(frozen=True, slots=True)
class MaterializedRevision:
    revision: ProtectedRevision
    content: bytes = field(repr=False)


def verify_protected_revision(reference: ProtectedReference, observed: MaterializedRevision, *,
                              committed_provider: str, committed_root: str, expected_scope: EvidenceScope,
                              now: datetime, max_bytes: int) -> None:
    """Require matching observed immutable revision and actual bounded bytes."""
    if (not isinstance(reference, ProtectedReference) or not isinstance(observed, MaterializedRevision)
            or not isinstance(reference.revision, ProtectedRevision)
            or not isinstance(reference.scope, EvidenceScope) or not isinstance(expected_scope, EvidenceScope)):
        raise IdentityEvidenceError("typed protected evidence required")
    scope = reference.scope
    if (scope != expected_scope or not 1900 <= scope.tax_year <= 9998
            or not scope.valid_from < scope.valid_to_exclusive):
        raise IdentityEvidenceError("protected evidence scope mismatch")
    revision = reference.revision
    if any(not isinstance(value, str) or not value or len(value.encode("utf-8")) > 256 for value in (
            revision.provider, revision.root_id, revision.object_id, revision.revision_id)):
        raise IdentityEvidenceError("invalid protected revision identity")
    if ((revision.provider, revision.root_id) != (committed_provider, committed_root)
            or observed.revision != revision):
        raise IdentityEvidenceError("protected source revision mismatch")
    if (not isinstance(now, datetime) or now.utcoffset() is None
            or not isinstance(reference.expires_at, datetime) or reference.expires_at.utcoffset() is None
            or reference.expires_at <= now or reference.revoked_at is not None):
        raise IdentityEvidenceError("protected evidence expired or revoked")
    if (type(max_bytes) is not int or max_bytes <= 0 or type(observed.content) is not bytes
            or not 0 < len(observed.content) <= max_bytes):
        raise IdentityEvidenceError("invalid protected content size")
    expected_digest = reference.content_digest
    if (not isinstance(expected_digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", expected_digest)
            or not compare_digest("sha256:" + sha256(observed.content).hexdigest(), expected_digest)):
        raise IdentityEvidenceError("protected content digest mismatch")
