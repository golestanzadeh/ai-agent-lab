# OI-0002 operational deployment and acceptance stop — 2026-10-11

## Owner-authorized uninterrupted completion attempt — 2026-10-12

Status: **TECHNICAL_BLOCKER / OPERATIONAL_PARTIAL_PASS / NOT ACCEPTED**.

The Owner's new authorization removed the former approval/Human-Gate blocker and authorized minimum Windows logon rights, disposable execution mechanisms and bounded operational remediation. Authenticated admission capacity was 77% five-hour and 72% weekly, above the mandatory reserve.

The Windows UAC path was verified with a non-mutating elevated probe. `SeBatchLogonRight` was granted to the four existing enabled `AITax*` principals. A passwordless local-account S4U task remained fail-closed (`Access denied`), so the accepted minimum mechanism used cryptographically random one-time passwords generated only inside the elevated process. Each task ran at `RunLevel Limited`; every task was deleted immediately and each account password was rotated again to a new undisclosed random value. No credential was written to Git, evidence, command output or chat. No account received Administrator membership.

The authoritative real-token evidence run is `run-20261012T174008Z`, retained under the protected local evidence root `C:\ProgramData\AI-Tax-Agent\OI0002-OPS-EVIDENCE2`. Each role wrote only to its own temporary evidence directory; after the task ended that directory was sealed read-only for the role, and the controller recorded a SHA-256 for the result in its protected summary. Earlier exploratory runs are not acceptance evidence. The authoritative run contains synthetic operational metadata only and no taxpayer data or key bytes. The exact effective-access results were:

| Principal | Allowed and verified | Denied and verified | Result |
| --- | --- | --- | --- |
| `AITaxKernel` | Kernel store and Kernel backup write | control read, Identity store/backup write, secrets write, key read/write | PASS |
| `AITaxIdentity` | Identity store/backup write and HMAC key read | control read, Kernel store/backup write, secrets write, key write | PASS |
| `AITaxKeyCustodian` | secrets write and key read/write-open | control read, Kernel/Identity store and backup write | PASS |
| `AITaxRecovery` | control read, all protected store/backup writes, key read/write-open | none within the recovery contract | PASS |

The official verifier executed under the real `AITaxRecovery` token and returned `OI0002_WINDOWS_CUSTODY_VERIFIED`. No probe modified the HMAC key; write tests opened the existing file without writing bytes. All probe files were uniquely named and removed. Readback found zero remaining `OI0002-Temporary-*` tasks, and all four accounts remained enabled.

Two reviewed scripts now make the real-token check reproducible without embedding credentials:

- `scripts/oi0002_windows_token_probe.ps1`
- `scripts/invoke_oi0002_windows_token_verification.ps1`

Focused Windows/identity/Kernel verification after implementation: `106 passed`, exit `0`. Complete unit regression: `1143 passed, 5 skipped`, exit `0`. Documentation/governance verification after the final evidence-hardening change: `26 passed`, exit `0`.

An independent read-only reviewer recomputed all four sealed result hashes, inspected the protected per-role ACLs, verified that no temporary task remained, reran the focused Windows/continuity/persistence selection (`61 passed`, exit `0`) and returned **PASS for report accuracy and the technical-blocker disposition**. This PASS is not OI-0002 acceptance and does not satisfy the missing operational service-contract criteria.

### Non-recoverable-in-package architecture blocker

The remaining required operational criteria cannot be executed honestly with the current accepted implementation:

1. `src/agent_lab/identity_continuity_authority.py:1` explicitly identifies the continuity adapter as synthetic. Lines 26–27 require an in-process `OrchestratorKernel` object, and every operation directly calls that object.
2. The protected ACL contract correctly prevents `AITaxIdentity` from opening the Kernel store. Therefore the current adapter cannot run under the real Identity token without weakening the accepted Kernel/Identity separation.
3. `IdentityPersistence.__init__` (`src/agent_lab/identity_persistence.py:76-95`) accepts generic callback functions for authorization and evidence resolution but has no durable Kernel client, manifest-bound permission client, continuity transaction, authenticated IPC or reviewed service boundary.
4. Consequently no accepted mechanism binds a real protected Identity commit/backup head to Kernel `PENDING → COMMITTED` while the two stores remain under their separate principals. Restart, populated restore, unauthorized-restore and rollback tests could be run only by using synthetic callbacks, direct cross-store access, Administrator substitution or a newly invented broker. Each would falsely label synthetic/test authority as operational proof or weaken the frozen security model.

Resolving this defect requires a separately reviewed Kernel/Identity service boundary (for example an authenticated, least-privilege local IPC contract), explicit binding of the Identity audit/backup head to Kernel continuity and restore authorization, and deployment lifecycle specifications. That is an architecture change, not a recoverable test failure or permission correction. The Owner's authorization forbids bypassing mandatory security criteria and parallel authority; it does not supply an accepted IPC/service contract. Accordingly OI-0002 cannot be marked `ACCEPTED / CLOSED` from the present evidence.

