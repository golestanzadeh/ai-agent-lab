"""Bounded Windows Named Pipe exchange, restricted to read-only Identity IPC.

This is a transport component, not deployment authorization.
"""
from __future__ import annotations

import threading
import time

from agent_lab.c09_named_pipe import (
    IDENTITY_PIPE, MAX_FRAME_BYTES, PinnedProcess, PipeSecurityError,
    verify_connected_server, retain_verified_server,
)


class PipeDeadlineError(PipeSecurityError):
    """The exchange is ambiguous; never infer that a peer did not execute."""


_halted=threading.Event()
_quarantined=[]  # Retain native buffers if the OS cannot acknowledge cancellation.


class OperationDeadline:
    def __init__(self, seconds: float = 5.0, cancellation: threading.Event | None = None):
        if isinstance(seconds,bool) or not isinstance(seconds,(float,int)) or not 0 < seconds <= 5:
            raise ValueError("deadline must be in (0,5] seconds")
        self.end=time.monotonic()+seconds
        self.cancellation=cancellation or threading.Event()

    def milliseconds(self):
        if self.cancellation.is_set():raise PipeDeadlineError("exchange cancelled; reconciliation required")
        remaining=self.end-time.monotonic()
        if remaining<=0:raise PipeDeadlineError("exchange expired; reconciliation required")
        return max(1,min(50,int(remaining*1000)))


def overlapped_io(handle, operation, deadline: OperationDeadline):
    """Complete/cancel one real Windows overlapped operation before releasing buffers."""
    import pywintypes
    import win32event
    import win32file
    overlap=pywintypes.OVERLAPPED();overlap.hEvent=win32event.CreateEvent(None,True,False,None)
    started=False
    try:
        result=operation(overlap)
        started=True
        while True:
            interval=deadline.milliseconds()
            if win32event.WaitForSingleObject(overlap.hEvent,interval)==win32event.WAIT_OBJECT_0:
                count=win32file.GetOverlappedResult(handle,overlap,False)
                return result,count
    except BaseException:
        if started:
            try:
                if hasattr(win32file,"CancelIoEx"):
                    win32file.CancelIoEx(handle,overlap)
                else:
                    # This pywin32 distribution omits the binding. Each owned
                    # handle has exactly one outstanding operation; native
                    # CancelIoEx(handle,NULL) cancels it without thread limits.
                    import ctypes
                    from ctypes import wintypes
                    native=ctypes.WinDLL("kernel32",use_last_error=True).CancelIoEx
                    native.argtypes=[wintypes.HANDLE,ctypes.c_void_p];native.restype=wintypes.BOOL
                    if not native(int(handle),None):
                        error=ctypes.get_last_error()
                        if error!=1168:raise pywintypes.error(error,"CancelIoEx","native cancellation failed")
            except pywintypes.error as exc:
                if exc.winerror!=1168:
                    _halted.set();_quarantined.append((handle,overlap,result));overlap=None
                    raise PipeDeadlineError("I/O cancellation failed; host must halt") from exc
            # Cancellation acknowledgement is required before buffer/event release.
            if win32event.WaitForSingleObject(overlap.hEvent,1000)!=win32event.WAIT_OBJECT_0:
                _halted.set()
                _quarantined.append((handle,overlap,result))
                overlap=None  # Never release a buffer/event still owned by native I/O.
                raise PipeDeadlineError("I/O cancellation not acknowledged; host must halt")
        raise
    finally:
        if overlap is not None:win32file.CloseHandle(overlap.hEvent)


