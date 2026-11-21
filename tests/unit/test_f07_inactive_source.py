"""Inactive source/custody composition with real Drive download code and synthetic HTTP."""
from dataclasses import replace
from datetime import date,datetime,timedelta,timezone
from hashlib import sha256
from types import SimpleNamespace
from unittest.mock import patch
import json

import httplib2
import pytest

from agent_lab.identity_mutation_source import (
    InactiveSourceBinding,InactiveSourceDependencies,InactiveGoogleDriveMutationSource,
    MutationReferences,adapter_build_digest,source_scope_digest,
)
from agent_lab.identity_protected_revision import ProtectedReference,ProtectedRevision
from agent_lab.identity_evidence_authority import EvidenceScope
from agent_lab.runtime_activation import RuntimeActivationConfiguration,CONFIG_FIELDS
from agent_lab.identity_persistence import IdentityPersistence
from agent_lab.case_registry import StorageScopeReference
from agent_lab.google_drive_storage import GoogleDriveMetadataAdapter
from agent_lab.case_scoped_drive import CaseScopedDriveResolver
from test_identity_logical_runtime import cases,PINS
from test_identity_persistence import KEY,A1,authorizer,evidence_resolver


class Result:
    def __init__(self,value):self.value=value
    def execute(self,**kwargs):return self.value


class Drive:
    """Exact Drive API/HTTP surface; no network or real credentials."""
    def __init__(self):
        self.data={"AUTH":b"synthetic owner authority","RECORD":json.dumps(dict(identity_id="P2",record_type="PERSON",status="ACTIVE",name=None,
            created_at="2026-01-01T00:00:00+00:00",updated_at="2026-01-01T00:00:00+00:00",record_schema_version=2,lookup_attributes=[]),sort_keys=True,separators=(",",":")).encode()}
        self.calls=[]
        self.attack=None
    def files(self):return self
    def revisions(self):return self
    def get(self,**kwargs):
        self.calls.append(("get",kwargs))
        obj=kwargs["fileId"]
        if "revisionId" in kwargs:
            return Result(dict(id="OTHER" if self.attack=="revision" else "1",mimeType="application/json",
                size=str(2**21 if self.attack=="size" else len(self.data[obj]))))
        return Result(dict(id="OTHER" if self.attack=="object" else obj,parents=["WRONG" if self.attack=="root" else "ROOT1"],trashed=False,version="1"))
    def get_media(self,**kwargs):
        self.calls.append(("media",kwargs))
        return SimpleNamespace(uri="https://synthetic.invalid/"+kwargs["fileId"],headers={},http=self)
    def request(self,uri,method,headers):
        self.calls.append(("http",dict(uri=uri,method=method,headers=headers)))
        data=self.data[uri.rsplit("/",1)[-1]]
        if self.attack=="content":data=b"altered bytes"
        if self.attack=="truncated":data=data[:-1]
        if self.attack=="no_progress":data=b""
        response=httplib2.Response(dict(status="200",**{"content-length":str(len(data))}))
        if self.attack=="redirect":response["content-location"]="https://unapproved.invalid/"
        return response,data


def drive_cases():
    from agent_lab.case_registry import CaseRegistry
    registry=CaseRegistry()
    for case in cases().all_records():
        registry.register(replace(case,storage_scope_reference=StorageScopeReference("google_drive",case.storage_scope_reference.root_id)))
    return registry


def drive_store(path,*,fault=None):
    return IdentityPersistence(path,cases=drive_cases(),authorize=authorizer,evidence_resolver=evidence_resolver,integrity_key=KEY,continuity_keys=PINS,fault_injector=fault)


def configuration():
    refs={key:"sha256:"+"a"*64 for key in CONFIG_FIELDS}
    return RuntimeActivationConfiguration.parse(dict(schema="ai-tax-agent.runtime-activation-preparation/1.0",deployment_id="TEST-DEPLOYMENT",
        owner_id="P1",case_id="C1",tax_year=2025,run_id="RUN-RUNTIME-1",references=refs))


def binding():
    configs=(configuration(),)
    revisions=tuple(ProtectedRevision("google_drive","ROOT1",obj,"1") for obj in ("AUTH","RECORD"))
    return InactiveSourceBinding("TEST-DEPLOYMENT","TEST-STORE",adapter_build_digest(),"sha256:"+"a"*64,
        source_scope_digest(configs,revisions),configs,revisions)


