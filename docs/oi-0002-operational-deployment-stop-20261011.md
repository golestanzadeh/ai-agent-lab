# OI-0002 operational deployment and acceptance stop — 2026-10-11

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
