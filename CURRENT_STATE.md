# Current State

## CURRENT_STAGE

**Agent Bridge Production, Durable Approval, and Local Sync Agent implementation are human accepted. Windows Relay architecture is human accepted and its implementation is technically verified, but Windows Relay Stage acceptance is still pending. Controlled Physical Migration is implemented and technically verified but real CASE-001 execution remains at its separate consequential Human Gate.**

D-021 implementation remains complete on branch `d021-agent-case-provisioning`. Standard case-storage provisioning is not physical document migration.

Human authorization issued on 2026-09-08 produced an **APPROVED** state in the historical process-local `ApprovalStore`; it was **not consumed**. Physical migration was **not started** and source documents remain unchanged. That historical approval remains non-durable and is not executable authority after process exit.

## LAST_ACCEPTED_STAGE

**Local Sync Agent Stage — human accepted 2026-09-10 after architecture acceptance, implementation, and technical verification.**

Durable Approval Stage and Agent Bridge Production were separately human accepted on 2026-09-10. Windows Relay architecture was human accepted on 2026-09-10; its implementation stage still requires separate human acceptance before local bootstrap.

Canonical main remains `ee59dadbc2c7f2433e8291f849fef3048b574a9c` until PR #1 is separately merged through the protected-main workflow. These acceptances do not themselves authorize automatic merge, release, runtime approval consumption, or physical migration.

## AGENT BRIDGE PRODUCTION MIGRATION — 2026-09-10

1. Baseline/canonical cleanup — **COMPLETE**.
2. Production architecture/governance — **HUMAN ACCEPTED**.
3. Protocol contract — **DEFINED**.
4. Security model — **DEFINED**.
5. Passive/observe-only Bridge — **PASS**.
6. Controlled Codex connection — **PASS**.
7. GitHub → Work owner-identity response path — **PASS**.
8. Controlled low-risk continuation — **PASS**.
9. Full Human Gate test — **PASS; HUMAN_REQUIRED terminal stop proved**.
10. Final verification/rollback hardening — **TECHNICAL PASS; HUMAN PRODUCTION ACCEPTANCE ISSUED 2026-09-10**.
11. Resume AI-Tax-Agent development at durable/reloadable approval lifecycle — **IMPLEMENTED + VERIFIED + HUMAN ACCEPTED 2026-09-10**.

## DURABLE APPROVAL IMPLEMENTATION

Human-accepted architecture: SQLite-backed durable/reloadable approval authority preserving the existing D-017 domain binding and lifecycle semantics.

Implemented artifacts:
- `docs/durable-approval-lifecycle.md`
- `src/agent_lab/durable_approval.py`
- `tests/unit/test_durable_approval.py`

Verification evidence:
- Run `34508255413`: durable approval tests **11 passed**; full suite **263 passed, 1 skipped**; job **success**.
- Documentation follow-up run `34508370273`: validator, durable approval tests, and full regression all **success**.
- State-recording run `34508467713`: kill-switch check, validator, durable approval tests, and full regression all **success**.
- Human stage acceptance issued 2026-09-10.

## CONTROLLED PHYSICAL MIGRATION EXECUTOR

Implemented artifacts:
- `docs/physical-migration-executor.md`
- `src/agent_lab/case001_physical_migration.py`
- `tests/unit/test_case001_physical_migration.py`
- `src/agent_lab/google_drive_mutation.py`
- `tests/unit/test_google_drive_mutation.py`
- `scripts/case001_controlled_migration.py`
- `tests/unit/test_case001_controlled_migration.py`

Implemented behavior:
- `DRY_RUN` is the default and performs zero storage mutation and zero approval consumption;
- `LIVE` fails before storage inspection unless explicitly enabled and supplied with exact newly created durable approval authority;
- the local harness reconstructs fresh case scope, metadata inventory, Document Identity linkage, deterministic Manifest, and Live Target Preflight before any possible live mutation;
- the harness requires the fresh real inventory to remain exactly **15 PDFs / 0 folders** and requires the target to remain empty;
- only explicit manifest object IDs and explicit source/target parent IDs are accepted;
- Google Drive mutation port exposes only explicit parent-scoped listing, single-parent inspection, and guarded parent move;
- no taxpayer-name, filename, folder-name, or Drive-wide discovery path exists in the mutation adapter;
- object IDs are preserved by parent moves;
- partial move failure triggers reverse-order rollback;
- post-migration verification requires exact target contents and absence of expected objects from source;
- approval is consumed only after successful post-migration verification;
- approval-consumption failure triggers storage rollback;
- incomplete rollback produces explicit terminal `PhysicalMigrationRollbackError` and can never be reported as success;
- a consumed approval replay fails closed before storage inspection;
- LIVE requires the exact explicit authorization sentinel plus human approver and authorization reference;
- the live harness refuses to create a second authority automatically when its durable approval database already exists, forcing human recovery/review instead of silent retry;
- stdout summary deliberately omits provider object IDs, source/target parent IDs, filenames, and complete mappings.

