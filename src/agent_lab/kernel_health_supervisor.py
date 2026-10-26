"""Development-only bounded process supervisor for potentially blocked health server.

No SCM installation, service-token impersonation, or protected operations.
"""
from __future__ import annotations

import multiprocessing
import time

from agent_lab.kernel_health_pipe import (
    DevelopmentKernelHealthServer, KernelHealthTransportError, PIPE_NAME,
)


def _serve_child(deployment_id, ready):
    server = DevelopmentKernelHealthServer(deployment_id)
    try:
        server.start()
        ready.send(("ready", None))
        # Blocking pipe work remains in this disposable process.
        while True:
            time.sleep(0.05)
    except BaseException:
        try:
            ready.send(("error", None))
        except OSError:
            pass
    finally:
        ready.close()


class BoundedDevelopmentHealthRuntime:
    """A stuck pipe connection cannot prevent the supervisor's stop() from returning."""

    def __init__(self, deployment_id: str):
        self.deployment_id = deployment_id
        self._process = None

    def start(self):
        if self._process is not None:
            raise KernelHealthTransportError("health process already started")
        ctx = multiprocessing.get_context("spawn")
        receiver, sender = ctx.Pipe(duplex=False)
        process = ctx.Process(target=_serve_child, args=(self.deployment_id, sender), daemon=True)
        try:
            process.start()
            sender.close()
            if not receiver.poll(4):
                raise KernelHealthTransportError("health process startup deadline exceeded")
            status, _ = receiver.recv()
            if status != "ready" or not process.is_alive():
                raise KernelHealthTransportError("health process startup failed closed")
            self._process = process
        except BaseException:
            if process.is_alive():
                process.terminate()
                process.join(1)
            process.close()
            raise
        finally:
            receiver.close()
            sender.close()

    def stop(self):
        process = self._process
        if process is None:
            return
        try:
            if process.is_alive():
                process.terminate()
            process.join(1)
            if process.is_alive():
                process.kill()
                process.join(1)
            if process.is_alive():
                raise KernelHealthTransportError("health process could not be stopped")
        finally:
            process.close()
            self._process = None
