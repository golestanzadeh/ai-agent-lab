import sqlite3
import pytest

from agent_lab.identity_evidence_authority import DurableIdentityEvidenceAuthority, IdentityEvidenceError


DIGEST = "sha256:" + "a" * 64


def make(tmp_path):
    db = tmp_path / "synthetic.sqlite"
    sqlite3.connect(db).close()
    return DurableIdentityEvidenceAuthority(db), db


def record(authority, event_id, kind, parent=None, case="CASE-SYNTHETIC", digest=DIGEST):
    return authority.append(event_id=event_id, kind=kind, case_id=case,
                            subject_id="synthetic-subject", actor_id="synthetic-owner",
                            reference_id="synthetic-ref", content_digest=digest,
                            parent_event_id=parent)


def test_durable_lifecycle_and_reopen(tmp_path):
    store, db = make(tmp_path)
    record(store, "d1", "OWNER_DECLARATION")
    record(store, "c1", "OWNER_CONFIRMATION", "d1")
    store.close()
    reopened = DurableIdentityEvidenceAuthority(db)
    record(reopened, "a1", "IDENTITY_AUTHORIZATION", "c1")
    with pytest.raises(IdentityEvidenceError):
        record(reopened, "a1", "IDENTITY_AUTHORIZATION", "c1")
    reopened.close()


def test_cross_case_and_mismatched_digest_fail_closed(tmp_path):
    store, _ = make(tmp_path)
    record(store, "d1", "OWNER_DECLARATION")
    with pytest.raises(IdentityEvidenceError):
        record(store, "c1", "OWNER_CONFIRMATION", "d1", case="OTHER")
    with pytest.raises(IdentityEvidenceError):
        record(store, "c2", "OWNER_CONFIRMATION", "d1", digest="sha256:" + "b" * 64)
    with pytest.raises(IdentityEvidenceError):
        record(store, "a1", "IDENTITY_AUTHORIZATION", "d1")
    store.close()
