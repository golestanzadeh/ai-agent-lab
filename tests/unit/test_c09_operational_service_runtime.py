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
