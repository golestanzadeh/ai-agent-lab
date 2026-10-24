[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$paths = @(
    'C:\ProgramData\AI-Tax-Agent\OI0002-OPS\Kernel',
    'C:\ProgramData\AI-Tax-Agent\OI0002-OPS\Identity',
    'C:\ProgramData\AI-Tax-Agent\OI0002-OPS-BACKUP\Kernel',
    'C:\ProgramData\AI-Tax-Agent\OI0002-OPS-BACKUP\Identity',
    'C:\ProgramData\AI-Tax-Agent\OI0002-CUSTODY'
)
$results = foreach ($path in $paths) {
    if (-not (Test-Path -LiteralPath $path)) {
        [ordered]@{ path=$path; exists=$false; canonical=$null; owner=$null; sddl=$null; reparse=$null }
        continue
    }
    try {
        $item = Get-Item -LiteralPath $path -Force
        $acl = Get-Acl -LiteralPath $path
        [ordered]@{
            path=$path; exists=$true; canonical=$item.FullName; owner=$acl.Owner; sddl=$acl.Sddl
            reparse=[bool]($item.Attributes -band [IO.FileAttributes]::ReparsePoint)
        }
    } catch {
        [ordered]@{ path=$path; exists=$true; error=$_.Exception.GetType().FullName; message=$_.Exception.Message }
    }
}
$parent = Get-Acl -LiteralPath 'C:\ProgramData\AI-Tax-Agent'
[ordered]@{
    schema='ai-tax-agent.c09-r3-hg02-readonly/1.0'
    caller_sid=([System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value)
    parent_owner=$parent.Owner
    parent_inheritance_protected=$parent.AreAccessRulesProtected
    targets=$results
    mutation_performed=$false
} | ConvertTo-Json -Depth 6
