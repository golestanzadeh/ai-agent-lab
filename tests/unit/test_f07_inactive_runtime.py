"""Native isolated Windows pipes and real authorities; synthetic inputs only."""
from contextlib import contextmanager
from dataclasses import replace
import sys
import threading
import uuid
from unittest.mock import patch

import pytest

from agent_lab.c09_operational_service_runtime import AuthorityPipeRuntime,KernelIdentityServiceClient
from agent_lab.c09_service_host import ServiceRole,ROLE_BINDINGS,ServiceHostError,current_process_sid
from agent_lab.c09_named_pipe import PinnedProcess,sha256_file
from agent_lab.c09_identity_client import IdentityClientError
from agent_lab.ipc_wire_primitives import decode_frame
from agent_lab.identity_logical_continuity import H
from test_c09_custodian_operational import fixture,rpc
from test_c09_operational_service_runtime import configuration
from test_identity_logical_runtime import store_at,KERNEL
from test_f07_atomic_mutation import Sources
from test_identity_persistence import A1
from test_orchestrator_kernel import task,manifest

pytestmark=pytest.mark.skipif(sys.platform!="win32",reason="native Windows Named Pipe integration")


@contextmanager
def runtime_at(tmp_path,*,source=True,routing=True,protected_source=None,mutation_source=None,permissions=None,inputs=None):
    import pywintypes,win32con,win32pipe,win32security
    kernel,identity,owner,pending,custodian,client,provider,session=fixture(tmp_path)
    sid=current_process_sid()
    import win32api,win32process
    image=win32process.GetModuleFileNameEx(win32api.GetCurrentProcess(),0)
    peer=PinnedProcess(sid,image,sha256_file(image))
    name=r"\\.\pipe\AI-Tax-Agent-F07-Mutation-Test-"+uuid.uuid4().hex
    def isolated_server(_name,*,overlapped):
        attrs=pywintypes.SECURITY_ATTRIBUTES()
        attrs.SECURITY_DESCRIPTOR=win32security.ConvertStringSecurityDescriptorToSecurityDescriptor(
            "D:P(A;;GRGW;;;"+sid+")",win32security.SDDL_REVISION_1)
        return win32pipe.CreateNamedPipe(name,win32pipe.PIPE_ACCESS_DUPLEX|win32pipe.FILE_FLAG_FIRST_PIPE_INSTANCE|win32con.FILE_FLAG_OVERLAPPED,
            win32pipe.PIPE_TYPE_MESSAGE|win32pipe.PIPE_READMODE_MESSAGE|win32pipe.PIPE_REJECT_REMOTE_CLIENTS,1,65540,65540,500,attrs)
    def authority_factory(_config):
        authority=store_at(tmp_path/"identity.sqlite")
        if source:authority._mutation_source=mutation_source or Sources()
        return authority
    state={"kernel":kernel,"host":None,"calls":[],"client":None,"owner":owner,"session":session}
    try:
        with patch("agent_lab.c09_pipe_transport.exchange_custodian_control",side_effect=rpc(custodian)):
            kernel.witness_identity_checkpoint(pending["receipt"]["checkpoint_id"],custodian=client,provider=provider,signing_key=KERNEL,kernel_key_id="TEST-KERNEL-KEY-1")
            identity.close()
            work=task(task_id="TASK-RUNTIME-1",role_id="IDENTITY_ADMINISTRATION_AGENT",permissions=permissions or ["identity_create","identity_read"],
                      case_context=dict(case_id="C1",tax_year=2025,run_id="RUN-RUNTIME-1"))
            work["inputs"]=inputs or [A1,"sha256:"+"8"*64]
            kernel.register_task(work,gate_triggers=[])
            grant=manifest(work,manifest_id="MAN-RUNTIME-1",tiers=["A4"])
            kernel.register_manifest(grant)
            kernel.validate_manifest(grant["manifest_id"])
            kernel.activate_manifest(grant["manifest_id"])
            state["arguments"]=dict(manifest_id=grant["manifest_id"],task_id=work["task_id"],run_id="RUN-RUNTIME-1",case_id="C1",tax_year=2025,
                operation="REGISTER_IDENTITY",authorization_references=[A1],transaction_id="tx:v1:123e4567-e89b-42d3-a456-426614174999")
            state["payload"]=dict(request_id="TEST-RUNTIME-P2",subject_id="P2",identity_record_ref="sha256:"+"8"*64,evidence_refs=["sha256:"+"8"*64])
            def compose():
                state["client"]=KernelIdentityServiceClient(state["kernel"],deployment_id=owner["deployment_id"],identity_server=peer,custodian=client,
                    provider=provider,signing_key=KERNEL,key_id="TEST-KERNEL-KEY-1",mutation_pipeline=True)
                if protected_source is None:
                    state["host"]=AuthorityPipeRuntime(configuration(owner["deployment_id"]),authority_factory,allowed_case_ids=frozenset({"C1"}),mutation_pipeline=routing)
                else:
                    from agent_lab.c09_operational_service_runtime import create_identity_service_host
                    host=create_identity_service_host(authority_factory,allowed_case_ids=frozenset({"C1"}),mutation_pipeline=routing,protected_source=protected_source)
                    state["host"]=host._runtime_factory(configuration(owner["deployment_id"]))
                state["host"].start()
            def restart():
                from agent_lab.orchestrator_kernel import OrchestratorKernel
                from test_kernel_identity_operational import ROOT
                state["host"].stop()
                state["kernel"].close()
                state["kernel"]=OrchestratorKernel(tmp_path/"kernel.sqlite",ROOT)
                state["kernel"].verify_identity_witness_state(owner["deployment_id"],custodian=client,provider=provider,signing_key=KERNEL,kernel_key_id="TEST-KERNEL-KEY-1")
                compose()
            state["restart"]=restart
            with patch.dict(ROLE_BINDINGS,{ServiceRole.IDENTITY:("AITaxIdentity",sid)}),patch("agent_lab.c09_operational_service_runtime.create_kernel_only_server",side_effect=isolated_server),patch("agent_lab.c09_named_pipe.KERNEL_SID",sid),patch("agent_lab.c09_pipe_transport.IDENTITY_PIPE",name):
                compose()
                yield state
    finally:
        active_error=sys.exc_info()[0] is not None
        try:
            if state["host"] is not None:state["host"].stop()
        except ServiceHostError:
            if not active_error:raise
        finally:
            custodian.close()
            state["kernel"].close()
            identity._db.close()


