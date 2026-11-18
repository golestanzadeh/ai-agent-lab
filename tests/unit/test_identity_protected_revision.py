from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256

import pytest

from agent_lab.identity_evidence_authority import EvidenceScope, IdentityEvidenceError
from agent_lab.identity_protected_revision import (
    MaterializedRevision, ProtectedReference, ProtectedRevision, verify_protected_revision,
)

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
SCOPE = EvidenceScope("TEST-CASE", 2026, "SUBJECT", "FACT", "ACTOR", "RUN", "TASK", "MANIFEST",
                      date(2026, 1, 1), date(2027, 1, 1))
REVISION = ProtectedRevision("test-provider", "ROOT", "OBJECT", "REVISION")
DATA = b"isolated test content"
REFERENCE = ProtectedReference(REVISION, SCOPE, "sha256:" + sha256(DATA).hexdigest(),
                               NOW + timedelta(seconds=1), None)
OBSERVED = MaterializedRevision(REVISION, DATA)


def check(reference=REFERENCE, observed=OBSERVED, **overrides):
    arguments = dict(committed_provider=REVISION.provider, committed_root=REVISION.root_id,
                     expected_scope=SCOPE, now=NOW, max_bytes=len(DATA))
    verify_protected_revision(reference, observed, **(arguments | overrides))


def test_matches_actual_bytes_without_printing_them():
    check()
    assert DATA.decode() not in repr(OBSERVED)


@pytest.mark.parametrize("field", ["provider", "root_id", "object_id", "revision_id"])
def test_rejects_observed_revision_substitution(field):
    with pytest.raises(IdentityEvidenceError, match="revision mismatch"):
        check(observed=replace(OBSERVED, revision=replace(REVISION, **{field: "OTHER"})))


@pytest.mark.parametrize("changes", [dict(case_id="OTHER"), dict(tax_year=2025),
                                     dict(subject_id="OTHER"), dict(manifest_id="OTHER")])
def test_rejects_scope_substitution(changes):
    with pytest.raises(IdentityEvidenceError, match="scope mismatch"):
        check(expected_scope=replace(SCOPE, **changes))


@pytest.mark.parametrize("change", [dict(expires_at=NOW), dict(revoked_at=NOW)])
def test_rejects_expired_or_revoked(change):
    with pytest.raises(IdentityEvidenceError, match="expired or revoked"):
        check(reference=replace(REFERENCE, **change))


def test_rejects_wrong_root_bytes_and_oversize():
    with pytest.raises(IdentityEvidenceError, match="revision mismatch"):
        check(committed_root="OTHER")
    with pytest.raises(IdentityEvidenceError, match="digest mismatch"):
        check(observed=replace(OBSERVED, content=b"x" * len(DATA)))
    with pytest.raises(IdentityEvidenceError, match="size"):
        check(max_bytes=len(DATA) - 1)
