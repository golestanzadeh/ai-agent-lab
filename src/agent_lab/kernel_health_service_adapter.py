"""Explicit non-deployed composition adapter for existing C09 ServiceHost.

This module never installs/starts SCM, grants permissions or enables operations.
Actual Windows service role is still enforced by ServiceHost at its own boundary.
"""
from __future__ import annotations

from agent_lab.c09_service_host import (
    ROLE_BINDINGS, ServiceConfiguration, ServiceHost, ServiceHostError, ServiceRole,
)
from agent_lab.kernel_health_supervisor import BoundedDevelopmentHealthRuntime


class RestrictedHealthRuntime:
    def __init__(self, config: ServiceConfiguration):
        expected_name, expected_sid = ROLE_BINDINGS[ServiceRole.KERNEL]
        if (config.schema != "ai-tax-agent.c09-service-config/1.0"
                or not isinstance(config.deployment_id, str)
                or not config.deployment_id
                or len(config.deployment_id.encode("utf-8")) > 128
                or config.role is not ServiceRole.KERNEL or config.service_name != expected_name
                or config.principal_sid != expected_sid or config.enabled is not True):
            raise ServiceHostError("Kernel health runtime binding rejected")
        self._server = BoundedDevelopmentHealthRuntime(config.deployment_id)

    def start(self) -> None:
        self._server.start()

    def stop(self) -> None:
        self._server.stop()


def create_restricted_health_host() -> ServiceHost:
    """Construct host; does not call start or alter run_scm_service."""
    return ServiceHost(ServiceRole.KERNEL, RestrictedHealthRuntime)
