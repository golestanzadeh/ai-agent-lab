# C09 witness crash and recovery matrix

Status: `DESIGN / LOCAL_SIMULATION_PASS`

| Observed state | Deterministic recovery | Acknowledgement |
|---|---|---|
| Kernel PENDING; Identity unchanged; no witness | Abort the pending operation and audit the abort. | Never acknowledged. |
| Identity new; Kernel PENDING; no witness | `FAIL_CLOSED_IDENTITY_AHEAD`; require governed reconciliation, never automatic replay. | Never acknowledged. |
| Exact witness exists; Kernel PENDING; Identity matches | Verify authentication, sequence, previous commitment, exact pending and provider version; complete Kernel COMMITTED idempotently. | Only after durable COMMITTED. |
| Witness ahead; no matching Kernel PENDING | Security incident; no synthetic pending may be invented. | Denied. |
| Kernel COMMITTED ahead of witness | Integrity violation; COMMITTED was illegal. Halt protected operations. | Denied/revoked if previously exposed. |
| Identity ahead of Kernel | Halt; require exact pending or Owner-authorized repair. | Denied. |
| Both local stores older than witness | Coordinated rollback detected by epoch/sequence/head mismatch. | Denied. |
| Missing sequence, conflicting successor, invalid MAC or multiple versions | Halt and preserve all evidence. | Denied. |
| Witness unavailable | No protected operation or restore finalizes. Read-only/nonprotected policy is separate. | Denied. |
| Restore requested | Verify one-time, expiring Owner authorization bound to current witness commitment, source backup digest, target epoch/head/generation and operator; append RESTORE transition before new epoch. | Only after new epoch genesis is witnessed and locally committed. |
| Reused/expired/mismatched restore authority | Reject and audit. | Denied. |

An authorized restore never deletes or rewrites witness history. It appends a signed transition from the current global commitment to a strictly greater epoch, then creates sequence 1 for that epoch. Any ambiguity remains fail-closed.

## 2026-10-22 implementation clarification
The Identity-ahead / Kernel PENDING / no-witness row above describes the conservative baseline, but current hardened simulator implements conditional RECONCILED_IDENTITY_AHEAD only when the exact previous externally authenticated base is verified and a matching pending operation exists. Outage, stale base, or ambiguity fail closed. This is local proof, not operational integration.