def _exchange_canonical(frame: bytes,expected_server: PinnedProcess,*,pipe_name,deadline=None):
    """Shared bounded byte transport; public role wrappers close the allowlist."""
    from agent_lab.ipc_wire_primitives import decode_frame
    if _halted.is_set():raise PipeDeadlineError("transport halted after unacknowledged cancellation")
    try:request=decode_frame(frame)
    except ValueError as exc:raise PipeSecurityError("invalid operational frame") from exc
    deadline=deadline or OperationDeadline()
    import pywintypes
    import win32con
    import win32file
    import win32pipe
    handle=None
    try:
        while handle is None:
            deadline.milliseconds()
            try:
                handle=win32file.CreateFile(pipe_name,win32con.GENERIC_READ|win32con.GENERIC_WRITE,0,None,win32con.OPEN_EXISTING,win32con.FILE_FLAG_OVERLAPPED,None)
            except pywintypes.error as exc:
                if exc.winerror not in (2,231):raise
                deadline.cancellation.wait(min(.01,deadline.milliseconds()/1000))
        win32pipe.SetNamedPipeHandleState(handle,win32pipe.PIPE_READMODE_MESSAGE,None,None)
        with retain_verified_server(handle,expected_server,checkpoint=deadline.milliseconds):
            deadline.milliseconds()
            _,count=overlapped_io(handle,lambda ov:win32file.WriteFile(handle,frame,ov),deadline)
            if count!=len(frame):raise PipeSecurityError("partial request; reconciliation required")
            result,count=overlapped_io(handle,lambda ov:win32file.ReadFile(handle,MAX_FRAME_BYTES+1,ov),deadline)
            response=bytes(result[1][:count])
            decode_frame(response)
            return response
    except PipeSecurityError:raise
    except Exception as exc:raise PipeSecurityError("operational read exchange failed; reconciliation required") from exc
    finally:
        if handle is not None and not any(entry[0]==handle for entry in _quarantined):win32file.CloseHandle(handle)


def exchange_operational_identity_read(frame,expected_server,*,deadline=None):
    if _halted.is_set():raise PipeDeadlineError("transport halted after unacknowledged cancellation")
    from agent_lab.ipc_wire_primitives import decode_frame
    try:request=decode_frame(frame)
    except ValueError as exc:raise PipeSecurityError("invalid operational frame") from exc
    if request.get("contract") not in {"oi0002.kernel-identity-c09/1.0","oi0002.kernel-identity-c09/1.1"} or request.get("message_type") not in {"READ_IDENTITY_STATE","GET_ENROLLMENT_STATUS"} or request.get("message_type")=="GET_ENROLLMENT_STATUS" and request.get("contract")!="oi0002.kernel-identity-c09/1.1":raise PipeSecurityError("only operational read frames are permitted")
    return _exchange_canonical(frame,expected_server,pipe_name=IDENTITY_PIPE,deadline=deadline)


def exchange_custodian_control(frame,expected_server,*,deadline=None):
    if _halted.is_set():raise PipeDeadlineError("transport halted after unacknowledged cancellation")
    from agent_lab.ipc_wire_primitives import decode_frame
    from agent_lab.c09_named_pipe import CUSTODIAN_PIPE
    try:request=decode_frame(frame)
    except ValueError as exc:raise PipeSecurityError("invalid Custodian frame") from exc
    if request.get("contract")!="ai-tax-agent.c09-custodian/1.1" or request.get("operation") not in {"AUTHENTICATE_WITNESS","VERIFY_WITNESS"}:raise PipeSecurityError("closed Custodian control required")
    return _exchange_canonical(frame,expected_server,pipe_name=CUSTODIAN_PIPE,deadline=deadline)


def exchange_identity_read(frame: bytes, expected_server: PinnedProcess) -> bytes:
    """Open frozen local pipe, pin server before writing, and read one frame."""
    if not isinstance(frame, bytes) or not 4 < len(frame) <= MAX_FRAME_BYTES:
        raise PipeSecurityError("outbound frame is outside the frozen bounds")
    from agent_lab.ipc_envelope import decode_and_validate_frame
    request = decode_and_validate_frame(frame)
    if request.message_type != "READ_IDENTITY_STATE":
        raise PipeSecurityError("protected mutations are not enabled")
    try:
        import win32con
        import win32file
        import win32pipe
        handle = win32file.CreateFile(
            IDENTITY_PIPE, win32con.GENERIC_READ | win32con.GENERIC_WRITE,
            0, None, win32con.OPEN_EXISTING, 0, None,
        )
        try:
            win32pipe.SetNamedPipeHandleState(handle, win32pipe.PIPE_READMODE_MESSAGE, None, None)
            verify_connected_server(handle, expected_server)
            win32file.WriteFile(handle, frame)
            _status, response = win32file.ReadFile(handle, MAX_FRAME_BYTES + 1)
            if not isinstance(response, bytes) or len(response) > MAX_FRAME_BYTES:
                raise PipeSecurityError("response exceeds frozen bounds")
            from agent_lab.ipc_response import decode_and_correlate_response
            decode_and_correlate_response(response, request)
            return response
        finally:
            win32file.CloseHandle(handle)
    except PipeSecurityError:
        raise
    except Exception as exc:
        raise PipeSecurityError("authenticated Identity pipe exchange unavailable") from exc
