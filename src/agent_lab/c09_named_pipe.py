"""Windows-local authenticated Named Pipe transport for the frozen C09 boundary."""
from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
import hashlib
from pathlib import Path
from typing import Callable

from agent_lab.ipc_envelope import ValidatedEnvelope, decode_and_validate_frame
from agent_lab.ipc_wire_primitives import MAX_PAYLOAD_BYTES, decode_frame


class PipeSecurityError(RuntimeError):
    pass


IDENTITY_PIPE = r"\\.\pipe\AI-Tax-Agent\Identity-v1"
CUSTODIAN_PIPE = r"\\.\pipe\AI-Tax-Agent\Custodian-v1"
KERNEL_SID = "S-1-5-21-212838446-3778166418-3746953556-1020"
MAX_FRAME_BYTES = MAX_PAYLOAD_BYTES + 4


@dataclass(frozen=True, slots=True)
class PinnedProcess:
    sid: str
    image_path: str
    image_sha256: str


@dataclass(frozen=True, slots=True)
class ProcessEvidence:
    sid: str
    image_path: str
    image_sha256: str
    pid_before: int
    pid_after: int


def verify_process_evidence(actual: ProcessEvidence, expected: PinnedProcess) -> None:
    if actual.pid_before <= 0 or actual.pid_before != actual.pid_after:
        raise PipeSecurityError("peer PID turnover detected")
    if actual.sid != expected.sid:
        raise PipeSecurityError("peer SID mismatch")
    if str(Path(actual.image_path)).casefold() != str(Path(expected.image_path)).casefold():
        raise PipeSecurityError("peer image path mismatch")
    if actual.image_sha256 != expected.image_sha256 or not actual.image_sha256.startswith("sha256:"):
        raise PipeSecurityError("peer image digest mismatch")


def kernel_only_sddl() -> str:
    return f"D:P(A;;GA;;;SY)(A;;GRGW;;;{KERNEL_SID})"


def read_one_canonical_message(read_message: Callable[[int], bytes]) -> tuple[bytes, dict]:
    frame = read_message(MAX_FRAME_BYTES + 1)
    if not isinstance(frame, bytes) or len(frame) > MAX_FRAME_BYTES:
        raise PipeSecurityError("pipe message exceeds the canonical frame bound")
    try:
        return frame, decode_frame(frame)
    except Exception as exc:
        raise PipeSecurityError("malformed or noncanonical pipe frame") from exc


def read_identity_request(read_message: Callable[[int], bytes]) -> ValidatedEnvelope:
    frame, _value = read_one_canonical_message(read_message)
    try:
        return decode_and_validate_frame(frame)
    except Exception as exc:
        raise PipeSecurityError("invalid Identity request envelope") from exc


def actual_named_pipe_client_sid(pipe_handle) -> str:
    """Impersonate the connected client and always revert before dispatch."""
    try:
        import win32api
        import win32con
        import win32pipe
        import win32security
        win32pipe.ImpersonateNamedPipeClient(pipe_handle)
        try:
            token = win32security.OpenThreadToken(win32api.GetCurrentThread(), win32con.TOKEN_QUERY, True)
            try:
                sid, _attributes = win32security.GetTokenInformation(token, win32security.TokenUser)
                return win32security.ConvertSidToStringSid(sid)
            finally:token.Close()
        finally:
            win32security.RevertToSelf()
    except Exception as exc:
        raise PipeSecurityError("actual Named Pipe client token is unavailable") from exc


def authorize_connected_kernel(pipe_handle) -> None:
    if actual_named_pipe_client_sid(pipe_handle) != KERNEL_SID:
        raise PipeSecurityError("connected client is not the pinned Kernel principal")


@contextmanager
def retain_verified_server(pipe_handle, expected: PinnedProcess, *, checkpoint=None):
    """Retain the server process handle, verify token/image/hash, then reject PID turnover."""
    process=token=None
    try:
        import win32api
        import win32con
        import win32pipe
        import win32process
        import win32security
        if checkpoint:checkpoint()
        pid_before = win32pipe.GetNamedPipeServerProcessId(pipe_handle)
        process = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid_before)
        token = win32security.OpenProcessToken(process, win32con.TOKEN_QUERY)
        sid, _attributes = win32security.GetTokenInformation(token, win32security.TokenUser)
        image_path = win32process.GetModuleFileNameEx(process, 0)
        pid_after = win32pipe.GetNamedPipeServerProcessId(pipe_handle)
        evidence = ProcessEvidence(win32security.ConvertSidToStringSid(sid), image_path, sha256_file(image_path,checkpoint=checkpoint), pid_before, pid_after)
        verify_process_evidence(evidence, expected)
        yield evidence
    except PipeSecurityError:
        raise
    except Exception as exc:
        raise PipeSecurityError("connected server identity is unavailable") from exc
    finally:
        if token is not None:token.Close()
        if process is not None:process.Close()


def verify_connected_server(pipe_handle, expected: PinnedProcess) -> ProcessEvidence:
    with retain_verified_server(pipe_handle,expected) as evidence:return evidence


def create_kernel_only_server(pipe_name: str, *, overlapped: bool = False):
    if pipe_name not in {IDENTITY_PIPE, CUSTODIAN_PIPE}:
        raise PipeSecurityError("pipe name is not frozen")
    try:
        import ntsecuritycon
        import pywintypes
        import win32con
        import win32pipe
        import win32security
        descriptor = win32security.ConvertStringSecurityDescriptorToSecurityDescriptor(kernel_only_sddl(), win32security.SDDL_REVISION_1)
        attributes = pywintypes.SECURITY_ATTRIBUTES(); attributes.SECURITY_DESCRIPTOR = descriptor
        access = win32pipe.PIPE_ACCESS_DUPLEX | win32pipe.FILE_FLAG_FIRST_PIPE_INSTANCE
        if overlapped:access |= win32con.FILE_FLAG_OVERLAPPED
        mode = win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT | win32pipe.PIPE_REJECT_REMOTE_CLIENTS
        return win32pipe.CreateNamedPipe(pipe_name, access, mode, 1, MAX_FRAME_BYTES, MAX_FRAME_BYTES, 5000, attributes)
    except Exception as exc:
        raise PipeSecurityError("secure first-instance Named Pipe creation failed") from exc


def sha256_file(path: str, *, checkpoint=None) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            if checkpoint:checkpoint()
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()
