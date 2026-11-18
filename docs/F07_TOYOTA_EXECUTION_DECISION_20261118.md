# F07 Toyota-style execution decision — 2026-11-18

Status: OWNER_APPROVED / EXECUTION_STRATEGY_ONLY
Scope: AI-Tax-Agent Family & Persons -> governed Identity Persistence
Authority: Owner approval in conversation, 2026-11-18.
This is an execution-priority decision, NOT a replacement of frozen security contracts, a live deployment authorization, or an independent implementation acceptance.

## Goal and measurable success
Deliver the shortest contract-compliant path from the existing Family & Persons dashboard to durable, authorized person creation, correction, case association and readback after page refresh and server restart. Demonstrate a real end-to-end result, not just passing unit tests. No real taxpayer enrollment until its separate Owner Human Gate.

## Verified starting point
- Repo HEAD at decision: 737bd76e125f74e1ebc75af1d5b6a9e6f76752ad.
- COMMIT/Witness versioned contract independently accepted: 8d0ebd3143fba7a7b28f2e25253f4bd90ebbdfdf (168 worker tests, 287 independent).
- Typed protected evidence revision/scope/expiry/revocation/content verifier independently accepted: eacbd5ed43a081c4e79e4784b963248f6b603dcc (24 focused tests in each reported run).
- Integrated F07 atomic mutation and recovery is NOT independently accepted or operational.
- Existing Family UI is a browser-memory preview; no durable Family write path has been proven.
- Local dashboard/UI and Google Drive auth contain unrelated uncommitted changes; preserve them.
- Last recorded Limit Guard observation (2026-11-18T10:01:32Z): 50% five-hour, 92% weekly; integrated EXPENSIVE estimate 35/15 deferred against 15% reserve. Recheck authenticated capacity before resuming; do not treat old telemetry as current.
- Live protected resolver/custody binding, Owner enrollment, Windows service deployment and operational C01-C13 remain separately gated.

## Owner decision: three bounded packages, in order
1. **Finish the existing Identity write path** from the accepted checkpoint, not a redesign. Implement durable Kernel Witness slot reservation/CAS shared with read/restore; existing Identity SQLite single-transaction evidence reservation/one-use consumption/domain mutation/logical head/audit/receipt; Custodian receipt binding; PREPARE/COMMIT/FINALIZE/GET_TRANSACTION/ABORT deterministic recovery. Use accepted IPC 1.1 and mapping 7859d1b. Run targeted failure, concurrency, replay, crash/restart, and compatibility tests; independent exact-SHA read-only review. Exit criterion: accepted inactive end-to-end mutation and recovery implementation with no fabricated operational authority.
2. **Controlled operational activation.** Inventory role-private source adapter/trust-root/key custody and Windows service prerequisites; produce exact actions, security impact, rollback/recovery and separately request the necessary Owner Human Gates. No installation, secret provisioning, live enrollment, real data mutation or external submission is implied by this document. Exit criterion: authenticated operational path demonstrated under explicitly authorized scope with independently reviewed evidence.
3. **Connect Family & Persons UI.** Replace temporary JS-only state with the approved authorized host/Kernel/Identity path. Keep one canonical Identity store, persistent person identity distinct from case/year role/facts, bilingual Persian/German RTL/LTR, owner-confirmed facts with evidence provenance and conflict flagging. Focused tests: create, read, correction, duplicate/authorization denial, audit, case isolation, refresh and restart. Exit criterion: demonstrable durable Family workflow in dashboard, not a mock.

## Toyota operating rules
- Minimize total complexity, maintenance, duplicated state, cost and unnecessary tests. Do not trade away verified security or reliability.
- No parallel SQLite/JSON/CSV person store, fake resolver, synthetic operational authority, bypass endpoint, new orchestrator or redundant checkpoint.
- Before each package: inspect all known dependencies and existing accepted contracts together; identify remaining true Owner decisions up front. No speculative contract expansion.
- Prefer the smallest implementation using accepted APIs and existing DBs; one accountable outcome per package. Keep independently reviewed exact SHA evidence and only necessary regression tests.
- Do not mark a package complete on test count alone; require its defined observable acceptance behavior.
- Stop for actual Owner-controlled trust, enrollment, deployment, external transmission or frozen-contract ambiguity only. State exact missing decision and smallest remedy; no repeated approval of already confirmed personal facts.
- Respect authenticated Limit Guard and reserve. On deferral, preserve exact resume point, avoid restarting discovery, and never fabricate a reset.
- Preserve unrelated uncommitted work; do not auto-commit or delete it. Update existing PROJECT_CHECKPOINT.md and OPEN_ITEMS.md rather than creating a parallel checkpoint.

## Immediate next action
Resume **Package 1** only after fresh capacity admission. Starting commit 737bd76e; inspect accepted 8d0ebd3/eacbd5e and existing architecture 7859d1b. Implement integrated atomic write/recovery, then obtain independent exact-SHA acceptance. Do NOT begin Package 2 or 3 merely because Package 1 tests pass.

## Reporting and recovery
At each package boundary report: exact commit SHA, changed files, targeted/independent tests, observable behavior verified, unaccepted assumptions, remaining Human Gates, next command/action and fresh capacity admission result. This decision is a priority/sequence freeze, not proof of successful runtime activation.
