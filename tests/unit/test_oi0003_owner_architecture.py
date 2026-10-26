from datetime import date
import sqlite3

import pytest

from agent_lab.identity_persistence import (
    IdentityPersistence, SubjectRelationship,
)
from test_identity_persistence import (
    A1, C1, D1, E1, E2, KEY, AUDIT, bind_fact, evidence_resolver,
    fact, open_store, registry, role,
)


IDS = iter(("PERSON-SUCC-" + "A" * 32, "PERSON-SUCC-" + "B" * 32))


def open_owner_store(tmp_path):
    ids = iter(("PERSON-SUCC-" + "A" * 32, "PERSON-SUCC-" + "B" * 32))
    cases = registry()
    store = IdentityPersistence(
        tmp_path / "identity.sqlite", cases=cases, authorize=lambda action, case, root, token: token == A1 and case == "C1" and root == "ROOT1",
        evidence_resolver=evidence_resolver, integrity_key=KEY,
        successor_id_factory=lambda: next(ids),
    )
    return cases, store


def test_successor_ids_are_separate_opaque_authority_allocations_and_idempotent(tmp_path):
    _, store = open_owner_store(tmp_path)
    person_a = store.allocate_successor_person(
        request_id="OWNER-APPROVED-A", case_id="C1", declaration_ref=D1, authorization_ref=A1,
    )
    person_b = store.allocate_successor_person(
        request_id="OWNER-APPROVED-B", case_id="C1", declaration_ref=D1, authorization_ref=A1,
    )
    replay = store.allocate_successor_person(
        request_id="OWNER-APPROVED-A", case_id="C1", declaration_ref=D1, authorization_ref=A1,
    )
    assert person_a.person_id != person_b.person_id
    assert replay.person_id == person_a.person_id
    assert person_a.preferred_display_name is None and person_b.preferred_display_name is None
    assert "CASE" not in person_a.person_id and "2025" not in person_a.person_id
    store.close()


def test_legacy_reference_is_preserved_unmapped_and_tamper_evident(tmp_path):
    cases, store = open_owner_store(tmp_path)
    store.preserve_legacy_reference(
        legacy_reference="CASE-001-OWNER", case_id="C1", evidence_ref=E1, authorization_ref=A1,
    )
    row = store._db.execute("SELECT * FROM legacy_identity_reference").fetchone()
    assert row["status"] == "PRESERVED_UNMAPPED" and row["mapped_subject_id"] is None
    store.close()
    reopened = IdentityPersistence(
        tmp_path / "identity.sqlite", cases=cases,
        authorize=lambda action, case, root, token: token == A1 and case == "C1" and root == "ROOT1",
        evidence_resolver=evidence_resolver, integrity_key=KEY,
    )
    assert reopened._db.execute("SELECT mapped_subject_id FROM legacy_identity_reference").fetchone()[0] is None
    reopened.close()


def test_marriage_relationship_scopes_shared_fact_between_two_case_subjects(tmp_path):
    cases, store = open_owner_store(tmp_path)
    a = store.allocate_successor_person(request_id="A",case_id="C1",declaration_ref=D1,authorization_ref=A1)
    b = store.allocate_successor_person(request_id="B",case_id="C1",declaration_ref=D1,authorization_ref=A1)
    store.bind_party(role(a.person_id,binding="A-ROLE",role_code="OTHER_DEPENDENT_OR_RELEVANT_PERSON",evidence=E1))
    store.bind_party(role(b.person_id,binding="B-ROLE",role_code="OTHER_DEPENDENT_OR_RELEVANT_PERSON",evidence=E2))
    relationship = SubjectRelationship(
        "REL-MARRIAGE-1", "C1", "MARRIAGE", min(a.person_id,b.person_id), max(a.person_id,b.person_id),
        date(2025,1,1), None, E1, A1,
    )
    store.bind_relationship(relationship)
    shared = store.bind_relationship_fact(
        request_id="MARRIAGE-FACT-1",case_id="C1",tax_year=2025,
        relationship_id=relationship.relationship_id,fact=fact(value="synthetic-confirmed-marriage"),
        declaration_artifact_ref=D1,confirmation_ref=C1,
        valid_from=date(2025,1,1),valid_to_exclusive=date(2026,1,1),authorization_ref=A1,
    )
    assert shared.relationship_id == relationship.relationship_id
    store.close()
    reopened=IdentityPersistence(
        tmp_path/"identity.sqlite",cases=cases,
        authorize=lambda action,case,root,token: token==A1 and case=="C1" and root=="ROOT1",
        evidence_resolver=evidence_resolver,integrity_key=KEY,
    )
    assert reopened.read_relationship_facts(case_id="C1",tax_year=2025,relationship_id="REL-MARRIAGE-1",authorization_ref=A1)==(shared,)
    reopened.close()


