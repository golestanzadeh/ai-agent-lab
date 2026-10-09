import hashlib, sqlite3
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
import pytest
from agent_lab.identity_evidence_authority import DurableIdentityEvidenceAuthority, EvidenceScope, IdentityEvidenceError

KEY=b"k"*32; CONTENT=b"synthetic protected bytes"; DIGEST="sha256:"+hashlib.sha256(CONTENT).hexdigest()

def scope(**changes):
    value=EvidenceScope("CASE-SYNTHETIC",2025,"SUBJECT-SYNTHETIC","church_tax","OWNER-SYNTHETIC","RUN-SYNTHETIC","TASK-SYNTHETIC","MAN-SYNTHETIC",date(2025,1,1),date(2026,1,1))
    return replace(value,**changes)

def make(tmp_path):
    db=tmp_path/"identity.sqlite"; sqlite3.connect(db).close(); return DurableIdentityEvidenceAuthority(db,integrity_key=KEY),db

def append_chain(store,*,expiry=None):
    common=dict(scope=scope(),provider="SYNTHETIC_PROTECTED",object_id="OBJ-1",document_revision="REV-1",content_digest=DIGEST)
    store.append(event_id="D1",kind="OWNER_DECLARATION",**common)
    store.append(event_id="C1",kind="OWNER_CONFIRMATION",parent_event_id="D1",**common)
    store.append(event_id="A1",kind="IDENTITY_AUTHORIZATION",parent_event_id="C1",expires_at=expiry,**common)

def loader(case,provider,obj,revision):
    assert (case,provider,obj,revision)==("CASE-SYNTHETIC","SYNTHETIC_PROTECTED","OBJ-1","REV-1"); return CONTENT

def test_restart_resolves_complete_chain_and_consumes_once(tmp_path):
    store,db=make(tmp_path); append_chain(store,expiry=datetime.now(timezone.utc)+timedelta(hours=1)); store.close()
    reopened=DurableIdentityEvidenceAuthority(db,integrity_key=KEY)
    assert reopened.resolve("A1",content_loader=loader,expected_scope=scope()).kind=="IDENTITY_AUTHORIZATION"
    reopened.consume_authorization("A1")
    with pytest.raises(IdentityEvidenceError,match="consumed"): reopened.resolve("A1",content_loader=loader,expected_scope=scope())
    reopened.close()

@pytest.mark.parametrize("changed",[{"case_id":"OTHER"},{"tax_year":2024},{"subject_id":"OTHER"},{"semantic_key":"other"},{"document_revision":"REV-2"}])
def test_exact_scope_and_revision_binding(tmp_path,changed):
    store,_=make(tmp_path); append_chain(store)
    if "document_revision" in changed:
        with pytest.raises(IdentityEvidenceError): store.resolve("A1",content_loader=lambda *a: (_ for _ in ()).throw(IdentityEvidenceError("revision unavailable")),expected_scope=scope())
    else:
        with pytest.raises(IdentityEvidenceError,match="scope mismatch"): store.resolve("A1",content_loader=loader,expected_scope=scope(**changed))
    store.close()

def test_missing_mismatched_revoked_expired_and_tampered_fail(tmp_path):
    store,db=make(tmp_path); append_chain(store)
    with pytest.raises(IdentityEvidenceError,match="digest mismatch"): store.resolve("A1",content_loader=lambda *a:b"changed",expected_scope=scope())
    store.revoke("C1",actor_id="OWNER-SYNTHETIC")
    with pytest.raises(IdentityEvidenceError,match="revoked"): store.resolve("A1",content_loader=loader,expected_scope=scope())
    store.close()
    raw=sqlite3.connect(db); raw.execute("UPDATE identity_evidence_v2 SET actor_id='ATTACKER' WHERE event_id='D1'"); raw.commit(); raw.close()
    with pytest.raises(IdentityEvidenceError,match="integrity"): DurableIdentityEvidenceAuthority(db,integrity_key=KEY)

def test_expired_authorization_and_wrong_key_fail(tmp_path):
    store,db=make(tmp_path); append_chain(store,expiry=datetime.now(timezone.utc)-timedelta(seconds=1)); store.close()
    reopened=DurableIdentityEvidenceAuthority(db,integrity_key=KEY)
    with pytest.raises(IdentityEvidenceError,match="expired"): reopened.resolve("A1",content_loader=loader,expected_scope=scope())
    reopened.close()
    with pytest.raises(IdentityEvidenceError,match="integrity"): DurableIdentityEvidenceAuthority(db,integrity_key=b"z"*32)
