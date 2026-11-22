"""Real Dashboard HTTP -> Kernel -> native Identity pipe -> canonical SQLite.

All identities, evidence, keys, custody/Witness provider and SIDs are isolated
synthetic fixtures; no production host import or live authority is used.
"""
import asyncio
import json
from datetime import date, timedelta
from hashlib import sha256
import sys
from unittest.mock import patch
from uuid import uuid4

import httpx
import pytest

from agent_lab.family_identity_gateway import FamilyIdentityGateway, FamilyMutationIntent, FamilyScope
from agent_lab.identity_mutation_source import ProtectedMutationSource, MaterializedMutation, EvidenceArtifact
from agent_lab.identity_protected_revision import ProtectedReference, ProtectedRevision, MaterializedRevision
from agent_lab.identity_evidence_authority import EvidenceScope
from agent_lab.ipc_wire_primitives import canonical_json_bytes as C, canonical_sha256 as H
from agent_lab.ui_dashboard import DashboardCase, create_dashboard_app
from test_f07_inactive_runtime import runtime_at
from test_identity_logical_runtime import NOW, cases, store_at
from test_identity_persistence import A1, B1, E2, D1
from test_orchestrator_kernel import task

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="real Windows Identity pipe")
RECORD = "sha256:" + "8" * 64
CORRECTED = "sha256:" + "7" * 64
VALUES = dict(first_name="Synthetic", last_name="Person", birth_date="1990-01-02", tax_id="12345678901", role="SPOUSE_OR_PARTNER")
EDIT = dict(first_name="Corrected", last_name="Person", birth_date="1990-01-02", tax_id="12345678901", person_id="P2")


def record(values, updated=NOW):
    return dict(identity_id="P2", record_type="PERSON", status="ACTIVE",
        name=values["first_name"] + " " + values["last_name"], created_at=NOW.isoformat(), updated_at=updated.isoformat(),
        lookup_attributes=[[key, values[key]] for key in ("first_name", "last_name", "birth_date", "tax_id")], record_schema_version=2)


