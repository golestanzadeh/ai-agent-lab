# UI25 — 2025 canonical test-backend integration

Date: 2026-10-16  
Baseline: `bb83ca6f48ca6946bf6461f93425a92e100c6289`  
Status: `TECHNICAL_PASS / SYNTHETIC_ONLY / REAL_CASE_BLOCKED`

## Scope and admission

Authenticated Codex telemetry at admission was 85% five-hour and 95% weekly remaining. The bounded UI/backend package fit while preserving the mandatory 15-point reserve. Work used the clean worktree matching `origin/oi0002-identity-persistence`; unrelated worktrees and local changes were preserved.

This package does not create a registry, database, scheduler or orchestrator. It reuses the pre-existing isolated `FunctionalTestStore`, `CaseRegistry`, `CaseStateStore` and product dashboard. It neither promotes the test store nor activates protected persistence.

## Implemented slice

The existing port-8766 functional UI could persist `TEST-*` rows, but projected status directly from its UI-owned SQLite table. It now reconstructs the existing canonical `CaseRegistry` and `CaseStateStore` from that isolated synthetic snapshot on startup and after case creation. Dashboard cases are projected only from validated canonical `CaseRecord` objects; document mutations require the exact case to resolve in that registry. Unsupported/corrupt lifecycle values fail closed during reopen.

Through the explicit test-only UI, a user can now:

- create a `TEST-*` case for tax year 2025;
- see its canonical `CREATED` lifecycle state in German LTR or Persian RTL;
- close and reopen the existing SQLite test store and recover the same case through `CaseRegistry`/`CaseStateStore`;
- upload a synthetic file for SHA-256 calculation, retain only its label/digest, reject a duplicate and recover that metadata after restart;
- select a case without cross-case document/issue leakage;
- see explicit localized TEST-only warnings; and
- retain disabled ELSTER/submission behavior.

The test store creates deterministic synthetic owner and storage references only for canonical-model validation. These are not real identities, protected roots or evidence authorities.

## Security and negative evidence

- non-`TEST-*` case creation is rejected;
- duplicate and invalid cases are rejected;
- unknown/cross-case document or issue access is rejected;
- a corrupted persisted lifecycle value prevents reopen;
- production dashboard test-mutation routes remain unavailable;
- no private document bytes are persisted—the file is bounded to 2 MB, read only to compute SHA-256 and discarded;
- no Kernel dispatch, protected resolver, PostgreSQL migration, external service or submission path was added.

## Verification

- focused UI/Case Registry/CaseState integration: `45 passed`;
- relevant UI/backend/documentation regression: `133 passed`;
- complete unit regression: `1361 passed, 5 skipped` in `250.99s`;
- German LTR and Persian RTL case display: PASS;
- create/persist/reopen synthetic 2025 case: PASS;
- synthetic document digest persistence/reopen: PASS;
- protected/live case behavior: NOT EXECUTED and not authorized.

## Acceptance boundary and exact blocker

This is not UI25-01 or UI25-02 full acceptance. `CaseRegistry` and `CaseStateStore` remain in-memory production models and have no accepted durable live resolver. OI-0002 operational IPC/protected persistence is not accepted, OI-0003 remains blocked, and no protected 2025 identity/case evidence is authorized. Therefore a real 2025 case cannot be created or reopened through the product UI.

The next dependency in the requested UI → Case → Documents → Kernel sequence is a Kernel-owned synthetic case/run composition contract. It must bind the exact canonical case identity to existing Kernel task/run scope without treating `FunctionalTestStore` as authoritative and without creating a second scheduler or orchestration path. Operational/real-case Kernel integration remains blocked by the accepted persistence and IPC gates.

## Exact continuation

Next independently executable package: design and implement one bounded **synthetic-only UI-to-Kernel case/run projection** using the existing `OrchestratorKernel`, with exact case/year/run scope, no protected mutation, no automatic dispatch and no new database authority. It requires fresh Limit Guard admission and focused independent security review before it may be represented as a verified development slice. If that contract cannot preserve Kernel sole-coordinator authority, stop at the architecture gate rather than connect the test store directly.
