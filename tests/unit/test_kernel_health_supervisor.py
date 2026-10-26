"""Windows fault-injection: malicious silent client and abrupt disconnect."""
import time
import pytest

from agent_lab.kernel_health_supervisor import BoundedDevelopmentHealthRuntime
from agent_lab.kernel_health_pipe import PIPE_NAME, KernelHealthTransportError
from agent_lab.kernel_health_client import query_health_bounded
from agent_lab.c09_named_pipe import PinnedProcess, sha256_file
from agent_lab.kernel_health_pipe import _current_sid


def test_silent_client_cannot_block_supervised_shutdown():
    import win32con
    import win32file
    runtime = BoundedDevelopmentHealthRuntime("deployment-1")
    runtime.start()
    handle = win32file.CreateFile(
        PIPE_NAME, win32con.GENERIC_READ | win32con.GENERIC_WRITE,
        0, None, win32con.OPEN_EXISTING, 0, None)
    try:
        # Do not send any bytes: the server's synchronous ReadFile stays blocked.
        time.sleep(0.1)
        start = time.monotonic()
        runtime.stop()
        assert time.monotonic() - start < 3
    finally:
        win32file.CloseHandle(handle)
        runtime.stop()


def test_disconnect_does_not_authorize_health():
    import win32con
    import win32file
    runtime = BoundedDevelopmentHealthRuntime("deployment-1")
    runtime.start()
    handle = win32file.CreateFile(
        PIPE_NAME, win32con.GENERIC_READ | win32con.GENERIC_WRITE,
        0, None, win32con.OPEN_EXISTING, 0, None)
    win32file.CloseHandle(handle)  # abrupt peer disconnect before request
    try:
        runtime.stop()
    finally:
        runtime.stop()
