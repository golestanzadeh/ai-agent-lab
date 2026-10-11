[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$DeploymentRoot)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = [IO.Path]::GetFullPath($DeploymentRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
if ($root -match '(?i)(OneDrive|Google Drive|Dropbox)') { throw 'OI0002_SYNCED_ROOT_FORBIDDEN' }
$manifestPath = Join-Path $root 'deployment.json'
if (-not (Test-Path -LiteralPath $manifestPath)) { throw 'OI0002_MANIFEST_MISSING' }
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
if ($manifest.schema_version -ne 1 -or $manifest.deployment_id -ne 'OI0002-LOCAL-WINDOWS-V1') { throw 'OI0002_MANIFEST_INVALID' }
if ([IO.Path]::GetFullPath($manifest.root).TrimEnd([IO.Path]::DirectorySeparatorChar) -ne $root) { throw 'OI0002_ROOT_MISMATCH' }

$expected = @{
    kernel = @($manifest.kernel_principal_sid, $manifest.recovery_principal_sid, 'S-1-5-18')
    identity = @($manifest.identity_principal_sid, $manifest.recovery_principal_sid, 'S-1-5-18')
    secrets = @($manifest.identity_principal_sid, $manifest.recovery_principal_sid, 'S-1-5-18')
    kernel_backup = @($manifest.kernel_principal_sid, $manifest.recovery_principal_sid, 'S-1-5-18')
    identity_backup = @($manifest.identity_principal_sid, $manifest.recovery_principal_sid, 'S-1-5-18')
}
foreach ($name in $expected.Keys) {
    $path = [string]$manifest.paths.$name
    if (-not (Test-Path -LiteralPath $path -PathType Container)) { throw "OI0002_PATH_MISSING: $name" }
    $acl = Get-Acl -LiteralPath $path
    if (-not $acl.AreAccessRulesProtected) { throw "OI0002_INHERITANCE_ENABLED: $name" }
    $actual = @($acl.Access | Where-Object AccessControlType -eq Allow | ForEach-Object {
        $_.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
    } | Select-Object -Unique)
    foreach ($sid in $expected[$name]) { if ($sid -notin $actual) { throw "OI0002_ACL_MISSING: $name $sid" } }
    foreach ($sid in $actual) { if ($sid -notin $expected[$name]) { throw "OI0002_ACL_UNAUTHORIZED: $name $sid" } }
}
$keyPath = Join-Path ([string]$manifest.paths.secrets) 'identity-hmac.key'
if (-not (Test-Path -LiteralPath $keyPath -PathType Leaf)) { throw 'OI0002_KEY_MISSING' }
if ((Get-Item -LiteralPath $keyPath).Length -ne 32) { throw 'OI0002_KEY_INVALID' }
if ([string]$manifest.paths.kernel -eq [string]$manifest.paths.identity) { throw 'OI0002_CUSTODY_ROOT_COLLISION' }
Write-Output 'OI0002_WINDOWS_CUSTODY_VERIFIED'
