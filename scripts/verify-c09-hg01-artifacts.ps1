[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$BuildRoot,
    [switch]$RequireOperationalSignature
)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($BuildRoot)
$repo = [IO.Path]::GetFullPath((Resolve-Path (Join-Path $PSScriptRoot '..')).Path)
$allowed = [IO.Path]::GetFullPath((Join-Path $repo '.runtime\hg01-build'))
if (-not $root.StartsWith($allowed + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Artifact root escaped the dedicated build boundary.' }
$names = @('AITaxKernel','AITaxIdentity','AITaxKeyCustodian')
foreach ($name in $names) {
    $exe = Join-Path $root "$name\dist\$name\$name.exe"
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { throw "Missing artifact: $name" }
    $hash = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLower()
    $signature = Get-AuthenticodeSignature -LiteralPath $exe
    if ($RequireOperationalSignature -and $signature.Status -ne 'Valid') { throw "Operational signature verification failed: $name" }
    [pscustomobject]@{ name=$name; path=$exe; sha256=$hash; authenticode=$signature.Status.ToString() }
}