class SyntheticSource(ProtectedMutationSource):
    def resolve(self, request, case, now):
        artifacts = []
        materials = ((A1, "IDENTITY_AUTHORIZATION", b"synthetic registration approval"),
                     (B1, "IDENTITY_AUTHORIZATION", b"synthetic role approval"),
                     (D1, "IDENTITY_AUTHORIZATION", b"synthetic correction approval"),
                     (E2, "ROLE_EVIDENCE", b"synthetic spouse declaration"),
                     (RECORD, "IDENTITY_RECORD", json.dumps(record(VALUES),ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()),
                     (CORRECTED, "IDENTITY_RECORD", json.dumps(record(EDIT,NOW+timedelta(seconds=1)),ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()))
        for reference, kind, raw in materials:
            revision = ProtectedRevision("private", case.storage_scope_reference.root_id, reference, "1")
            scope = EvidenceScope("C1", 2025, "P2", "synthetic.person",
                request["actor_instance_id"], request["run_id"], request["task_id"], request["manifest_id"], date(2025, 1, 1), date(2026, 1, 1))
            accepted = ProtectedReference(revision, scope, "sha256:" + sha256(raw).hexdigest(), now + timedelta(minutes=1), None)
            artifacts.append(EvidenceArtifact(reference, kind, accepted, MaterializedRevision(revision, raw)))
        return MaterializedMutation("P2", "TEST-FAMILY-AUTH:" + request["authorization_references"][0], tuple(artifacts))


def family_task(**kwargs):
    kwargs["permissions"] = ["identity_create", "identity_read", "identity_update", "case_party_bind"]
    value = task(**kwargs)
    value["budget"]["tool_call_limit"] = 100
    value["inputs"] = [A1, B1, D1, E2, RECORD, CORRECTED]
    return value


def gateway(state):
    def scope(auth=A1):
        return FamilyScope("P1", "C1", 2025, "RUN-RUNTIME-1", "TASK-RUNTIME-1", "MAN-RUNTIME-1", auth, "2025-01-01")

    def resolve(case, year, run, action, values):
        if action == "create" and values == VALUES:
            return (
                FamilyMutationIntent(scope(), "REGISTER_IDENTITY", dict(request_id="TEST-FAMILY-REGISTER", subject_id="P2", identity_record_ref=RECORD, evidence_refs=[RECORD]), "tx:v1:" + str(uuid4()), H(values)),
                FamilyMutationIntent(scope(B1), "BIND_PARTY", dict(request_id="TEST-FAMILY-PARTY", subject_id="P2", party_role="SPOUSE_OR_PARTNER", valid_from="2025-01-01", valid_to_exclusive="", evidence_refs=[E2]), "tx:v1:" + str(uuid4()), H(values)))
        if action == "correct" and values == EDIT:
            return (FamilyMutationIntent(scope(D1), "CORRECT_PERSON", dict(request_id="TEST-FAMILY-CORRECT", subject_id="P2", identity_record_ref=CORRECTED,
                expected_record_digest="sha256:"+sha256(json.dumps(record(VALUES),ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest(), evidence_refs=sorted([CORRECTED, E2])), "tx:v1:" + str(uuid4()), H(values)),)
        raise PermissionError("no matching authenticated fixture declaration")

    return FamilyIdentityGateway(cases=cases(), owner_id="P1", client=state["client"], read_scope=lambda *_: scope(), resolve_intents=resolve)


def app_at(state):
    return create_dashboard_app(read_cases=lambda: (DashboardCase("C1", 2025, "CREATED"),), family_gateway=gateway(state))


QUERY = "?case_id=C1&tax_year=2025&run_id=RUN-RUNTIME-1"
HEADERS = {"Origin": "http://127.0.0.1:8766", "Content-Type": "application/json"}


def test_actual_dashboard_create_correct_refresh_restart(tmp_path):
    with patch("test_f07_inactive_runtime.Sources", SyntheticSource), patch("test_f07_inactive_runtime.task", side_effect=family_task):
        with runtime_at(tmp_path,mutation_source=SyntheticSource(),permissions=["identity_create","identity_read","identity_update","case_party_bind"],inputs=[A1,B1,D1,E2,RECORD,CORRECTED]) as state:
            async def first():
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app_at(state)), base_url="http://127.0.0.1:8766") as browser:
                    for lang, direction in (("fa-IR", "rtl"), ("de-DE", "ltr")):
                        page = await browser.get("/?tab=family&case_id=C1&run_id=RUN-RUNTIME-1&lang=" + lang)
                        assert page.status_code == 200 and 'dir="' + direction + '"' in page.text
                    response = await browser.post("/family/persons" + QUERY, content=C(dict(action="create", values=VALUES)), headers=HEADERS)
                    assert response.status_code == 200, response.text
                    for _ in range(2):
                        response = await browser.get("/family/persons" + QUERY)
                        assert response.status_code == 200, response.text
                        person = next(p for p in response.json()["people"] if p["person_id"] == "P2")
                        assert person["name"] == "Synthetic Person" and person["role"] == "SPOUSE_OR_PARTNER"
                    response = await browser.post("/family/persons" + QUERY, content=C(dict(action="correct", values=EDIT)), headers=HEADERS)
                    assert response.status_code == 200, response.text
                    duplicate = await browser.post("/family/persons" + QUERY, content=C(dict(action="create", values=VALUES)), headers=HEADERS)
                    assert duplicate.status_code == 409
            asyncio.run(first())
            state["restart"]()
            async def restarted():
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app_at(state)), base_url="http://127.0.0.1:8766") as browser:
                    response = await browser.get("/family/persons" + QUERY)
                    assert response.status_code == 200, response.text
                    person = next(p for p in response.json()["people"] if p["person_id"] == "P2")
                    assert person["name"] == "Corrected Person" and person["attributes"]["birth_date"] == "1990-01-02"
                    assert response.json()["relationship_writes_available"] is False
            asyncio.run(restarted())
            authority = store_at(tmp_path / "identity.sqlite")
            try:
                authority._verify_audit_continuity(); authority._verify_data_integrity(); authority._verify_logical_integrity()
                assert authority._db.execute("SELECT COUNT(*) FROM identity_history WHERE identity_id='P2'").fetchone()[0] == 2
                assert authority._db.execute("SELECT COUNT(*) FROM case_party_role WHERE subject_id='P2'").fetchone()[0] == 1
            finally:
                authority.close()


