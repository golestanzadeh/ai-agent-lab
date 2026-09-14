param(
    [string]$RepoPath = 'C:\Users\rezag\ai-agent-lab',
    [string]$Branch = 'd021-agent-case-provisioning',
    [string]$Repository = 'golestanzadeh/ai-agent-lab',
    [string]$TaskName = 'AI-Tax-Agent Windows Relay'
)

$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path -LiteralPath $RepoPath).Path
$relayScript = Join-Path $repo 'scripts\windows_relay.py'
if (-not (Test-Path -LiteralPath $relayScript -PathType Leaf)) {
    throw 'WINDOWS_RELAY_SCRIPT_MISSING'
}
if (-not (Test-Path -LiteralPath (Join-Path $repo '.git') -PathType Container)) {
    throw 'NOT_GIT_REPOSITORY_ROOT'
}

$currentBranch = (& git -C $repo branch --show-current).Trim()
if ($LASTEXITCODE -ne 0 -or $currentBranch -ne $Branch) {
    throw 'WRONG_BRANCH'
}

$status = & git -C $repo status --porcelain
if ($LASTEXITCODE -ne 0) {
    throw 'GIT_STATUS_FAILED'
}
if ($status) {
    throw 'DIRTY_WORKTREE'
}

$pythonCommand = Get-Command python -ErrorAction Stop
$pythonConsole = $pythonCommand.Source
if (-not $pythonConsole) {
    throw 'PYTHON_NOT_FOUND'
}
$pythonWindowless = Join-Path (Split-Path -Parent $pythonConsole) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonWindowless -PathType Leaf)) {
    throw 'PYTHONW_NOT_FOUND'
}

$arguments = '"{0}" --repo "{1}" --repository "{2}" --branch "{3}"' -f $relayScript, $repo, $Repository, $Branch
$action = New-ScheduledTaskAction -Execute $pythonWindowless -Argument $arguments -WorkingDirectory $repo
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes 1) `
    -RepetitionDuration (New-TimeSpan -Days 3650)
$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 2) `
    -Hidden

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description 'Fail-closed GitHub-to-Windows relay for AI-Tax-Agent' `
    -Force | Out-Null

$installed = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
if ($installed.Actions.Execute -ne $pythonWindowless -or -not $installed.Settings.Hidden) {
    throw 'TASK_VERIFY_FAILED'
}

Write-Output ('WINDOWS_RELAY_TASK_INSTALLED name="{0}" branch="{1}"' -f $TaskName, $Branch)
