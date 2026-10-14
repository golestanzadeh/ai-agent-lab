# UI25-01 independent audit and IPC continuation — 2026-10-14

## UI25-01 audit

Initial reviewed SHA: `79dde300945eef063e19c75ff8f176107eff14be`

Independent reviewer: `/root/ui25_01_independent_audit`

Initial decision: `UI25-01_INDEPENDENT_UI_AUDIT_FAIL`

The responsive stylesheet hides visible navigation-label spans at tablet/mobile widths. The nine actionable sidebar links lacked their own accessible names, so their screen-reader names collapsed to decorative glyphs. The correction adds localized `aria-label` values without changing routes, data authority or submission behavior.

Remediation SHA: `6dd95f5c58230bf41c7e8ae81e79d46c11844b88`

Independent re-review decision: **`UI25-01_INDEPENDENT_UI_AUDIT_PASS`**

Verification:

- focused dashboard: `19 passed`, exit 0;
- relevant UI and local-launcher regression: `93 passed`, exit 0;
- German LTR and Persian RTL labels, language/case persistence, focus visibility, skip navigation, exactly one selected-case `aria-current`, fail-closed source behavior, unknown-case isolation and inert submission all passed review.

This is not full UI25-01 acceptance. The real durable case resolver remains an independent persistence/IPC prerequisite.

## Authenticated IPC continuation

Architecture remediation SHA: `ef8c2b4bb800dd04e7c92deb5deca841c53c9d16`

Independent re-review SHA: `7629b43bb2e5fb26cbb7bef3c534e40bf1392e70`

The re-review found F01-F04 and F06 adequately specified for later implementation verification, but required proof that this host supports the ADR-mandated TPM 2.0 NV monotonic counter. The Owner subsequently ran the prepared elevated read-only diagnostic. The ignored local JSON was examined without copying host identity or raw event data into Git:

- `Get-Tpm`: `TpmPresent=false`, `TpmReady=false`, `TpmEnabled=false`, `TpmActivated=false`;
- `TpmTool getdeviceinformation`: `0x800710df`, device not ready;
- `Win32_Tpm`: no TPM instance;
- `SecurityDevices`: no matching PnP device;
- Microsoft Platform Crypto Provider: `0x80090030 NTE_DEVICE_NOT_READY`;
- TBS TPM2 NV capability context creation: `0x8028400F`.

Decision: **`TPM_NV_UNSUPPORTED_VERIFIED / BLOCKED_ARCHITECTURE`**.

The ADR explicitly forbids substituting a file counter, registry value, software-only HMAC, database comparison or administrator assertion. No IPC implementation can therefore begin under the accepted architecture. No TPM, BIOS/UEFI, key, service, ACL, principal, database or protected data was changed.

## Exact next action

The Owner must select or authorize investigation of a different independently non-rollbackable freshness authority suitable for this Windows-local/Docker and future VPS deployment model. That choice is an architecture Human Gate. The ADR must then be revised and independently security-reviewed on an exact commit before authenticated IPC implementation begins. C09 remains OPEN / NOT ACCEPTED; OI-0002 is not closed and OI-0003 remains blocked.
