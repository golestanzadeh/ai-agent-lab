[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('A','B')] [string]$BuildId
)
$ErrorActionPreference = 'Stop'
# Stabilize hash-dependent collection iteration in PyInstaller's child Python processes.
# This is a build-only setting, not an operational runtime security setting.
$env:PYTHONHASHSEED = '0'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $root '.runtime\hg01-build-venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Pinned HG01 build virtual environment is unavailable.' }
$head = (& git -C $root rev-parse HEAD).Trim()
$out = Join-Path $root ".runtime\hg01-build\$head\$BuildId"
$allowedRoot = [IO.Path]::GetFullPath((Join-Path $root '.runtime\hg01-build'))
$resolvedOut = [IO.Path]::GetFullPath($out)
if (-not $resolvedOut.StartsWith($allowedRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Build output escaped the dedicated runtime root.' }
if (Test-Path -LiteralPath $out) { Remove-Item -LiteralPath $out -Recurse -Force }
New-Item -ItemType Directory -Force -Path $out | Out-Null
$entries = @(
    @{ Name='AITaxKernel'; Script='src\agent_lab\c09_kernel_service.py' },
    @{ Name='AITaxIdentity'; Script='src\agent_lab\c09_identity_service.py' },
    @{ Name='AITaxKeyCustodian'; Script='src\agent_lab\c09_custodian_service.py' }
)
foreach ($entry in $entries) {
    $roleRoot = Join-Path $out $entry.Name
    # PyInstaller emits ordinary progress logs on stderr; rely on its exit code, not PowerShell's NativeCommandError wrapping.
    $ErrorActionPreference = 'Continue'
    & $python -m PyInstaller --noconfirm --clean --onedir --noupx --name $entry.Name --paths (Join-Path $root 'src') --distpath (Join-Path $roleRoot 'dist') --workpath (Join-Path $roleRoot 'work') --specpath (Join-Path $roleRoot 'spec') (Join-Path $root $entry.Script)
    $buildExitCode = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($buildExitCode -ne 0) { throw "PyInstaller failed for $($entry.Name) (exit $buildExitCode)." }
}
$manifest = @()
Get-ChildItem -LiteralPath $out -Recurse -File | Where-Object { $_.FullName -notmatch '\\(work|spec)\\' } | Sort-Object FullName | ForEach-Object {
    $relative = $_.FullName.Substring($out.Length + 1).Replace('\','/')
    $manifest += [ordered]@{ path=$relative; size=$_.Length; sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower() }
}
$manifestJson = $manifest | ConvertTo-Json -Depth 4
[System.IO.File]::WriteAllText((Join-Path $out 'artifact-tree.json'), $manifestJson, (New-Object System.Text.UTF8Encoding($false)))
Write-Output $out
