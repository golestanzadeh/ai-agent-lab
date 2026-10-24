[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$accounts = 'AITaxKernel','AITaxIdentity','AITaxKeyCustodian','AITaxRecovery' | ForEach-Object {
    $account = Get-LocalUser -Name $_
    [ordered]@{ name=$account.Name; enabled=$account.Enabled; sid=$account.SID.Value }
}
$services = @(Get-CimInstance Win32_Service | Where-Object {
    $_.Name -like '*AITax*' -or $_.DisplayName -like '*AI-Tax*'
} | ForEach-Object { [ordered]@{ name=$_.Name; state=$_.State; start_name=$_.StartName } })
$tasks = @(Get-ScheduledTask | Where-Object {
    $_.TaskName -like '*AI-Tax*' -or $_.Principal.UserId -like '*AITax*'
} | ForEach-Object { [ordered]@{ name=$_.TaskName; state=[string]$_.State; run_as=$_.Principal.UserId } })
[ordered]@{
    schema='ai-tax-agent.c09-r3-readonly-inventory/1.0'
    computer=$env:COMPUTERNAME
    caller_sid=([System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value)
    accounts=$accounts
    services=$services
    scheduled_tasks=$tasks
    gcloud_available=[bool](Get-Command gcloud.cmd -ErrorAction SilentlyContinue)
} | ConvertTo-Json -Depth 5