class Dependencies(InactiveSourceDependencies):
    def __init__(self):
        self.drive=Drive()
        self.revoked=False
        self.missing_credentials=False
        self.reference_attack=None
        self.credential_calls=0
    def verify_binding(self,value,config,now):
        if self.revoked:raise PermissionError("synthetic revoked custody")
        assert value.mode=="INACTIVE" and config==configuration()
    def references(self,request,case,config,now):
        scope=EvidenceScope("C1",2025,"P2","identity.registration",request["actor_instance_id"],request["run_id"],request["task_id"],request["manifest_id"],date(2025,1,1),date(2026,1,1))
        if self.reference_attack=="scope":scope=replace(scope,case_id="C2")
        records=[]
        for ref,kind,obj in ((A1,"IDENTITY_AUTHORIZATION","AUTH"),("sha256:"+"8"*64,"IDENTITY_RECORD","RECORD")):
            revision=ProtectedRevision("google_drive","ROOT1",obj,"1")
            if self.reference_attack=="allowlist":revision=replace(revision,object_id="UNAUTHORIZED")
            expires=now-timedelta(seconds=1) if self.reference_attack=="expired" else now+timedelta(minutes=1)
            accepted=ProtectedReference(revision,scope,"sha256:"+sha256(self.drive.data[obj]).hexdigest(),expires,now if self.reference_attack=="revoked" else None)
            records.append((ref,kind,accepted))
        return MutationReferences("P2","TEST-AUTHORIZATION-1",tuple(records))
    def drive_service(self,reference):
        self.credential_calls+=1
        assert reference=="sha256:"+"a"*64
        if self.missing_credentials:raise RuntimeError("TEST-SECRET-MUST-NOT-LEAK")
        return self.drive


def request():
    return dict(deployment_id="TEST-DEPLOYMENT",case_id="C1",tax_year="2025",run_id="RUN-RUNTIME-1",actor_instance_id="TEST-ACTOR",
        task_id="TEST-TASK",manifest_id="TEST-MANIFEST",authorization_references=[A1],payload=dict(subject_id="P2",identity_record_ref="sha256:"+"8"*64,evidence_refs=["sha256:"+"8"*64]))


def bound(tmp_path,dependencies=None):
    from test_identity_logical_runtime import owner_artifact,NOW
    from test_c09_operational_service_runtime import configuration as service_configuration
    authority=drive_store(tmp_path/"identity.sqlite")
    authority.enroll_logical_identity(owner_artifact(authority),now=NOW)
    ports=dependencies or Dependencies()
    source=InactiveGoogleDriveMutationSource(binding(),ports)
    source.bind_authority(authority,service_configuration())
    return authority,source,ports


def test_exact_revision_bytes_and_scope(tmp_path):
    authority,source,ports=bound(tmp_path)
    try:
        from agent_lab.identity_mutation_source import resolve
        material,refs=resolve(source,request(),authority._cases.get("C1"),datetime.now(timezone.utc))
        assert material.subject_id=="P2" and len(refs)==2
        assert refs["sha256:"+"8"*64].observed.content==ports.drive.data["RECORD"]
        assert all(kwargs["revisionId"]=="1" for method,kwargs in ports.drive.calls if method=="media")
        assert all(method!="list" for method,_ in ports.drive.calls)
    finally:authority.close()


@pytest.mark.parametrize("attack",["revision","size","object","root","content","truncated","redirect","no_progress"])
def test_drive_revision_failures(tmp_path,attack):
    authority,source,ports=bound(tmp_path)
    ports.drive.attack=attack
    try:
        with pytest.raises(Exception):source.resolve(request(),authority._cases.get("C1"),datetime.now(timezone.utc))
        assert authority._load_identity("P2") is None
    finally:authority.close()


@pytest.mark.parametrize("attack",["scope","allowlist","expired","revoked"])
def test_bad_reference_denied_before_credentials(tmp_path,attack):
    authority,source,ports=bound(tmp_path)
    ports.reference_attack=attack
    try:
        with pytest.raises(PermissionError):source.resolve(request(),authority._cases.get("C1"),datetime.now(timezone.utc))
        assert ports.credential_calls==0 and ports.drive.calls==[]
    finally:authority.close()


@pytest.mark.parametrize("attack",["credentials","custody"])
def test_custody_failure_does_not_expose_secret_or_read_content(tmp_path,attack):
    authority,source,ports=bound(tmp_path)
    ports.missing_credentials=attack=="credentials"
    ports.revoked=attack=="custody"
    try:
        with pytest.raises(PermissionError) as error:source.resolve(request(),authority._cases.get("C1"),datetime.now(timezone.utc))
        assert "TEST-SECRET" not in str(error.value) and error.value.__cause__ is None
        assert ports.drive.calls==[]
    finally:authority.close()