@pytest.mark.parametrize("attack", ["case", "year", "run", "origin", "host", "null", "unapproved", "duplicates", "large"])
def test_dashboard_authorization_and_scope_denial(tmp_path, attack):
    with patch("test_f07_inactive_runtime.Sources", SyntheticSource), patch("test_f07_inactive_runtime.task", side_effect=family_task):
        with runtime_at(tmp_path,mutation_source=SyntheticSource(),permissions=["identity_create","identity_read","identity_update","case_party_bind"],inputs=[A1,B1,D1,E2,RECORD,CORRECTED]) as state:
            async def denied():
                query = QUERY
                headers = dict(HEADERS)
                values = dict(VALUES)
                if attack == "case":query = query.replace("C1", "C2")
                if attack == "year":query = query.replace("2025", "2024")
                if attack == "run":query = query.replace("RUN-RUNTIME-1", "OTHER-RUN")
                if attack == "origin":headers["Origin"] = "https://hostile.invalid"
                if attack == "null":headers["Origin"] = "null"
                if attack == "host":headers["Host"] = "hostile.invalid"
                if attack == "unapproved":values["first_name"] = "Unapproved"
                body = C(dict(action="create", values=values))
                if attack == "duplicates":body = b'{"action":"create","action":"correct","values":{}}'
                if attack == "large":body = b"x" * 8193
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app_at(state)), base_url="http://127.0.0.1:8766") as browser:
                    response = await browser.post("/family/persons" + query, content=body, headers=headers)
                    assert response.status_code in {403, 409, 413}, response.text
            asyncio.run(denied())
            authority = store_at(tmp_path / "identity.sqlite")
            try:assert authority._load_identity("P2") is None
            finally:authority.close()


def test_missing_live_runtime_has_no_preview_or_fallback():
    async def check():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_dashboard_app()), base_url="http://127.0.0.1:8766") as browser:
            response = await browser.get("/family/persons" + QUERY)
            assert response.status_code == 503
    asyncio.run(check())


def test_explicit_lost_read_recovery_is_scoped_and_does_not_redispatch(tmp_path):
    from agent_lab.family_identity_gateway import FamilyReadPending, FamilyUnavailable
    with patch("test_f07_inactive_runtime.task", side_effect=family_task):
        with runtime_at(tmp_path, mutation_source=SyntheticSource(),
                permissions=["identity_create", "identity_read", "identity_update", "case_party_bind"],
                inputs=[A1, B1, D1, E2, RECORD, CORRECTED]) as state:
            g = gateway(state)
            g.mutate("C1", 2025, "RUN-RUNTIME-1", "create", VALUES)
            original = state["client"].read
            def lost(**kwargs):
                original(**kwargs)  # Real native I/O, SQLite and Witness finality.
                raise TimeoutError("synthetic caller lost the released response")
            with patch.object(state["client"], "read", side_effect=lost):
                with pytest.raises(FamilyReadPending) as pending:
                    g.read("C1", 2025, "RUN-RUNTIME-1")
            authority = store_at(tmp_path / "identity.sqlite")
            before = authority._audit_head()
            authority.close()
            result = g.read("C1", 2025, "RUN-RUNTIME-1", recovery=pending.value.transaction_id)
            assert result["people"][0]["person_id"] == "P2"
            authority = store_at(tmp_path / "identity.sqlite")
            assert authority._audit_head() == before
            authority.close()
            for field, value in (("case_id", "C2"), ("tax_year", 2024), ("run_id", "OTHER"), ("manifest_id", "OTHER")):
                arguments = dict(transaction_id=pending.value.transaction_id, case_id="C1", tax_year=2025,
                    run_id="RUN-RUNTIME-1", task_id="TASK-RUNTIME-1", manifest_id="MAN-RUNTIME-1",
                    operation="READ_FAMILY", payload=dict(subject_id="", as_of_date="2025-01-01"), authorization_references=[A1])
                arguments[field] = value
                with pytest.raises(Exception):state["client"].recover_read(**arguments)
            g.mutate("C1", 2025, "RUN-RUNTIME-1", "correct", EDIT)
            with pytest.raises(FamilyUnavailable):
                g.read("C1", 2025, "RUN-RUNTIME-1", recovery=pending.value.transaction_id)


