# UI package 2 — synthetic presentation-state contract

## Purpose

Package 2 provides a framework-neutral state boundary for a later interactive UI.
It is local, synthetic, and non-production. It contains no renderer, server,
authentication, external connection, protected ERiC access, or submission path.

## Contract

- Workspace selection resolves an exact synthetic `case_id` through the Case
  Registry and verifies the requested tax year.
- Selecting a case produces a fresh state. Documents, findings, evidence gaps,
  preview, run identity, and Human-Gate state from another case are never retained.
- Case content can be attached only when its `case_id` matches the selected scope.
- Documents, findings, and previews are represented only by canonical immutable
  SHA-256 references; private contents are not carried in the presentation state.
- A visible Human Gate carries its exact action, artifact reference, destination,
  and timezone-aware expiry. `NOT_REQUIRED` cannot carry hidden authority fields.
- Submission stays disabled with the immutable reason
  `PRODUCTION_SUBMISSION_PATH_NOT_AUTHORIZED`.
- Official receipts, real data classifications, and network calls are rejected.

## Verification scenarios

The tests cover registry resolution, exact tax-year matching, synthetic isolation,
cross-case content rejection, stale-state clearing, exact Human-Gate fields,
canonical unique references, and non-forgeable submission/external denial.

## Next gate

This state model can be consumed by different UI technologies. Selecting and
implementing the renderer/server framework, production hosting, authentication,
real-data access, protected ERiC access, or any submission path remains outside
this package.
