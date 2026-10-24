import json
from pathlib import Path

import pytest

from agent_lab.c09_r3_deployment import (
    CloudPrincipal, PathIdentity, R3DeploymentError, R3PreparationPlan, WindowsPrincipal,
)


def plan(**changes):
    paths = (
        r"C:\ProgramData\AI-Tax-Agent\Kernel", r"C:\ProgramData\AI-Tax-Agent\Identity",
        r"D:\AI-Tax-Agent\KernelBackup", r"D:\AI-Tax-Agent\IdentityBackup",
        r"C:\Program Files\AI-Tax-Agent\kernel.exe", r"C:\Program Files\AI-Tax-Agent\identity.exe",
        r"C:\Program Files\AI-Tax-Agent\custodian.exe", r"E:\AI-Tax-Agent\Custody",
    )
    values = dict(
        deployment_id="C09-R3-SYNTHETIC",
        windows=tuple(
            WindowsPrincipal(role, account, f"S-1-5-21-212838446-3778166418-3746953556-{rid}", True)
            for role, account, rid in (
                ("KERNEL", "AITaxKernel", 1020), ("IDENTITY", "AITaxIdentity", 1021),
                ("KEY_CUSTODIAN", "AITaxKeyCustodian", 1022), ("RECOVERY", "AITaxRecovery", 1023),
            )
        ),
        writer=CloudPrincipal("WITNESS_WRITER", "c09-witness-test@ai-tax-agent-507813.iam.gserviceaccount.com", frozenset({"storage.objects.create"})),
        reader=CloudPrincipal("WITNESS_READER", "c09-witness-reader@ai-tax-agent-507813.iam.gserviceaccount.com", frozenset({"storage.objects.get", "storage.objects.list"})),
        identity_pipe=r"\\.\pipe\AI-Tax-Agent\Identity-v1",
        custodian_pipe=r"\\.\pipe\AI-Tax-Agent\Custodian-v1",
        kernel_store=r"C:\ProgramData\AI-Tax-Agent\Kernel",
        identity_store=r"C:\ProgramData\AI-Tax-Agent\Identity",
        kernel_backup=r"D:\AI-Tax-Agent\KernelBackup",
        identity_backup=r"D:\AI-Tax-Agent\IdentityBackup",
        kernel_executable=r"C:\Program Files\AI-Tax-Agent\kernel.exe",
        identity_executable=r"C:\Program Files\AI-Tax-Agent\identity.exe",
        custodian_executable=r"C:\Program Files\AI-Tax-Agent\custodian.exe",
        custody_root=r"E:\AI-Tax-Agent\Custody",
        path_evidence=tuple(PathIdentity(path, f"VOL-{index}", f"FILE-{index}") for index, path in enumerate(paths)),
        key_reference="provider-ref://witness-hmac/C09-R3",
        restore_key_reference="provider-ref://offline-owner-restore/C09-R3",
    )
    values.update(changes)
    return R3PreparationPlan(**values)


def test_r3_t01_exact_principal_isolation_and_default_deny():
    candidate = plan(); candidate.validate()
    assert candidate.authorize("KERNEL", "identity_pipe.connect")
    assert not candidate.authorize("IDENTITY", "identity_pipe.connect")
    assert not candidate.authorize("UNKNOWN", "identity_store.modify")
    duplicate = list(candidate.windows); duplicate[-1] = WindowsPrincipal("RECOVERY", "AITaxRecovery", duplicate[0].sid, True)
    with pytest.raises(R3DeploymentError, match="pinned"):
        plan(windows=tuple(duplicate)).validate()
    swapped = list(candidate.windows); swapped[0], swapped[1] = (
        WindowsPrincipal("KERNEL", swapped[1].account, swapped[1].sid, True),
        WindowsPrincipal("IDENTITY", swapped[0].account, swapped[0].sid, True),
    )
    with pytest.raises(R3DeploymentError, match="pinned"):
        plan(windows=tuple(swapped)).validate()


def test_r3_t02_fixed_distinct_local_ipc_and_closed_capabilities():
    candidate = plan(); candidate.validate()
    with pytest.raises(R3DeploymentError, match="pipe"):
        plan(custodian_pipe=candidate.identity_pipe).validate()
    assert not candidate.authorize("KERNEL", "identity_restore")


def test_r3_t03_signing_key_reference_is_opaque_and_nonexportable():
    candidate = plan(); candidate.validate()
    assert candidate.authorize("KEY_CUSTODIAN", "witness_key.use_nonexportable")
    assert not candidate.authorize("KERNEL", "witness_key.use_nonexportable")
    for bad in (
        "literal:secret", "env-value:KEY", "provider-ref://x?Secret=value", "provider-ref://x/path#token",
        "provider-ref://user@x/path", "provider-ref://x/path%2fsecret", "provider-ref://x/path with space",
    ):
        with pytest.raises(R3DeploymentError, match="opaque"):
            plan(key_reference=bad).validate()


def test_r3_t04_restore_is_ungranted_and_owner_key_is_separate():
    candidate = plan(); candidate.validate()
    assert not any(candidate.authorize(role, "identity_restore") for role in candidate.authorization_matrix())
    with pytest.raises(R3DeploymentError, match="independent"):
        plan(restore_key_reference=candidate.key_reference).validate()
    with pytest.raises(R3DeploymentError, match="providers"):
        plan(restore_key_reference="provider-ref://witness-hmac/other").validate()
    with pytest.raises(R3DeploymentError, match="cannot activate"):
        plan(restore_enabled=True).validate()


