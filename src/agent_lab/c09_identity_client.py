"""Kernel-side authenticated Identity read client boundary.

Transport is injected; this module does not claim live SCM activation.
"""
from __future__ import annotations

from typing import Callable
from agent_lab.c09_named_pipe import (
    IDENTITY_PIPE, MAX_FRAME_BYTES, PinnedProcess, ProcessEvidence,
    verify_process_evidence,
)
from agent_lab.ipc_envelope import ValidatedEnvelope
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