def stage(state,message,payload=None,**changes):
    arguments={**state["arguments"],**changes}
    return state["client"].mutation_stage(**arguments,message_type=message,payload=state["payload"] if payload is None else payload)


@pytest.mark.parametrize("outcome",["complete","abort","lost_commit","cancel_commit"])
def test_native_pipeline_and_recovery(tmp_path,outcome):
    from agent_lab.c09_pipe_transport import _exchange_canonical,PipeDeadlineError
    with runtime_at(tmp_path) as state:
        cancellation=threading.Event()
        # Record actual transported stages, without replacing native I/O.
        def exchange(frame,*args,**kwargs):
            message=decode_frame(frame)["message_type"]
            state["calls"].append(message)
            reply=_exchange_canonical(frame,*args,**kwargs)
            if message=="COMMIT_MUTATION":
                if outcome=="lost_commit":
                    raise PipeDeadlineError("synthetic lost committed response")
                if outcome=="cancel_commit":cancellation.set()
            return reply
        with patch("agent_lab.c09_pipe_transport._exchange_canonical",side_effect=exchange):
            prepared=stage(state,"PREPARE_MUTATION")
            assert prepared["outcome"]=="PREPARED"
            original=state["kernel"]._identity_payload("identity_kernel_state","deployment_id",state["owner"]["deployment_id"])["mutations"][state["arguments"]["transaction_id"]]["prepare_request"]["request_digest"]
            linkage={"original_request_digest":original}
            if outcome=="abort":
                assert stage(state,"ABORT_PREPARED",linkage)["outcome"]=="ABORTED"
                assert stage(state,"GET_TRANSACTION",linkage)["outcome"]=="ABORTED"
                assert len(state["session"].objects)==1
                return
            if outcome in {"lost_commit","cancel_commit"}:
                with pytest.raises(IdentityClientError):stage(state,"COMMIT_MUTATION",cancellation=cancellation)
                assert state["calls"].count("COMMIT_MUTATION")==1
                state["restart"]()
                committed=stage(state,"GET_TRANSACTION",linkage)
            else:
                committed=stage(state,"COMMIT_MUTATION")
                assert stage(state,"GET_TRANSACTION",linkage)["result"]==committed["result"]
            assert committed["outcome"]=="IDENTITY_COMMITTED"
            pending=state["client"].reconcile("MUTATION:"+state["arguments"]["transaction_id"])
            receipt=pending["receipt"]
            verify=pending["custodian_verification"]["response"]
            final=dict(staged_receipt_digest=H(receipt),witness_object_key=pending["object_key"],witness_generation=pending["generation"],
                witness_preimage_digest=receipt["witness_preimage_digest"],signed_record_digest=verify["signed_record_digest"],custodian_verification_digest=H(verify),custodian_nonce=verify["nonce"])
            assert stage(state,"FINALIZE_MUTATION",final)["outcome"]=="COMMITTED_FINAL"
            state["restart"]()
            assert stage(state,"GET_TRANSACTION",linkage)["outcome"]=="COMMITTED_FINAL"
            assert len(state["session"].objects)==2
        authority=store_at(tmp_path/"identity.sqlite")
        try:
            assert authority._load_identity("P2") is not None
            authority._verify_logical_integrity()
        finally:authority.close()


