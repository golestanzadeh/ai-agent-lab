# C09 nonblocking local development decision

Date: 2026-10-14
Authority: Owner direction in ChatGPT conversation; implementation disposition pending canonical checkpoint integration.

## Scope

AI-Tax-Agent initially runs on the owner's Windows laptop, optionally under Docker, and must remain portable to a replacement laptop or VPS. No new orchestrator, database, scheduler, or service is authorized by this decision.

## Decision

- C09 rollback protection remains OPEN / NOT ACCEPTED and must not be represented as passed.
- C09 alone is NOT a global blocker for independently safe development, synthetic tests, localization, UI/navigation, and other work that does not depend on rollback guarantees.
- Do not relax unrelated IPC, identity isolation, persistence, authorization, approval, submission, deployment, or independent-acceptance gates. Operations requiring an accepted anti-rollback guarantee remain restricted.
- Maintain the Deterministic Orchestrator Kernel as sole execution coordinator.
- For initial local deployment, keep freshness state outside rollback-prone Docker volumes and Kernel/Identity snapshots; require startup/restore checks and fail-closed behavior for detected stale state. A local-only anchor does not protect against full-host Administrator rollback.
- Migration to a new laptop or VPS requires explicit owner-approved restore/migration, with verification of generation and heads. Do not silently reinitialize state.
- GitHub can store code and evidence but must not be treated as the sole monotonic witness. In the private PoC, the scoped contents:write App token successfully forced a test branch from G3 to G1, then restored G3. This disproves branch-head immutability for that configuration; it is not an operational Kernel/Identity C09 test.

## Execution policy

C09_NOT_ACCEPTED != PROJECT_EXECUTION_BLOCKED.

Independent work may proceed through existing authorization and quality gates. Do not mark OI-0002 fully ACCEPTED/CLOSED until its frozen acceptance criteria are met or a separately approved and reviewed revision to that acceptance contract explicitly defines a bounded partial release. Preserve C09 as a tracked security debt, and preserve full operational closure requirements.

## Next bounded steps

1. Reconcile this decision into the canonical checkpoint and active work instructions, with no rewrite of historical evidence.
2. Inventory independent UI25 and IPC packages, their actual prerequisites, and limit guard.
3. Select a package that does not rely on C09 operational acceptance and run its existing tests before broader implementation.
4. Keep C09 startup/restore and authorized migration tests as an independent track.
