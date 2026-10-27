from unittest.mock import patch
import pytest

from agent_lab.c09_identity_client import correlate_identity_read, IdentityClientError
from agent_lab.c09_identity_dispatch import dispatch_identity_read, IdentityDispatchError


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
