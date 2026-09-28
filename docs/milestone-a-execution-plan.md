# Milestone A Execution Plan

Status: **OWNER-AUTHORIZED / EXECUTION ACTIVE**
Plan identifier: `MILESTONE-A-PLAN-20260927-001`  
Recovered baseline: `62747b16a11dbd997f0c023c6c40c0f2f408cc5f` on `d021-agent-case-provisioning`

## Purpose and authority boundary

This document reconciles the Owner-directed Milestone A workstreams A-01 through A-09 with the implemented repository. It is an execution plan, not executable authority. It neither registers packages in a live Kernel task registry nor permits implementation.

The existing durable authorities are narrower:

- D-051 was limited to the remaining local synthetic Phase P1 packages and is fully exercised.
- The UI authority completed UI-1 through UI-19 and did not authorize operational product composition or a new durable workflow architecture.
- `ORCH-CONT-20260927-001` authorized milestone-control infrastructure and its bounded synthetic continuity proof, now complete under D-140. It expressly did not amplify product authority.
- The recovered `PRD-RECOVERY-PLAN-001` was planning-only and stated that its proposed queue did not authorize execution.

Owner directive `MILESTONE-A-20260927-001` approved this exact package envelope on 2026-09-27. The hash-bound authority and five tasks are now registered in the existing local Kernel; registration does not itself complete or dispatch a package.

## Golden journey and coverage manifest (A-01)

Required local synthetic journey:

`Create Case -> Intake -> Process -> Specialist Review -> Chief Review -> Calculation -> Form Preview -> Human approval stage 1 -> Human approval stage 2 -> Synthetic Submission -> Receipt -> Recovery`

| Step | Reusable verified implementation | Remaining Milestone A gap |
|---|---|---|
| Create Case | case registry, identity association, case creation workflow, case state | compose into one product service and persistent journey |
| Intake | document inventory, identity, processing contracts; UI synthetic intake display | authorized action boundary and durable product transition |
| Process | document extraction and six-role tax runtime | orchestration adapter and persistent status/error result |
| Specialist/Chief review | tax runtime review stages and bounded recovery policy | product actions, role transition, correction loop |
| Calculation | tax calculation contracts and synthetic dataset | composition into case-bound journey |
| Form Preview | immutable synthetic preview and E10 profile v14 readiness | product action and exact lineage persistence |
| Human approvals | durable two-stage approval lifecycle | journey binding, expiry/revocation recovery, UI action boundary |
| Synthetic submission | deterministic submission lifecycle/idempotency and audit | journey composition only; external execution remains denied |
| Receipt/recovery | placeholder receipt/recovery contracts and runtime recovery inspection | durable product-visible receipt/retry/crash matrix |
| UI | Persian local display-only prototype through UI-19 | governed mutation routes and action authorization |
| CI/setup | unit suite and passive Agent Bridge workflow | reproducible Milestone A integration job and setup proof |

## Bounded package queue

Every package uses local synthetic data only. Budgets are ceilings, not entitlements: `token_budget=30000`, `tool_call_budget=60`, `wall_clock_seconds=3600`, `retries=1`; package count ceiling is five and queue-exhaustion replan ceiling is two. All packages require independent acceptance, exact changed-path evidence, targeted tests, relevant regression, and a durable checkpoint before successors become ready.

### `MA-01-GOLDEN-JOURNEY-CONTRACT`

- Covers A-01.
- Deliverable: versioned journey contract and machine-checkable coverage manifest mapped only to existing exact component APIs.
- Acceptance: all stages, identities, dependencies, blockers, and exclusions are closed enums; unsupported capabilities fail closed; no duplicate subsystem is introduced.
- Recovery: documentation/contract-only rollback; no runtime state.
- Execution result: implemented and independently accepted. Authority hash `sha256:2a6d89b6c350b5a1b653bfb7b8b1ddf472188785104389967786e23d97249d09`; journey hash `sha256:62fea6ef5936cb6897b7ff54a37a43ba98bc90e6adbae20b1c5e9bb64565d6ad`; focused suite `44 passed`; documentation suite `9 passed`; full unit regression `876 passed, 1 warning`; O2 validator `PASS`; Kernel checkpoint `sha256:9c7f5a28521d82ac70ffd2dd8c9d5de74b8c9e6512ac977380508ac50656625b`. Next ready package: `PKG-MA-02-COMPOSITION-AND-STORE`.

### `MA-02-COMPOSITION-AND-STORE`

- Covers A-02 and A-03; depends on `MA-01-GOLDEN-JOURNEY-CONTRACT`.
- Deliverable: one composition service over existing components plus a case-scoped durable synthetic workflow store with atomic transitions and restart recovery.
- Acceptance: mandatory `case_id`, cross-case rejection, schema/version rejection, idempotent transition identity, transactional audit, crash/reopen tests, and no second case/approval/orchestrator store.
- Recovery: fail closed on corrupt/partial state; resume only from verified durable transition.
- Execution result: implemented and independently accepted. The Case Registry remains authoritative; the store persists only scoped workflow metadata. Focused verification `39 passed`; full unit regression `883 passed, 1 warning`; Kernel checkpoint `sha256:7434e9ef9fc227ddb6a808629c647644d637d225ecf5524b49f0d5ebb8071663`.