@pytest.mark.parametrize("origin", ["https://127.0.0.1:8766", "http://localhost:8766", "http://127.0.0.1:0", "http://127.0.0.1:65536", "http://remote.invalid:8766"])
def test_configured_origin_is_exact_ipv4_loopback(origin):
    with pytest.raises(ValueError):create_dashboard_app(loopback_origin=origin)


def test_duplicate_tax_identifier_and_stale_correction_preserve_history(tmp_path):
    from dataclasses import replace
    from test_identity_persistence import open_store, person, role
    _, authority = open_store(tmp_path)
    original = replace(person(), lookup_attributes=(("tax_id", "12345678901"),))
    authority.register_identity(case_id="C1", record=original, authorization_ref=A1)
    authority.bind_party(role())
    with pytest.raises(ValueError, match="duplicate authoritative"):
        authority.register_identity(case_id="C1", record=replace(original, person_id="P2"), authorization_ref=A1)
    with pytest.raises(ValueError, match="stale"):
        authority.correct_person(case_id="C1", record=replace(original, updated_at=original.updated_at+timedelta(seconds=1)),
            expected_record_digest="sha256:"+"0"*64, evidence_ref=E2, authorization_ref=A1)
    assert authority._db.execute("SELECT COUNT(*) FROM identity_history").fetchone()[0] == 1
    authority._verify_audit_continuity()
    authority.close()


def test_supported_marriage_readback_restart_and_parent_child_denial(tmp_path):
    from agent_lab.identity_persistence import SubjectRelationship
    from test_identity_persistence import open_store, register, role, E1
    _, authority = open_store(tmp_path)
    register(authority); register(authority, "P2")
    authority.bind_party(role())
    authority.bind_party(role("P2", binding="R2", role_code="SPOUSE_OR_PARTNER", evidence=E2))
    marriage = SubjectRelationship("REL-TEST", "C1", "MARRIAGE", "P1", "P2", date(2025,1,1), None, E1, A1)
    authority.bind_relationship(marriage)
    authority.close()
    _, authority = open_store(tmp_path)
    assert authority.list_relationships("C1", on_date=date(2025,6,1), authorization_ref=A1) == (marriage,)
    from dataclasses import replace
    with pytest.raises(ValueError):authority.bind_relationship(replace(marriage, relationship_id="REL-CHILD", relationship_type="PARENT_CHILD"))
    with pytest.raises(PermissionError):authority.list_relationships("C2", on_date=date(2025,6,1), authorization_ref=A1)
    authority._verify_audit_continuity();authority.close()


def test_family_result_rejects_cross_subject_and_unknown_fields():
    from copy import deepcopy
    from agent_lab.ipc_operational_read import validate_result
    from test_identity_persistence import E1
    request = dict(case_id="C1", tax_year="2025", run_id="RUN-1", domain_operation="READ_FAMILY",
                   payload=dict(subject_id="", as_of_date="2025-01-01"))
    person = dict(person_id="P1", status="ACTIVE", preferred_display_name="Synthetic", created_at="2026-01-01T00:00:01.000000Z",
        updated_at="2026-01-01T00:00:01.000000Z", schema_version="2", lookup_attributes=[])
    party = dict(binding_id="R1", case_id="C1", subject_type="PERSON", subject_id="P1", role="PRIMARY_TAXPAYER",
        valid_from="2025-01-01", valid_to_exclusive="", evidence_ref=E1, authorization_ref=A1)
    result = {key:request[key] for key in ("case_id","tax_year","run_id","domain_operation")}
    result["items"]=[dict(people=[dict(person=person,party=party)],relationships=[])]
    validate_result(result,request)
    for field,value in (("person_id","P2"),("unexpected","x")):
        bad=deepcopy(result);bad["items"][0]["people"][0]["person"][field]=value
        with pytest.raises(ValueError):validate_result(bad,request)


