import json
from pathlib import Path

import pytest

from agent_lab.c09_r3_deployment import (
    CloudPrincipal, R3DeploymentError, R3PreparationPlan, WindowsPrincipal,
)


def plan(**changes):
    values = dict(
        deployment_id="C09-R3-SYNTHETIC",
        windows=tuple(
            WindowsPrincipal(role, account, f"S-1-5-21-1-2-3-{rid}", True)
            for role, account, rid in (
                ("KERNEL", "AITaxKernel", 1020), ("IDENTITY", "AITaxIdentity", 1021),
                ("KEY_CUSTODIAN", "AITaxKeyCustodian", 1022), ("RECOVERY", "AITaxRecovery", 1023),
            )
        ),
        writer=CloudPrincipal("WITNESS_WRITER", "writer@project.iam.gserviceaccount.com", frozenset({"storage.objects.create"})),
        reader=CloudPrincipal("WITNESS_READER", "reader@project.iam.gserviceaccount.com", frozenset({"storage.objects.get", "storage.objects.list"})),
        identity_pipe=r"\\.\pipe\AI-Tax-Agent\Identity-v1",
        custodian_pipe=r"\\.\pipe\AI-Tax-Agent\Custodian-v1",
        kernel_store=r"C:\ProgramData\AI-Tax-Agent\Kernel",
        identity_store=r"C:\ProgramData\AI-Tax-Agent\Identity",
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
    with pytest.raises(R3DeploymentError, match="distinct"):
        plan(windows=tuple(duplicate)).validate()


def test_r3_t02_fixed_distinct_local_ipc_and_closed_capabilities():
    candidate = plan(); candidate.validate()
    with pytest.raises(R3DeploymentError, match="pipe"):
        plan(custodian_pipe=candidate.identity_pipe).validate()
    assert not candidate.authorize("KERNEL", "identity_restore")


def test_r3_t03_signing_key_reference_is_opaque_and_nonexportable():
    candidate = plan(); candidate.validate()
    assert candidate.authorize("KEY_CUSTODIAN", "witness_key.use_nonexportable")
    assert not candidate.authorize("KERNEL", "witness_key.use_nonexportable")
    for bad in ("literal:secret", "env-value:KEY", "provider-ref://x?secret=value"):
        with pytest.raises(R3DeploymentError, match="opaque"):
            plan(key_reference=bad).validate()


def test_r3_t04_restore_is_ungranted_and_owner_key_is_separate():
    candidate = plan(); candidate.validate()
    assert not any(candidate.authorize(role, "identity_restore") for role in candidate.authorization_matrix())
    with pytest.raises(R3DeploymentError, match="independent"):
        plan(restore_key_reference=candidate.key_reference).validate()
    with pytest.raises(R3DeploymentError, match="cannot activate"):
        plan(restore_enabled=True).validate()


def test_r3_t05_writer_reader_exact_separation():
    candidate = plan(); candidate.validate()
    assert candidate.writer.permissions == frozenset({"storage.objects.create"})
    assert candidate.reader.permissions == frozenset({"storage.objects.get", "storage.objects.list"})
    with pytest.raises(R3DeploymentError, match="distinct"):
        plan(reader=CloudPrincipal("WITNESS_READER", candidate.writer.identity, frozenset({"storage.objects.get", "storage.objects.list"}))).validate()
    with pytest.raises(R3DeploymentError, match="allowlist"):
        plan(writer=CloudPrincipal("WITNESS_WRITER", candidate.writer.identity, frozenset({"storage.objects.create", "storage.objects.delete"}))).validate()


def test_r3_t06_missing_or_inactive_custody_fails_closed():
    candidate = plan()
    inactive = list(candidate.windows); inactive[2] = WindowsPrincipal("KEY_CUSTODIAN", "AITaxKeyCustodian", inactive[2].sid, False)
    with pytest.raises(R3DeploymentError, match="inactive"):
        plan(windows=tuple(inactive)).validate()
    with pytest.raises(R3DeploymentError, match="cannot activate"):
        plan(retention_locked=True).validate()


def test_r3_templates_are_inert_secret_free_and_default_deny():
    root = Path(__file__).resolve().parents[2]
    deployment = json.loads((root / "config/c09-r3/deployment-preparation.json").read_text(encoding="utf-8"))
    iam = json.loads((root / "config/c09-r3/gcs-iam-proposal.json").read_text(encoding="utf-8"))
    assert deployment["activation"] == "DISABLED_HUMAN_GATE_REQUIRED"
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

