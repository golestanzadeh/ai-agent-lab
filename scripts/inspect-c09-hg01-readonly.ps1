[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$expected = @(
    @{ role='KERNEL'; name='AITaxKernel'; sid='S-1-5-21-212838446-3778166418-3746953556-1020' },
    @{ role='IDENTITY'; name='AITaxIdentity'; sid='S-1-5-21-212838446-3778166418-3746953556-1021' },
    @{ role='KEY_CUSTODIAN'; name='AITaxKeyCustodian'; sid='S-1-5-21-212838446-3778166418-3746953556-1022' }
)
$accounts = foreach ($item in $expected) {
    $account = Get-LocalUser -Name $item.name
    [ordered]@{
        role=$item.role
        name=$account.Name
        enabled=$account.Enabled
        sid=$account.SID.Value
        exact_match=($account.Enabled -and $account.SID.Value -eq $item.sid)
    }
}
$serviceNames = $expected.name
$services = @(Get-CimInstance Win32_Service | Where-Object { $serviceNames -contains $_.Name } | ForEach-Object {
    [ordered]@{ name=$_.Name; state=$_.State; start_mode=$_.StartMode; start_name=$_.StartName; path=$_.PathName }
})
[ordered]@{
    schema='ai-tax-agent.c09-r3-hg01-readonly/1.0'
    host=$env:COMPUTERNAME
    caller_sid=([System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value)
    accounts=$accounts
    service_count=$services.Count
    services=$services
    mutation_performed=$false
} | ConvertTo-Json -Depth 5
