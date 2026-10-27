"""Fail-closed Windows SCM host primitives for the three fixed C09 roles."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import threading
from typing import Callable, Protocol


class ServiceHostError(RuntimeError):
    pass


class ServiceRole(str, Enum):
    KERNEL = "KERNEL"
    IDENTITY = "IDENTITY"
    KEY_CUSTODIAN = "KEY_CUSTODIAN"


class Lifecycle(str, Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    HALTED = "HALTED"


ROLE_BINDINGS = {
    ServiceRole.KERNEL: ("AITaxKernel", "S-1-5-21-212838446-3778166418-3746953556-1020"),
    ServiceRole.IDENTITY: ("AITaxIdentity", "S-1-5-21-212838446-3778166418-3746953556-1021"),
    ServiceRole.KEY_CUSTODIAN: ("AITaxKeyCustodian", "S-1-5-21-212838446-3778166418-3746953556-1022"),
}
CONFIG_ROOT = Path(r"C:\ProgramData\AI-Tax-Agent\Config")


@dataclass(frozen=True, slots=True)
class ServiceConfiguration:
    schema: str
    deployment_id: str
    role: ServiceRole
    service_name: str
    principal_sid: str
    enabled: bool

    @classmethod
    def load(cls, path: Path, expected_role: ServiceRole) -> "ServiceConfiguration":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ServiceHostError("service configuration is unavailable or malformed") from exc
        required = {"schema", "deployment_id", "role", "service_name", "principal_sid", "enabled"}
        if not isinstance(payload, dict) or set(payload) != required:
            raise ServiceHostError("service configuration has an unknown or incomplete schema")
        try:
            role = ServiceRole(payload["role"])
        except (TypeError, ValueError) as exc:
            raise ServiceHostError("service role is invalid") from exc
        expected_name, expected_sid = ROLE_BINDINGS[expected_role]
        if payload["schema"] != "ai-tax-agent.c09-service-config/1.0" or role is not expected_role:
            raise ServiceHostError("service role substitution denied")
        if payload["service_name"] != expected_name or payload["principal_sid"] != expected_sid:
            raise ServiceHostError("service identity does not match the pinned manifest")
        if not isinstance(payload["deployment_id"], str) or not payload["deployment_id"] or len(payload["deployment_id"].encode()) > 128:
            raise ServiceHostError("deployment identity is invalid")
        if payload["enabled"] is not True:
            raise ServiceHostError("service configuration is disabled")
        return cls(payload["schema"], payload["deployment_id"], role, expected_name, expected_sid, True)


class ComponentRuntime(Protocol):
    def start(self) -> None: ...
    def stop(self) -> None: ...


class ServiceHost:
    def __init__(self, role: ServiceRole, runtime_factory: Callable[[ServiceConfiguration], ComponentRuntime]) -> None:
        self.role = role
        self._runtime_factory = runtime_factory
        self._runtime: ComponentRuntime | None = None
        self._state = Lifecycle.STOPPED
        self._lock = threading.Lock()

    @property
    def state(self) -> Lifecycle:
        return self._state

    def start(self, config: ServiceConfiguration, actual_sid: str) -> None:
        with self._lock:
            if self._state is not Lifecycle.STOPPED:
                raise ServiceHostError("service start is not valid in the current state")
            self._state = Lifecycle.STARTING
            if config.role is not self.role or actual_sid != config.principal_sid:
                self._state = Lifecycle.HALTED
                raise ServiceHostError("actual Windows service principal is unauthorized")
            try:
                runtime = self._runtime_factory(config)
                runtime.start()
            except Exception as exc:
                self._state = Lifecycle.HALTED
                raise ServiceHostError("component startup failed closed") from exc
            self._runtime = runtime
            self._state = Lifecycle.RUNNING

    def stop(self) -> None:
        with self._lock:
            if self._state is Lifecycle.STOPPED:
                return
            if self._state is not Lifecycle.RUNNING or self._runtime is None:
                self._state = Lifecycle.HALTED
                raise ServiceHostError("service cannot stop cleanly from the current state")
            self._state = Lifecycle.STOPPING
            try:
                self._runtime.stop()
            except Exception as exc:
                self._state = Lifecycle.HALTED
                raise ServiceHostError("component shutdown failed closed") from exc
            self._runtime = None
            self._state = Lifecycle.STOPPED


def current_process_sid() -> str:
    """Read the actual process token; no caller-supplied identity is accepted."""
    try:
        import win32api
        import win32con
        import win32security
        token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY)
        sid, _attributes = win32security.GetTokenInformation(token, win32security.TokenUser)
        return win32security.ConvertSidToStringSid(sid)
    except Exception as exc:
        raise ServiceHostError("actual Windows process token is unavailable") from exc


def fixed_config_path(role: ServiceRole) -> Path:
    return CONFIG_ROOT / f"{ROLE_BINDINGS[role][0]}.json"


def unavailable_runtime(_config: ServiceConfiguration) -> ComponentRuntime:
    raise ServiceHostError("operational component composition is not implemented")


def run_scm_service(role: ServiceRole, runtime_factory=None) -> None:
    """Run one fixed role under SCM; deliberately exposes no install/remove CLI."""
    try:
        import servicemanager
        import win32event
        import win32service
        import win32serviceutil
    except ImportError as exc:
        raise ServiceHostError("pywin32 service host dependency is unavailable") from exc

    service_name = ROLE_BINDINGS[role][0]

    class FixedRoleService(win32serviceutil.ServiceFramework):
        _svc_name_ = service_name
        _svc_display_name_ = service_name

        def __init__(self, args):
            super().__init__(args)
            self._stop_event = win32event.CreateEvent(None, 0, 0, None)
            self._host = ServiceHost(role, runtime_factory or unavailable_runtime)

        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            self._host.stop()
            win32event.SetEvent(self._stop_event)

        def SvcDoRun(self):
            config = ServiceConfiguration.load(fixed_config_path(role), role)
            self._host.start(config, current_process_sid())
            servicemanager.LogInfoMsg(f"{service_name} entered RUNNING")
            win32event.WaitForSingleObject(self._stop_event, win32event.INFINITE)

    servicemanager.Initialize()
    servicemanager.PrepareToHostSingle(FixedRoleService)
    servicemanager.StartServiceCtrlDispatcher()
