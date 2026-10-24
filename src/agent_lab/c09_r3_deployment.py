"""Fail-closed R3 deployment preparation models; never mutates host or cloud state."""
from __future__ import annotations

from dataclasses import dataclass
import re


class R3DeploymentError(ValueError):
    pass


SID_RE = re.compile(r"^S-1-5-21-(?:[0-9]+-){3}[0-9]+$")
GCS_WRITER_PERMISSIONS = frozenset({"storage.objects.create"})
GCS_READER_PERMISSIONS = frozenset({"storage.objects.get", "storage.objects.list"})
FORBIDDEN_GCS_PERMISSIONS = frozenset({
    "storage.objects.delete", "storage.objects.update", "storage.buckets.setIamPolicy",
    "storage.buckets.update", "storage.buckets.delete", "storage.objects.setRetention",
})


@dataclass(frozen=True, slots=True)
class WindowsPrincipal:
    role: str
    account: str
    sid: str
    enabled: bool

    def validate(self) -> None:
        if self.role not in {"KERNEL", "IDENTITY", "KEY_CUSTODIAN", "RECOVERY"}:
            raise R3DeploymentError("unknown Windows principal role")
        if not self.account.startswith("AITax") or not SID_RE.fullmatch(self.sid):
            raise R3DeploymentError("principal must use a pinned local AITax account and SID")
        if not self.enabled:
            raise R3DeploymentError("required principal is inactive")


@dataclass(frozen=True, slots=True)
class CloudPrincipal:
    role: str
    identity: str
    permissions: frozenset[str]
    keyless: bool = True

    def validate(self) -> None:
        expected = {"WITNESS_WRITER": GCS_WRITER_PERMISSIONS, "WITNESS_READER": GCS_READER_PERMISSIONS}.get(self.role)
        if expected is None or self.permissions != expected:
            raise R3DeploymentError("cloud principal permissions are not the exact closed allowlist")
        if not self.identity.endswith(".iam.gserviceaccount.com") or not self.keyless:
            raise R3DeploymentError("cloud principal must be a keyless service account")
        if self.permissions & FORBIDDEN_GCS_PERMISSIONS:
            raise R3DeploymentError("cloud principal has administrative or destructive permission")


@dataclass(frozen=True, slots=True)
class R3PreparationPlan:
    deployment_id: str
    windows: tuple[WindowsPrincipal, ...]
    writer: CloudPrincipal
    reader: CloudPrincipal
    identity_pipe: str
    custodian_pipe: str
    kernel_store: str
    identity_store: str
    key_reference: str
    restore_key_reference: str
    restore_enabled: bool = False
    retention_locked: bool = False

    def validate(self) -> None:
        if not self.deployment_id or len(self.deployment_id.encode()) > 128:
            raise R3DeploymentError("invalid deployment identity")
        if len(self.windows) != 4:
            raise R3DeploymentError("exactly four Windows principals are required")
        for principal in self.windows:
            principal.validate()
        roles = {p.role for p in self.windows}
        if roles != {"KERNEL", "IDENTITY", "KEY_CUSTODIAN", "RECOVERY"}:
            raise R3DeploymentError("all four distinct Windows roles are required")
        if len({p.sid for p in self.windows}) != 4 or len({p.account.casefold() for p in self.windows}) != 4:
            raise R3DeploymentError("Windows principals must be distinct")
        self.writer.validate(); self.reader.validate()
        if self.writer.identity == self.reader.identity:
            raise R3DeploymentError("Witness Writer and Reader must be distinct")
        if self.identity_pipe == self.custodian_pipe or not all(p.startswith("\\\\.\\pipe\\AI-Tax-Agent\\") for p in (self.identity_pipe, self.custodian_pipe)):
            raise R3DeploymentError("distinct fixed local pipe names are required")
        if self.kernel_store.casefold() == self.identity_store.casefold():
            raise R3DeploymentError("Kernel and Identity stores must be separate")
        for reference in (self.key_reference, self.restore_key_reference):
            if not reference.startswith("provider-ref://") or any(marker in reference for marker in ("secret=", "literal:", "env-value:")):
                raise R3DeploymentError("only opaque provider key references are permitted")
        if self.key_reference == self.restore_key_reference:
            raise R3DeploymentError("Witness and Owner restore custody must be independent")
        if self.restore_enabled or self.retention_locked:
            raise R3DeploymentError("preparation cannot activate restore or retention lock")

    def authorization_matrix(self) -> dict[str, frozenset[str]]:
        self.validate()
        return {
            "KERNEL": frozenset({"identity_pipe.connect", "custodian_pipe.connect", "witness.create.request"}),
            "IDENTITY": frozenset({"identity_store.modify", "identity_pipe.serve"}),
            "KEY_CUSTODIAN": frozenset({"custodian_pipe.serve", "witness_key.use_nonexportable"}),
            "RECOVERY": frozenset({"recovery.inspect"}),
            "WITNESS_WRITER": GCS_WRITER_PERMISSIONS,
            "WITNESS_READER": GCS_READER_PERMISSIONS,
        }

    def authorize(self, role: str, action: str) -> bool:
        """Default deny; preparation deliberately grants no restore capability."""
        return action in self.authorization_matrix().get(role, frozenset())

