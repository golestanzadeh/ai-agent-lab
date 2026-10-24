"""Fail-closed R3 deployment preparation models; never mutates host or cloud state."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import PureWindowsPath
import re
from collections.abc import Mapping
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
HG03_WRITER_ROLE = "projects/ai-tax-agent-507813/roles/c09WitnessWriter"
HG03_READER_OBJECT_ROLE = "projects/ai-tax-agent-507813/roles/c09WitnessObjectReader"
HG03_READER_LIST_ROLE = "projects/ai-tax-agent-507813/roles/c09WitnessBucketLister"
HG03_PREFIX = "witness/v1/C09-R3-OPERATIONAL-PENDING/"
HG03_OBJECT_CONDITION = "resource.name.startsWith('projects/_/buckets/ai-tax-agent-c09-witness-test-507813/objects/witness/v1/C09-R3-OPERATIONAL-PENDING/')"
HG03_BUCKET_CONDITION = "resource.name == 'projects/_/buckets/ai-tax-agent-c09-witness-test-507813'"
HG03_BLOCKERS = (
    "No approved operational local keyless source credential or Windows-service-to-service-account binding exists.",
    "Current bucket roles are unconditioned predefined roles; proposed custom roles and conditions are not deployed.",
    "Project legacy basic-principal bucket bindings can bypass the proposed Writer/Reader restrictions and require a separately reviewed safe removal/replacement plan.",
    "The Owner user currently has serviceAccountTokenCreator on both identities; this is historical test access, not accepted operational custody.",
    "Live negative enforcement and revocation probes cannot occur until a separately approved IAM change.",
)


def validate_hg03_manifest(manifest: Mapping[str, object], policy: Mapping[str, object]) -> None:
    """Validate the inert HG-03 readiness package; this function performs no I/O."""
    if manifest.get("schema") != "ai-tax-agent.c09-r3-gcs-iam-readiness/1.0":
        raise R3DeploymentError("unknown HG-03 schema")
    if manifest.get("proposal_only") is not True or manifest.get("apply_authorized") is not False:
        raise R3DeploymentError("HG-03 package must remain inert")
    target = manifest.get("target")
    if not isinstance(target, Mapping) or target.get("project") != "ai-tax-agent-507813" or target.get("bucket") != "ai-tax-agent-c09-witness-test-507813" or target.get("prefix") != HG03_PREFIX or target.get("writer") != PINNED_CLOUD["WITNESS_WRITER"] or target.get("reader") != PINNED_CLOUD["WITNESS_READER"]:
        raise R3DeploymentError("HG-03 target is not exactly pinned")
    observed = manifest.get("observed")
    if not isinstance(observed, Mapping) or observed.get("bucket_policy_version") != 1 or observed.get("bucket_policy_version_field_present") is not False or not observed.get("bucket_policy_etag"):
        raise R3DeploymentError("ambiguous or stale HG-03 inventory")
    if observed.get("user_managed_writer_keys") != 0 or observed.get("user_managed_reader_keys") != 0:
        raise R3DeploymentError("user-managed service-account key is forbidden")
    proposed = manifest.get("proposed")
    if not isinstance(proposed, Mapping):
        raise R3DeploymentError("missing HG-03 proposal")
    roles = proposed.get("custom_roles")
    expected_roles = {
        HG03_WRITER_ROLE: ["storage.objects.create"],
        HG03_READER_OBJECT_ROLE: ["storage.objects.get"],
        HG03_READER_LIST_ROLE: ["storage.objects.list"],
    }
    if not isinstance(roles, list) or {item.get("name"): item.get("permissions") for item in roles if isinstance(item, Mapping)} != expected_roles:
        raise R3DeploymentError("HG-03 custom roles exceed or differ from the closed allowlist")
    bindings = proposed.get("bindings")
    if not isinstance(bindings, list) or len(bindings) != 3:
        raise R3DeploymentError("HG-03 requires exactly three conditioned bindings")
    expected = {
        (PINNED_CLOUD["WITNESS_WRITER"], HG03_WRITER_ROLE, "OBJECT_PREFIX"),
        (PINNED_CLOUD["WITNESS_READER"], HG03_READER_OBJECT_ROLE, "OBJECT_PREFIX"),
        (PINNED_CLOUD["WITNESS_READER"], HG03_READER_LIST_ROLE, "EXACT_BUCKET"),
    }
    actual = {(item.get("principal"), item.get("role"), item.get("condition_kind")) for item in bindings if isinstance(item, Mapping)}
    expected_conditions = {
        (PINNED_CLOUD["WITNESS_WRITER"], HG03_WRITER_ROLE): HG03_OBJECT_CONDITION,
        (PINNED_CLOUD["WITNESS_READER"], HG03_READER_OBJECT_ROLE): HG03_OBJECT_CONDITION,
        (PINNED_CLOUD["WITNESS_READER"], HG03_READER_LIST_ROLE): HG03_BUCKET_CONDITION,
    }
    if actual != expected or any(item.get("condition_expression") != expected_conditions.get((item.get("principal"), item.get("role"))) for item in bindings if isinstance(item, Mapping)):
        raise R3DeploymentError("missing, invalid or substituted HG-03 conditioned binding")
    delivery = manifest.get("keyless_delivery")
    if not isinstance(delivery, Mapping) or delivery.get("operational_status") != "UNRESOLVED_FAIL_CLOSED" or delivery.get("long_lived_keys_allowed") is not False:
        raise R3DeploymentError("invalid credential-delivery posture")
    required = delivery.get("required_properties")
    required_fields = {"binding", "acquisition", "maximum_lifetime_seconds", "scope", "audience", "rotation_revocation", "failure", "audit", "recovery"}
    if not isinstance(required, Mapping) or set(required) != required_fields or required.get("maximum_lifetime_seconds") != 3600 or not all(required.get(field) for field in required_fields):
        raise R3DeploymentError("incomplete keyless credential-delivery contract")
    blockers = manifest.get("approval_blockers")
    if manifest.get("approval_ready") is not False or blockers != list(HG03_BLOCKERS):
        raise R3DeploymentError("unverified HG-03 package cannot be approval-ready")
    if policy.get("version") != 3 or policy.get("etag") != observed.get("bucket_policy_etag"):
        raise R3DeploymentError("proposed policy is not bound to the observed ETag")
    policy_bindings = policy.get("bindings")
    if not isinstance(policy_bindings, list):
        raise R3DeploymentError("proposed policy is malformed")
    service_bindings = [item for item in policy_bindings if isinstance(item, Mapping) and any(str(member).startswith("serviceAccount:") for member in item.get("members", []))]
    if len(service_bindings) != 3 or any(item.get("condition", {}).get("expression") != expected_conditions.get((str(item["members"][0]).removeprefix("serviceAccount:"), item.get("role"))) for item in service_bindings):
        raise R3DeploymentError("proposed policy differs from the exact conditioned bindings")


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

