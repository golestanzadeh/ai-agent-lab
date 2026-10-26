from agent_lab.c09_service_host import (
    Lifecycle, ROLE_BINDINGS, ServiceConfiguration, ServiceHostError, ServiceRole,
)
from agent_lab.kernel_health_service_adapter import create_restricted_health_host
from agent_lab.kernel_health_pipe import _current_sid
import pytest


def _config():
    name, sid = ROLE_BINDINGS[ServiceRole.KERNEL]
    return ServiceConfiguration(
        "ai-tax-agent.c09-service-config/1.0", "deployment-1",
        ServiceRole.KERNEL, name, sid, True,
    )


def test_existing_host_rejects_unprivileged_windows_user():
    host = create_restricted_health_host()
    assert host.state is Lifecycle.STOPPED
    with pytest.raises(ServiceHostError, match="unauthorized"):
        host.start(_config(), _current_sid())
    assert host.state is Lifecycle.HALTED


def test_existing_host_lifecycle_synthetic_only():
    host = create_restricted_health_host()
    config = _config()
    # Simulated SID argument tests lifecycle only; not operational identity evidence.
    host.start(config, config.principal_sid)
    try:
        assert host.state is Lifecycle.RUNNING
    finally:
        host.stop()
    assert host.state is Lifecycle.STOPPED
