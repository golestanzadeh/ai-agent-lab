# Current State

## CURRENT_STAGE

**Agent Bridge production and Step 11 durable/reloadable approval lifecycle are human accepted. The next work package is controlled physical migration executor design and verification.**

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

## STEP-11 DURABLE APPROVAL IMPLEMENTATION

Human-accepted architecture: SQLite-backed durable/reloadable approval authority preserving the existing D-017 domain binding and lifecycle semantics.

Implemented artifacts:
- `docs/durable-approval-lifecycle.md`
- `src/agent_lab/durable_approval.py`
- `tests/unit/test_durable_approval.py`
- bounded updates to `docs/approval-gate.md`, `ROADMAP.md`, and CI verification.

Core behavior implemented:
- SQLite schema version `1`;
- durable approval and audit ID counters;
- immutable `MigrationApproval` reconstruction from persistent rows;
- SHA-256 integrity verification for approval and durable approval-audit records;
- exact D-017 `ApprovalGate` binding validation after reload;
- `BEGIN IMMEDIATE` write serialization;
- approval state change and matching approval-lifecycle audit event in the same SQLite transaction;
- restart-safe `PENDING`, `APPROVED`, terminal `CONSUMED`, `REJECTED`, `REVOKED`, and `EXPIRED` semantics;
- exactly-once consumption across independent store instances;
- rollback of state, audit event, and counters when durable audit insertion fails;
- fail-closed behavior for corrupt records and unsupported schema versions;
- no import path from legacy review/export data into executable authority.

Verification evidence:
- Run `34508255413`: durable approval tests **11 passed**; full suite **263 passed, 1 skipped**; job **success**.
- Documentation follow-up run `34508370273`: validator, durable approval tests, and full regression all **success**.
- State-recording run `34508467713`: kill-switch check, validator, durable approval tests, and full regression all **success** at commit `771d4b265cf955c35a6edc2a1747a44f90925a4d`.
- Human stage acceptance issued 2026-09-10.

## DURABLE APPROVAL SAFETY BOUNDARY

The historical CASE-001 process-local approval is **not migrated or upgraded** into durable executable authority. A review export, chat message, GitHub comment, remembered ID, or historical process-local state cannot be treated as executable approval.

Future executable durable authority requires a newly created durable approval request and a new explicit human grant against the exact authoritative case/run/manifest/preflight/execution binding.

No real approval was consumed during implementation or testing. Tests use synthetic cases and temporary SQLite databases only.

## NEXT WORK PACKAGE

**Controlled Physical Migration Executor: design → bounded implementation → synthetic/dry-run verification → rollback/post-migration verification proof → consequential Human Gate.**

Until that package reaches its final Human Gate, work is limited to design, implementation and non-production verification. It must not:
- create or grant a real CASE-001 durable approval;
- consume any real approval;
- move, rename, delete or mutate the 15 real source PDFs;
- execute physical migration against real Google Drive case data.

The executor design must preserve exact case/run/manifest/preflight/execution binding, immutable sources, deterministic destination mapping, idempotency/replay protection, partial-failure recovery, audit linkage, and post-migration verification. Real execution remains separately human authorized.

## PRODUCTION SAFETY BOUNDARY

Agent Bridge remains a **development control plane only**. It is not runtime tax authority.

It does not authorize or perform physical Google Drive migration, D-017 approval consumption, source-document mutation, destructive operations, autonomous merge/release/stage acceptance, or direct autonomous write to `main`.

`HUMAN_REQUIRED` remains terminal until explicit human authorization permits a new action.

## VERIFIED_RUNTIME_STATE

- GitHub is the durable source of truth; local Python/Docker is the execution environment; Google Drive holds private case data.
- Multi-case architecture requires mandatory `case_id`, persistent `person_id`/`entity_id`, and explicit `tax_period`.
- Real CASE-001 source inventory: **15 PDFs, 0 folders**.
- Real CASE-001 / 2024 target tree: six standard subfolders provisioned; target Documents verified empty at the recorded D-021 checkpoint.
- Real run: `RUN-00000001`; historical process-local approval identifier: `APP-00000001`.
- Historical approval: **APPROVED / NOT CONSUMED / NON-DURABLE / NOT AUTO-IMPORTED**.
- Physical Google Drive migration: **NOT STARTED**.

## ACTIVE_CONSTRAINTS

- Source documents are immutable.
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
- `docs/codex-agent-workflow.md`
- `docs/d-019-controlled-agent-assisted-development-workflow.md`
- `docs/approval-gate.md`