The exact next action is Owner/architecture-authority approval of a bounded Kernel↔Identity operational service contract, followed by implementation, real-token restart/backup/restore/rollback verification and a new independent review. OI-0003 remains blocked and was not started.

## Final operational acceptance follow-up — 2026-10-12

Status: **HUMAN_REQUIRED / OPERATIONAL_ACCEPTANCE_BLOCKED / NOT ACCEPTED**.

The exact governed target was recovered at Owner-acceptance commit `605e502d61556258d219c3ab2b6cf12372c2d451`. This commit records the Owner's acceptance of REMEDIATION-02 only; it does not release the separate OI-0002 operational gates.

The host state has changed since the original stop. The four distinct local principals now exist and are enabled:

- `AITaxKernel` (`S-1-5-21-212838446-3778166418-3746953556-1020`)
- `AITaxIdentity` (`S-1-5-21-212838446-3778166418-3746953556-1021`)
- `AITaxKeyCustodian` (`S-1-5-21-212838446-3778166418-3746953556-1022`)
- `AITaxRecovery` (`S-1-5-21-212838446-3778166418-3746953556-1023`)

The current Codex process is still `desktop-hvruqb7\rezag` and is not elevated. No OI-0002-specific Windows service or Scheduled Task, and no task running under an `AITax*` principal, was found. Three unrelated legacy `AI-Tax-Agent` tasks running as `rezag` were excluded from this claim. Three bounded roots were observed under `C:\ProgramData\AI-Tax-Agent`:

- `OI0002`: official verifier returned `OI0002_MANIFEST_MISSING`.
- `OI0002-TEST`: official verifier returned `OI0002_MANIFEST_MISSING`; the visible root still inherits the parent ACL.
- `OI0002-TEST2`: the current medium-integrity user was denied access before the manifest could be read. This is useful negative-access evidence, but it is not proof of the exact ACL allowlist, effective access under each service token, key custody, application wiring, restart, backup/restore or rollback behavior.

No protected content or key bytes were read or printed, and no Windows account, ACL, secret, service, task, database or backup was changed. The two incomplete roots were not deleted because their ownership and intended recovery status are not established.

Verification on exact SHA `605e502d61556258d219c3ab2b6cf12372c2d451`:

- Focused Windows custody, identity persistence, evidence, continuity and Kernel tests: `104 passed`, `0 failed`, exit `0`.
- Complete unit regression: `1141 passed, 5 skipped`, exit `0`, `256.66s`.
- The first attempted focused command used one incorrect test filename and therefore collected no tests; it was corrected before any test result was claimed.

Authenticated capacity at admission was 94% five-hour remaining (reset `2026-10-12T21:37:10Z`) and 75% weekly remaining (reset `2026-10-18T14:48:11Z`), preserving the mandatory 15-point reserve.

The exact missing authority is an approved elevated execution context plus an approved non-secret-bearing mechanism to execute the operational probes under each of the four actual `AITax*` tokens. Passwords or other credentials must not be placed in Git, chat, command output or test evidence. In that context, the existing provisioner/verifier must first establish one canonical disposable root; the application must then be wired through its real persistence contracts and the effective-access, restart, populated backup/restore, unauthorized restore, rollback and audit-continuity scenarios must be executed. Only a separate independent review of that new exact evidence may recommend `INDEPENDENT_REVIEW_PASS / OWNER_ACCEPTANCE_READY`.

Until that Human Gate is satisfied, `E-03`, `C-02`, `C-06`, overall OI-0002 and OI-0003 remain blocked. REMEDIATION-02 remains Owner-accepted on its independent-review evidence and was not reopened.

An independent read-only reviewer reproduced the host-state claims, reran the focused suite (`104 passed`, exit `0`), and returned **PASS for the accuracy of this stop/handoff and its blocker disposition**. That review explicitly does not accept OI-0002; it confirms that `HUMAN_REQUIRED / OPERATIONAL_ACCEPTANCE_BLOCKED` is the evidence-supported result.

## Outcome

Status: **BLOCKED / NOT ACCEPTED**.

The authorized Windows deployment was attempted only through the fail-closed preflight. The current process runs as `desktop-hvruqb7\rezag` with a medium-integrity token and a deny-only Administrators group. It therefore cannot create or configure the required dedicated identities and protected ACLs. Running the provisioner against `C:\ProgramData\AI-Tax-Agent\OI0002` returned `OI0002_ELEVATION_REQUIRED`; readback confirmed `TARGET_NOT_CREATED`. No Windows account, ACL, secret, database, backup or production state was changed.

The implementation worker did not claim operational acceptance. `E-03`, `C-02`, `C-06`, `REMEDIATION-02` and `OI-0003` remain blocked.

## Recovery and capacity gate

- Authorized branch: `oi0002-identity-persistence`.
- Recovered synchronized clean baseline: `9923edb75edf7094f5ef0638c6d4d8e89848bdad`.
- Starting authenticated Codex capacity: 76% five-hour remaining and 96% weekly remaining.
- Starting reset timestamps: `2026-10-11T19:48:11Z` and `2026-10-18T14:48:11Z`.
- The deterministic reserve admitted the bounded implementation, regression, review and reporting work.
- Ending authenticated Codex capacity measured `2026-10-11T17:47:52+02:00`: 47% five-hour remaining and 92% weekly remaining, with the same reset timestamps. The 15-point five-hour reserve is preserved.

