# OI-0002 REMEDIATION-02 implementation report — 2026-10-11

Status: **REVIEW_READY / NOT ACCEPTED**  
Authority: Project Owner bounded authorization for F02, F05 and F07  
Baseline: `691774e7349ce4322ebe8e181493888758371b37`

## Scope and boundaries

This package corrects only F02, F05 and F07 with synthetic data. It does not bootstrap CASE-001 identities, access taxpayer data, activate production, merge to main, transmit externally, release a Human Gate, or execute OI-0003. The existing Deterministic Orchestrator Kernel and frozen SQLite persistence architecture remain authoritative; no parallel orchestrator, scheduler, database or checkpoint was introduced.

The original checkout contained unrelated uncommitted operational-probe work. It was preserved untouched. Implementation was performed in a clean detached worktree from the synchronized authorized branch head.

## F02 — dedicated identity administration authority

- Added versioned successor contract set `ORCHESTRATOR_CONTRACT_SET_V2_IDENTITY_ADMINISTRATION` under `contracts/orchestrator/v2`.
- Added the dedicated `IDENTITY_ADMINISTRATION_AGENT` and exactly six capabilities: `identity_create`, `identity_read`, `identity_update`, `identity_status_transition`, `case_party_bind`, and `subject_fact_bind`.
- The Kernel validates the exact accepted v1 or v2 contract digest and records the active contract-set identity in checkpoints.
- Identity operations map only to the dedicated capabilities. Generic derived-artifact capabilities no longer authorize identity lifecycle operations.
- Existing Kernel expiry, revocation, Kill Switch, case, year and run enforcement remains the final permission decision point.

## F05 — immutable effective-dated corrections

- Added immutable `case_party_role_history` revisions protected by the existing HMAC integrity key.
- Added evidence-backed closure of an open role interval.
- A correction requires exact case scope, the dedicated party-binding permission, canonical correction evidence, canonical authorization, protected evidence resolution and a non-empty half-open interval.
- Original and corrected revisions are both retained. Tampering with either fails closed on reopen.
- Existing role-specific cross-subject and same-subject cardinality rules remain enforced; adjacent intervals remain valid.

## F07 — atomic schema v1→v2 migration

- Migration now executes under one `BEGIN IMMEDIATE` transaction.
- Legacy tables are renamed inside the transaction, v2 objects are created, verified rows are copied, indexes are recreated, and legacy tables are removed only before the same atomic commit.
- Fault injection covers after begin, after rename, after schema creation, after copy, before commit and after commit.
- Every pre-commit interruption rolls back to intact v1. A post-commit interruption leaves a verifiable complete v2 store and matching audit anchor.
- Populated synthetic identity, role and audit rows survive migration and verify after reopen.
- A v1 store containing lineage that cannot be safely reconstructed remains intact at v1 and is rejected for separately reviewed evidence-backed migration.

## Verification evidence

- Corrected focused F02/F05/F07 suite: `39 passed`, exit 0.
- Corrected relevant Kernel, persistence, evidence and continuity suite: `83 passed`, exit 0.
- Final corrected complete unit regression: `1134 passed, 5 skipped`, exit 0, 243.10 seconds.
- Successor contract JSON parsing: PASS.
- `git diff --check`: PASS.

Tests include generic tax-role denial, dedicated-role expiry and Kill Switch denial, immutable correction history and tamper rejection, role boundary behavior, five pre-commit crash points, post-commit recovery, populated migration readback, and preservation of unsupported legacy lineage.

## Independent-review correction cycle

The first independent review of `89d861ecfb8848edfe8629e7b314cd10b70bf95c` passed F02 but rejected F05 and F07. It reproduced an unauthenticated `correction_evidence_ref` history column and loss of recoverable legacy audit semantics. The corrected candidate binds and compares the correction reference inside each HMAC-protected history payload, requires complete revision sequences, rejects deleted/orphaned/mismatched history, and preserves every legacy audit field and original timestamp in an HMAC-protected v2 lineage table. It also adds a signed in-transaction migration receipt so a crash after database commit but before anchor publication can reconcile deterministically. The corrected exact SHA requires a new independent review; the earlier FAIL is preserved, not overwritten.

The second independent review of `290f96d35f1d78a2d21606136aa7cfa621b4f5c2` passed F02, F05, exact legacy-audit preservation and commit-to-anchor recovery, but found that the signed recovery receipt remained reusable after successful publication. The final candidate gives that HMAC-protected receipt crash-safe one-time `PENDING → CONSUMED` semantics. A pending receipt may reconcile exactly one missing anchor at its bound audit head; successful publication consumes it, and later anchor deletion fails closed. A fresh empty database is distinguished from an existing empty database so the latter cannot silently regenerate a deleted anchor. A third independent review of the final exact SHA is required.

## Files changed

- `contracts/orchestrator/v2/*`
- `src/agent_lab/identity_permission_adapter.py`
- `src/agent_lab/identity_persistence.py`
- `src/agent_lab/orchestrator_kernel.py`
- `tests/unit/test_identity_persistence.py`
- `docs/oi-0002-persistence-operations.md`
- Governed checkpoint/state/index records associated with this report.

## Acceptance handoff

Implementation disposition is `REVIEW_READY`, never `ACCEPTED`. A separate independent reviewer must inspect the exact pushed commit, reproduce F02/F05/F07 adversarial behavior and regression evidence, and return PASS or actionable findings. OI-0002 remains OPEN until independent PASS and the Owner's final acceptance decision. OI-0003 remains blocked.

Operational Windows acceptance remains a separate unresolved boundary: this package does not claim real service-token effective access, deployed restart, populated operational backup/restore or rollback evidence.