@pytest.mark.parametrize("field,value",[("mode","LIVE"),("adapter_build_ref","sha256:"+"0"*64),("source_scope_digest","sha256:"+"0"*64),("credential_custody_ref","sha256:"+"1"*64)])
def test_closed_inactive_binding_rejects_substitution(field,value):
    with pytest.raises((PermissionError,ValueError)):
        InactiveGoogleDriveMutationSource(replace(binding(),**{field:value}),Dependencies())


def test_factory_and_native_commit_recovery(tmp_path):
    from test_f07_inactive_runtime import runtime_at,stage
    from agent_lab.identity_logical_continuity import H
    ports=Dependencies()
    source=InactiveGoogleDriveMutationSource(binding(),ports)
    with patch("test_kernel_identity_operational.store_at",side_effect=drive_store),patch("test_f07_inactive_runtime.store_at",side_effect=drive_store):
        with runtime_at(tmp_path,source=False,protected_source=source) as state:
            assert stage(state,"PREPARE_MUTATION")["outcome"]=="PREPARED"
            committed=stage(state,"COMMIT_MUTATION")
            assert committed["outcome"]=="IDENTITY_COMMITTED"
            state["restart"]()
            original=state["kernel"]._identity_payload("identity_kernel_state","deployment_id","TEST-DEPLOYMENT")["mutations"][state["arguments"]["transaction_id"]]["prepare_request"]["request_digest"]
            recovered=stage(state,"GET_TRANSACTION",dict(original_request_digest=original))
            assert recovered["result"]==committed["result"]
            pending=state["client"].reconcile("MUTATION:"+state["arguments"]["transaction_id"])
            receipt=pending["receipt"];verified=pending["custodian_verification"]["response"]
            final=dict(staged_receipt_digest=H(receipt),witness_object_key=pending["object_key"],witness_generation=pending["generation"],
                witness_preimage_digest=receipt["witness_preimage_digest"],signed_record_digest=verified["signed_record_digest"],custodian_verification_digest=H(verified),custodian_nonce=verified["nonce"])
            assert stage(state,"FINALIZE_MUTATION",final)["outcome"]=="COMMITTED_FINAL"
            assert len(state["session"].objects)==2


@pytest.mark.parametrize("failure",["custody","keys","store","role"])
def test_factory_fails_closed_before_source_access(tmp_path,failure):
    from test_identity_logical_runtime import owner_artifact,NOW
    from test_c09_operational_service_runtime import configuration as service_configuration
    from agent_lab.c09_operational_service_runtime import create_identity_service_host
    from agent_lab.c09_service_host import ServiceRole,ROLE_BINDINGS
    authority=drive_store(tmp_path/"identity.sqlite")
    authority.enroll_logical_identity(owner_artifact(authority),now=NOW)
    ports=Dependencies()
    ports.revoked=failure=="custody"
    config=service_configuration()
    value=binding()
    if failure=="keys":authority._continuity_keys=None
    if failure=="store":value=replace(value,store_id="WRONG-STORE")
    if failure=="role":
        name,sid=ROLE_BINDINGS[ServiceRole.KEY_CUSTODIAN]
        config=replace(config,role=ServiceRole.KEY_CUSTODIAN,service_name=name,principal_sid=sid)
    source=InactiveGoogleDriveMutationSource(value,ports)
    host=create_identity_service_host(lambda cfg:authority,allowed_case_ids=frozenset({"C1"}),protected_source=source)
    # Invoke only the existing dependency factory. No service is started.
    with pytest.raises(Exception):
        if failure=="role":source.bind_authority(authority,config)
        else:host._runtime_factory(config)._factory(config)
    assert ports.drive.calls==[] and ports.credential_calls==0
    if failure=="role":authority.close()


def test_commit_revalidates_source_bytes_and_preserves_reservation(tmp_path):
    from test_f07_inactive_runtime import runtime_at,stage
    from agent_lab.c09_identity_client import IdentityClientError
    from agent_lab.identity_atomic_mutation import load
    ports=Dependencies()
    source=InactiveGoogleDriveMutationSource(binding(),ports)
    with patch("test_kernel_identity_operational.store_at",side_effect=drive_store),patch("test_f07_inactive_runtime.store_at",side_effect=drive_store):
        with runtime_at(tmp_path,source=False,protected_source=source) as state:
            assert stage(state,"PREPARE_MUTATION")["outcome"]=="PREPARED"
            ports.drive.attack="content"
            with pytest.raises(IdentityClientError):stage(state,"COMMIT_MUTATION")
            authority=drive_store(tmp_path/"identity.sqlite")
            try:
                assert authority._load_identity("P2") is None
                assert load(authority,"AUTH:TEST-AUTHORIZATION-1")["state"]=="RESERVED"
                authority._verify_logical_integrity()
            finally:authority.close()
            assert len(state["session"].objects)==1