Verification evidence:
- CI run `34509462092`: physical migration executor tests **9 passed**; full suite **272 passed, 1 skipped**; job **success**.
- CI run `34509683965`: executor tests **9 passed**, guarded Drive mutation adapter tests **7 passed**, durable approval tests **11 passed**, Agent Bridge validator **6 passed**, full regression **279 passed, 1 skipped**; job **success**.
- CI run `34509914717`: all migration/durable/Bridge regression checks **success** after Human-Gate state advancement.
- CI run `34510246145`: Bridge validator **6 passed**, Durable Approval **11 passed**, physical executor **9 passed**, guarded Drive adapter **7 passed**, controlled harness safety **6 passed**, full regression **285 passed, 1 skipped**; job **success**.
- Local Windows verification 2026-09-11: controlled migration work package **34 passed**; full regression **310 passed, 1 skipped**. Synthetic end-to-end harness coverage now proves durable approval creation/grant, exact 15-object move, post-verification consumption, durable reload, and terminal `CONSUMED` persistence without live Drive mutation.
- All CI migration tests use synthetic storage/fake Drive services and temporary test authority only.
- No real Google Drive object was moved, renamed, deleted, overwritten, or otherwise mutated by these tests.

## LOCAL SYNC AGENT

Architecture and implementation stage human-accepted 2026-09-10. Implemented artifacts:
- `docs/local-sync-agent.md`
- `src/agent_lab/local_sync.py`
- `scripts/local_sync_agent.py`
- `scripts/install_local_sync_task.ps1`
- `tests/unit/test_local_sync.py`

Implemented behavior:
- one-shot reconciliation intended for Windows Task Scheduler every minute;
- exact repository-root and configured-branch validation;
- dirty tree fails closed before fetch/merge/push;
- strictly-behind local branch updates only through `merge --ff-only`;
- strictly-ahead already committed non-main branch may push normally;
- `main` is never auto-pushed;
- divergence, detached/wrong branch, missing remote, or Git failures stop without reset/rebase/stash/commit/force-push;
- the CLI stores its overlap lock only under `.git` and recovers a stale lock after ten minutes;
- no repository credential, OAuth token, tax data, Drive artifact, or durable approval database is synchronized by this mechanism.

Verification evidence:
- CI run `34512131024`: Local Sync Agent targeted tests **10 passed**; full regression **295 passed, 1 skipped**; job **success**.
- Existing Agent Bridge, Durable Approval and controlled migration suites remained green in the same run.
- Verification used fake Git behavior only and did not access or modify the user's Windows checkout.
- Human stage acceptance issued 2026-09-10.

## WINDOWS RELAY

Architecture human-accepted 2026-09-10. Implemented artifacts:
- `docs/windows-relay.md`
- `src/agent_lab/windows_relay.py`
- `scripts/windows_relay.py`
- `scripts/install_windows_relay_task.ps1`
- `tests/unit/test_windows_relay.py`

Implemented behavior:
- closes the GitHub-to-local-Windows execution gap without installing a GitHub self-hosted Actions runner;
- polls only the exact configured `origin/d021-agent-case-provisioning` relay request file;
- strict protocol v1 rejects unknown fields and arbitrary command/script/path payloads;
- initial allowlist contains only `LOCAL_SYNC_BOOTSTRAP`;
- requires Windows, exact repository root, exact approved branch, and clean worktree;
- uses local `.git/windows-relay-state.json` for replay/interruption fail-closed behavior;
- may publish only the bounded `.github/windows-relay/response.json` result on the approved non-main branch;
- response publication stages exactly that one path and uses normal non-force push;
- cannot modify `main`, merge/release, access Drive/tax data, grant/consume approval, or perform CASE-001 migration;
- local relay installation itself remains a one-time trusted host bootstrap.

Verification evidence:
- CI run `34515017873`: Windows Relay targeted tests **14 passed**; Local Sync targeted tests **10 passed**; full regression **309 passed, 1 skipped**; job **success**.
- Passive CI remained read-only and ran on GitHub-hosted Ubuntu only; it did not install or execute anything on the user's Windows host.

Pending Human Gate:
- Windows Relay implementation requires explicit **Windows Relay Stage** acceptance before the one-time local relay bootstrap is performed.

## REAL CASE-001 EXECUTION HUMAN GATE

All implementation and non-production verification needed before the consequential gate are complete, including the 2026-09-11 synthetic end-to-end controlled harness test. Real CASE-001 remains blocked until the human explicitly authorizes the live attempt and the creation/grant of its new durable executable approval.

At the real attempt, the local harness will reconstruct fresh authoritative state and fail closed unless all of these still match:
- `CASE-001`, tax period 2024 and the exact registered source scope;
- live inventory remains exactly the expected 15 PDFs / 0 folders;
- exact current Manifest identity and complete object mapping;
- fresh successful Live Target Preflight and target still empty;
- exact source/target parent IDs;
- a **new durable approval request and explicit human grant** bound to the reconstructed manifest, preflight, run, actor, and `PHYSICAL_MIGRATION` operation;
- exact explicit live authorization sentinel.

