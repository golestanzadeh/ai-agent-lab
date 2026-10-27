"""Real Windows pipe I/O, isolated current-user endpoint; NOT four-principal acceptance."""
import sys
import threading
import uuid
from unittest.mock import patch

import pytest
from agent_lab.c09_named_pipe import PinnedProcess,sha256_file
from agent_lab.c09_pipe_transport import exchange_operational_identity_read,OperationDeadline,PipeSecurityError
from agent_lab.c09_service_host import current_process_sid
from test_f07_operational_read import V


@pytest.mark.skipif(sys.platform!="win32",reason="actual Windows pipe verification")
@pytest.mark.parametrize("mode",["reply","silent","disconnect","wrong-digest","wrong-sid","wrong-path","malformed","oversized","cancel"])
def test_actual_local_exchange(mode):
    import pywintypes
    import win32con
    import win32file
    import win32pipe
    import win32security
    name=r"\\.\pipe\AI-Tax-Agent-F07-Test-"+uuid.uuid4().hex
    sid=current_process_sid()
    attrs=pywintypes.SECURITY_ATTRIBUTES()
    attrs.SECURITY_DESCRIPTOR=win32security.ConvertStringSecurityDescriptorToSecurityDescriptor("D:P(A;;GRGW;;;"+sid+")",win32security.SDDL_REVISION_1)
    handle=win32pipe.CreateNamedPipe(name,win32pipe.PIPE_ACCESS_DUPLEX|win32pipe.FILE_FLAG_FIRST_PIPE_INSTANCE,win32pipe.PIPE_TYPE_MESSAGE|win32pipe.PIPE_READMODE_MESSAGE|win32pipe.PIPE_REJECT_REMOTE_CLIENTS,1,65536,65536,500,attrs)
    stop=threading.Event();cancellation=threading.Event();received=[]
    def server():
        try:
            try:win32pipe.ConnectNamedPipe(handle,None)
            except pywintypes.error as exc:
                if exc.winerror!=535:raise
            _,data=win32file.ReadFile(handle,65537);received.append(bytes(data))
            if mode=="cancel":cancellation.set()
            if mode in {"silent","cancel"}:stop.wait(2)
            elif mode in {"reply","malformed","oversized"}:
                data=bytes.fromhex(V["vectors"][1]["response_frame_hex"]) if mode=="reply" else b"bad" if mode=="malformed" else b"x"*65537
                win32file.WriteFile(handle,data)
                stop.wait(2)  # DisconnectNamedPipe would discard an unread queued reply.
        except pywintypes.error:pass
        finally:
            try:win32pipe.DisconnectNamedPipe(handle)
            except pywintypes.error:pass
    thread=threading.Thread(target=server,daemon=True);thread.start()
    peer=PinnedProcess(sid if mode!="wrong-sid" else sid+"0",sys.executable if mode!="wrong-path" else sys.executable+".wrong","sha256:"+"0"*64 if mode=="wrong-digest" else sha256_file(sys.executable))
    try:
        with patch("agent_lab.c09_pipe_transport.IDENTITY_PIPE",name):
            if mode=="reply":assert exchange_operational_identity_read(bytes.fromhex(V["vectors"][1]["frame_hex"]),peer,deadline=OperationDeadline(1,cancellation))==bytes.fromhex(V["vectors"][1]["response_frame_hex"])
            else:
                with pytest.raises(PipeSecurityError):exchange_operational_identity_read(bytes.fromhex(V["vectors"][1]["frame_hex"]),peer,deadline=OperationDeadline(.2,cancellation))
        if mode in {"wrong-digest","wrong-sid","wrong-path"}:assert not received
        if mode in {"silent","cancel"}:assert len(received)==1  # Timeout may follow execution; never retry.
    finally:
        stop.set();win32file.CloseHandle(handle);thread.join(2)
        assert not thread.is_alive()


@pytest.mark.skipif(sys.platform!="win32",reason="actual Windows pipe verification")
def test_absent_server_connection_is_bounded():
    import time
    peer=PinnedProcess(current_process_sid(),sys.executable,sha256_file(sys.executable))
    started=time.monotonic()
    with patch("agent_lab.c09_pipe_transport.IDENTITY_PIPE",r"\\.\pipe\AI-Tax-Agent-F07-Absent-"+uuid.uuid4().hex):
        with pytest.raises(PipeSecurityError):exchange_operational_identity_read(bytes.fromhex(V["vectors"][1]["frame_hex"]),peer,deadline=OperationDeadline(.05))
    assert time.monotonic()-started<1
