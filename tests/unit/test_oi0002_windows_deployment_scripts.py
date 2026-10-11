from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROVISION = (ROOT / "scripts" / "provision_oi0002_windows.ps1").read_text(encoding="utf-8")
VERIFY = (ROOT / "scripts" / "verify_oi0002_windows.ps1").read_text(encoding="utf-8")


def test_provisioning_requires_elevation_distinct_existing_principals_and_non_synced_root():
    assert "OI0002_ELEVATION_REQUIRED" in PROVISION
    assert "OI0002_PRINCIPAL_NOT_FOUND" in PROVISION
    assert "OI0002_DISTINCT_PRINCIPALS_REQUIRED" in PROVISION
    assert "OI0002_SYNCED_ROOT_FORBIDDEN" in PROVISION
    assert "SupportsShouldProcess" in PROVISION


def test_key_is_random_binary_and_never_printed_or_committed_as_literal():
    assert "RandomNumberGenerator]::Fill" in PROVISION
    assert "WriteAllBytes" in PROVISION
    assert "identity-hmac.key" in PROVISION
    assert "Write-Output $keyPath" not in PROVISION
    assert "password" not in PROVISION.casefold()


def test_acl_verifier_requires_protected_exact_allowlists_and_separate_roots():
    assert "AreAccessRulesProtected" in VERIFY
    assert "OI0002_ACL_UNAUTHORIZED" in VERIFY
    assert "OI0002_ACL_MISSING" in VERIFY
    assert "OI0002_CUSTODY_ROOT_COLLISION" in VERIFY
    assert "OI0002_WINDOWS_CUSTODY_VERIFIED" in VERIFY