def test_r3_t05_writer_reader_exact_separation():
    candidate = plan(); candidate.validate()
    assert candidate.writer.permissions == frozenset({"storage.objects.create"})
    assert candidate.reader.permissions == frozenset({"storage.objects.get", "storage.objects.list"})
    with pytest.raises(R3DeploymentError, match="pinned"):
        plan(reader=CloudPrincipal("WITNESS_READER", candidate.writer.identity, frozenset({"storage.objects.get", "storage.objects.list"}))).validate()
    with pytest.raises(R3DeploymentError, match="allowlist"):
        plan(writer=CloudPrincipal("WITNESS_WRITER", candidate.writer.identity, frozenset({"storage.objects.create", "storage.objects.delete"}))).validate()
    with pytest.raises(R3DeploymentError, match="pinned"):
        plan(writer=CloudPrincipal("WITNESS_WRITER", "attacker@other.iam.gserviceaccount.com", frozenset({"storage.objects.create"}))).validate()
    with pytest.raises(R3DeploymentError, match="keyless"):
        plan(writer=CloudPrincipal("WITNESS_WRITER", candidate.writer.identity, candidate.writer.permissions, keyless=False)).validate()


def test_r3_t06_missing_or_inactive_custody_fails_closed():
    candidate = plan()
    inactive = list(candidate.windows); inactive[2] = WindowsPrincipal("KEY_CUSTODIAN", "AITaxKeyCustodian", inactive[2].sid, False)
    with pytest.raises(R3DeploymentError, match="inactive"):
        plan(windows=tuple(inactive)).validate()
    with pytest.raises(R3DeploymentError, match="cannot activate"):
        plan(retention_locked=True).validate()
    with pytest.raises(R3DeploymentError, match="nested"):
        plan(identity_store=r"C:\ProgramData\AI-Tax-Agent\Kernel\Identity").validate()
    with pytest.raises(R3DeploymentError, match="canonical"):
        plan(identity_store=r"C:\ProgramData\AI-Tax-Agent\..\Identity").validate()
    evidence = list(candidate.path_evidence); evidence[1] = PathIdentity(evidence[1].path, evidence[0].volume_serial, evidence[0].file_id)
    with pytest.raises(R3DeploymentError, match="alias"):
        plan(path_evidence=tuple(evidence)).validate()
    evidence = list(candidate.path_evidence); evidence[1] = PathIdentity(evidence[1].path, evidence[1].volume_serial, evidence[1].file_id, "MOUNT_POINT")
    with pytest.raises(R3DeploymentError, match="reparse"):
        plan(path_evidence=tuple(evidence)).validate()


def test_r3_templates_are_inert_secret_free_and_default_deny():
    root = Path(__file__).resolve().parents[2]
    deployment = json.loads((root / "config/c09-r3/deployment-preparation.json").read_text(encoding="utf-8"))
    iam = json.loads((root / "config/c09-r3/gcs-iam-proposal.json").read_text(encoding="utf-8"))
    assert deployment["activation"] == "DISABLED_HUMAN_GATE_REQUIRED"
    assert deployment["approval_ready"] is False and iam["approval_ready"] is False
    assert deployment["restore_enabled"] is False and deployment["retention_lock_enabled"] is False
    assert deployment["contains_secret_material"] is False
    assert iam["proposal_only"] is True and iam["apply"] is False
    assert all("storage.buckets.setIamPolicy" in binding["forbidden_permissions"] for binding in iam["bindings"])


def test_r3_inventory_script_is_read_only_and_privacy_minimized():
    root = Path(__file__).resolve().parents[2]
    script = (root / "scripts/inspect-c09-r3-readonly.ps1").read_text(encoding="utf-8")
    forbidden = ("Set-Acl", "New-Service", "Set-Service", "New-LocalUser", "Set-LocalUser", "gcloud ", "Get-Content")
    assert not any(token.casefold() in script.casefold() for token in forbidden)
    assert "Get-LocalUser" in script and "Get-CimInstance Win32_Service" in script


def test_hg01_manifest_is_exact_but_not_approval_ready_without_real_binaries():
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "config/c09-r3/hg01-windows-services.json").read_text(encoding="utf-8"))
    assert manifest["approval_ready"] is False and manifest["execution_authorized"] is False
    assert manifest["status"] == "BLOCKED_MISSING_SERVICE_IMPLEMENTATION_AND_REPRODUCIBLE_BUILD"
    assert [item["name"] for item in manifest["services"]] == ["AITaxKernel", "AITaxIdentity", "AITaxKeyCustodian"]
    assert all(item["executable_path"] is None and item["executable_sha256"] is None for item in manifest["services"])
    assert all(item["startup"] == "DEMAND_START_DISABLED_UNTIL_OWNER_APPROVAL" for item in manifest["services"])


def test_hg01_inventory_is_read_only_and_install_commands_are_never_executed():
    root = Path(__file__).resolve().parents[2]
    script = (root / "scripts/inspect-c09-hg01-readonly.ps1").read_text(encoding="utf-8")
    forbidden = ("sc.exe", "New-Service", "Set-Service", "Start-Service", "Stop-Service", "Set-Acl", "Set-LocalUser")
    assert not any(token.casefold() in script.casefold() for token in forbidden)
    assert "Get-LocalUser" in script and "Get-CimInstance Win32_Service" in script