def test_relationship_rejects_same_subject_wrong_order_and_cross_case(tmp_path):
    _, store = open_owner_store(tmp_path)
    a=store.allocate_successor_person(request_id="A",case_id="C1",declaration_ref=D1,authorization_ref=A1)
    b=store.allocate_successor_person(request_id="B",case_id="C1",declaration_ref=D1,authorization_ref=A1)
    for invalid in (
        SubjectRelationship("R-SAME","C1","MARRIAGE",a.person_id,a.person_id,date(2025,1,1),None,E1,A1),
        SubjectRelationship("R-ORDER","C1","MARRIAGE",max(a.person_id,b.person_id),min(a.person_id,b.person_id),date(2025,1,1),None,E1,A1),
        SubjectRelationship("R-CROSS","C2","MARRIAGE",min(a.person_id,b.person_id),max(a.person_id,b.person_id),date(2025,1,1),None,E1,A1),
    ):
        with pytest.raises((ValueError,PermissionError)):
            store.bind_relationship(invalid)
    store.close()


@pytest.mark.parametrize("table",[
    "successor_identity_allocation","legacy_identity_reference",
    "subject_relationship","relationship_fact_binding",
])
def test_deleted_authority_row_is_rejected_on_restart(tmp_path,table):
    cases,store=open_owner_store(tmp_path)
    a=store.allocate_successor_person(request_id="A",case_id="C1",declaration_ref=D1,authorization_ref=A1)
    b=store.allocate_successor_person(request_id="B",case_id="C1",declaration_ref=D1,authorization_ref=A1)
    store.preserve_legacy_reference(legacy_reference="LEGACY-OWNER",case_id="C1",evidence_ref=E1,authorization_ref=A1)
    for subject,binding in ((a.person_id,"RA"),(b.person_id,"RB")):
        store.bind_party(role(subject,binding=binding,role_code="OTHER_DEPENDENT_OR_RELEVANT_PERSON"))
    store.bind_relationship(SubjectRelationship("REL-1","C1","MARRIAGE",min(a.person_id,b.person_id),max(a.person_id,b.person_id),date(2025,1,1),None,E1,A1))
    store.bind_relationship_fact(request_id="RF1",case_id="C1",tax_year=2025,relationship_id="REL-1",fact=fact(),declaration_artifact_ref=D1,confirmation_ref=C1,valid_from=date(2025,1,1),valid_to_exclusive=date(2026,1,1),authorization_ref=A1)
    store.close()
    with sqlite3.connect(tmp_path/"identity.sqlite") as db:
        db.execute(f"DELETE FROM {table}")
    db.close()
    with pytest.raises(ValueError,match="completeness"):
        IdentityPersistence(tmp_path/"identity.sqlite",cases=cases,authorize=lambda *args:True,evidence_resolver=evidence_resolver,integrity_key=KEY)
    renamed=tmp_path/"quarantined.sqlite"
    (tmp_path/"identity.sqlite").rename(renamed)
    renamed.unlink()


@pytest.mark.parametrize("corruption",["audit","identity"])
def test_rejected_startup_releases_windows_handle(tmp_path,corruption):
    cases,store=open_owner_store(tmp_path)
    store.allocate_successor_person(request_id="A",case_id="C1",declaration_ref=D1,authorization_ref=A1)
    store.close()
    with sqlite3.connect(tmp_path/"identity.sqlite") as db:
        if corruption=="audit": db.execute("UPDATE identity_audit SET event_payload='{}'")
        else: db.execute("UPDATE identity_record SET payload='{}'")
    db.close()
    with pytest.raises(ValueError):
        IdentityPersistence(tmp_path/"identity.sqlite",cases=cases,authorize=lambda *args:True,evidence_resolver=evidence_resolver,integrity_key=KEY)
    renamed=tmp_path/"recovery.sqlite"
    (tmp_path/"identity.sqlite").rename(renamed)
    renamed.unlink()
