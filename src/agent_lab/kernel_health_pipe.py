"""Development-only Windows Named Pipe Kernel HEALTH transport.

Not SCM deployment, protected dispatcher, Identity authority, or production readiness.
The peer ACL is limited to the *current* Windows user for local integration tests.
"""
from __future__ import annotations

import threading
import uuid

from agent_lab.kernel_health_contract import MAX_BYTES, HealthProtocolError, encode_request, handle_request, validate_response


class KernelHealthTransportError(RuntimeError):
    pass


PIPE_NAME = r"\\.\pipe\AI-Tax-Agent-Kernel-Health-Dev-v1"


def _win32():
    try:
        import pywintypes
        import win32api
        import win32con
        import win32event
        import win32file
        import win32pipe
        import win32security
        return pywintypes, win32api, win32con, win32event, win32file, win32pipe, win32security
    except ImportError as exc:
        raise KernelHealthTransportError("Windows Named Pipe support unavailable") from exc


def _current_sid():
    _, api, con, _, _, _, sec = _win32()
    token = sec.OpenProcessToken(api.GetCurrentProcess(), con.TOKEN_QUERY)
    sid, _ = sec.GetTokenInformation(token, sec.TokenUser)
    return sec.ConvertSidToStringSid(sid)


def _read_message(handle):
    pyw, _, _, _, file, _, _ = _win32()
    try:
        status, data = file.ReadFile(handle, MAX_BYTES + 1)
        if status != 0 or not isinstance(data, bytes) or len(data) > MAX_BYTES:
            raise KernelHealthTransportError("invalid health message size")
        return data
    except pyw.error as exc:
        raise KernelHealthTransportError("health pipe read failed") from exc


class DevelopmentKernelHealthServer:
    """Single-instance, single-request-per-connection, current-user-only local endpoint."""

    def __init__(self, deployment_id: str, pipe_name: str = PIPE_NAME):
        encode_request(deployment_id, "validation")
        if pipe_name != PIPE_NAME:
            raise KernelHealthTransportError("unapproved health endpoint")
        self.deployment_id = deployment_id
        self.pipe_name = pipe_name
        self._thread = None
        self._stop = threading.Event()
        self._ready = threading.Event()
        self._failure = None

    def start(self):
        if self._thread is not None:
            raise KernelHealthTransportError("already started")
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()
        if not self._ready.wait(5) or self._failure:
            raise KernelHealthTransportError("health server failed to start") from self._failure

    def _serve(self):
        pyw, _, con, _, file, pipe, sec = _win32()
        handle = None
        try:
            sid = _current_sid()
            sddl = "D:P(A;;GA;;;SY)(A;;GRGW;;;" + sid + ")"
            descriptor = sec.ConvertStringSecurityDescriptorToSecurityDescriptor(sddl, sec.SDDL_REVISION_1)
            attrs = pyw.SECURITY_ATTRIBUTES()
            attrs.SECURITY_DESCRIPTOR = descriptor
            handle = pipe.CreateNamedPipe(
                self.pipe_name, pipe.PIPE_ACCESS_DUPLEX | pipe.FILE_FLAG_FIRST_PIPE_INSTANCE,
                pipe.PIPE_TYPE_MESSAGE | pipe.PIPE_READMODE_MESSAGE | pipe.PIPE_WAIT | pipe.PIPE_REJECT_REMOTE_CLIENTS,
                1, MAX_BYTES + 1, MAX_BYTES + 1, 1000, attrs)
            self._ready.set()
            while not self._stop.is_set():
                try:
                    pipe.ConnectNamedPipe(handle, None)
                except pyw.error as exc:
                    if exc.winerror != 535:  # ERROR_PIPE_CONNECTED
                        raise
                try:
                    request = _read_message(handle)
                    sec.ImpersonateNamedPipeClient(handle)
                    try:
                        token = sec.OpenThreadToken(__import__("win32api").GetCurrentThread(), con.TOKEN_QUERY, True)
                        actual, _ = sec.GetTokenInformation(token, sec.TokenUser)
                        if sec.ConvertSidToStringSid(actual) != sid:
                            raise KernelHealthTransportError("client identity mismatch")
                    finally:
                        sec.RevertToSelf()
                    response = handle_request(request, self.deployment_id)
                    file.WriteFile(handle, response)
                except (KernelHealthTransportError, HealthProtocolError, pyw.error) as exc:
                    self._failure = exc  # diagnostic only; never return failure details to peer
                finally:
                    try:
                        pipe.DisconnectNamedPipe(handle)
                    except pyw.error:
                        pass
        except Exception as exc:
            self._failure = exc
            self._ready.set()
        finally:
            if handle is not None:
                file.CloseHandle(handle)

    def stop(self):
        self._stop.set()
        if self._thread is None:
            return
        try:
            query_health(self.deployment_id, timeout_ms=1000)
        except KernelHealthTransportError:
            pass
        self._thread.join(timeout=3)
        if self._thread.is_alive():
            raise KernelHealthTransportError("health server did not stop")
        self._thread = None


def query_health(deployment_id: str, *, timeout_ms: int = 2000) -> dict:
    """Local development probe only; does NOT authenticate a production service image."""
    if not isinstance(timeout_ms, int) or isinstance(timeout_ms, bool) or not 1 <= timeout_ms <= 5000:
        raise KernelHealthTransportError("invalid timeout")
    request = encode_request(deployment_id, str(uuid.uuid4()))
    pyw, _, con, _, file, pipe, _ = _win32()
    handle = None
    try:
        pipe.WaitNamedPipe(PIPE_NAME, timeout_ms)
        handle = file.CreateFile(PIPE_NAME, con.GENERIC_READ | con.GENERIC_WRITE, 0, None, con.OPEN_EXISTING, 0, None)
        pipe.SetNamedPipeHandleState(handle, pipe.PIPE_READMODE_MESSAGE, None, None)
        file.WriteFile(handle, request)
        response = _read_message(handle)
        return validate_response(response, request)
    except (pyw.error, HealthProtocolError, KernelHealthTransportError) as exc:
        raise KernelHealthTransportError("Kernel health communication failed closed") from exc
    finally:
        if handle is not None:
            file.CloseHandle(handle)
