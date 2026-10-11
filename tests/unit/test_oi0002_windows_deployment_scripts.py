from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
PROVISION = (ROOT / "scripts" / "provision_oi0002_windows.ps1").read_text(encoding="utf-8")
VERIFY = (ROOT / "scripts" / "verify_oi0002_windows.ps1").read_text(encoding="utf-8")


def test_provisioning_requires_elevation_distinct_existing_principals_and_non_synced_root():
    assert "OI0002_ELEVATION_REQUIRED" in PROVISION
    assert "OI0002_PRINCIPAL_NOT_FOUND" in PROVISION
    assert "OI0002_DISTINCT_PRINCIPALS_REQUIRED" in PROVISION
    assert "OI0002_SYNCED_ROOT_FORBIDDEN" in PROVISION
    assert "SupportsShouldProcess" in PROVISION
    assert "OI0002_UNRECOGNIZED_NONEMPTY_ROOT" in PROVISION
    assert "KeyCustodianPrincipal" in PROVISION


def test_key_is_random_binary_and_never_printed_or_committed_as_literal():
    assert "RandomNumberGenerator]::Fill" in PROVISION
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
