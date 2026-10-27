"""Authenticated Identity read dispatcher boundary.

No operational persistence authority is conferred by the development IPC
contract. Mutation and all unknown messages fail closed.
"""
from __future__ import annotations

from typing import Callable
from agent_lab.c09_named_pipe import (
    PipeSecurityError, authorize_connected_kernel, read_identity_request,
)
from agent_lab.ipc_envelope import ValidatedEnvelope


class IdentityDispatchError(RuntimeError):
    pass


def dispatch_identity_read(
    pipe_handle: object,
    read_message: Callable[[int], bytes],
    read_handler: Callable[[ValidatedEnvelope], bytes],
) -> bytes:
    """Authorize actual connected Kernel token before parsing or dispatch."""
    try:
        authorize_connected_kernel(pipe_handle)
        request = read_identity_request(read_message)
        if request.message_type != "READ_IDENTITY_STATE":
            raise IdentityDispatchError("mutation dispatch is not operationally accepted")
        response = read_handler(request)
        if not isinstance(response, bytes):
            raise IdentityDispatchError("read handler must return a canonical frame")
        from agent_lab.ipc_response import decode_and_correlate_response
        decode_and_correlate_response(response, request)
        return response
    except IdentityDispatchError:
        raise
    except Exception as exc:
        raise IdentityDispatchError("authenticated Identity read dispatch rejected") from exc
