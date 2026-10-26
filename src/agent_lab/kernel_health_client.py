"""Fail-closed, bounded development Kernel health client with pinned peer evidence.

A separate spawned worker is forcibly terminated on deadline; no unbounded
ReadFile/WriteFile in the caller. Not an operational service authorization.
"""
from __future__ import annotations

import multiprocessing
import queue
import uuid

from agent_lab.c09_named_pipe import PinnedProcess, verify_connected_server
from agent_lab.kernel_health_contract import MAX_BYTES, encode_request, validate_response
from agent_lab.kernel_health_pipe import PIPE_NAME, KernelHealthTransportError, _win32, _read_message


def _exchange(deployment_id: str, expected: PinnedProcess, timeout_ms: int) -> dict:
    pyw, _, con, _, file, pipe, _ = _win32()
    handle = None
    try:
        pipe.WaitNamedPipe(PIPE_NAME, timeout_ms)
        handle = file.CreateFile(PIPE_NAME, con.GENERIC_READ | con.GENERIC_WRITE, 0, None, con.OPEN_EXISTING, 0, None)
        verify_connected_server(handle, expected)
        pipe.SetNamedPipeHandleState(handle, pipe.PIPE_READMODE_MESSAGE, None, None)
        request = encode_request(deployment_id, str(uuid.uuid4()))
        file.WriteFile(handle, request)
        return validate_response(_read_message(handle), request)
    finally:
        if handle is not None:
            file.CloseHandle(handle)


def _worker(result_queue, deployment_id, expected, timeout_ms):
    try:
        result_queue.put(("ok", _exchange(deployment_id, expected, timeout_ms)))
    except BaseException:
        result_queue.put(("error", None))


def query_health_bounded(deployment_id: str, expected: PinnedProcess, *, timeout_ms: int = 2000) -> dict:
    """Enforce wall-clock deadline, including blocked peer I/O and process cleanup."""
    if not isinstance(timeout_ms, int) or isinstance(timeout_ms, bool) or not 100 <= timeout_ms <= 10000:
        raise KernelHealthTransportError("invalid health deadline")
    if not isinstance(expected, PinnedProcess) or not expected.sid or not expected.image_path or not expected.image_sha256:
        raise KernelHealthTransportError("missing pinned server identity")
    encode_request(deployment_id, "validation")
    context = multiprocessing.get_context("spawn")
    result_queue = context.Queue(maxsize=1)
    process = context.Process(target=_worker, args=(result_queue, deployment_id, expected, timeout_ms), daemon=True)
    try:
        process.start()
        process.join(timeout_ms / 1000)
        if process.is_alive():
            process.terminate()
            process.join(2)
            if process.is_alive():
                process.kill()
                process.join(2)
            raise KernelHealthTransportError("health deadline exceeded")
        try:
            status, payload = result_queue.get(timeout=0.5)
        except queue.Empty as exc:
            raise KernelHealthTransportError("health worker failed without response") from exc
        if status != "ok" or process.exitcode != 0:
            raise KernelHealthTransportError("health peer verification or communication failed")
        return payload
    finally:
        result_queue.close()
        result_queue.join_thread()
        if process.is_alive():
            process.kill()
            process.join(2)
        process.close()