The historical process-local `APP-00000001` is **not** valid for this purpose and must not be imported or upgraded.

Because Google Drive and SQLite are not one distributed transaction, any crash that leaves external placement uncertain must fail closed on restart and require human recovery rather than automatic replay.

## PRODUCTION SAFETY BOUNDARY

Agent Bridge remains a **development control plane only**. It is not runtime tax authority.

It does not itself authorize physical Google Drive migration, D-017 approval consumption, source-document mutation, destructive operations, autonomous merge/release/stage acceptance, or direct autonomous write to `main`.

`HUMAN_REQUIRED` remains terminal until explicit human authorization permits a new action.

## VERIFIED_RUNTIME_STATE

- GitHub is the durable source of truth; local Python/Docker is the execution environment; Google Drive holds private case data.
- Multi-case architecture requires mandatory `case_id`, persistent `person_id`/`entity_id`, and explicit `tax_period`.
- Last recorded real CASE-001 source inventory: **15 PDFs, 0 folders**.
- Last recorded real CASE-001 / 2024 target Documents scope was empty at the D-021 checkpoint; it must be freshly revalidated before execution.
- Historical run: `RUN-00000001`; historical process-local approval identifier: `APP-00000001`.
- Historical approval: **APPROVED / NOT CONSUMED / NON-DURABLE / NOT AUTO-IMPORTED / NOT EXECUTABLE**.
- Physical Google Drive migration: **NOT STARTED**.
- Local Sync Agent: **IMPLEMENTED + TECHNICALLY VERIFIED + HUMAN STAGE ACCEPTED / LOCAL INSTALLATION AND LIVE SMOKE TEST AUTHORIZED BUT NOT YET VERIFIED**.
- Windows Relay: **ARCHITECTURE HUMAN ACCEPTED + IMPLEMENTED + TECHNICALLY VERIFIED / STAGE ACCEPTANCE AND LOCAL BOOTSTRAP PENDING**.

## ACTIVE_CONSTRAINTS

- Source documents are immutable except for an explicitly authorized parent move performed by the controlled migration executor; document content must never be altered.
- No broad/unscoped Drive search for case data.
- Every case-data operation requires validated case scope and fails closed on ambiguity.
- Private Drive IDs, OAuth tokens, credentials, client secrets and private document information must never be committed.
- Human authority remains required wherever D-019 or a consequential-action contract requires it.
- Local Sync may never auto-commit, force-push, repair divergence, or auto-push `main`.
- Windows Relay may execute only versioned allowlisted local task types and may never accept arbitrary shell commands from GitHub state.

## AUTHORITATIVE_REFERENCES

- `AGENTS.md`
- `CONSTITUTION.md`
- `DECISIONS.md`
- `ROADMAP.md`
- `docs/agent-bridge-production.md`
- `docs/durable-approval-lifecycle.md`
- `docs/physical-migration-executor.md`
- `docs/local-sync-agent.md`
- `docs/windows-relay.md`
- `docs/case001-migration-compatibility.md`
- `docs/codex-agent-workflow.md`
- `docs/d-019-controlled-agent-assisted-development-workflow.md`
- `docs/approval-gate.md`
- Fresh local metadata-only CASE-001 dry-run 2026-09-12: **15 documents / 0 folders**, manifest `sha256:94b563afc299a1c3da3b5e57ab6deb023952e15ae8e6abb274223f5d72b85587`, preflight `sha256:16d9b1bd5ed8fb08d5cac0aa22a00333fa2d2c783da7fa38899efad747379853`; approval status remained null, approval consumption false, Drive mutation false. This reconfirms readiness at the Human Gate without authorizing live execution.

- 2026-09-12 Live Execution Readiness Gate: targeted migration/approval suite **34 passed**; fresh provider-backed metadata-only dry-run reconfirmed **15 documents / 0 folders**, unchanged manifest/preflight identities, null approval status, no approval consumption, and zero Drive mutation. Status: **CASE001_LIVE_READY -> HUMAN_REQUIRED**. Real execution remains unauthorized.

- 2026-09-12 CASE-001 live physical migration: human-authorized OAuth scope expansion completed; existing durable approval APP-00000001 was recovered and exact-context validated; 15/15 manifest documents moved from the legacy source to the accepted target; post-verification found source 0 and target 15 with exact target parents; approval reached CONSUMED. D-021 physical migration is complete.

- 2026-09-12 D-022 started under human phase authorization. Step 1 intake completed against live CASE-001 target: 15 PDFs confirmed. Step 2 initial identification completed where evidence supports it. Native PDF text extraction succeeded for 5/15; 10/15 are image-only and require OCR before evidence-grounded extraction/classification can continue. No tax values were guessed. Status: D022_OCR_REQUIRED.

- 2026-09-12 D-022 extraction and validation completed. All 15 CASE-001 PDFs are readable through native-text or rendered-page vision fallback. Address/route endpoints and cross-year payment/service-year semantics are explicit dataset rules. Full regression: 317 passed, 1 skipped. Status: D022_DATASET_VALIDATED_HUMAN_REQUIRED.
