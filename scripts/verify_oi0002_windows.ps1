[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$DeploymentRoot,
    [Parameter(Mandatory=$true)][string]$KernelPrincipal,
    [Parameter(Mandatory=$true)][string]$IdentityPrincipal,
    [Parameter(Mandatory=$true)][string]$KeyCustodianPrincipal,
    [Parameter(Mandatory=$true)][string]$RecoveryPrincipal
)
$ErrorActionPreference='Stop'; Set-StrictMode -Version Latest
function Resolve-Sid([string]$Name){ try{return ([Security.Principal.NTAccount]::new($Name)).Translate([Security.Principal.SecurityIdentifier]).Value}catch{throw "OI0002_PRINCIPAL_NOT_FOUND: $Name"} }
function Canonical-Child([string]$Root,[string]$Path){
    if(-not [IO.Path]::IsPathRooted($Path)){throw 'OI0002_ABSOLUTE_PATH_REQUIRED'}
    $full=[IO.Path]::GetFullPath($Path).TrimEnd([IO.Path]::DirectorySeparatorChar); $prefix=$Root+[IO.Path]::DirectorySeparatorChar
    if(-not $full.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){throw "OI0002_PATH_OUTSIDE_ROOT: $full"}
    if($full -match '(?i)(OneDrive|Google Drive|Dropbox)'){throw 'OI0002_SYNCED_ROOT_FORBIDDEN'}
    if((Get-Item -LiteralPath $full).Attributes -band [IO.FileAttributes]::ReparsePoint){throw "OI0002_REPARSE_POINT_FORBIDDEN: $full"}
    return $full
}
function Assert-Acl([string]$Path,[string]$OwnerSid,[hashtable]$Expected){
    $acl=Get-Acl -LiteralPath $Path
    if(-not $acl.AreAccessRulesProtected){throw "OI0002_INHERITANCE_ENABLED: $Path"}
    $owner=([Security.Principal.NTAccount]::new($acl.Owner)).Translate([Security.Principal.SecurityIdentifier]).Value
    if($owner -ne $OwnerSid){throw "OI0002_OWNER_MISMATCH: $Path"}
    if(@($acl.Access|Where-Object AccessControlType -eq Deny).Count){throw "OI0002_DENY_ACE_PRESENT: $Path"}
    $actual=@{}
    foreach($ace in @($acl.Access|Where-Object AccessControlType -eq Allow)){
        $sid=$ace.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
        if($actual.ContainsKey($sid)){throw "OI0002_DUPLICATE_ACE: $Path $sid"}
        $actual[$sid]=[int64]$ace.FileSystemRights
    }
    foreach($sid in $Expected.Keys){if(-not $actual.ContainsKey($sid) -or $actual[$sid] -ne [int64]$Expected[$sid]){throw "OI0002_ACL_RIGHTS_MISMATCH: $Path $sid"}}
    foreach($sid in $actual.Keys){if(-not $Expected.ContainsKey($sid)){throw "OI0002_ACL_UNAUTHORIZED: $Path $sid"}}
}
if(-not [IO.Path]::IsPathRooted($DeploymentRoot)){throw 'OI0002_ABSOLUTE_ROOT_REQUIRED'}
$root=[IO.Path]::GetFullPath($DeploymentRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
if($root -match '(?i)(OneDrive|Google Drive|Dropbox)'){throw 'OI0002_SYNCED_ROOT_FORBIDDEN'}
$kernelSid=Resolve-Sid $KernelPrincipal; $identitySid=Resolve-Sid $IdentityPrincipal; $keySid=Resolve-Sid $KeyCustodianPrincipal; $recoverySid=Resolve-Sid $RecoveryPrincipal; $systemSid='S-1-5-18'
if(($kernelSid,$identitySid,$keySid,$recoverySid|Select-Object -Unique).Count -ne 4){throw 'OI0002_DISTINCT_PRINCIPALS_REQUIRED'}
$manifestPath=Join-Path (Join-Path $root 'control') 'deployment.json'; if(-not(Test-Path -LiteralPath $manifestPath)){throw 'OI0002_MANIFEST_MISSING'}
$manifest=Get-Content -Raw -LiteralPath $manifestPath|ConvertFrom-Json
if($manifest.schema_version -ne 1 -or $manifest.deployment_id -ne 'OI0002-LOCAL-WINDOWS-V1'){throw 'OI0002_MANIFEST_INVALID'}
if([IO.Path]::GetFullPath($manifest.root).TrimEnd([IO.Path]::DirectorySeparatorChar) -ne $root){throw 'OI0002_ROOT_MISMATCH'}
$trusted=@($kernelSid,$identitySid,$keySid,$recoverySid); $observed=@($manifest.kernel_principal_sid,$manifest.identity_principal_sid,$manifest.key_custodian_principal_sid,$manifest.recovery_principal_sid)
if(Compare-Object $trusted $observed){throw 'OI0002_MANIFEST_PRINCIPAL_MISMATCH'}
$names=@('control','kernel','identity','secrets','kernel_backup','identity_backup'); $canonical=@{}
foreach($name in $names){$canonical[$name]=Canonical-Child $root ([string]$manifest.paths.$name)}
if(@($canonical.Values|Select-Object -Unique).Count -ne $names.Count){throw 'OI0002_CUSTODY_ROOT_COLLISION'}
$full=[int64][Security.AccessControl.FileSystemRights]::FullControl; $readExec=[int64][Security.AccessControl.FileSystemRights]::ReadAndExecute; $read=[int64][Security.AccessControl.FileSystemRights]::Read
Assert-Acl $canonical.control $recoverySid @{$recoverySid=$full;$systemSid=$full}
Assert-Acl $canonical.kernel $recoverySid @{$kernelSid=$full;$recoverySid=$full;$systemSid=$full}
Assert-Acl $canonical.identity $recoverySid @{$identitySid=$full;$recoverySid=$full;$systemSid=$full}
Assert-Acl $canonical.secrets $recoverySid @{$keySid=$full;$recoverySid=$full;$systemSid=$full;$identitySid=$readExec}
Assert-Acl $canonical.kernel_backup $recoverySid @{$kernelSid=$full;$recoverySid=$full;$systemSid=$full}
Assert-Acl $canonical.identity_backup $recoverySid @{$identitySid=$full;$recoverySid=$full;$systemSid=$full}
$keyPath=Join-Path $canonical.secrets 'identity-hmac.key'; if((Get-Item -LiteralPath $keyPath).Length -ne 32){throw 'OI0002_KEY_INVALID'}
Assert-Acl $keyPath $keySid @{$keySid=$full;$recoverySid=$full;$systemSid=$full;$identitySid=$read}
Assert-Acl $manifestPath $recoverySid @{$recoverySid=$full;$systemSid=$full}
Write-Output 'OI0002_WINDOWS_CUSTODY_VERIFIED'
