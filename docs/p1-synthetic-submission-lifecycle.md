# Phase P1 continuous package — Synthetic Submission Lifecycle and Idempotency

Status: **COMPLETE / VERIFIED UNDER CONTINUOUS NON-PRODUCTION AUTHORITY**

## Boundary

This package models only local synthetic state. It contains no transmitter, ERiC
FFI, official XML, credential access, signing, endpoint, network call, real receipt,
or real taxpayer data. A planned attempt is an inert audit artifact and is never
authority or capability to transmit.

## Design

`src/agent_lab/elster_submission_lifecycle.py` binds each lifecycle to the exact
synthetic preview, envelope, case/run, destination approval, and a stable SHA-256
idempotency key.

- The first evaluation produces exactly one inert attempt plan.
- Re-evaluation with an unresolved plan produces no duplicate plan.
- A synthetic success terminates the lifecycle and requires an explicitly labelled
  placeholder that cannot claim an external receipt.
- An uncertain outcome blocks automatically and can never be retried.
- A definite synthetic failure permits at most one retry, and only when the exact
  destination approval explicitly allows that retry.
- Both attempts retain the same idempotency key. A second failure exhausts the
  lifecycle and no third attempt can be represented.
- Mutated, reordered, duplicated, cross-bound, expired, or incomplete history fails
  closed.

## Acceptance criteria

- Attempt and result identities are deterministic and mutation-sensitive.
- Case, run, preview, envelope, approval, attempt number, time, and idempotency
  bindings are enforced.
- Duplicate planning and automatic replay after uncertainty are impossible.
- Retry count cannot exceed the approved single retry.
- Receipt evidence is visibly synthetic and cannot claim an external response.
- Direct construction or replacement cannot enable transmission, a transmitter,
  credentials, or network activity.

## Verification evidence

- Targeted lifecycle suite: `15 passed`.
- Relevant Phase P1 suite: `92 passed`.
- Full repository regression: `474 passed, 1 skipped`.
- Python compile check: passed.
- All values and results were local and synthetic.

## Continuation boundary

No package-level Human Gate applies under D-051. The next registered work is a
local synthetic lifecycle-audit and restart-recovery package. Registration,
protected retrieval, official ERiC mapping, credentials, real data, connectivity,
production, protected `main`, and transmission remain Human Gates.
