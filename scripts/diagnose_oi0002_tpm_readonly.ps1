[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$principal = [Security.Principal.WindowsPrincipal]::new(
    [Security.Principal.WindowsIdentity]::GetCurrent()
)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    [Console]::Error.WriteLine('OI0002_ADMIN_REQUIRED: run this read-only diagnostic from an elevated PowerShell session.')
    exit 5
}

function Invoke-CapturedCommand {
    param(
        [Parameter(Mandatory)] [string] $FilePath,
        [Parameter()] [string[]] $ArgumentList = @()
    )
    $text = & $FilePath @ArgumentList 2>&1 | Out-String
    [ordered]@{
        command = (($FilePath, $ArgumentList) -join ' ').Trim()
        exit_code = $LASTEXITCODE
        output = $text.Trim()
    }
}

function Invoke-CapturedScript {
    param(
        [Parameter(Mandatory)] [string] $Name,
        [Parameter(Mandatory)] [scriptblock] $Script
    )
    try {
        $value = & $Script
        [ordered]@{ command = $Name; exit_code = 0; output = $value }
    }
    catch {
        [ordered]@{
            command = $Name
            exit_code = 1
            error_type = $_.Exception.GetType().FullName
            error = $_.Exception.Message
        }
    }
}

# Read-only TPM Base Services query. TPM2_GetCapability(CAP_HANDLES,
# TPM_HR_NV_INDEX, 64) enumerates visible NV handles; it does not define,
# write, increment, clear, own, activate or otherwise change TPM state.
Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;

public static class Oi0002TbsReadOnly {
    [StructLayout(LayoutKind.Sequential)]
    private struct TBS_CONTEXT_PARAMS2 {
        public UInt32 version;
        public UInt32 flags;
    }

    [DllImport("tbs.dll")]
    private static extern UInt32 Tbsi_Context_Create(
        ref TBS_CONTEXT_PARAMS2 contextParams,
        out IntPtr context
    );

    [DllImport("tbs.dll")]
    private static extern UInt32 Tbsip_Submit_Command(
        IntPtr context,
        UInt32 locality,
        UInt32 priority,
        byte[] commandBuffer,
        UInt32 commandBufferLength,
        byte[] resultBuffer,
        ref UInt32 resultBufferLength
    );

    [DllImport("tbs.dll")]
    private static extern UInt32 Tbsip_Context_Close(IntPtr context);

    public static string GetNvHandleCapabilityHex() {
        var parameters = new TBS_CONTEXT_PARAMS2 {
            version = 2,
            // includeTpm20 | requestRaw
            flags = 0x00000006
        };
        IntPtr context;
        UInt32 result = Tbsi_Context_Create(ref parameters, out context);
        if (result != 0) {
            throw new Win32Exception(unchecked((int)result),
                "Tbsi_Context_Create failed: 0x" + result.ToString("X8"));
        }
        try {
            // TPM_ST_NO_SESSIONS, size 22, TPM2_CC_GetCapability,
            // TPM_CAP_HANDLES, TPM_HR_NV_INDEX, propertyCount 64.
            byte[] command = new byte[] {
                0x80,0x01, 0x00,0x00,0x00,0x16, 0x00,0x00,0x01,0x7A,
                0x00,0x00,0x00,0x01, 0x01,0x00,0x00,0x00,
                0x00,0x00,0x00,0x40
            };
            byte[] response = new byte[8192];
            UInt32 responseLength = (UInt32)response.Length;
            result = Tbsip_Submit_Command(
                context, 0, 200, command, (UInt32)command.Length,
                response, ref responseLength
            );
            if (result != 0) {
                throw new Win32Exception(unchecked((int)result),
                    "Tbsip_Submit_Command failed: 0x" + result.ToString("X8"));
            }
            byte[] exact = new byte[responseLength];
            Array.Copy(response, exact, responseLength);
            return BitConverter.ToString(exact).Replace("-", "").ToLowerInvariant();
        }
        finally {
            Tbsip_Context_Close(context);
        }
    }
}
'@

$eventLogs = Invoke-CapturedScript -Name 'Get-WinEvent TPM logs and recent events' -Script {
    $logs = Get-WinEvent -ListLog '*TPM*' -ErrorAction SilentlyContinue |
        Select-Object LogName, IsEnabled, RecordCount, LastWriteTime
    $events = foreach ($log in $logs | Where-Object IsEnabled) {
        Get-WinEvent -FilterHashtable @{
            LogName = $log.LogName
            StartTime = (Get-Date).AddDays(-30)
        } -MaxEvents 50 -ErrorAction SilentlyContinue |
            Select-Object TimeCreated, Id, LevelDisplayName, ProviderName, Message
    }
    [ordered]@{ logs = @($logs); recent_events = @($events) }
}

$report = [ordered]@{
    schema_version = 1
    diagnostic = 'OI-0002 TPM host feasibility read-only'
    measured_at_utc = [DateTime]::UtcNow.ToString('o')
    computer_name = $env:COMPUTERNAME
    is_elevated = $true
    identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    os = Invoke-CapturedScript -Name 'Get-ComputerInfo' -Script {
        Get-ComputerInfo -Property OsName, OsVersion, OsArchitecture, BiosFirmwareType
    }
    tpm = Invoke-CapturedScript -Name 'Get-Tpm' -Script { Get-Tpm }
    tpm_tool = Invoke-CapturedCommand -FilePath "$env:WINDIR\System32\TpmTool.exe" -ArgumentList @('getdeviceinformation')
    win32_tpm = Invoke-CapturedScript -Name 'Win32_Tpm CIM' -Script {
        Get-CimInstance -Namespace 'root\CIMV2\Security\MicrosoftTpm' -ClassName Win32_Tpm |
            Select-Object IsActivated_InitialValue, IsEnabled_InitialValue,
                IsOwned_InitialValue, ManufacturerId, ManufacturerIdTxt,
                ManufacturerVersion, ManufacturerVersionFull20,
                PhysicalPresenceVersionInfo, SpecVersion
    }
    security_devices = Invoke-CapturedScript -Name 'Get-PnpDevice SecurityDevices' -Script {
        Get-PnpDevice -Class SecurityDevices |
            Select-Object Status, Class, FriendlyName, InstanceId, Problem,
                ConfigManagerErrorCode
    }
    secure_boot = Invoke-CapturedScript -Name 'Confirm-SecureBootUEFI' -Script {
        Confirm-SecureBootUEFI
    }
    platform_crypto_provider = Invoke-CapturedCommand -FilePath "$env:WINDIR\System32\certutil.exe" -ArgumentList @('-csplist')
    tpm_event_logs = $eventLogs
    tbs_nv_handle_capability = Invoke-CapturedScript -Name 'TPM2_GetCapability NV handles via TBS' -Script {
        [Oi0002TbsReadOnly]::GetNvHandleCapabilityHex()
    }
    files = Invoke-CapturedScript -Name 'TPM interface file inventory' -Script {
        Get-Item "$env:WINDIR\System32\tbs.dll",
            "$env:WINDIR\System32\drivers\tpm.sys",
            "$env:WINDIR\System32\TpmTool.exe" |
            Select-Object FullName, Length, @{n='FileVersion';e={$_.VersionInfo.FileVersion}}
    }
    interpretation_notice = @(
        'This report is read-only and does not prove authority to define or increment an application-owned NV counter.',
        'Visible NV handles or a ready TPM prove command-path availability only.',
        'A later separately authorized disposable proof is still required for exact NV policy, custody, persistence, restart and recovery behavior.'
    )
}

$report | ConvertTo-Json -Depth 12
