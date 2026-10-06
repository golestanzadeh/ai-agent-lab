param(
    [string]$RepoPath = "C:\Users\rezag\ai-agent-lab",
    [string]$Branch = "d021-agent-case-provisioning",
    [string]$TaskName = "AI-Tax-Agent Local Sync"
)

$ErrorActionPreference = "Stop"

$repo = (Resolve-Path $RepoPath).Path
$script = Join-Path $repo "scripts\local_sync_agent.py"
if (-not (Test-Path $script)) {
    throw "Local Sync Agent script not found: $script"
}

$python = (Get-Command python -ErrorAction Stop).Source
$arguments = '"{0}" --repo "{1}" --branch "{2}"' -f $script, $repo, $Branch

$action = New-ScheduledTaskAction -Execute $python -Argument $arguments -WorkingDirectory $repo
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes 1) `
    -RepetitionDuration (New-TimeSpan -Days 3650)
$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 2)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Fail-closed GitHub/local synchronization for AI-Tax-Agent" `
    -Force | Out-Null

Start-ScheduledTask -TaskName $TaskName
Write-Host "Installed and started: $TaskName"
Write-Host "Repository: $repo"
Write-Host "Branch: $Branch"
