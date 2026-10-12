from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
PROVISION = (ROOT / "scripts" / "provision_oi0002_windows.ps1").read_text(encoding="utf-8")
VERIFY = (ROOT / "scripts" / "verify_oi0002_windows.ps1").read_text(encoding="utf-8")
TOKEN_PROBE = (ROOT / "scripts" / "oi0002_windows_token_probe.ps1").read_text(encoding="utf-8")
TOKEN_RUNNER = (ROOT / "scripts" / "invoke_oi0002_windows_token_verification.ps1").read_text(encoding="utf-8")


def test_provisioning_requires_elevation_distinct_existing_principals_and_non_synced_root():
    assert "OI0002_ELEVATION_REQUIRED" in PROVISION
    assert "OI0002_PRINCIPAL_NOT_FOUND" in PROVISION
    assert "OI0002_DISTINCT_PRINCIPALS_REQUIRED" in PROVISION
    assert "OI0002_SYNCED_ROOT_FORBIDDEN" in PROVISION
    assert "SupportsShouldProcess" in PROVISION
    assert "OI0002_UNRECOGNIZED_NONEMPTY_ROOT" in PROVISION
    assert "KeyCustodianPrincipal" in PROVISION


def test_partial_deployment_resume_checks_known_paths_and_key_length():
    assert "OI0002_UNRECOGNIZED_NONEMPTY_ROOT" in PROVISION
    assert "OI0002_INVALID_EXISTING_KEY" in PROVISION
    assert "(Get-Item -LiteralPath $existingKey).Length -ne 32" in PROVISION
    assert "[IO.FileAttributes]::ReparsePoint" in PROVISION


def test_root_acl_is_applied_only_after_child_custody_is_configured():
    root_acl = "Set-DirectoryAcl $root $recoverySid"
    assert PROVISION.count(root_acl) == 1
    root_position = PROVISION.index(root_acl)
    for child in ("control", "kernel", "identity", "secrets", "kernel_backup", "identity_backup"):
        assert PROVISION.index(f"Set-DirectoryAcl $paths.{child} ") < root_position
    assert PROVISION.index("Set-FileAcl $manifestPath") < root_position


def test_key_is_random_binary_and_never_printed_or_committed_as_literal():
    assert "RandomNumberGenerator]::Create" in PROVISION
    assert "$rng.GetBytes($key)" in PROVISION
    assert "$rng.Dispose()" in PROVISION
    assert "[IO.File]::WriteAllText" in PROVISION
    assert "[Text.UTF8Encoding]::new($false)" in PROVISION
    assert "-Encoding utf8NoBOM" not in PROVISION
    assert "WriteAllBytes" in PROVISION
    assert "identity-hmac.key" in PROVISION
    assert "Write-Output $keyPath" not in PROVISION
    assert "password" not in PROVISION.casefold()


def test_acl_verifier_requires_protected_exact_allowlists_and_separate_roots():
    assert "AreAccessRulesProtected" in VERIFY
    assert "OI0002_ACL_UNAUTHORIZED" in VERIFY
    assert "OI0002_OWNER_MISMATCH" in VERIFY
    assert "OI0002_ACL_RULE_MISMATCH" in VERIFY
    assert "OI0002_MANIFEST_PRINCIPAL_MISMATCH" in VERIFY
    assert "OI0002_PATH_OUTSIDE_ROOT" in VERIFY
    assert "OI0002_REPARSE_POINT_FORBIDDEN" in VERIFY
    assert "OI0002_NONCANONICAL_CUSTODY_PATH" in VERIFY
    assert "OI0002_CUSTODY_ROOT_COLLISION" in VERIFY
    assert "OI0002_WINDOWS_CUSTODY_VERIFIED" in VERIFY


def test_real_token_probe_covers_positive_and_negative_effective_access():
    for check in (
        "control_read", "kernel_write", "identity_write", "secrets_write",
        "kernel_backup_write", "identity_backup_write", "key_read", "key_write",
    ):
        assert check in TOKEN_PROBE
    for role in ("Kernel", "Identity", "KeyCustodian", "Recovery"):
        assert role in TOKEN_PROBE
    assert "OI0002_EFFECTIVE_ACCESS_MISMATCH" in TOKEN_PROBE
    assert "OI0002_WINDOWS_CUSTODY_VERIFIED" in VERIFY


def test_token_runner_uses_limited_temporary_tasks_and_rotates_passwords():
    assert "New-RandomPassword" in TOKEN_RUNNER
    assert "-RunLevel Limited" in TOKEN_RUNNER
    assert "Unregister-ScheduledTask" in TOKEN_RUNNER
    assert TOKEN_RUNNER.count("SetPassword") >= 2
    assert "Add-LocalGroupMember" not in TOKEN_RUNNER
    assert "-RunLevel Highest" not in TOKEN_RUNNER
    assert "OI0002-Temporary-" in TOKEN_RUNNER
    assert "Write-Output $password" not in TOKEN_RUNNER
    assert "Out-File $password" not in TOKEN_RUNNER
    assert "Get-FileHash -Algorithm SHA256" in TOKEN_RUNNER
    assert "ReadAndExecute" in TOKEN_RUNNER
    assert "evidence=\"$($role.ToLowerInvariant())/result.json\"" in TOKEN_RUNNER


@pytest.mark.skipif(shutil.which("powershell") is None, reason="Windows PowerShell unavailable")
@pytest.mark.parametrize(
    ("root", "error"),
    [("relative-root", "OI0002_ABSOLUTE_ROOT_REQUIRED"),
     (r"C:\\Users\\Example\\OneDrive\\OI0002", "OI0002_SYNCED_ROOT_FORBIDDEN")],
)
def test_provisioning_rejects_unsafe_root_before_privileged_mutation(root, error):
    script = ROOT / "scripts" / "provision_oi0002_windows.ps1"
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-File", str(script),
         "-DeploymentRoot", root, "-KernelPrincipal", "K", "-IdentityPrincipal", "I",
         "-KeyCustodianPrincipal", "S", "-RecoveryPrincipal", "R", "-WhatIf"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert error in result.stderr
