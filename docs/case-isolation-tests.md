# Case Isolation and Cross-Case Contamination Tests

## Status

Foundational isolation acceptance suite implemented and verified.

## Purpose

These tests verify that the deterministic case boundaries prevent one tax case from accessing, reading, or using state belonging to another case.

Cross-case contamination is both a security failure and a correctness failure.

## Scope

The acceptance suite covers the deterministic chain:

```text
Case Registry
      ↓
Case State / Run ID
      ↓
Case-Scoped Storage Resolver
      ↓
Audit Boundary
```

The suite uses two independent cases with the same persistent person owner but different tax periods and storage roots. This proves that persistent identity does not collapse case identity.

## Required invariants

- `CASE-A` cannot access `CASE-B` storage.
- `CASE-B` cannot access `CASE-A` storage.
- A run created for one case cannot be used as the run of another case.
- Audit retrieval for one case cannot return another case's events.
- Case-state lookup is bound to the requested `case_id`.
- Unknown cases cannot enter any case-scoped boundary.
- Different cases cannot share the same registered storage root under current registry invariants.
- Cases belonging to the same persistent person remain distinct by `case_id` and `tax_period`.

## Test location

`tests/unit/test_case_isolation.py`

## Verification

Local execution completed successfully:

```text
10 passed in 0.14s
```

The result verifies the current deterministic isolation boundaries only. It does not yet prove isolation for a live Google Drive adapter, because that adapter has not been implemented.

## Non-goals

These tests do not yet cover:

- Google Drive API behavior;
- authorization/authentication policy;
- multi-user access control;
- durable database isolation;
- distributed execution;
- malicious model behavior beyond deterministic boundary misuse;
- production penetration testing.

Those require separate implementation and evaluation layers.
