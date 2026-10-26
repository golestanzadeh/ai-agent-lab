"""Real pinned-peer and deadline tests for development transport."""
import sys
import time

import pytest

from agent_lab.c09_named_pipe import PinnedProcess, sha256_file
from agent_lab.kernel_health_client import query_health_bounded
from agent_lab.kernel_health_pipe import (
    DevelopmentKernelHealthServer, KernelHealthTransportError, _current_sid,
)

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows only")


def _expected():
    import win32api
    import win32process
    path = win32process.GetModuleFileNameEx(win32api.GetCurrentProcess(), 0)
    return PinnedProcess(_current_sid(), path, sha256_file(path))


def test_bounded_pinned_roundtrip():
    server = DevelopmentKernelHealthServer("deployment-1")
    server.start()
    try:
        result = query_health_bounded("deployment-1", _expected(), timeout_ms=5000)
        assert result["status"] == "ALIVE_RESTRICTED"
    finally:
        server.stop()


def test_wrong_pinned_sid_fails_closed():
    server = DevelopmentKernelHealthServer("deployment-1")
    server.start()
    try:
        expected = _expected()
        wrong = PinnedProcess("S-1-5-18", expected.image_path, expected.image_sha256)
        with pytest.raises(KernelHealthTransportError):
            query_health_bounded("deployment-1", wrong, timeout_ms=5000)
    finally:
        server.stop()


def test_deadline_for_missing_endpoint():
    start = time.monotonic()
    with pytest.raises(KernelHealthTransportError):
        query_health_bounded("deployment-1", _expected(), timeout_ms=1200)
    assert time.monotonic() - start < 4


def test_missing_pin_denied():
    with pytest.raises(KernelHealthTransportError):
        query_health_bounded("deployment-1", PinnedProcess("", "", ""))
