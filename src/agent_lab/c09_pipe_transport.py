"""Bounded Windows Named Pipe exchange, restricted to read-only Identity IPC.

This is a transport component, not deployment authorization.
"""
from __future__ import annotations

from agent_lab.c09_named_pipe import (
    IDENTITY_PIPE, MAX_FRAME_BYTES, PinnedProcess, PipeSecurityError,
    verify_connected_server,
)


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
