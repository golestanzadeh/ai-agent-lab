"""Fail-closed transport tests without impersonating a Windows service."""
import pytest
from agent_lab.c09_named_pipe import PipeSecurityError
from agent_lab.c09_pipe_transport import exchange_identity_read


@pytest.mark.parametrize("frame", [b"", b"abcd", "not bytes"])
def test_invalid_outbound_frame_denied_before_open(frame):
    with pytest.raises(PipeSecurityError):
        exchange_identity_read(frame, None)


def test_oversized_outbound_frame_denied_before_open():
    with pytest.raises(PipeSecurityError):
        exchange_identity_read(b"x" * 65537, None)


def test_noncanonical_outbound_frame_denied_before_open():
    with pytest.raises(Exception):
        exchange_identity_read(b"\\x05\\x00\\x00\\x00hello", None)
