# OI-0002 independent IPC ADR re-review — 2026-10-14

Review identity: `/root/oi0002_ipc_independent_rereview_20261014`  
Reviewed commit: `ef8c2b4bb800dd04e7c92deb5deca841c53c9d16`  
Reviewed artifact: `docs/oi-0002-kernel-identity-ipc-adr-20261013.md`  
Prior independent review: commit `86a96d06b5c1091a273badadbe3b988831b8ea27`  
Decision: **`ARCHITECTURE_BLOCKED_BY_HOST_FEASIBILITY`**

## Independence and bounded scope

This review was performed in the dedicated worktree `C:\Users\rezag\ai-agent-lab-oi0002-ipc-rereview` on branch `codex/oi0002-ipc-independent-rereview-20261014`. The reviewer did not author the ADR or its remediation and did not modify the ADR, implementation, service configuration, TPM, keys, ACLs, principals, protected data or runtime. The exact target was clean and checked out at the SHA above. The complete prior report was read with `git show`; it was not merged.

The review used only frozen C01–C13 and re-examined F01–F06 plus directly introduced contradictions. It does not demand implementation evidence at ADR phase. Read-only host inspection was limited to TPM/device/provider/OS/interface discovery; no TPM index or key was created and no security or service state changed.

## Executive conclusion

F01, F02, F03, F04 and F06 now have sufficiently precise architecture contracts; their remaining proof belongs to implementation and the four-principal operational campaign. In particular, the signed row-derived reservation and five-second commit permit do not authorize a missing, expired, revoked, replayed or differently bound transaction; `ANCHOR_PENDING` is explicitly non-finalizable; physical restore covers the complete deployment store; and canonical bytes and pipe framing are normative.

F05 is not accepted on this deployment host. The ADR correctly makes a usable TPM 2.0 NV counter a pre-implementation prerequisite and forbids fallback. Read-only inspection could not establish a ready TPM, a usable Platform Crypto Provider, an enumerated TPM security device, or usable NV-counter facilities. `TpmTool` returned `0x800710df` (`The device is not ready for use`), while `certutil -csplist` enumerated Microsoft Platform Crypto Provider but failed it with `NTE_DEVICE_NOT_READY`. Therefore the proposed non-rollbackable freshness authority is not verified or presently usable on this host. TPM presence must not be inferred from `tbs.dll`, `tpm.sys`, or Windows 11 alone.

## F01–F06 disposition

| Finding | Classification | Independent assessment |
| --- | --- | --- |
| F01 | `IMPLEMENTATION_VERIFICATION_REQUIRED` | `reservation-proof/v1` can be signed only from a reread durable PENDING row and is bound to deployment, transaction, request, operation, projected heads, generation and lifetime. Identity verifies it without Kernel DB access. Missing, fabricated, expired, replayed and mismatched proofs deny before change. Restart may issue fresh proofs only from the same durable PENDING row. Negative and restart evidence remains implementation work. |
| F02 | `IMPLEMENTATION_VERIFICATION_REQUIRED` | `commit-permit/v1` is emitted only after a committed serializable revalidation/reservation row and expires within five seconds. Revocation either serializes before issuance or after the bounded fence expires/terminates; it is not indefinitely blocked by an open database transaction. Identity checks time and one-time use atomically with mutation. Expiry/restart requires fresh full revalidation. A permit cannot authorize an unreserved, revoked-before-issuance, expired, replayed or differently bound transaction. Precise lock/expiry implementation and adversarial timing tests remain required. |
| F03 | `IMPLEMENTATION_VERIFICATION_REQUIRED` | Identity persists `ANCHOR_PENDING`; `GET_TRANSACTION` returns `NOT_FINALIZABLE`; Kernel cannot finalize until TPM witness binding, file and directory durability, reread verification, receipt consumption and `COMMITTED_FINAL`. Repeated publication failure fails closed. Exact Windows durability and crash evidence remains implementation work. |
| F04 | `IMPLEMENTATION_VERIFICATION_REQUIRED` | Physical backup/restore is explicitly `DEPLOYMENT_STORE`, uses `*` case/year sentinels, binds deployment/store identity and the ordered complete case-generation manifest, and selects a whole staged generation. Case-only or incomplete authorization denies before staging/replacement. Multi-case and interrupted-generation tests remain implementation work. |
| F05 | `UNRESOLVED` | The external TPM-counter concept would detect coordinated rollback and is separated from both recovery sets. Its service has no domain decision authority, so it does not create a second transaction coordinator or fifth domain principal. However the exact deployment prerequisite is not verified and current host probes report no ready/usable TPM path. Custody, NV authorization policy, atomic advance/witness journal, crash reconstruction, journal loss and TPM loss/migration therefore cannot yet be realized or verified here. The ADR itself requires `BLOCKED_ARCHITECTURE` in this condition. |
| F06 | `IMPLEMENTATION_VERIFICATION_REQUIRED` | RFC 8785 is normatively selected with a stricter type/Unicode/timestamp profile; digests identify exact canonical UTF-8 bytes; length excludes the prefix; one frame equals one pipe message; split reads, `ERROR_MORE_DATA`, EOF, concatenation, trailing bytes and malformed input have exact rejection behavior. Full-schema and cross-runtime vectors remain implementation work. |

