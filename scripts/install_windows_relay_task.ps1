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
$python = $pythonCommand.Source
if (-not $python) {
    throw 'PYTHON_NOT_FOUND'
}

$taskCommand = '"{0}" "{1}" --repo "{2}" --repository "{3}" --branch "{4}"' -f $python, $relayScript, $repo, $Repository, $Branch

& schtasks.exe /Create /SC MINUTE /MO 1 /TN $TaskName /TR $taskCommand /F | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw 'TASK_CREATE_FAILED'
}

& schtasks.exe /Query /TN $TaskName | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw 'TASK_VERIFY_FAILED'
}

Write-Output ('WINDOWS_RELAY_TASK_INSTALLED name="{0}" branch="{1}"' -f $TaskName, $Branch)
