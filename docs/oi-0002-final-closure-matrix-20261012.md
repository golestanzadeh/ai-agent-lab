# OI-0002 final closure matrix and UI recovery handoff

Date: 2026-10-12  
Authority: Owner instruction `OI-0002 Final Closure and UI Delivery Recovery`  
Recovery baseline: `03425904661640d52e1ec158404719748164475c`  
Status: `MATRIX_FROZEN / BLOCKED_CAPACITY_BEFORE_IMPLEMENTATION`

This is the single bounded acceptance scope for the remaining OI-0002 work. It preserves accepted REMEDIATION-02, the four Windows principals, protected `OI0002-TEST2`, sealed real-token run `run-20261012T174008Z`, the official custody-verifier PASS and existing regression evidence. It does not add a new acceptance requirement, Orchestrator, database, scheduler or execution authority.

## Frozen closure matrix

| ID | Requirement | Existing evidence | Status | Exact missing implementation | Required operational test | Independent acceptance criterion |
| --- | --- | --- | --- | --- | --- | --- |
| C01 | Existing Kernel remains sole transaction coordinator | Kernel continuity/restore primitives and accepted remediation tests | PASS at code level | None; IPC must delegate to these primitives | Verify every accepted IPC operation maps to one Kernel transaction and no parallel authority exists | Reviewer traces request → Kernel decision → durable result and finds no alternate coordinator |
| C02 | Identity remains independently protected | Exact Windows ACL verifier and sealed four-token matrix | PASS | Preserve current roots/allowlists | Re-run only after deployment-affecting changes; reject cross-store access | Real Kernel/Identity tokens cannot open each other's DB; Recovery remains bounded |
| C03 | Authenticated, narrow local IPC | No accepted operational boundary; current adapter is in-process synthetic | BLOCKED | Versioned Windows-local authenticated IPC contract with peer-token identity and closed operation allowlist | Correct role succeeds; wrong principal, operation, case/year/task/manifest and replay fail | Separate reviewer verifies OS-authenticated caller identity, default-deny dispatch and no credential transport |
| C04 | Durable transaction correlation/idempotency | Kernel task/manifest/run binding and continuity tables exist | BLOCKED | Versioned transaction envelope and durable request/result/idempotency records | Duplicate, reordered and mismatched transaction IDs; restart retry | Exactly one logical outcome per transaction; mismatches fail closed and audit is reconstructable |
| C05 | PENDING → Identity Commit → COMMITTED | Kernel primitives pass synthetic tests | BLOCKED | Bind IPC transaction to an actual Identity commit head | Normal commit plus termination before and after Identity commit | Deterministic state after restart; no unbound commit or false COMMITTED state |
| C06 | Identity audit/backup head bound to Kernel | Identity audit anchors and backups pass independently | BLOCKED | Versioned head/epoch commitment carried through the Kernel record | Tamper, substituted DB/anchor/backup, stale head and old epoch | Every accepted state and restore matches the exact Kernel-bound head and generation |
| C07 | Deterministic restart/reconciliation | Synthetic continuity/reconciliation tests | BLOCKED operationally | IPC recovery state machine using existing Kernel primitives | Kernel restart, Identity restart, IPC interruption at every boundary | Repeated recovery converges to the same safe result or fail-closed state |
| C08 | Authorized backup/restore | Identity consistent backup and Kernel restore-authorization primitives | BLOCKED operationally | Cross-service restore protocol binding digest, head, generation and one-time authorization | Populated backup/restore, interrupted restore, expired/revoked/consumed/wrong-operator authorization | Authorized restore reproduces exact state once; every substitution and retry is rejected |
| C09 | Rollback protection | Monotonic Kernel epoch/head and audit anchors pass synthetic tests | BLOCKED operationally | Enforce continuity verification at service startup and restore completion | Replace Identity DB+anchor with older generation; replace Kernel state; mixed-generation rollback | Both single-store and coordinated rollback fail closed without silent reinitialization |
| C10 | Identity/family behavior and evidence | REMEDIATION-02 Owner-accepted; F02/F05/F07 independent PASS | PASS at component level | Route accepted operations through IPC without replacing modules | Normal identity/family create/read/correction, unauthorized lifecycle/fact operation | Existing semantics and immutable lineage remain unchanged across processes/restarts |
| C11 | Audit completeness and custody | HMAC/audit-chain tests; sealed real-token custody evidence | PARTIAL PASS | Cross-service audit correlation with privacy-minimized transaction IDs/outcomes | Success, denial, crash, retry, restore and rollback produce correlated records | Reviewer reconstructs every campaign scenario without secrets/private data or mutable gaps |
| C12 | Compatibility/future freeze | Frozen Persistence Contract and regression suite | BLOCKED final | Versioned public contract, compatibility tests and prohibition on internal storage coupling | Contract-version compatibility and unsupported-version rejection | Exact contract version frozen; later clients use only public interface; OI-0002 need not reopen absent a demonstrated defect |
| C13 | Complete verification and closure | Focused `106`, full `1143 passed/5 skipped`; custody review PASS | BLOCKED | Implement C03–C09/C11/C12, run one real four-principal campaign and independent review | All scenarios above plus focused/security/full regression | Independent reviewer returns PASS on frozen SHA/evidence; canonical state has no remaining OI-0002 blocker |

