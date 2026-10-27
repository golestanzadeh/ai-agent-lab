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


def dispatch_operational_identity_read(pipe_handle,read_message,authority,public_key,*,
                                       expected_scope,expected_key_id,now=None):
    """Authenticated/audited denial until logical continuity bootstrap is accepted.

    This deliberately has no arbitrary read handler or trusted-head callback.
    It cannot return READ_OK or promote the development dispatcher.
    """
    from datetime import datetime,timezone
    from agent_lab.c09_named_pipe import MAX_FRAME_BYTES
    from agent_lab.identity_persistence import IdentityPersistence
    from agent_lab.ipc_operational_read import validate_request,validate_response
    from agent_lab.ipc_wire_primitives import decode_frame,canonical_sha256,encode_frame
    try:
        authorize_connected_kernel(pipe_handle)
        if not isinstance(authority,IdentityPersistence):raise IdentityDispatchError("existing Identity authority required")
        request=decode_frame(read_message(MAX_FRAME_BYTES+1))
        validate_request(request,public_key,expected_scope=expected_scope,
            expected_key_id=expected_key_id,now=now or datetime.now(timezone.utc).replace(tzinfo=None))
        authority.record_ipc_boundary_denial(case_id=request["case_id"],tax_year=int(request["tax_year"]),
            request_digest=request["request_digest"],operation=request["domain_operation"])
        response={name:request[name] for name in ("contract","message_type","transaction_id","request_digest")}
        response.update(outcome="DENIED",identity_epoch="",identity_head="",staged_receipt_digest="",
            witness_preimage_digest="",signed_record_digest="",denial_code="TEMPORARY_FAILURE",result="")
        response["response_digest"]=canonical_sha256(response)
        validate_response(response,request)
        return encode_frame(response)
    except Exception as exc:raise IdentityDispatchError("operational boundary rejected without domain access") from exc


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
