[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('Kernel','Identity','KeyCustodian','Recovery')][string]$Role,
    [Parameter(Mandatory=$true)][string]$DeploymentRoot,
    [Parameter(Mandatory=$true)][string]$OutputPath,
    [Parameter(Mandatory=$true)][string]$VerifierPath
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Test-Readable([string]$Path) {
    try { $stream=[IO.File]::Open($Path,'Open','Read','ReadWrite'); $stream.Dispose(); return $true } catch [UnauthorizedAccessException] { return $false }
}
function Test-WriteOpen([string]$Path) {
    try { $stream=[IO.File]::Open($Path,'Open','Write','ReadWrite'); $stream.Dispose(); return $true } catch [UnauthorizedAccessException] { return $false }
}
function Test-DirectoryWrite([string]$Path,[string]$Label) {
    $probe=Join-Path $Path ('.oi0002-access-'+$Label+'-'+[guid]::NewGuid().ToString('N'))
    try { [IO.File]::WriteAllBytes($probe,[byte[]](1,2,3)); return $true } catch [UnauthorizedAccessException] { return $false } finally { Remove-Item -LiteralPath $probe -Force -ErrorAction SilentlyContinue }
}
function Assert-Equal([string]$Name,[bool]$Actual,[bool]$Expected,[System.Collections.IDictionary]$Results) {
    $Results[$Name]=$Actual
    if($Actual -ne $Expected){throw "OI0002_EFFECTIVE_ACCESS_MISMATCH:${Role}:${Name} expected=$Expected actual=$Actual"}
}

$paths=@{
    control=Join-Path $DeploymentRoot 'control'; kernel=Join-Path $DeploymentRoot 'kernel';
    identity=Join-Path $DeploymentRoot 'identity'; secrets=Join-Path $DeploymentRoot 'secrets';
    kernel_backup=Join-Path $DeploymentRoot 'backup-kernel'; identity_backup=Join-Path $DeploymentRoot 'backup-identity'
}
$manifest=Join-Path $paths.control 'deployment.json'
$key=Join-Path $paths.secrets 'identity-hmac.key'
$expect=@{
    Kernel=@{control_read=$false;kernel_write=$true;identity_write=$false;secrets_write=$false;kernel_backup_write=$true;identity_backup_write=$false;key_read=$false;key_write=$false}
    Identity=@{control_read=$false;kernel_write=$false;identity_write=$true;secrets_write=$false;kernel_backup_write=$false;identity_backup_write=$true;key_read=$true;key_write=$false}
    KeyCustodian=@{control_read=$false;kernel_write=$false;identity_write=$false;secrets_write=$true;kernel_backup_write=$false;identity_backup_write=$false;key_read=$true;key_write=$true}
    Recovery=@{control_read=$true;kernel_write=$true;identity_write=$true;secrets_write=$true;kernel_backup_write=$true;identity_backup_write=$true;key_read=$true;key_write=$true}
}
$results=[ordered]@{}
try {
    Assert-Equal 'control_read' (Test-Readable $manifest) $expect[$Role].control_read $results
    Assert-Equal 'kernel_write' (Test-DirectoryWrite $paths.kernel $Role) $expect[$Role].kernel_write $results
    Assert-Equal 'identity_write' (Test-DirectoryWrite $paths.identity $Role) $expect[$Role].identity_write $results
    Assert-Equal 'secrets_write' (Test-DirectoryWrite $paths.secrets $Role) $expect[$Role].secrets_write $results
    Assert-Equal 'kernel_backup_write' (Test-DirectoryWrite $paths.kernel_backup $Role) $expect[$Role].kernel_backup_write $results
    Assert-Equal 'identity_backup_write' (Test-DirectoryWrite $paths.identity_backup $Role) $expect[$Role].identity_backup_write $results
    Assert-Equal 'key_read' (Test-Readable $key) $expect[$Role].key_read $results
    Assert-Equal 'key_write' (Test-WriteOpen $key) $expect[$Role].key_write $results
    if($Role -eq 'Recovery') {
        $verify=& powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $VerifierPath -DeploymentRoot $DeploymentRoot -KernelPrincipal AITaxKernel -IdentityPrincipal AITaxIdentity -KeyCustodianPrincipal AITaxKeyCustodian -RecoveryPrincipal AITaxRecovery 2>&1
        $results.verifier=($verify -join "`n")
        if($LASTEXITCODE -ne 0 -or $results.verifier -notmatch 'OI0002_WINDOWS_CUSTODY_VERIFIED'){throw 'OI0002_RECOVERY_VERIFIER_FAILED'}
    }
    [ordered]@{schema_version=1;status='PASS';role=$Role;principal=[Security.Principal.WindowsIdentity]::GetCurrent().Name;results=$results} | ConvertTo-Json -Depth 5 | Out-File -LiteralPath $OutputPath -Encoding utf8
    exit 0
} catch {
    [ordered]@{schema_version=1;status='FAIL';role=$Role;principal=[Security.Principal.WindowsIdentity]::GetCurrent().Name;results=$results;error=$_.Exception.Message} | ConvertTo-Json -Depth 5 | Out-File -LiteralPath $OutputPath -Encoding utf8
    exit 1
}
