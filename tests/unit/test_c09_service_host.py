import json
from pathlib import Path

import pytest

from agent_lab.c09_service_host import (
    Lifecycle, ROLE_BINDINGS, ServiceConfiguration, ServiceHost, ServiceHostError, ServiceRole,
)


class Runtime:
    def __init__(self, fail_start=False, fail_stop=False):
        self.fail_start = fail_start; self.fail_stop = fail_stop
    def start(self):
        if self.fail_start: raise RuntimeError("start")
    def stop(self):
        if self.fail_stop: raise RuntimeError("stop")


def config(role=ServiceRole.KERNEL):
    name, sid = ROLE_BINDINGS[role]
    return ServiceConfiguration("ai-tax-agent.c09-service-config/1.0", "C09-R3-SYNTHETIC", role, name, sid, True)


def test_each_role_has_a_distinct_fixed_entry_point_and_identity():
    assert len({value[0] for value in ROLE_BINDINGS.values()}) == 3
    assert len({value[1] for value in ROLE_BINDINGS.values()}) == 3
    root = Path(__file__).resolve().parents[2]
    for role, module in ((ServiceRole.KERNEL, "c09_kernel_service.py"), (ServiceRole.IDENTITY, "c09_identity_service.py"), (ServiceRole.KEY_CUSTODIAN, "c09_custodian_service.py")):
        text = (root / "src/agent_lab" / module).read_text(encoding="utf-8")
        assert f"ServiceRole.{role.name}" in text
        assert "argv" not in text and "HandleCommandLine" not in text


def test_lifecycle_starts_and_stops_deterministically():
    candidate = config(); host = ServiceHost(candidate.role, lambda _cfg: Runtime())
    host.start(candidate, candidate.principal_sid)
    assert host.state is Lifecycle.RUNNING
    host.stop(); assert host.state is Lifecycle.STOPPED
    host.stop(); assert host.state is Lifecycle.STOPPED


def test_wrong_actual_sid_and_role_substitution_halt():
    candidate = config()
    host = ServiceHost(candidate.role, lambda _cfg: Runtime())
    with pytest.raises(ServiceHostError, match="unauthorized"):
        host.start(candidate, ROLE_BINDINGS[ServiceRole.IDENTITY][1])
    assert host.state is Lifecycle.HALTED
    host = ServiceHost(ServiceRole.IDENTITY, lambda _cfg: Runtime())
    with pytest.raises(ServiceHostError, match="unauthorized"):
        host.start(candidate, candidate.principal_sid)


def test_start_and_stop_fail_closed():
    candidate = config(); host = ServiceHost(candidate.role, lambda _cfg: Runtime(fail_start=True))
    with pytest.raises(ServiceHostError, match="startup"):
        host.start(candidate, candidate.principal_sid)
    assert host.state is Lifecycle.HALTED
    host = ServiceHost(candidate.role, lambda _cfg: Runtime(fail_stop=True))
    host.start(candidate, candidate.principal_sid)
    with pytest.raises(ServiceHostError, match="shutdown"):
        host.stop()
    assert host.state is Lifecycle.HALTED


@pytest.mark.parametrize("change", [
    lambda p: p.update(role="IDENTITY"), lambda p: p.update(service_name="Other"),
    lambda p: p.update(principal_sid=ROLE_BINDINGS[ServiceRole.IDENTITY][1]), lambda p: p.update(enabled=False),
    lambda p: p.update(schema="unknown"), lambda p: p.update(extra="value"),
])
def test_config_loader_rejects_invalid_or_substituted_configuration(tmp_path, change):
    name, sid = ROLE_BINDINGS[ServiceRole.KERNEL]
    payload = {"schema": "ai-tax-agent.c09-service-config/1.0", "deployment_id": "C09-R3-SYNTHETIC", "role": "KERNEL", "service_name": name, "principal_sid": sid, "enabled": True}
    change(payload); path = tmp_path / "service.json"; path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ServiceHostError):
        ServiceConfiguration.load(path, ServiceRole.KERNEL)


def test_missing_and_malformed_configuration_fail_closed(tmp_path):
    with pytest.raises(ServiceHostError): ServiceConfiguration.load(tmp_path / "missing.json", ServiceRole.KERNEL)
    path = tmp_path / "bad.json"; path.write_text("{", encoding="utf-8")
    with pytest.raises(ServiceHostError): ServiceConfiguration.load(path, ServiceRole.KERNEL)
