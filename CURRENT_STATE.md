# Current State

## CURRENT_STAGE

**Agent Bridge Production and Durable Approval are human accepted. The Controlled Physical Migration Executor work package is implemented and technically verified; real CASE-001 execution is now at its separate consequential Human Gate.**

D-021 implementation remains complete on branch `d021-agent-case-provisioning`. Standard case-storage provisioning is not physical document migration.

Human authorization issued on 2026-09-08 produced an **APPROVED** state in the historical process-local `ApprovalStore`; it was **not consumed**. Physical migration was **not started** and source documents remain unchanged. That historical approval remains non-durable and is not executable authority after process exit.

## LAST_ACCEPTED_STAGE

**Durable Approval Stage — human accepted 2026-09-10 after architecture acceptance, implementation, and technical verification.**

Agent Bridge Production was separately human accepted on 2026-09-10.

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

Implemented behavior:
- `DRY_RUN` is the default and performs zero storage mutation and zero approval consumption;
- `LIVE` fails before storage inspection unless explicitly enabled and supplied with exact durable approval authority;
- only explicit manifest object IDs and explicit source/target parent IDs are accepted;
- Google Drive mutation port exposes only explicit parent-scoped listing, single-parent inspection, and guarded parent move;
- no taxpayer-name, filename, folder-name, or Drive-wide discovery path exists in the mutation adapter;
- object IDs are preserved by parent moves;
- target must still be empty at execution time;
- every expected source object must still be directly under the explicit source parent;
- partial move failure triggers reverse-order rollback;
- post-migration verification requires exact target contents and absence of expected objects from source;
- approval is consumed only after successful post-migration verification;
- approval-consumption failure triggers storage rollback;
- incomplete rollback produces explicit terminal `PhysicalMigrationRollbackError` and can never be reported as success;
- a consumed approval replay fails closed before storage inspection.

Verification evidence:
- CI run `34509462092`: physical migration executor tests **9 passed**; full suite **272 passed, 1 skipped**; job **success**.
- CI run `34509683965`: executor tests **9 passed**, guarded Drive mutation adapter tests **7 passed**, durable approval tests **11 passed**, Agent Bridge validator **6 passed**, full regression **279 passed, 1 skipped**; job **success**.
- All migration tests use synthetic storage/fake Drive services and temporary test authority only.
- No real Google Drive object was moved, renamed, deleted, overwritten, or otherwise mutated by these tests.

## REAL CASE-001 EXECUTION HUMAN GATE

Technical implementation is complete enough to prepare real execution, but real CASE-001 remains blocked until a separate consequential Human Gate explicitly authorizes it.

Before a real move, the runtime must reconstruct fresh authoritative state and fail closed unless all of these still match:
- `CASE-001`, tax period 2024 and the exact registered source scope;
- live inventory remains exactly the expected 15 PDFs / 0 folders;
- exact current Manifest identity and complete object mapping;
- fresh successful Live Target Preflight and target still empty;
- exact source/target parent IDs;
- a **new durable approval request and explicit human grant** bound to the reconstructed manifest, preflight, run, actor, and `PHYSICAL_MIGRATION` operation;
- explicit live execution enablement.

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

## ACTIVE_CONSTRAINTS

- Source documents are immutable except for an explicitly authorized parent move performed by the controlled migration executor; document content must never be altered.
- No broad/unscoped Drive search for case data.
- Every case-data operation requires validated case scope and fails closed on ambiguity.
- Private Drive IDs, OAuth tokens, credentials, client secrets and private document information must never be committed.
- Human authority remains required wherever D-019 or a consequential-action contract requires it.

## AUTHORITATIVE_REFERENCES

- `AGENTS.md`
- `CONSTITUTION.md`
- `DECISIONS.md`
- `ROADMAP.md`
- `docs/agent-bridge-production.md`
- `docs/durable-approval-lifecycle.md`
- `docs/physical-migration-executor.md`
- `docs/case001-migration-compatibility.md`
- `docs/codex-agent-workflow.md`
- `docs/d-019-controlled-agent-assisted-development-workflow.md`
- `docs/approval-gate.md`
