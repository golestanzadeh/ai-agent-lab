"""Real MAC/SQLite operations; provider/pipe transport injected only in tests."""
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import json
import sqlite3
from urllib.parse import unquote

import pytest
from agent_lab.c09_custodian_operational import OperationalCustodianRuntime,CustodianServiceClient,pack,unpack
from agent_lab.c09_named_pipe import PinnedProcess
from agent_lab.c09_service_host import ROLE_BINDINGS,ServiceRole
from agent_lab.c09_gcs_witness_adapter import GCSWitnessAdapter
from agent_lab.c09_witness_protocol import WitnessRecord,WitnessError
from agent_lab.ipc_wire_primitives import decode_frame,encode_frame
from agent_lab.identity_logical_continuity import sign_kernel_proof
from test_kernel_identity_operational import bootstrap,issue
from test_identity_logical_runtime import KERNEL

MAC=b"PUBLIC-SYNTHETIC-CUSTODIAN-TEST-KEY-ONLY!!!!"


class Response:
    def __init__(self,status,data=None,content=b""):self.status_code=status;self.data=data;self.content=content
    def json(self):return self.data


class ObjectSession:
    def __init__(self):self.objects={};self.calls=[];self.fail_after_upload=False;self.corrupt=False
    def request(self,method,path,**kwargs):
        self.calls.append((method,path,kwargs))
        if method=="POST":
            key=kwargs["params"]["name"]
            if key in self.objects:return Response(412)
            generation=str(len(self.objects)+1);self.objects[key]=(generation,kwargs["data"])
            if self.fail_after_upload:
                import requests
                self.fail_after_upload=False;raise requests.Timeout("ambiguous synthetic upload")
            return Response(200,{"generation":generation})
        if path.endswith("/o"):
            return Response(200,{"items":[{"name":key,"generation":gen,"size":str(len(raw))} for key,(gen,raw) in self.objects.items()]})
        key=unquote(path.split("/o/",1)[1]);generation=kwargs["params"]["generation"]
        stored=self.objects.get(key)
        if stored is None or stored[0]!=generation:return Response(404)
        return Response(200,content=stored[1]+(b"corrupt" if self.corrupt else b""))


def fixture(tmp_path,*,prepare=True):
    kernel,identity,owner,state=bootstrap(tmp_path)
    pending=None
    if prepare:
        request=issue(kernel,owner);response=identity.read_operational_identity(request,allowed_case_ids=frozenset())
        pending=kernel.stage_identity_audit_checkpoint(request,response)
    path=tmp_path/"existing-custodian.sqlite"
    with sqlite3.connect(path):pass
    host=OperationalCustodianRuntime(deployment_id=owner["deployment_id"],key_id="TEST-CUSTODIAN-KEY",protected_key=MAC,kernel_key_id="TEST-KERNEL-KEY-1",kernel_public_key=KERNEL.public_key(),replay_db_path=path)
    host.start()
    pinned=PinnedProcess(ROLE_BINDINGS[ServiceRole.KEY_CUSTODIAN][1],r"C:\Controlled\Custodian.exe","sha256:"+"a"*64)
    client=CustodianServiceClient(deployment_id=owner["deployment_id"],pinned_server=pinned,custodian_key_id="TEST-CUSTODIAN-KEY")
    session=ObjectSession();provider=GCSWitnessAdapter("test-bucket",lambda:"TEST-WRITER",lambda:"TEST-READER",session)
    return kernel,identity,owner,pending,host,client,provider,session


def rpc(host,observed=None):
    def exchange(frame,pin,**kwargs):
        request=decode_frame(frame)
        if observed is not None:observed.append(request)
        return encode_frame(host.handle(request))
    return exchange


