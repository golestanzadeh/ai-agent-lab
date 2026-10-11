[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory=$true)][string]$DeploymentRoot,
    [Parameter(Mandatory=$true)][string]$KernelPrincipal,
    [Parameter(Mandatory=$true)][string]$IdentityPrincipal,
    [Parameter(Mandatory=$true)][string]$RecoveryPrincipal
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Assert-Elevated {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'OI0002_ELEVATION_REQUIRED'
    }
}

function Resolve-PrincipalSid([string]$Name) {
    try {
        return ([Security.Principal.NTAccount]::new($Name)).Translate([Security.Principal.SecurityIdentifier])
    } catch {
        throw "OI0002_PRINCIPAL_NOT_FOUND: $Name"
    }
}

function Assert-ProtectedRoot([string]$Path) {
    $full = [IO.Path]::GetFullPath($Path)
    if (-not [IO.Path]::IsPathRooted($full)) { throw 'OI0002_ABSOLUTE_ROOT_REQUIRED' }
    if ($full -match '(?i)(OneDrive|Google Drive|Dropbox)') { throw 'OI0002_SYNCED_ROOT_FORBIDDEN' }
    if ($full -eq [IO.Path]::GetPathRoot($full)) { throw 'OI0002_BROAD_ROOT_FORBIDDEN' }
    return $full.TrimEnd([IO.Path]::DirectorySeparatorChar)
}

function Set-ExactAcl([string]$Path, [Security.Principal.SecurityIdentifier[]]$AllowedSids) {
    $acl = [Security.AccessControl.DirectorySecurity]::new()
    $acl.SetAccessRuleProtection($true, $false)
    $inherit = [Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit'
    $propagate = [Security.AccessControl.PropagationFlags]::None
    foreach ($sid in $AllowedSids) {
        $rule = [Security.AccessControl.FileSystemAccessRule]::new(
            $sid, [Security.AccessControl.FileSystemRights]::FullControl,
            $inherit, $propagate, [Security.AccessControl.AccessControlType]::Allow)
        [void]$acl.AddAccessRule($rule)
    }
    Set-Acl -LiteralPath $Path -AclObject $acl
}

Assert-Elevated
$root = Assert-ProtectedRoot $DeploymentRoot
$kernelSid = Resolve-PrincipalSid $KernelPrincipal
$identitySid = Resolve-PrincipalSid $IdentityPrincipal
$recoverySid = Resolve-PrincipalSid $RecoveryPrincipal
$systemSid = [Security.Principal.SecurityIdentifier]::new('S-1-5-18')
if (($kernelSid.Value, $identitySid.Value, $recoverySid.Value | Select-Object -Unique).Count -ne 3) {
    throw 'OI0002_DISTINCT_PRINCIPALS_REQUIRED'
}

$paths = [ordered]@{
    kernel = Join-Path $root 'kernel'
    identity = Join-Path $root 'identity'
    secrets = Join-Path $root 'secrets'
    kernel_backup = Join-Path $root 'backup-kernel'
    identity_backup = Join-Path $root 'backup-identity'
}

if ($PSCmdlet.ShouldProcess($root, 'Provision protected OI-0002 deployment')) {
    New-Item -ItemType Directory -Path $root -Force | Out-Null
    foreach ($path in $paths.Values) { New-Item -ItemType Directory -Path $path -Force | Out-Null }
    Set-ExactAcl $paths.kernel @($kernelSid, $recoverySid, $systemSid)
    Set-ExactAcl $paths.identity @($identitySid, $recoverySid, $systemSid)
    Set-ExactAcl $paths.secrets @($identitySid, $recoverySid, $systemSid)
    Set-ExactAcl $paths.kernel_backup @($kernelSid, $recoverySid, $systemSid)
    Set-ExactAcl $paths.identity_backup @($identitySid, $recoverySid, $systemSid)

    $keyPath = Join-Path $paths.secrets 'identity-hmac.key'
    if (-not (Test-Path -LiteralPath $keyPath)) {
        $key = [byte[]]::new(32)
        [Security.Cryptography.RandomNumberGenerator]::Fill($key)
        [IO.File]::WriteAllBytes($keyPath, $key)
        [Array]::Clear($key, 0, $key.Length)
    }
    $keyAcl = [Security.AccessControl.FileSecurity]::new()
    $keyAcl.SetAccessRuleProtection($true, $false)
    foreach ($sid in @($identitySid, $recoverySid, $systemSid)) {
        [void]$keyAcl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new(
            $sid, [Security.AccessControl.FileSystemRights]::Read,
            [Security.AccessControl.AccessControlType]::Allow))
    }
    Set-Acl -LiteralPath $keyPath -AclObject $keyAcl

    $manifest = [ordered]@{
        schema_version = 1
        deployment_id = 'OI0002-LOCAL-WINDOWS-V1'
        root = $root
        kernel_principal_sid = $kernelSid.Value
        identity_principal_sid = $identitySid.Value
        recovery_principal_sid = $recoverySid.Value
        paths = $paths
        key_reference = 'file:secrets/identity-hmac.key'
    }
    $manifestPath = Join-Path $root 'deployment.json'
    $manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $manifestPath -Encoding utf8NoBOM
    Set-ExactAcl $root @($kernelSid, $identitySid, $recoverySid, $systemSid)
    Write-Output $manifestPath
}
