"""Real Windows local Named Pipe smoke, no SCM or protected credentials."""
import sys
import pytest

from agent_lab.kernel_health_pipe import (
    DevelopmentKernelHealthServer, KernelHealthTransportError, query_health,
)

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows Named Pipe only")


def test_real_named_pipe_roundtrip_and_shutdown():
    server = DevelopmentKernelHealthServer("development-1")
    server.start()
    try:
        result = query_health("development-1")
        assert result["status"] == "ALIVE_RESTRICTED"
        assert result["deployment_id"] == "development-1"
        with pytest.raises(KernelHealthTransportError):
            query_health("wrong-deployment")
    finally:
        server.stop()
    with pytest.raises(KernelHealthTransportError):
        query_health("development-1", timeout_ms=100)


def test_invalid_timeout_rejected():
    for value in (0, -1, 5001, True, "100"):
        with pytest.raises(KernelHealthTransportError):
            query_health("development-1", timeout_ms=value)


def test_second_server_cannot_take_first_instance():
    first = DevelopmentKernelHealthServer("development-1")
    second = DevelopmentKernelHealthServer("development-1")
    first.start()
    try:
        with pytest.raises(KernelHealthTransportError):
            second.start()
    finally:
        first.stop()
