"""Fail-closed R3 deployment preparation models; never mutates host or cloud state."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import PureWindowsPath
import re
from urllib.parse import urlsplit


class R3DeploymentError(ValueError):
    pass


SID_RE = re.compile(r"^S-1-5-21-(?:[0-9]+-){3}[0-9]+$")
PINNED_WINDOWS = {
    "KERNEL": ("aitaxkernel", "S-1-5-21-212838446-3778166418-3746953556-1020"),
    "IDENTITY": ("aitaxidentity", "S-1-5-21-212838446-3778166418-3746953556-1021"),
    "KEY_CUSTODIAN": ("aitaxkeycustodian", "S-1-5-21-212838446-3778166418-3746953556-1022"),
    "RECOVERY": ("aitaxrecovery", "S-1-5-21-212838446-3778166418-3746953556-1023"),
}
PINNED_CLOUD = {
    "WITNESS_WRITER": "c09-witness-test@ai-tax-agent-507813.iam.gserviceaccount.com",
    "WITNESS_READER": "c09-witness-reader@ai-tax-agent-507813.iam.gserviceaccount.com",
}
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
        expected = PINNED_WINDOWS.get(self.role)
        if expected is None:
            raise R3DeploymentError("unknown Windows principal role")
        if not SID_RE.fullmatch(self.sid) or (self.account.casefold(), self.sid) != expected:
            raise R3DeploymentError("principal must match the manifest-pinned account and SID")
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
        if self.identity != PINNED_CLOUD[self.role]:
            raise R3DeploymentError("cloud principal must match the manifest-pinned identity")
        if not self.keyless:
            raise R3DeploymentError("cloud principal lacks verified keyless-mode evidence")
        if self.permissions & FORBIDDEN_GCS_PERMISSIONS:
            raise R3DeploymentError("cloud principal has administrative or destructive permission")


@dataclass(frozen=True, slots=True)
class PathIdentity:
    path: str
    volume_serial: str
    file_id: str
    reparse_tag: str | None = None


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
    kernel_backup: str
    identity_backup: str
    kernel_executable: str
    identity_executable: str
    custodian_executable: str
    custody_root: str
    path_evidence: tuple[PathIdentity, ...]
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
        paths = tuple(self._canonical_path(value) for value in (
            self.kernel_store, self.identity_store, self.kernel_backup, self.identity_backup,
            self.kernel_executable, self.identity_executable, self.custodian_executable, self.custody_root,
        ))
        if len(set(paths)) != len(paths):
            raise R3DeploymentError("stores, backups, executables and custody roots must be distinct")
        for index, left in enumerate(paths):
            for right in paths[index + 1:]:
                if self._is_ancestor(left, right) or self._is_ancestor(right, left):
                    raise R3DeploymentError("custody paths must not be nested")
        if len(self.path_evidence) != len(paths):
            raise R3DeploymentError("complete path identity evidence is required")
        evidence_paths = tuple(self._canonical_path(item.path) for item in self.path_evidence)
        if set(evidence_paths) != set(paths):
            raise R3DeploymentError("path identity evidence does not match the manifest")
        if any(item.reparse_tag is not None or not item.volume_serial or not item.file_id for item in self.path_evidence):
            raise R3DeploymentError("reparse or incomplete path identity evidence is forbidden")
        if len({(item.volume_serial.casefold(), item.file_id.casefold()) for item in self.path_evidence}) != len(paths):
            raise R3DeploymentError("path identity alias is forbidden")
        providers = []
        for reference in (self.key_reference, self.restore_key_reference):
            providers.append(self._key_provider(reference))
        if self.key_reference == self.restore_key_reference:
            raise R3DeploymentError("Witness and Owner restore custody must be independent")
        if providers[0] == providers[1]:
            raise R3DeploymentError("Witness and Owner restore custody providers must be independent")
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

    @staticmethod
    def _canonical_path(value: str) -> tuple[str, ...]:
        if not isinstance(value, str) or any(ord(ch) < 32 for ch in value) or value != value.strip():
            raise R3DeploymentError("custody path is malformed")
        path = PureWindowsPath(value)
        if not path.is_absolute() or any(part in {".", ".."} or part.endswith((".", " ")) for part in path.parts):
            raise R3DeploymentError("custody path must be canonical and absolute")
        return tuple(part.casefold() for part in path.parts)

    @staticmethod
    def _is_ancestor(left: tuple[str, ...], right: tuple[str, ...]) -> bool:
        return len(left) < len(right) and right[:len(left)] == left

    @staticmethod
    def _key_provider(reference: str) -> str:
        if not isinstance(reference, str) or reference != reference.strip() or any(ord(ch) < 33 for ch in reference):
            raise R3DeploymentError("only opaque provider key references are permitted")
        if "%" in reference or any(marker in reference.casefold() for marker in ("secret", "token", "password", "literal", "env-value", "private-key")):
            raise R3DeploymentError("only opaque provider key references are permitted")
        parsed = urlsplit(reference)
        if parsed.scheme != "provider-ref" or not parsed.netloc or not parsed.path.strip("/") or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise R3DeploymentError("only opaque provider key references are permitted")
        if not re.fullmatch(r"[a-z0-9-]+", parsed.netloc) or not re.fullmatch(r"/[A-Za-z0-9._/-]+", parsed.path):
            raise R3DeploymentError("only opaque provider key references are permitted")
        return parsed.netloc