@pytest.mark.parametrize("failure",["source","routing","case","year","run","halted","cancelled","unknown"])
def test_native_runtime_fails_closed(tmp_path,failure):
    with runtime_at(tmp_path,source=failure!="source",routing=failure!="routing") as state:
        changes={}
        message="PREPARE_MUTATION"
        if failure=="case":changes["case_id"]="C2"
        if failure=="year":changes["tax_year"]=2024
        if failure=="run":changes["run_id"]="RUN-OTHER"
        if failure=="halted":state["kernel"].set_kill_switch("HALTED",actor_id="HUMAN_PROJECT_OWNER",authority_reference="TEST-STOP")
        if failure=="cancelled":
            cancellation=threading.Event();cancellation.set();changes["cancellation"]=cancellation
        if failure=="unknown":message="UNSUPPORTED"
        with pytest.raises(Exception):stage(state,message,**changes)
        authority=store_at(tmp_path/"identity.sqlite")
        try:assert authority._load_identity("P2") is None
        finally:authority.close()
        assert len(state["session"].objects)==1


def test_mutation_routing_disabled_before_kernel_use():
    from agent_lab.c09_operational_service_runtime import KernelIdentityServiceClient
    client=object.__new__(KernelIdentityServiceClient)
    client._mutation_pipeline=False
    with pytest.raises(ServiceHostError,match="disabled"):
        client.mutation_stage(manifest_id="",task_id="",run_id="",case_id="",tax_year=2025,operation="REGISTER_IDENTITY",
            message_type="PREPARE_MUTATION",payload={},authorization_references=[],transaction_id="")


@pytest.mark.parametrize("field",["transaction_id","request_digest","response_digest"])
def test_native_response_substitution_rejected(tmp_path,field):
    from agent_lab.c09_pipe_transport import _exchange_canonical
    from agent_lab.ipc_wire_primitives import encode_frame
    with runtime_at(tmp_path) as state:
        def corrupt(frame,*args,**kwargs):
            response=decode_frame(_exchange_canonical(frame,*args,**kwargs))
            response[field]="sha256:"+"0"*64
            if field!="response_digest":
                response.pop("response_digest")
                response["response_digest"]=H(response)
            return encode_frame(response)
        with patch("agent_lab.c09_pipe_transport._exchange_canonical",side_effect=corrupt):
            with pytest.raises(IdentityClientError):stage(state,"PREPARE_MUTATION")
        state["kernel"]._verify_identity_protocol_state()
        tx=state["kernel"]._identity_payload("identity_kernel_state","deployment_id",state["owner"]["deployment_id"])["mutations"][state["arguments"]["transaction_id"]]
        assert "prepare_response" not in tx
        assert len(state["session"].objects)==1


def test_existing_factories_preserve_inactive_dependency_injection():
    from agent_lab.c09_operational_service_runtime import create_identity_service_host,create_kernel_service_host
    from agent_lab.c09_service_host import ServiceConfiguration
    identity=create_identity_service_host(lambda cfg:None,allowed_case_ids=frozenset({"C1"}))
    assert identity._runtime_factory(configuration())._mutation_pipeline is False
    enabled=create_identity_service_host(lambda cfg:None,allowed_case_ids=frozenset({"C1"}),mutation_pipeline=True)
    assert enabled._runtime_factory(configuration())._mutation_pipeline is True
    name,sid=ROLE_BINDINGS[ServiceRole.KERNEL]
    config=ServiceConfiguration("ai-tax-agent.c09-service-config/1.0","TEST-DEPLOYMENT",ServiceRole.KERNEL,name,sid,True)
    kernel=create_kernel_service_host(lambda cfg:None,identity_server=None,custodian=None,provider=None,signing_key=None,key_id="",mutation_pipeline=True)
    assert kernel._runtime_factory(config)._bindings["mutation_pipeline"] is True


@pytest.mark.parametrize("failure",["unreserved","revoked"])
def test_client_rejects_invalid_kernel_authority_before_transport(tmp_path,failure):
    from datetime import datetime,timezone
    from agent_lab.c09_identity_client import exchange_operational_identity_mutation
    from agent_lab.ipc_wire_primitives import encode_frame
    from agent_lab.orchestrator_kernel import OrchestratorKernel
    from test_kernel_identity_operational import ROOT
    with runtime_at(tmp_path) as state:
        kernel=state["kernel"]
        request=kernel.issue_identity_mutation(deployment_id=state["owner"]["deployment_id"],**state["arguments"],
            message_type="PREPARE_MUTATION",payload=state["payload"],signing_key=KERNEL,key_id="TEST-KERNEL-KEY-1")
        other=None
        if failure=="unreserved":
            other=OrchestratorKernel(tmp_path/"other-kernel.sqlite",ROOT)
            kernel=other
        else:
            kernel.set_kill_switch("HALTED",actor_id="HUMAN_PROJECT_OWNER",authority_reference="TEST-STOP")
        try:
            with patch("agent_lab.c09_pipe_transport.exchange_operational_identity_mutation") as transport:
                with pytest.raises(IdentityClientError):
                    exchange_operational_identity_mutation(encode_frame(request),state["client"]._identity,KERNEL.public_key(),kernel=kernel,
                        expected_scope={key:request[key] for key in "deployment_id case_id tax_year run_id task_id manifest_id actor_instance_id role_id".split()},
                        now=datetime.now(timezone.utc).replace(tzinfo=None),expected_key_id="TEST-KERNEL-KEY-1")
                transport.assert_not_called()
        finally:
            if other is not None:other.close()