No new criterion may be added during implementation unless a reproducible security or correctness defect demonstrates that the matrix is insufficient. Such a finding must be recorded separately with its evidence and scope impact.

## Approved bounded architecture direction

The Owner has approved a narrow, authenticated Windows-local IPC boundary. The next package must record one ADR choosing the simplest native mechanism that authenticates the actual Windows peer token, exposes only versioned Identity operations, carries exact Kernel authorization context and transaction identity, and never grants either service direct access to the other's database. The ADR requires independent architecture/security PASS before code implementation. It may not introduce a broker authority, shared DB, cloud service, general queue, scheduler or second Orchestrator.

## Limit Guard admission

Authenticated admission measurement:

- five-hour remaining: 45%; reset `2026-10-12T21:37:10Z`;
- weekly remaining: 67%; reset `2026-10-18T14:48:11Z`;
- mandatory five-hour reserve: 15 percentage points;
- usable five-hour capacity: 30 percentage points.

Conservative whole-mission estimate: 45–55 five-hour percentage points for ADR and independent architecture review, IPC implementation, fault/security tests, four-principal operational campaign, remediation, full regression, independent final acceptance and checkpointing. The available 30 points cannot admit the whole mission while preserving the reserve. Therefore no IPC implementation was started and no reset credit was consumed. Exact resume condition: re-read authenticated capacity after the five-hour reset and proceed only if the deterministic guard admits the entire remaining matrix.

## UI delivery readiness recovery

The approved roadmap remains `ROADMAP.md` Track 3A and `docs/ui25-execution-and-acceptance-plan.md`; no replacement roadmap was created.

| UI area | Verified present state | Dependency disposition |
| --- | --- | --- |
| UI25-00 inventory | Existing synthetic UI, functional-test app and fail-closed product dashboard are distinguished | Completed technical inventory; Owner UI acceptance remains separate |
| UI25-01 dashboard shell | Product-facing dashboard, German LTR/Persian RTL, fail-closed source injection and disabled submission navigation exist | Safe synthetic/navigation work is independently testable now |
| UI25-02 Case/Tax Year | No approved durable live case resolver/create/reopen contract | Depends on accepted persistence foundation; do not create a UI-owned DB |
| UI25-03 Family/Carryover | UI structure can be designed/tested synthetically | Real binding depends on OI-0002 and separately governed OI-0003/annual gates |
| UI25-04 Documents | Synthetic intake and hashing can be tested | Protected live intake/provider use remains separately gated |
| UI25-05 Kernel/Agents | Navigation/status presentation can be tested | Real dispatch requires the existing Kernel and accepted case/run composition |
| UI25-06–09 workflow/result | Layout, localization and synthetic state tests can proceed | Real data propagation depends on accepted identity/evidence/case services |
| UI25-10 Approval/Export | Must remain disabled | Existing Human Gates and two-stage external authorization remain mandatory |
| UI25-11 localization/mobile | German/Persian direction/navigation tests already pass | Owner device acceptance remains outstanding |
| UI25-12 E2E | Not ready | Requires dependency-order completion and Owner hands-on acceptance |

Next executable UI package after OI-0002 closure: **UI25-02 durable Case/Tax-Year resolver integration into the existing fail-closed dashboard**, preceded by a dependency audit confirming the accepted persistence interface. Existing Owner-approved UI25 planning authorizes preparation and safe synthetic UI tests; real product integration/Owner package acceptance must follow the package gates recorded in the UI25 plan. OI-0003, production deployment and external submission remain outside this instruction.

## Exact continuation

After capacity readmission: create the single bounded ADR for the approved Kernel↔Identity Windows-local IPC; obtain independent architecture/security PASS; implement only C03–C09/C11/C12; run the complete four-principal campaign; freeze SHA/evidence; obtain independent final PASS; then and only then record `OI-0002 / ACCEPTED / CLOSED` and resume the approved UI delivery sequence. Do not start OI-0003.
