[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory=$true)][string]$DeploymentRoot,
    [Parameter(Mandatory=$true)][string]$KernelPrincipal,
    [Parameter(Mandatory=$true)][string]$IdentityPrincipal,
    [Parameter(Mandatory=$true)][string]$KeyCustodianPrincipal,
    [Parameter(Mandatory=$true)][string]$RecoveryPrincipal
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Assert-ProtectedRoot([string]$Path) {
    if (-not [IO.Path]::IsPathRooted($Path)) { throw 'OI0002_ABSOLUTE_ROOT_REQUIRED' }
    $full = [IO.Path]::GetFullPath($Path).TrimEnd([IO.Path]::DirectorySeparatorChar)
    if ($full -match '(?i)(OneDrive|Google Drive|Dropbox)') { throw 'OI0002_SYNCED_ROOT_FORBIDDEN' }
    if ($full -eq [IO.Path]::GetPathRoot($full)) { throw 'OI0002_BROAD_ROOT_FORBIDDEN' }
    return $full
}
function Assert-Elevated {
    $id=[Security.Principal.WindowsIdentity]::GetCurrent(); $p=[Security.Principal.WindowsPrincipal]::new($id)
    if (-not $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'OI0002_ELEVATION_REQUIRED' }
}
function Resolve-Sid([string]$Name) {
    try { return ([Security.Principal.NTAccount]::new($Name)).Translate([Security.Principal.SecurityIdentifier]) }
    catch { throw "OI0002_PRINCIPAL_NOT_FOUND: $Name" }
}
function Add-Ace($Acl,$Sid,$Rights,$Inheritance) {
    [void]$Acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($Sid,$Rights,$Inheritance,[Security.AccessControl.PropagationFlags]::None,[Security.AccessControl.AccessControlType]::Allow))
}
function Set-DirectoryAcl([string]$Path,$OwnerSid,$FullSids,$TraverseSids=@()) {
    $acl=[Security.AccessControl.DirectorySecurity]::new(); $acl.SetAccessRuleProtection($true,$false); $acl.SetOwner($OwnerSid)
    $inherit=[Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit'
    foreach($sid in $FullSids){ Add-Ace $acl $sid ([Security.AccessControl.FileSystemRights]::FullControl) $inherit }
    foreach($sid in $TraverseSids){ Add-Ace $acl $sid ([Security.AccessControl.FileSystemRights]::ReadAndExecute) ([Security.AccessControl.InheritanceFlags]::None) }
    Set-Acl -LiteralPath $Path -AclObject $acl
}
function Set-FileAcl([string]$Path,$OwnerSid,$FullSids,$ReadSids=@()) {
    $acl=[Security.AccessControl.FileSecurity]::new(); $acl.SetAccessRuleProtection($true,$false); $acl.SetOwner($OwnerSid)
    foreach($sid in $FullSids){ [void]$acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($sid,[Security.AccessControl.FileSystemRights]::FullControl,[Security.AccessControl.AccessControlType]::Allow)) }
    foreach($sid in $ReadSids){ [void]$acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($sid,[Security.AccessControl.FileSystemRights]::Read,[Security.AccessControl.AccessControlType]::Allow)) }
    Set-Acl -LiteralPath $Path -AclObject $acl
}

$root=Assert-ProtectedRoot $DeploymentRoot
Assert-Elevated
$kernelSid=Resolve-Sid $KernelPrincipal; $identitySid=Resolve-Sid $IdentityPrincipal
$keySid=Resolve-Sid $KeyCustodianPrincipal; $recoverySid=Resolve-Sid $RecoveryPrincipal
$systemSid=[Security.Principal.SecurityIdentifier]::new('S-1-5-18')
if (($kernelSid.Value,$identitySid.Value,$keySid.Value,$recoverySid.Value | Select-Object -Unique).Count -ne 4) { throw 'OI0002_DISTINCT_PRINCIPALS_REQUIRED' }
$paths=[ordered]@{control=Join-Path $root 'control';kernel=Join-Path $root 'kernel';identity=Join-Path $root 'identity';secrets=Join-Path $root 'secrets';kernel_backup=Join-Path $root 'backup-kernel';identity_backup=Join-Path $root 'backup-identity'}
if (Test-Path -LiteralPath $root) { $entries=@(Get-ChildItem -LiteralPath $root -Force); if ($entries.Count -gt 0 -and -not (Test-Path -LiteralPath (Join-Path $paths.control 'deployment.json'))) { throw 'OI0002_UNRECOGNIZED_NONEMPTY_ROOT' } }
if ($PSCmdlet.ShouldProcess($root,'Provision protected OI-0002 deployment')) {
    New-Item -ItemType Directory -Path $root -Force | Out-Null
    foreach($path in $paths.Values){ New-Item -ItemType Directory -Path $path -Force | Out-Null }
    Set-DirectoryAcl $root $recoverySid @($recoverySid,$systemSid) @($kernelSid,$identitySid,$keySid)
    Set-DirectoryAcl $paths.control $recoverySid @($recoverySid,$systemSid)
    Set-DirectoryAcl $paths.kernel $recoverySid @($kernelSid,$recoverySid,$systemSid)
    Set-DirectoryAcl $paths.identity $recoverySid @($identitySid,$recoverySid,$systemSid)
    Set-DirectoryAcl $paths.secrets $recoverySid @($keySid,$recoverySid,$systemSid) @($identitySid)
    Set-DirectoryAcl $paths.kernel_backup $recoverySid @($kernelSid,$recoverySid,$systemSid)
    Set-DirectoryAcl $paths.identity_backup $recoverySid @($identitySid,$recoverySid,$systemSid)
    $keyPath=Join-Path $paths.secrets 'identity-hmac.key'
    if (-not (Test-Path -LiteralPath $keyPath)) { $key=[byte[]]::new(32); [Security.Cryptography.RandomNumberGenerator]::Fill($key); [IO.File]::WriteAllBytes($keyPath,$key); [Array]::Clear($key,0,$key.Length) }
    Set-FileAcl $keyPath $keySid @($keySid,$recoverySid,$systemSid) @($identitySid)
    $manifest=[ordered]@{schema_version=1;deployment_id='OI0002-LOCAL-WINDOWS-V1';root=$root;kernel_principal_sid=$kernelSid.Value;identity_principal_sid=$identitySid.Value;key_custodian_principal_sid=$keySid.Value;recovery_principal_sid=$recoverySid.Value;paths=$paths;key_reference='file:secrets/identity-hmac.key'}
    $manifestPath=Join-Path $paths.control 'deployment.json'
    $manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $manifestPath -Encoding utf8NoBOM
    Set-FileAcl $manifestPath $recoverySid @($recoverySid,$systemSid)
    Write-Output $manifestPath
}
