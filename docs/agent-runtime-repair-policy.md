# Local Agent Runtime repair/replay policy

Status: **BOUNDED EXECUTOR IMPLEMENTED / LOCAL SYNTHETIC NON-PRODUCTION ONLY**

## Purpose and authority

This policy defines when the existing four-role local Agent Runtime may continue after an interrupted `resume` operation. It uses the read-only recovery inspector as its evidence source and does not authorize provider workers, arbitrary tasks, real data, credentials, networking, subprocesses, production, protected-main action, external transfer, or changes to the accepted organization and Kernel contracts.

The safe operation is continuation from the first demonstrably unstarted stage. A completed stage is never replayed. The word *repair* means recording one bounded continuation decision against verified durable evidence; it never means rewriting history, deleting artifacts, weakening acceptance, or guessing what an interrupted stage did.

## Required evidence

A repair decision is eligible only when all of the following are true:

1. The package still validates against the exact authorized local synthetic work contract.
2. The immutable plan and runtime-state files match the package digest and plan evidence.
3. The Kernel audit chain and latest `PACKAGE-PLANNED` checkpoint verify exactly.
4. The kill switch is `RUNNING`, identifying an interrupted resume rather than a normal planned or completed boundary.
5. Durable task, manifest, response, acceptance, and artifact evidence forms one exact ordered prefix of the authorized stages.
6. Every completed stage has its expected immutable artifact, response digest, dependencies, budget record, and required independent acceptance.
7. The first remaining stage has no task, manifest, response, acceptance, artifact, or other side-effect evidence.
8. No later stage has any durable trace.
9. No earlier repair decision or repair attempt exists for the same package and planned-checkpoint identity.

Missing, contradictory, malformed, reordered, partially written, or extra evidence makes the state ineligible and requires Human review.

## Ordered stage model

The authorized order remains:

`PLAN -> PLAN_ACCEPTANCE -> IMPLEMENT -> QA -> QA_ACCEPTANCE -> IMPLEMENT_ACCEPTANCE -> COMPLETE_CHECKPOINT`

`PLAN` and `PLAN_ACCEPTANCE` must already be complete at the verified planned checkpoint. A repair may continue only at one of these exact boundaries:

| Durable prefix | First permitted continuation | Result |
| --- | --- | --- |
| Plan only | `IMPLEMENT` | Eligible only when implementation has no trace |
| Plan + implementation | `QA` | Never replay implementation |
| Through QA | `QA_ACCEPTANCE` | Never rewrite QA evidence |
| Through QA acceptance | `IMPLEMENT_ACCEPTANCE` | Requires the exact accepted QA lineage |
| Through both acceptances | `COMPLETE_CHECKPOINT` | Halt, checkpoint, and verify only |
| Completed checkpoint | none | Idempotent no-op; already complete |

Any partial evidence inside a stage is ambiguous. The policy does not clean it up or replay it.

## Idempotency and duplicate prevention

- The repair key is the digest of package identity, package digest, planned checkpoint ID/hash, exact completed-stage prefix, and policy version.
- A repair authorization and attempt are write-once records bound to that key.
- At most **one** repair attempt is permitted for one planned-checkpoint identity.
- Re-evaluating an already completed package returns `ALREADY_COMPLETED` without mutation.
- Re-evaluating a consumed repair key returns `REPAIR_ALREADY_ATTEMPTED` and performs no work.
- Existing task IDs, manifest IDs, response IDs, acceptance records, or artifact paths are never reused for a stage whose completion is uncertain.
- The continuation executor must check the audit chain, checkpoint, kill switch, and absence of first-remaining-stage evidence again immediately before mutation.

## Fail-closed outcomes

The policy has only these outcomes:

- `ELIGIBLE_CONTINUE_FROM_NEXT_STAGE` — all required evidence is exact and one repair attempt remains;
- `ALREADY_COMPLETED` — the complete checkpoint is verified; no mutation is permitted;
- `REPAIR_ALREADY_ATTEMPTED` — the bounded attempt was consumed; Human review is required;
- `AMBIGUOUS_OR_UNSAFE` — any invariant is missing or contradictory; Human review is required;
- `EXTERNAL_OR_PRODUCTION_BOUNDARY` — requested capability exceeds this policy; Human approval is required.

There is no automatic deletion, rollback, overwrite, retry loop, best-effort inference, or attempt to repair a corrupted audit chain.

## Bounded execution

An eligible continuation:

1. records its write-once repair decision before executing a remaining stage;
2. consumes the sole repair attempt;
3. executes only the remaining suffix through the existing fixed in-process workers;
4. preserves the existing budgets, timeouts, dependency checks, independent acceptance, and kill switch;
5. halts and records failure evidence on any error without a second automatic attempt;
6. creates the existing complete checkpoint only after all exact evidence and acceptances pass;
7. verifies the audit chain and returns a read-only recovery assessment.

## Implementation acceptance criteria

- Eligibility is derived entirely from verified durable state, never caller assertions.
- Every valid completed-prefix boundary has a deterministic test.
- Partial-stage, extra-stage, artifact-only, response-only, wrong-dependency, missing-acceptance, changed-package, changed-checkpoint, consumed-attempt, and tampered-audit cases fail closed.
- A completed package is an idempotent no-op.
- A completed stage is never invoked twice.
- The repair-attempt ceiling is exactly one per planned-checkpoint identity.
- No test or implementation path enables an external or production capability.

## Next implementation boundary

The versioned deterministic policy evaluator and bounded continuation executor are implemented. The evaluator classifies durable evidence and produces a hash-bound decision. The executor writes that exact decision once before mutation, consumes the sole attempt, rechecks checkpoint and kill-switch state, executes only the unstarted suffix, preserves independent acceptance, and verifies the completed checkpoint and audit chain. Completed state is an idempotent no-op.

Verification: the targeted runtime repair/recovery/runtime suite passes with `34 passed`, including every permitted continuation boundary, planned-boundary completion, completed-state no-op, completed-stage non-replay, partial/extra-stage ambiguity, and consumed-attempt rejection.

The complete local unit regression passes with `712 passed, 1 warning` after integration of the repair evaluator, executor, and boundary matrix.