### `MA-03-INTAKE-REVIEW-DECLARATION`

- Covers A-04 and A-05; depends on `MA-02-COMPOSITION-AND-STORE`.
- Deliverable: narrowly allowlisted local actions for synthetic intake, processing, specialist/chief review, corrections, calculation, and declaration preparation using existing services.
- Acceptance: closed action catalog, role/sequence enforcement, deterministic lineage, correction invalidation, no arbitrary command execution, and complete negative isolation tests.
- Recovery: one write-once attempt per transition with exact prior-state verification.
- Execution result: implemented and independently accepted. Six closed role-bound actions, exact prior-state checks, durable pre-validation attempt reservation, deterministic auditable lineage, exact-active correction invalidation, and negative isolation are verified. Focused verification `16 passed`; full unit regression `892 passed, 1 warning`; Kernel checkpoint `sha256:c90bbe7a41bf1ade4e491c4abdec8ac11473da2f782ef7e9b7f759a5434dd2d3`.

### `MA-04-APPROVAL-SUBMISSION-RECEIPT`

- Covers A-06 and A-07; depends on `MA-03-INTAKE-REVIEW-DECLARATION`.
- Deliverable: bind the existing durable two-stage approval lifecycle to the synthetic journey and existing inert submission/receipt/recovery contracts.
- Acceptance: two distinct approvals, exact payload/recipient/channel/expiry binding, revocation and expiry rejection, idempotent synthetic submission, duplicate prevention, receipt persistence, restart/retry proof, and zero external connectivity.
- Recovery: no approval import from text/export; durable reload and one-time consumption only.
- Execution result: Owner-approved option B is implemented and independently accepted. Coordinator contract version 1 resides in the existing `DurableApprovalStore`; the separate workflow database is coordinated by deterministic transition identities and durable ordered markers, without any atomicity claim across databases. Intent, exact case/year/run/operation, approval consumption, result, and receipt are integrity-bound. Crash/restart/replay is verified after the intent commit, approval-consumption commit, every workflow commit, and every coordinator-marker commit. Revocation, expiry, second-operation reuse, registered and unregistered cross-case scope, corruption, duplicate result/receipt prevention, and zero external activity fail closed. Focused verification `32 passed`; full unit regression `913 passed, 1 warning`; independent acceptance `PASS`.

### `MA-05-E2E-FAILURE-CI`

- Covers A-08 and A-09; depends on `MA-04-APPROVAL-SUBMISSION-RECEIPT`.
- Deliverable: full synthetic golden-journey integration proof, failure matrix, reproducible local setup, and a narrowly scoped CI workflow.
- Acceptance: success path plus cross-case, crash, retry, duplicate, stale approval, revocation, expiry, corruption, and recovery cases; clean fresh setup; CI performs no secret-bearing or external tax action.
- Recovery: test artifacts are non-authoritative; failure persists an actionable STOP diagnostic.
- Execution result: implemented and independently accepted. The complete twelve-stage synthetic journey reopens at `RECOVERY` with exactly one durable coordinator operation, result, and placeholder receipt. Existing focused suites plus the new stale-preview proof cover cross-case, every commit crash boundary, replay/retry, duplicate prevention, revocation, expiry, corruption, and recovery. A fresh temporary virtual environment with only pytest installed passes the focused surface. The read-only hash-pinned CI workflow has no secrets or external tax action; on failure it records an actionable diagnostic and checkpoint through the existing Kernel and uploads only non-authoritative recovery evidence. Focused verification `62 passed`; full unit regression `915 passed, 1 warning`; independent acceptance `PASS`.

## Intended artifact boundary

If the consolidated authority is granted, the implementation may add narrowly scoped files for the journey contract/manifest, composition service, synthetic workflow store, and Milestone A integration tests, and may update existing UI, approval, submission, documentation, state, and test files. Any new file must be separately registered in `ROADMAP.md` before creation. Creating or changing a CI workflow is included only if explicitly approved.

## Explicit exclusions

Real taxpayer data, provider credentials, Manufacturer-ID, certificates, protected-document copying, official ERiC engine execution, signing, networking, ELSTER/Finanzamt contact, external transmission, production deployment, protected-main action, release, destructive action, Constitution changes, a second Orchestrator/Bridge/scheduler, and a general-purpose shell remain prohibited.

## Consolidated authority required

Owner authority `MILESTONE-A-20260927-001` now covers the five packages above. Anything outside this boundary, especially real-data/provider transfer, requires its separate recorded authority. The synthetic queue can continue package-by-package after each independent acceptance and durable checkpoint.
