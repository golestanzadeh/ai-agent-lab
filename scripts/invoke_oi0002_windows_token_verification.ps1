[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$DeploymentRoot,
    [Parameter(Mandatory=$true)][string]$EvidenceRoot,
    [Parameter(Mandatory=$true)][string]$RepositoryRoot
)
$ErrorActionPreference='Stop'; Set-StrictMode -Version Latest
function Assert-Elevated {
    $id=[Security.Principal.WindowsIdentity]::GetCurrent(); $p=[Security.Principal.WindowsPrincipal]::new($id)
    if(-not $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'OI0002_ELEVATION_REQUIRED'}
}
function New-RandomPassword {
    $bytes=[byte[]]::new(36); $rng=[Security.Cryptography.RandomNumberGenerator]::Create()
    try{$rng.GetBytes($bytes);return ([Convert]::ToBase64String($bytes)+'!aA7')}finally{$rng.Dispose();[Array]::Clear($bytes,0,$bytes.Length)}
}
function Wait-Task([string]$Name) {
    $deadline=[DateTime]::UtcNow.AddSeconds(60)
    do{Start-Sleep -Milliseconds 250;$task=Get-ScheduledTask -TaskName $Name;$info=Get-ScheduledTaskInfo -TaskName $Name}while($task.State -ne 'Ready' -and [DateTime]::UtcNow -lt $deadline)
    if($task.State -ne 'Ready'){throw "OI0002_TASK_TIMEOUT:$Name"}
    return $info.LastTaskResult
}
Assert-Elevated
$runId='run-'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$runRoot=Join-Path $EvidenceRoot $runId
New-Item -ItemType Directory -Path $runRoot -Force | Out-Null
$current=[Security.Principal.WindowsIdentity]::GetCurrent().User; $system=[Security.Principal.SecurityIdentifier]::new('S-1-5-18')
$accounts=[ordered]@{Kernel='AITaxKernel';Identity='AITaxIdentity';KeyCustodian='AITaxKeyCustodian';Recovery='AITaxRecovery'}
$sids=@{}; foreach($name in $accounts.Values){$sids[$name]=([Security.Principal.NTAccount]::new("$env:COMPUTERNAME\$name")).Translate([Security.Principal.SecurityIdentifier])}
$acl=[Security.AccessControl.DirectorySecurity]::new();$acl.SetAccessRuleProtection($true,$false);$inherit=[Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit'
foreach($sid in @($sids.Values)){[void]$acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($sid,'ReadAndExecute',$inherit,'None','Allow'))}
foreach($sid in @($system,$current)){[void]$acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($sid,'FullControl',$inherit,'None','Allow'))}
Set-Acl -LiteralPath $runRoot -AclObject $acl
$probe=Join-Path $runRoot 'token-probe.ps1';$verifier=Join-Path $runRoot 'verify-windows.ps1'
Copy-Item -LiteralPath (Join-Path $RepositoryRoot 'scripts\oi0002_windows_token_probe.ps1') -Destination $probe
Copy-Item -LiteralPath (Join-Path $RepositoryRoot 'scripts\verify_oi0002_windows.ps1') -Destination $verifier
$summary=[ordered]@{schema_version=1;run_id=$runId;deployment_root=$DeploymentRoot;roles=[ordered]@{}}
foreach($role in $accounts.Keys){
    $name=$accounts[$role];$password=New-RandomPassword;$taskName="OI0002-Temporary-$role-Token-Probe"
    $roleRoot=Join-Path $runRoot $role.ToLowerInvariant();New-Item -ItemType Directory -Path $roleRoot -Force|Out-Null
    $roleAcl=[Security.AccessControl.DirectorySecurity]::new();$roleAcl.SetAccessRuleProtection($true,$false)
    [void]$roleAcl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($sids[$name],'Modify',$inherit,'None','Allow'))
    foreach($sid in @($system,$current)){[void]$roleAcl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($sid,'FullControl',$inherit,'None','Allow'))}
    Set-Acl -LiteralPath $roleRoot -AclObject $roleAcl
    $output=Join-Path $roleRoot 'result.json'
    try{
        ([ADSI]("WinNT://./$name,user")).SetPassword($password)
        $args="-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$probe`" -Role $role -DeploymentRoot `"$DeploymentRoot`" -OutputPath `"$output`" -VerifierPath `"$verifier`""
        $action=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $args
        $settings=New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 3) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
        Register-ScheduledTask -TaskName $taskName -Action $action -User "$env:COMPUTERNAME\$name" -Password $password -RunLevel Limited -Settings $settings -Force|Out-Null
        Start-ScheduledTask -TaskName $taskName
        $code=Wait-Task $taskName
        if($code -ne 0){throw "OI0002_TOKEN_PROBE_FAILED:${role}:${code}"}
        $record=Get-Content -Raw -LiteralPath $output|ConvertFrom-Json
        if($record.status -ne 'PASS'){throw "OI0002_TOKEN_PROBE_REPORTED_FAIL:$role"}
        $digest=(Get-FileHash -Algorithm SHA256 -LiteralPath $output).Hash.ToLowerInvariant()
        $summary.roles[$role]=[ordered]@{status='PASS';principal=$record.principal;evidence="$($role.ToLowerInvariant())/result.json";sha256=$digest}
    }finally{
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
        try{([ADSI]("WinNT://./$name,user")).SetPassword((New-RandomPassword))}catch{}
        if(Test-Path -LiteralPath $roleRoot){
            $sealed=[Security.AccessControl.DirectorySecurity]::new();$sealed.SetAccessRuleProtection($true,$false)
            [void]$sealed.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($sids[$name],'ReadAndExecute',$inherit,'None','Allow'))
            foreach($sid in @($system,$current)){[void]$sealed.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($sid,'FullControl',$inherit,'None','Allow'))}
            Set-Acl -LiteralPath $roleRoot -AclObject $sealed
        }
        $password=$null
    }
}
$summary.status='PASS';$summary|ConvertTo-Json -Depth 5|Out-File -LiteralPath (Join-Path $runRoot 'summary.json') -Encoding utf8
Write-Output $runRoot