## Critical-path analysis

### Reservation, permit, restart and revocation

Identity accepts COMMIT only with both signed proofs and exact PREPARED bindings. Reservation is derived from a durable reread rather than caller fields. Permit issuance revalidates every authorization dimension and commits a bounded use reservation before signing. The five-second `not_after` is checked independently by Identity and is never extended during reconciliation. A crash before Identity commit makes the permit expire; the Kernel must perform current-state revalidation before a replacement permit. Exact retries after a recorded result return that result and cannot repeat mutation.

The fence description does not require a database lock to remain held while Identity works: the fence row is committed before signing, and revocation serializes against its bounded terminal/expiry state. Consequently the architecture does not require indefinite revocation blocking. Implementation must prove that expiry is evaluated durably without relying on a live Kernel process and that revocation cannot be starved by repeated refreshes.

### Anchor finality

`ANCHOR_PENDING` cannot produce a final result. A TPM advance is irreversible, so recovery is restricted to completing the exact pending transaction; ambiguous witness or journal state is a governed fail-closed event. This is precise enough for ADR review, subject to the F05 host blocker.

### Restore scope

The recovery unit is the entire staged deployment store: database, WAL state and anchor selected by one generation pointer, with an exact complete affected-case manifest. This resolves the earlier case-scoped authorization of a whole-database replacement. Implementation must still prove the platform-specific durability of the generation pointer and all directory/file flushes.

### Freshness authority and four-principal model

The proposed Key-Custodian endpoint is a narrow cryptographic/freshness mechanism. Kernel alone chooses and orders transactions; the custodian accepts only the exact next counter value and signed binding. This preserves C01. `AITaxKeyCustodian` is already one of the frozen four principals, so no new principal is introduced. The append-only request/result journal is additional custodian state, but not another transaction coordinator.

The unresolved issue is feasibility, not an invented acceptance criterion: the ADR explicitly requires the operational preflight to prove NV counter support and declares absence `BLOCKED_ARCHITECTURE`. A TPM-backed CNG signing key and the TPM Base Services library do not by themselves prove application-controlled NV counter definition, authorization, persistence, or recovery.

## Read-only Windows host feasibility gate

| Capability | Evidence | Classification |
| --- | --- | --- |
| Windows deployment baseline | `Win32_OperatingSystem`: Windows 11 Pro, version `10.0.26100`, 64-bit | `VERIFIED_ON_HOST` |
| Current execution integrity | `whoami /groups`: Medium Mandatory Level (`S-1-16-8192`) | `VERIFIED_ON_HOST` |
| TPM 2.0 presence/readiness | `Get-Tpm` required Administrator; `TpmTool getdeviceinformation` failed `0x800710df`, device not ready; TPM WMI access denied; no `SecurityDevices` PnP object enumerated | `UNSUPPORTED_OR_BLOCKED` |
| CNG platform provider | `certutil -csplist` enumerated Microsoft Platform Crypto Provider but reported `NTE_DEVICE_NOT_READY`; its legacy provider registry key was absent | `UNSUPPORTED_OR_BLOCKED` |
| Low-level Windows TPM interfaces | `C:\Windows\System32\tbs.dll`, `tpm.sys` and `TpmTool.exe` exist | `SUPPORTED_IN_PRINCIPLE_NOT_VERIFIED` |
| Application-controlled TPM NV counter with required policy | No safe read-only probe established index availability, TPM command authorization, per-deployment allocation, restart persistence or loss/migration behavior | `UNSUPPORTED_OR_BLOCKED` |
| Named-pipe/CNG design generally | Windows 11 supplies the underlying Named Pipe, token and CNG APIs; no service implementation was installed or exercised | `SUPPORTED_IN_PRINCIPLE_NOT_VERIFIED` |