def test_flat_record_mac_key_separation_and_genesis_release(tmp_path):
    kernel,identity,owner,pending,host,client,provider,session=fixture(tmp_path)
    try:
        assert not hasattr(client,"_key")
        with patch("agent_lab.c09_pipe_transport.exchange_custodian_control",side_effect=rpc(host)):
            response=kernel.witness_identity_checkpoint(pending["receipt"]["checkpoint_id"],custodian=client,provider=provider,signing_key=KERNEL,kernel_key_id="TEST-KERNEL-KEY-1")
        assert response["outcome"]=="ENROLLMENT_READY"
        state=kernel._identity_payload("identity_kernel_state","deployment_id",owner["deployment_id"])
        assert state["status"]=="ACTIVE" and (state["witness_epoch"],state["witness_sequence"])==(1,1)
        raw=next(iter(session.objects.values()))[1]
        record=WitnessRecord.from_bytes(raw,MAC)
        assert record.identity_head.startswith("sha256:") and "preimage" not in json.loads(raw)
        with pytest.raises(Exception):issue(kernel,owner)
        kernel._verify_identity_protocol_state()
    finally:host.close();identity.close();kernel.close()


def test_no_append_or_release_when_custodian_unavailable(tmp_path):
    kernel,identity,owner,pending,host,client,provider,session=fixture(tmp_path)
    try:
        with patch("agent_lab.c09_pipe_transport.exchange_custodian_control",side_effect=ConnectionError("unavailable")):
            with pytest.raises(ConnectionError):kernel.witness_identity_checkpoint(pending["receipt"]["checkpoint_id"],custodian=client,provider=provider,signing_key=KERNEL,kernel_key_id="TEST-KERNEL-KEY-1")
        assert session.calls==[]
        assert kernel._identity_payload("identity_kernel_checkpoint","checkpoint_id",pending["receipt"]["checkpoint_id"])["status"]=="AUDIT_CHECKPOINT_PENDING"
    finally:host.close();identity.close();kernel.close()


def test_ambiguous_upload_resumes_exact_record_without_second_append(tmp_path):
    kernel,identity,owner,pending,host,client,provider,session=fixture(tmp_path);session.fail_after_upload=True
    try:
        with patch("agent_lab.c09_pipe_transport.exchange_custodian_control",side_effect=rpc(host)):
            with pytest.raises(WitnessError):kernel.witness_identity_checkpoint(pending["receipt"]["checkpoint_id"],custodian=client,provider=provider,signing_key=KERNEL,kernel_key_id="TEST-KERNEL-KEY-1")
            assert kernel._identity_payload("identity_kernel_checkpoint","checkpoint_id",pending["receipt"]["checkpoint_id"])["status"]=="AUDIT_CHECKPOINT_PENDING"
            result=kernel.witness_identity_checkpoint(pending["receipt"]["checkpoint_id"],custodian=client,provider=provider,signing_key=KERNEL,kernel_key_id="TEST-KERNEL-KEY-1")
        assert result["outcome"]=="ENROLLMENT_READY" and sum(method=="POST" for method,_,_ in session.calls)==1
    finally:host.close();identity.close();kernel.close()


@pytest.mark.parametrize("field",["staged_receipt_digest","unsigned_record_digest","kernel_pending_head","identity_new_head","witness_object_key","contract"])
def test_signed_substitution_and_downgrade_rejected(tmp_path,field):
    kernel,identity,owner,pending,host,client,provider,session=fixture(tmp_path);observed=[]
    try:
        with patch("agent_lab.c09_pipe_transport.exchange_custodian_control",side_effect=rpc(host,observed)):
            client.authenticate(pending,KERNEL,"TEST-KERNEL-KEY-1")
        bad=deepcopy(observed[0]);bad["nonce"]="f"*64
        bad[field]="ai-tax-agent.c09-custodian/1.0" if field=="contract" else "sha256:"+"0"*64
        bad=sign_kernel_proof(bad,KERNEL)
        with pytest.raises((ValueError,PermissionError)):host.handle(bad)
    finally:host.close();identity.close();kernel.close()


