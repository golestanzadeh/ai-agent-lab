from unittest.mock import patch
import pytest

from agent_lab.c09_identity_client import correlate_identity_read, IdentityClientError
from agent_lab.c09_identity_client import exchange_validated_identity_read
from agent_lab.c09_identity_dispatch import dispatch_identity_read, IdentityDispatchError
from agent_lab.c09_named_pipe import PinnedProcess,MAX_FRAME_BYTES
from agent_lab.ipc_envelope import validate_envelope
from agent_lab.ipc_wire_primitives import encode_frame
from test_ipc_envelope import envelope
from test_ipc_response import response


def test_dispatch_denies_untrusted_kernel_before_read():
    called = []
    with patch("agent_lab.c09_identity_dispatch.authorize_connected_kernel", side_effect=RuntimeError("denied")):
        with pytest.raises(IdentityDispatchError):
            dispatch_identity_read(None, lambda n: called.append(n), lambda req: b"")
    assert called == []


def test_client_rejects_unvalidated_request_without_exchange():
    called = []
    with pytest.raises(IdentityClientError):
        correlate_identity_read(None, None, lambda *args: called.append(args))
    assert called == []


def test_dispatch_rejects_invalid_frame_without_handler():
    called = []
    with patch("agent_lab.c09_identity_dispatch.authorize_connected_kernel"):
        with pytest.raises(IdentityDispatchError):
            dispatch_identity_read(None, lambda n: b"invalid", lambda req: called.append(req))
    assert called == []


def read_frame():
    value=envelope(message_type="READ_IDENTITY_STATE",domain_operation="READ_FACTS",capability="identity_read")
    return encode_frame(value),validate_envelope(value)


def test_composed_read_exchange_preserves_request_and_correlates_response():
    frame,request=read_frame(); observed=[]
    pinned=PinnedProcess("S-TEST","C:/controlled/identity.exe","sha256:"+"a"*64)
    def transport(actual,expected):
        observed.append((actual,expected))
        return encode_frame(response(request,"READ_OK"))
    result=exchange_validated_identity_read(frame,pinned,transport)
    assert result.transaction_id==request.transaction_id and result.outcome=="READ_OK"
    assert observed==[(frame,pinned)]


@pytest.mark.parametrize("frame",[b"",b"bad",b"x"*(MAX_FRAME_BYTES+1),"not-bytes"],ids=["empty","malformed","oversized","wrong-type"])
def test_composed_exchange_rejects_malformed_before_transport(frame):
    called=[]
    with pytest.raises(IdentityClientError):
        exchange_validated_identity_read(frame,None,lambda *args:called.append(args))
    assert called==[]


def test_composed_exchange_rejects_mutations_before_transport():
    called=[]
    with pytest.raises(IdentityClientError):
        exchange_validated_identity_read(encode_frame(envelope()),None,lambda *args:called.append(args))
    assert called==[]


def test_composed_exchange_rejects_response_substitution_and_transport_failure():
    frame,request=read_frame()
    wrong=response(request,"READ_OK");wrong["transaction_id"]="tx:v1:123e4567-e89b-42d3-a456-426614174001"
    with pytest.raises(IdentityClientError):
        exchange_validated_identity_read(frame,None,lambda *args:encode_frame(wrong))
    def unavailable(*args):raise RuntimeError("controlled disconnection")
    with pytest.raises(IdentityClientError):
        exchange_validated_identity_read(frame,None,unavailable)


def test_composed_exchange_uses_existing_native_transport_by_default():
    frame,request=read_frame()
    with patch("agent_lab.c09_pipe_transport.exchange_identity_read",return_value=encode_frame(response(request,"DENIED","AUTHORIZATION_DENIED"))) as native:
        result=exchange_validated_identity_read(frame,None)
    native.assert_called_once_with(frame,None)
    assert result.outcome=="DENIED"