No conclusion about physical TPM absence is made. The narrower and sufficient conclusion is that the required TPM NV-counter mechanism is not verified and is presently blocked on this host. Elevation alone is not assumed to cure `device not ready`, missing provider/device enumeration, NV policy support, or operational custody.

## Frozen C01–C13 impact

| Criterion | Re-review disposition |
| --- | --- |
| C01 | Contract adequate; Kernel remains the sole transaction coordinator. Implementation verification required. |
| C02 | No architecture regression; preserved custody requires operational verification after deployment-affecting change. |
| C03 | Contract adequate for exact-token, closed local IPC and authorization proofs. Implementation verification required. |
| C04 | Contract adequate for canonical transaction identity, durable idempotency and mismatch denial. Implementation verification required. |
| C05 | Contract adequate through non-finalizable `ANCHOR_PENDING`; implementation/crash verification required and F05 witness availability remains a dependency. |
| C06 | Exact heads/generations/anchors are bound, but operational acceptance is blocked with F05 host feasibility. |
| C07 | Reconciliation table is deterministic and fail-closed; implementation/fault verification required. |
| C08 | Deployment-store restore scope and one-time use are precise; implementation/operational verification required. |
| C09 | **BLOCKED**: coordinated rollback protection depends on the unavailable/unverified TPM NV counter. |
| C10 | No contract-level regression to accepted Identity/family semantics; routing verification remains future work. |
| C11 | Correlation and privacy-minimized audit contract is adequate; implementation reconstruction evidence required. |
| C12 | Exact contract/version/canonical bytes are frozen; compatibility implementation tests required. |
| C13 | **BLOCKED** by C09 host feasibility; the implementation and complete campaign may not begin. |

No new contradiction was found for C01–C04, C07–C08 or C10–C12 at contract level. C05/C06/C11 depend on the F03 implementation and freshness witness. This is not a failure for missing implementation tests.

## Verification record

Read-only inspection and static verification commands/results:

- `git status --short --branch`, `git rev-parse HEAD`, `git branch --show-current` — clean exact target on the dedicated branch.
- `git show 86a96d06b5c1091a273badadbe3b988831b8ea27:docs/oi-0002-independent-ipc-architecture-security-review-20261013.md` — complete prior review read without merge.
- `Get-Tpm` — blocked because Administrator privilege is required.
- `TpmTool getdeviceinformation` — failed `0x800710df`, device not ready.
- `Get-CimInstance root\CIMV2\Security\MicrosoftTpm:Win32_Tpm` — access denied.
- `Get-PnpDevice -Class SecurityDevices` — no matching device enumerated.
- `certutil -csplist` — Platform Crypto Provider enumerated but failed `NTE_DEVICE_NOT_READY`; legacy provider registry query returned key not found.
- OS, integrity, `tbs.dll`, `tpm.sys` and tool presence queries — succeeded as recorded above.
- Documentation index test and static document checks are recorded in the review commit.

Starting authenticated capacity supplied by the supervisor at `2026-10-14T11:47:17.460775Z` was five-hour 99% remaining (reset `2026-10-14T16:46:54Z`) and weekly 90% remaining (reset `2026-10-20T08:19:11Z`). The existing `BOUNDED(15/5)` guard returned `RUN_OPERATION_FITS` and the 15-point reserve was preserved.

Ending authenticated telemetry was read once with the existing reader and explicit executable `C:\Users\rezag\AppData\Roaming\npm\codex.cmd`, persisted to the existing ignored `.runtime/usage/CODEX_USAGE.json`, and verified by readback at `2026-10-14T11:51:36.599707Z`: five-hour 92% remaining (8% used; reset `2026-10-14T16:46:54Z`), weekly 89% remaining (11% used; reset `2026-10-20T08:19:11Z`), ordinary usage allowed. The 15-point reserve remains intact.

## Decision and exact continuation

**`ARCHITECTURE_BLOCKED_BY_HOST_FEASIBILITY`**

Reason: F01–F04 and F06 are contract-resolved pending implementation verification, but F05's mandatory independently monotonic TPM NV counter cannot be verified or used on the target host from the available read-only evidence; the ADR forbids fallback and expressly blocks architecture in this state.

One bounded next action: under separately authorized host-administration control, establish whether firmware exposes a ready TPM 2.0 and whether Windows permits the exact application-owned NV-counter lifecycle and policy; record read-only/vendor/API evidence where possible. If unsupported, the Owner must approve a different independently non-rollbackable authority and require a new independent ADR review. No IPC implementation, fallback counter, TPM provisioning, remediation loop, merge, release, security change or OI-0003 work is authorized by this review.
