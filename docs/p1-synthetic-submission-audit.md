# Phase P1 continuous package — Synthetic Submission Audit and Restart Recovery

Status: **COMPLETE / VERIFIED UNDER CONTINUOUS NON-PRODUCTION AUTHORITY**

## Boundary

This package creates only local synthetic audit snapshots. It does not persist tax
amounts or purpose text, access credentials, connect to a service, receive a real
receipt, or authorize or perform transmission.

## Design

`src/agent_lab/elster_submission_audit.py` converts the already validated synthetic
attempt plans and results into a privacy-minimized append-ordered event stream.
Every event binds case, run, idempotency key, attempt number, artifact reference,
timestamp, and the preceding event digest. The snapshot binds the chain head and
the synthetic preview identity.

`restore_synthetic_lifecycle_audit` accepts only the exact versioned JSON shape and
requires the caller's expected case, run, and idempotency key. It reconstructs one
of five states: awaiting a synthetic result, definite failure recorded, uncertain
and blocked, complete with a placeholder, or retry exhausted.

The recovery path fails closed on malformed JSON, unexpected fields, digest or
head mutation, event reordering or truncation, invalid state transitions, missing
receipt-placeholder evidence, and cross-case/run/key recovery attempts.

## Privacy and capability guarantees

- The snapshot contains no tax values, purpose text, source material, or official
  receipt content.
- The data classification is permanently `SYNTHETIC`.
- Recovery is descriptive only; it cannot plan a retry or create authority.
- Transmission, credentials, networking, and claims of an external receipt remain
  absent and non-forgeably disabled.

## Verification evidence

- Targeted audit/recovery suite: `12 passed`.
- Relevant Phase P1 suite: `104 passed`.
- Full repository regression: `486 passed, 1 skipped`.
- Python compile check: passed.

## Continuation boundary

No package-level Human Gate applies under D-051. The next registered package is a
local synthetic submission-readiness dossier that aggregates immutable P1 evidence
and explicit blockers without introducing any execution capability.
