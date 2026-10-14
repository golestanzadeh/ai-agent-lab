# OI-0002 TPM host feasibility diagnostic — 2026-10-14

Reference independent review: `7629b43bb2e5fb26cbb7bef3c534e40bf1392e70`

Decision: **`OWNER_ADMIN_DIAGNOSTIC_REQUIRED`**

## Scope and safety

This bounded task diagnoses only the remaining F05 host prerequisite. No TPM initialization, clear, reset, ownership, NV-index operation, key operation, BIOS/UEFI change, driver/security/ACL/service/principal change, IPC implementation, ADR edit or acceptance-matrix edit occurred.

The current process is `desktop-hvruqb7\rezag` at Medium Mandatory Level (`S-1-16-8192`), not an elevated Administrator token. The non-elevated evidence cannot distinguish a disabled/unready TPM from information hidden behind the Administrator boundary, and cannot establish usable application-owned NV-counter authorization. The task therefore stops at the required Owner boundary.

## Non-elevated host evidence

| Question | Command and result | Exit/error evidence | Conclusion |
| --- | --- | --- | --- |
| TPM status | `Get-Tpm` | Printed `Administrator privilege is required to execute this command`; the cmdlet did not expose a reliable process exit code | Administrator evidence required |
| TPM device information | `%WINDIR%\System32\TpmTool.exe getdeviceinformation` | exit `-2147020577` / `0x800710df`: `The device is not ready for use` | TPM command path presently not ready |
| TPM WMI/CIM | `Get-CimInstance root\CIMV2\Security\MicrosoftTpm:Win32_Tpm` | captured diagnostic exit `1`: `Access denied` | Administrator evidence required |
| PnP TPM/security device | `Get-PnpDevice -Class SecurityDevices` | captured diagnostic exit `1`: no matching `Win32_PnPEntity` | No device enumerated to this token; not proof of physical absence |
| Firmware boot type | `Get-ComputerInfo -Property BiosFirmwareType,...` | exit `0`; `BiosFirmwareType: Bios`, Windows 11 Pro `10.0.26100`, 64-bit | Legacy/BIOS is reported; elevated Secure Boot confirmation still required |
| Secure Boot | `Confirm-SecureBootUEFI` | captured diagnostic exit `1`: access denied | Administrator evidence required |
| TPM event channels | read-only `Get-WinEvent` queries | matching TPM operational logs/providers were not exposed to this token | Elevated inventory required |
| Platform Crypto Provider | `certutil -csplist` | exit `-2146893776` / `0x80090030` `NTE_DEVICE_NOT_READY` | Provider exists but required device is not ready |
| Windows TPM interfaces | file inventory | `tbs.dll`, `tpm.sys`, `TpmTool.exe` exist | Support in principle only; not NV feasibility |

TPM presence, readiness, ownership, TPM 2.0 capability, visibility of NV indexes, ability to define a counter, and ability to bind that counter to `AITaxKeyCustodian` are separate questions. None of the evidence above proves the latter two.

## Prepared elevated read-only diagnostic

Script: `scripts/diagnose_oi0002_tpm_readonly.ps1`

The script refuses to run without an elevated Administrator token. It performs only read operations:

- `Get-Tpm`, `TpmTool getdeviceinformation` and `Win32_Tpm` status;
- TPM/SecurityDevices PnP and driver information;
- UEFI/Secure Boot status and TPM event-channel evidence;
- Microsoft Platform Crypto Provider enumeration;
- file/version inventory for Windows TPM interfaces;
- one raw TPM 2.0 `TPM2_GetCapability(TPM_CAP_HANDLES, TPM_HR_NV_INDEX, 64)` through TBS. This enumerates visible NV handles only and does not define, write, increment, delete, clear, own or activate anything.

From an **Owner-opened elevated PowerShell** window, run exactly:

```powershell
Set-Location -LiteralPath 'C:\Users\rezag\ai-agent-lab-oi0002-tpm-diagnostic'
New-Item -ItemType Directory -Force -Path '.runtime\diagnostics' | Out-Null
powershell.exe -NoProfile -ExecutionPolicy Bypass -File '.\scripts\diagnose_oi0002_tpm_readonly.ps1' | Set-Content -LiteralPath '.runtime\diagnostics\oi0002-tpm-readonly-20261014.json' -Encoding utf8
```

Expected evidence path:

`C:\Users\rezag\ai-agent-lab-oi0002-tpm-diagnostic\.runtime\diagnostics\oi0002-tpm-readonly-20261014.json`

The output remains ignored local diagnostic evidence. It must be examined before any feasibility conclusion. Do not paste secrets or unrelated event logs into Git or chat.

## Remaining verification requirements

Even a ready TPM 2.0 and a successful read-only NV-handle query are insufficient for `TPM_NV_FEASIBLE_VERIFIED`. A later separately authorized disposable proof would still need to demonstrate, without touching production state:

1. Windows/TBS permits the exact TPM 2.0 NV counter lifecycle required by the ADR.
2. The NV authorization policy can be held by the existing `AITaxKeyCustodian` principal without Kernel, Identity, Recovery or Administrator receiving counter-management authority.
3. The counter survives service and host restart, rejects stale/incorrect expected values, and has defined TPM-loss/migration behavior.
4. Key-Custodian witness/journal recovery cannot silently substitute or roll back the TPM value.

This task does not authorize that state-changing disposable proof. It only gathers the prerequisite read-only evidence.

## Exact continuation

The Owner must run the prepared script manually in an elevated PowerShell session and return the resulting JSON for examination. Until that evidence is reviewed, F05 remains unresolved, IPC implementation remains forbidden and no ADR remediation or alternative freshness authority is authorized.