@pytest.mark.parametrize("boundary",["BEFORE_COMMIT","AFTER_COMMIT","AFTER_ANCHOR","AFTER_RECEIPT_CONSUMED"])
def test_custodian_anchor_crash_exact_retry(tmp_path,boundary):
    kernel,identity,owner,pending,host,client,provider,session=fixture(tmp_path);requests=[]
    def capture(frame,*args,**kwargs):
        requests.append(decode_frame(frame));raise ConnectionError("capture only")
    try:
        with patch("agent_lab.c09_pipe_transport.exchange_custodian_control",side_effect=capture):
            with pytest.raises(ConnectionError):client.authenticate(pending,KERNEL,"TEST-KERNEL-KEY-1")
        def fail(stage):
            if stage==boundary:raise RuntimeError("injected crash")
        host._fault=fail
        with pytest.raises(RuntimeError):host.handle(requests[0])
        host.close()
        host=OperationalCustodianRuntime(deployment_id=owner["deployment_id"],key_id="TEST-CUSTODIAN-KEY",protected_key=MAC,kernel_key_id="TEST-KERNEL-KEY-1",kernel_public_key=KERNEL.public_key(),replay_db_path=tmp_path/"existing-custodian.sqlite")
        host.start();response=host.handle(requests[0]);again=host.handle(requests[0])
        assert response==again
        assert WitnessRecord.from_bytes(unpack(response["authenticated_record_bytes"]),MAC).operation_id.startswith("AUDIT:")
        assert host._db.execute("SELECT COUNT(*) FROM custodian11_event").fetchone()[0]==1
        assert host._db.execute("SELECT COUNT(*) FROM custodian11_anchor_pending").fetchone()[0]==0
    finally:host.close();identity.close();kernel.close()


@pytest.mark.parametrize("changed", [None, "profile", "witness_slot", "audit_cut_head", "logical_head", "prepared_request_digest"])
def test_mutation_receipt_exact_preimage_and_replay(tmp_path, changed):
    from test_f07_commit_witness import recovery_exchange
    from agent_lab.identity_logical_continuity import H
    _, response, _, context, _ = recovery_exchange()
    commit = context["original_commit"]
    receipt = response["result"]["receipt"]
    path = tmp_path / "custodian.sqlite"
    with sqlite3.connect(path):
        pass
    from test_f07_commit_witness import KEY
    host = OperationalCustodianRuntime(deployment_id=commit["deployment_id"], key_id="TEST-MAC", protected_key=MAC,
        kernel_key_id="TEST-KERNEL", kernel_public_key=KEY.public_key(), replay_db_path=path)
    host.start()
    pin = PinnedProcess(ROLE_BINDINGS[ServiceRole.KEY_CUSTODIAN][1], r"C:\Controlled\Custodian.exe", "sha256:"+"a"*64)
    client = CustodianServiceClient(deployment_id=commit["deployment_id"], pinned_server=pin, custodian_key_id="TEST-MAC")
    pending = dict(receipt=deepcopy(receipt), unsigned_record_bytes=response["result"]["unsigned_record_bytes"])
    if changed:
        if changed == "profile":
            pending["receipt"][changed] = "identity-audit-checkpoint/1"
        elif changed == "witness_slot":
            pending["receipt"][changed]["sequence"] = "11"
        else:
            pending["receipt"][changed] = "sha256:"+"0"*64
    try:
        with patch("agent_lab.c09_pipe_transport.exchange_custodian_control", side_effect=rpc(host)):
            if changed:
                with pytest.raises((ValueError, PermissionError)):
                    client.authenticate(pending, KEY, "TEST-KERNEL")
                assert host._db.execute("SELECT COUNT(*) FROM custodian11_event").fetchone()[0] == 0
            else:
                raw = client.authenticate(pending, KEY, "TEST-KERNEL")
                assert client.authenticate(pending, KEY, "TEST-KERNEL") == raw
                record, evidence = client.verify(raw, "42", commit["transaction_id"], KEY, "TEST-KERNEL", retain_evidence=True)
                assert record == WitnessRecord.from_bytes(raw, MAC)
                assert evidence["request"]["nonce"] == evidence["response"]["nonce"]
                assert evidence["response"]["outcome"] == "VERIFIED"
                assert H(evidence["response"]).startswith("sha256:")
                assert client.verify(raw, "42", commit["transaction_id"], KEY, "TEST-KERNEL") == record
    finally:
        host.close()
