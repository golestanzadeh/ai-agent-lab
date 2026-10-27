"""SCM composition/native isolated current-user pipes, NOT deployment acceptance."""
import sys
import threading
import uuid
from unittest.mock import patch
import pytest
from agent_lab.c09_operational_service_runtime import AuthorityPipeRuntime
from agent_lab.c09_service_host import ServiceConfiguration,ServiceRole,ROLE_BINDINGS,ServiceHostError,current_process_sid
from agent_lab.c09_named_pipe import PinnedProcess,sha256_file
from agent_lab.c09_pipe_transport import exchange_operational_identity_read,OperationDeadline
from agent_lab.ipc_wire_primitives import encode_frame,decode_frame
from test_kernel_identity_operational import bootstrap,issue
from test_identity_logical_runtime import store_at


def configuration(deployment="TEST-DEPLOYMENT"):
    name,sid=ROLE_BINDINGS[ServiceRole.IDENTITY]
    return ServiceConfiguration("ai-tax-agent.c09-service-config/1.0",deployment,ServiceRole.IDENTITY,name,sid,True)


def test_actual_wrong_service_token_cannot_open_authority():
    opened=[];config=configuration()
    runtime=AuthorityPipeRuntime(config,lambda cfg:opened.append(cfg))
    with patch("agent_lab.c09_operational_service_runtime.current_process_sid",return_value="UNAUTHORIZED"):
        with pytest.raises(ServiceHostError,match="token"):runtime.start()
    assert opened==[]


def test_kernel_service_wrong_token_and_stopped_client(tmp_path):
    from agent_lab.c09_operational_service_runtime import KernelServiceRuntime
    name,sid=ROLE_BINDINGS[ServiceRole.KERNEL]
    config=ServiceConfiguration("ai-tax-agent.c09-service-config/1.0","TEST-DEPLOYMENT",ServiceRole.KERNEL,name,sid,True)
    opened=[]
    runtime=KernelServiceRuntime(config,lambda cfg:opened.append(cfg),identity_server=None,custodian=None,provider=None,signing_key=None,key_id="")
    with patch("agent_lab.c09_operational_service_runtime.current_process_sid",return_value="UNAUTHORIZED"):
        with pytest.raises(ServiceHostError,match="token"):runtime.start()
    assert opened==[] and runtime.client is None
    runtime.stop()
    with pytest.raises(ServiceHostError,match="stopped"):runtime.check_health()


@pytest.mark.skipif(sys.platform!="win32",reason="real native Windows pipe")
@pytest.mark.parametrize("authorized",[True,False])
def test_actual_native_authority_response_and_stop_restart(tmp_path,authorized):
    import pywintypes,win32con,win32pipe,win32security
    kernel,identity,owner,state=bootstrap(tmp_path);identity.close()
    sid=current_process_sid();peer=PinnedProcess(sid,sys.executable,sha256_file(sys.executable))
    config=configuration(owner["deployment_id"])
    name=r"\\.\pipe\AI-Tax-Agent-F07-Runtime-Test-"+uuid.uuid4().hex
    def isolated_server(_name,*,overlapped):
        attrs=pywintypes.SECURITY_ATTRIBUTES()
        attrs.SECURITY_DESCRIPTOR=win32security.ConvertStringSecurityDescriptorToSecurityDescriptor("D:P(A;;GRGW;;;"+sid+")",win32security.SDDL_REVISION_1)
        return win32pipe.CreateNamedPipe(name,win32pipe.PIPE_ACCESS_DUPLEX|win32pipe.FILE_FLAG_FIRST_PIPE_INSTANCE|win32con.FILE_FLAG_OVERLAPPED,win32pipe.PIPE_TYPE_MESSAGE|win32pipe.PIPE_READMODE_MESSAGE|win32pipe.PIPE_REJECT_REMOTE_CLIENTS,1,65540,65540,500,attrs)
    try:
        with patch("agent_lab.c09_operational_service_runtime.current_process_sid",return_value=config.principal_sid),patch("agent_lab.c09_operational_service_runtime.create_kernel_only_server",side_effect=isolated_server),patch("agent_lab.c09_named_pipe.KERNEL_SID",sid if authorized else sid+"0"),patch("agent_lab.c09_pipe_transport.IDENTITY_PIPE",name):
            for attempt in range(2):
                runtime=AuthorityPipeRuntime(config,lambda cfg:store_at(tmp_path/"identity.sqlite"))
                runtime.start()
                try:
                    request=issue(kernel,owner)
                    if not authorized:
                        from agent_lab.c09_named_pipe import PipeSecurityError
                        with pytest.raises(PipeSecurityError):exchange_operational_identity_read(encode_frame(request),peer,deadline=OperationDeadline(3))
                        runtime.check_health()
                        continue
                    try:response=decode_frame(exchange_operational_identity_read(encode_frame(request),peer,deadline=OperationDeadline(3)))
                    except Exception:
                        if runtime._connection_error is not None:raise runtime._connection_error
                        raise
                    assert response["outcome"]=="ENROLLMENT_READY"
                    assert response["request_digest"]==request["request_digest"]
                finally:runtime.stop()
                assert not runtime._thread.is_alive()
    finally:kernel.close()