def test_private_intent_mapping_cannot_substitute_different_person_values(tmp_path):
    from dataclasses import replace
    with patch("test_f07_inactive_runtime.task", side_effect=family_task):
        with runtime_at(tmp_path, mutation_source=SyntheticSource(),
                permissions=["identity_create", "identity_read", "identity_update", "case_party_bind"],
                inputs=[A1, B1, D1, E2, RECORD, CORRECTED]) as state:
            g=gateway(state)
            original=g._resolve
            changed={**VALUES,"first_name":"Different"}
            # A buggy private mapper selects a valid, approved but different DTO.
            g._resolve=lambda c,y,r,a,v: tuple(replace(intent,input_digest=H(v)) for intent in original(c,y,r,a,VALUES))
            with pytest.raises(Exception):g.mutate("C1",2025,"RUN-RUNTIME-1","create",changed)
            authority=store_at(tmp_path/"identity.sqlite")
            assert authority._load_identity("P2") is None
            authority._verify_audit_continuity();authority.close()


def test_atomic_correction_preserves_accepted_legacy_person_schema(tmp_path):
    from test_f07_atomic_mutation import Sources, prepare_request, resign, execute, commit_request
    from test_identity_logical_runtime import enrolled
    from test_identity_persistence import E1
    from agent_lab.identity_atomic_mutation import decode_record
    authority,_,logical=enrolled(tmp_path/"identity.sqlite")
    original=authority._identity_payload(authority._load_identity("P1"))
    assert original["record_schema_version"]==1
    replacement={**original,"name":"Legacy Corrected","updated_at":(authority._load_identity("P1").updated_at+timedelta(seconds=1)).isoformat(),
                 "lookup_attributes":[["first_name","Legacy"],["last_name","Corrected"],["birth_date","1990-01-02"]]}
    with pytest.raises(ValueError):decode_record(replacement)  # REGISTER still requires2.
    source=Sources();source.subject="P1"
    source.materials=((A1,"IDENTITY_AUTHORIZATION",b"synthetic legacy correction approval","AUTH"),
                      (E1,"ROLE_EVIDENCE",b"synthetic original case role","ROLE"),
                      (RECORD,"IDENTITY_RECORD",json.dumps(replacement,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode(),"REPLACEMENT"))
    authority._mutation_source=source
    request=prepare_request(logical)
    request.update(domain_operation="CORRECT_PERSON",capability="identity_update",
        payload=dict(request_id="TEST-LEGACY-CORRECTION",subject_id="P1",identity_record_ref=RECORD,
            expected_record_digest="sha256:"+sha256(json.dumps(original,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
            evidence_refs=sorted([RECORD,E1]),owner_input_digest=H(dict(replacement["lookup_attributes"]))))
    request=resign(request)
    assert execute(authority,request)["outcome"]=="PREPARED"
    assert execute(authority,commit_request(authority,request))["outcome"]=="IDENTITY_COMMITTED"
    assert authority._load_identity("P1").schema_version==1
    authority.close()
    reopened=store_at(tmp_path/"identity.sqlite")
    assert reopened._load_identity("P1").preferred_display_name=="Legacy Corrected"
    assert reopened._db.execute("SELECT COUNT(*) FROM identity_history WHERE identity_id='P1'").fetchone()[0]==2
    reopened._verify_data_integrity();reopened._verify_logical_integrity();reopened.close()


@pytest.mark.parametrize("lost",["PREPARE_MUTATION","COMMIT_MUTATION","WITNESS","FINALIZE_MUTATION","BETWEEN_STEPS"])
def test_original_write_workflow_recovers_from_dashboard_after_restart(tmp_path,lost):
    with patch("test_f07_inactive_runtime.task",side_effect=family_task):
        with runtime_at(tmp_path,mutation_source=SyntheticSource(),
                permissions=["identity_create","identity_read","identity_update","case_party_bind"],
                inputs=[A1,B1,D1,E2,RECORD,CORRECTED]) as state:
            native=state["client"].mutation_stage
            reconcile=state["client"].reconcile
            calls=[]
            from agent_lab.c09_pipe_transport import _exchange_canonical as native_exchange
            from agent_lab.ipc_wire_primitives import decode_frame
            def exchange_loss(frame,*args,**kwargs):
                result=native_exchange(frame,*args,**kwargs)
                request=decode_frame(frame)
                if request["domain_operation"]=="BIND_PARTY" and request["message_type"]==lost:
                    raise TimeoutError("synthetic lost native response before Kernel recording")
                return result
            def stage_loss(**kwargs):
                if lost=="BETWEEN_STEPS" and kwargs["operation"]=="BIND_PARTY":raise TimeoutError("synthetic interruption between transactions")
                result=native(**kwargs)
                return result
            def witness_loss(checkpoint):
                result=reconcile(checkpoint);calls.append(checkpoint)
                if lost=="WITNESS" and len(calls)==2:raise TimeoutError("synthetic lost Witness response")
                return result
            async def start():
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app_at(state)),base_url="http://127.0.0.1:8766") as browser:
                    reply=await browser.post("/family/persons"+QUERY,content=C(dict(action="create",values=VALUES)),headers=HEADERS)
                    assert reply.status_code==409,reply.text
                    assert reply.json()["detail"]=="FAMILY_MUTATION_RECONCILIATION_REQUIRED"
                    return reply.json()["workflow_id"]
            with patch.object(state["client"],"mutation_stage",side_effect=stage_loss),patch.object(state["client"],"reconcile",side_effect=witness_loss),patch("agent_lab.c09_pipe_transport._exchange_canonical",side_effect=exchange_loss):
                workflow=asyncio.run(start())
            state["restart"]()
            g=gateway(state);g._resolve=None  # No transient browser intent or mapper survives restart.
            app=create_dashboard_app(read_cases=lambda:(DashboardCase("C1",2025,"CREATED"),),family_gateway=g)
            async def recover():
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://127.0.0.1:8766") as browser:
                    pending=await browser.get("/family/pending"+QUERY)
                    assert pending.status_code==200 and pending.json()["pending"]==[dict(workflow_id=workflow,action="create")]
                    denied=await browser.post("/family/persons/recover"+QUERY.replace("C1","C2"),content=C(dict(workflow_id=workflow)),headers=HEADERS)
                    assert denied.status_code==403
                    reply=await browser.post("/family/persons/recover"+QUERY,content=C(dict(workflow_id=workflow)),headers=HEADERS)
                    assert reply.status_code==200,reply.text
                    assert reply.json()["status"]=="COMMITTED_FINAL"
                    assert (await browser.get("/family/pending"+QUERY)).json()=={"pending":[]}
                    data=await browser.get("/family/persons"+QUERY)
                    assert data.status_code==200,data.text
                    assert data.json()["people"][0]["person_id"]=="P2"
            asyncio.run(recover())
            authority=store_at(tmp_path/"identity.sqlite")
            assert authority._db.execute("SELECT COUNT(*) FROM identity_history WHERE identity_id='P2'").fetchone()[0]==1
            assert authority._db.execute("SELECT COUNT(*) FROM case_party_role WHERE subject_id='P2'").fetchone()[0]==1
            assert authority._logical_row()["epoch"]==2
            authority._verify_audit_continuity();authority.close()
            assert state["kernel"]._identity_payload("identity_kernel_state","deployment_id",state["owner"]["deployment_id"])["active_mutation"] is None