## Scoped implementation

Three pushed commits were produced:

1. `d8f197e5512bf20d3c8197896fa198e2a10f1c7a` — fail-closed Windows custody provisioning and verification entry points.
2. `3834367ac45d2a78298036b62eb5df77813523b5` — separate Kernel, Identity, key-custodian and recovery principals; recovery-controlled manifest; exact ACL allowlists; independent HMAC custody; unsafe-root rejection; and consistent-snapshot SQLite audit verification.
3. `2537901a6ecd6e1ca7e584875a3881cc2d09fd44` — exact fixed custody-path binding, root ACL verification, and ACE rights/inheritance/propagation matching. The subsequent reporting change also extends reparse inspection from each child through the deployment root to the volume boundary.
4. `c84d67da7c6b8e18863610a79a4440ab47a0d93a` — exact final implementation SHA; completes volume-boundary reparse inspection and records the governed operational stop.

Changed implementation files:

- `scripts/provision_oi0002_windows.ps1`
- `scripts/verify_oi0002_windows.ps1`
- `src/agent_lab/identity_evidence_authority.py`
- `tests/unit/test_oi0002_windows_deployment_scripts.py`

The provisioner creates only the protected directory/key/manifest custody topology. It does not claim to install a Windows service, activate production, initialize application databases, populate backups or prove restore behavior.

## Verification actually executed

- PowerShell AST parsing: both deployment scripts, zero errors.
- Focused custody/evidence/continuity verification after final code correction: `25 passed`, exit 0.
- Earlier combined focused verification after the consistent-snapshot correction: `51 passed`, exit 0.
- Repeated evidence-concurrency probe: `30/30` passed.
- Complete unit regression at `3834367`: `1119 passed, 5 skipped`, exit 0, 255.24 seconds.

The independent reviewer reproduced the earlier audit-integrity race before correction and then observed the relevant suite pass (`72 passed`) plus `10/10` repeated concurrency runs. The reviewer confirmed code-level correction of manifest trust and independent key custody, while withholding acceptance because real deployment evidence does not exist. A final narrow review of `2537901` is recorded below.

## Acceptance criteria disposition

| Criterion | Result | Evidence / blocker |
| --- | --- | --- |
| Dedicated Kernel and Identity identities | BLOCKED | No elevated authority to create or configure them. |
| Least-privilege ACLs | BLOCKED | Exact verifier/provisioner contracts exist; no actual ACL/effective-access readback. |
| HMAC key custody | BLOCKED | Separate custodian design is implemented; no operational principal or protected key was created. |
| Independent Kernel/Identity backups | BLOCKED | Separate protected target directories are specified; no populated backup or restore rehearsal. |
| Restart/recovery continuity | BLOCKED | Synthetic tests pass; no deployed service restart or rollback exercise. |
| Unauthorized access probes | BLOCKED | No service identities/tokens exist on this host for real access probes. |
| Application wiring | BLOCKED | No deployed database/service configuration was activated. |
| Independent acceptance | BLOCKED | Reviewer withheld PASS pending operational evidence and remaining real-host verification. |

## Security review and residual risks

The first review rejected the initial implementation for manifest trust, incomplete ACL verification, replaceable-key custody, insufficient path confinement, weak behavioral tests and absent operational evidence. The first five code-addressable issues were tightened in the subsequent commits. The remaining material risks require a disposable elevated deployment: effective-access probes under each actual principal, application initialization/wiring, restart behavior, populated independent backups, authorized restore, unauthorized restore, rollback and audit continuity.

No real taxpayer data, credentials or private identity values were written to Git. No ELSTER/Finanzamt transmission, merge, release, production activation, scheduler or downstream OI-0003 execution occurred.

## Exact continuation

The next permitted action is an Owner-governed **elevated disposable-host deployment**, using four pre-approved distinct Windows principals and the pushed provision/verify scripts at `C:\ProgramData\AI-Tax-Agent\OI0002`. It must then initialize the real Kernel and Identity stores through their existing contracts, exercise each service under its own token, capture redacted ACL/effective-access evidence, restart both services, create and restore populated independent backups, reject unauthorized restore and rollback, and rerun the complete regression. A separate independent reviewer must inspect the resulting exact SHA and operational evidence before any Owner gate disposition. Until then OI-0002 stays open and every dependent gate stays blocked.

## Final independent review

The final narrow review of exact final implementation SHA `c84d67da7c6b8e18863610a79a4440ab47a0d93a` passed the ancestor-reparse correction at code level, confirmed zero PowerShell AST errors and `5 passed` focused script tests, and found the governed records accurate. It still withheld acceptance because explicit ACE inspection is not an effective-access test under each real service token. That requirement cannot be honestly satisfied without the approved elevated disposable-host principals. Final recommendation remains **BLOCKED / NOT ACCEPTED**.