@pytest.mark.skipif(sys.platform!="win32",reason="real native Windows pipe")
@pytest.mark.parametrize("fault",[RuntimeError("internal dispatcher failure"),ValueError("authority integrity corruption")])
def test_authenticated_internal_failure_halts_worker_and_service(tmp_path,fault):
    import pywintypes,win32con,win32pipe,win32security
    from agent_lab.c09_service_host import ServiceHost,Lifecycle
    from agent_lab.c09_named_pipe import PipeSecurityError
    kernel,identity,owner,state=bootstrap(tmp_path);identity.close()
    sid=current_process_sid();config=configuration(owner["deployment_id"])
    name=r"\\.\pipe\AI-Tax-Agent-F07-Fault-Test-"+uuid.uuid4().hex
    closed=threading.Event()
    def factory(cfg):
        authority=store_at(tmp_path/"identity.sqlite")
        original=authority.close
        def close():
            try:original()
            finally:closed.set()
        authority.close=close
        return authority
    def server(_name,*,overlapped):
        attrs=pywintypes.SECURITY_ATTRIBUTES()
        attrs.SECURITY_DESCRIPTOR=win32security.ConvertStringSecurityDescriptorToSecurityDescriptor("D:P(A;;GRGW;;;"+sid+")",win32security.SDDL_REVISION_1)
        return win32pipe.CreateNamedPipe(name,win32pipe.PIPE_ACCESS_DUPLEX|win32pipe.FILE_FLAG_FIRST_PIPE_INSTANCE|win32con.FILE_FLAG_OVERLAPPED,win32pipe.PIPE_TYPE_MESSAGE|win32pipe.PIPE_READMODE_MESSAGE|win32pipe.PIPE_REJECT_REMOTE_CLIENTS,1,65540,65540,500,attrs)
    runtime=AuthorityPipeRuntime(config,factory);host=ServiceHost(ServiceRole.IDENTITY,lambda cfg:runtime)
    peer=PinnedProcess(sid,sys.executable,sha256_file(sys.executable))
    try:
        with patch("agent_lab.c09_operational_service_runtime.current_process_sid",return_value=config.principal_sid),patch("agent_lab.c09_operational_service_runtime.create_kernel_only_server",side_effect=server),patch("agent_lab.c09_named_pipe.KERNEL_SID",sid),patch("agent_lab.c09_pipe_transport.IDENTITY_PIPE",name),patch("agent_lab.c09_identity_dispatch.dispatch_stateful_identity_read",side_effect=fault) as dispatcher:
            host.start(config,config.principal_sid)
            with pytest.raises(PipeSecurityError):exchange_operational_identity_read(encode_frame(issue(kernel,owner)),peer,deadline=OperationDeadline(3))
            assert closed.wait(2)
            with pytest.raises(ServiceHostError):host.check_health()
            assert host.state is Lifecycle.HALTED and dispatcher.call_count==1
            assert runtime._stop.is_set() and not runtime._thread.is_alive()
    finally:kernel.close()


def test_concrete_kernel_service_client_releases_only_after_witness(tmp_path):
    from agent_lab.c09_operational_service_runtime import KernelIdentityServiceClient
    from agent_lab.identity_logical_continuity import H
    from test_c09_custodian_operational import fixture,rpc
    from test_identity_logical_runtime import KERNEL
    kernel,identity,owner,pending,host,custodian,provider,session=fixture(tmp_path,prepare=False)
    pin=PinnedProcess(ROLE_BINDINGS[ServiceRole.IDENTITY][1],r"C:\Controlled\Identity.exe","sha256:"+"b"*64)
    client=KernelIdentityServiceClient(kernel,deployment_id=owner["deployment_id"],identity_server=pin,custodian=custodian,provider=provider,signing_key=KERNEL,key_id="TEST-KERNEL-KEY-1")
    def identity_port(frame,*args,**kwargs):
        assert not session.objects
        request=decode_frame(frame)
        return encode_frame(identity.read_operational_identity(request,allowed_case_ids=frozenset()))
    try:
        with patch("agent_lab.c09_pipe_transport.exchange_operational_identity_read",side_effect=identity_port),patch("agent_lab.c09_pipe_transport.exchange_custodian_control",side_effect=rpc(host)):
            result=client.read(manifest_id=owner["bootstrap_manifest_id"],task_id=owner["bootstrap_task_id"],run_id=owner["bootstrap_run_id"],case_id="*",tax_year="*",operation="READ_ENROLLMENT_STATUS",payload={"enrollment_id":owner["enrollment_id"],"owner_authorization_digest":H(owner)},authorization_references=[H(owner)])
        assert result["outcome"]=="ENROLLMENT_READY" and len(session.objects)==1
        assert kernel._connection.execute("SELECT COUNT(*) FROM identity_kernel_checkpoint WHERE payload_json LIKE '%RELEASED%'").fetchone()[0]==1
    finally:host.close();identity.close();kernel.close()
