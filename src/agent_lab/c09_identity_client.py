"""Kernel-side authenticated Identity read client boundary.

Transport is injected; this module does not claim live SCM activation.
"""
from __future__ import annotations

from typing import Callable
from agent_lab.c09_named_pipe import (
    IDENTITY_PIPE, MAX_FRAME_BYTES, PinnedProcess, ProcessEvidence,
    verify_process_evidence,
)
from agent_lab.ipc_envelope import ValidatedEnvelope, decode_and_validate_frame
from agent_lab.ipc_response import CorrelatedResponse, decode_and_correlate_response


class IdentityClientError(RuntimeError):
    pass


def correlate_identity_read(
    request: ValidatedEnvelope,
    expected_server: PinnedProcess,
    exchange: Callable[[str, ValidatedEnvelope], tuple[ProcessEvidence, bytes]],
) -> CorrelatedResponse:
    if not isinstance(request, ValidatedEnvelope) or request.message_type != "READ_IDENTITY_STATE":
        raise IdentityClientError("only validated read requests are supported")
    try:
        evidence, frame = exchange(IDENTITY_PIPE, request)
        verify_process_evidence(evidence, expected_server)
        if not isinstance(frame, bytes) or len(frame) > MAX_FRAME_BYTES:
            raise IdentityClientError("invalid response frame")
        return decode_and_correlate_response(frame, request)
    except Exception as exc:
        raise IdentityClientError("Identity peer or response rejected") from exc


def exchange_validated_identity_read(
    request_frame: bytes,
    expected_server: PinnedProcess,
    transport: Callable[[bytes, PinnedProcess], bytes] | None = None,
) -> CorrelatedResponse:
    """Compose the existing canonical transport with strict response correlation."""
    try:
        if not isinstance(request_frame, bytes) or len(request_frame) > MAX_FRAME_BYTES:
            raise IdentityClientError("invalid request frame")
        request = decode_and_validate_frame(request_frame)
        if request.message_type != "READ_IDENTITY_STATE":
            raise IdentityClientError("only read requests are supported")
        if transport is None:
            from agent_lab.c09_pipe_transport import exchange_identity_read
            transport = exchange_identity_read
        response_frame = transport(request_frame, expected_server)
        return decode_and_correlate_response(response_frame, request)
    except Exception as exc:
        raise IdentityClientError("Identity read exchange rejected") from exc
