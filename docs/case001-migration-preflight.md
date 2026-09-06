# CASE-001 Physical Migration Preflight

**Status:** Structural preflight boundary implemented; no physical Drive mutation performed
**Last updated:** 2026-09-06

## Purpose

The migration manifest proves that the live source inventory can be mapped to stable logical document identities. It does not prove that a physical destination is safe to use.

The preflight boundary is the final deterministic safety layer before any physical migration executor is allowed to write to storage.

## Required checks

Before physical migration can be authorized, all of the following must be true:

1. `case_id` is `CASE-001`.
2. `tax_period` is 2024.
3. The manifest contains the expected documents.
4. Every source object mapping is unique.
5. Every logical document mapping is unique.
6. The target scope is an actual storage scope, not a planned path.
7. The target scope is empty before first execution.
8. The manifest has already passed migration compatibility validation.
9. A human approval record exists for the consequential physical operation.
10. Rollback and post-migration verification are defined before execution.

## Current implementation

`src/agent_lab/case001_migration_preflight.py` implements the non-mutating structural gate.

It accepts only explicit facts about the target scope:

- whether the target is an actual storage scope;
- whether the target is empty.

It never discovers a target by broad Drive search and never performs Drive writes.

The preflight fails closed when the target is still a planned logical scope or is not empty.

## Why target existence is explicit

The current live manifest intentionally used:

```text
planned:AI-Tax-Agent/Tax_Years/2024/Cases/CASE-001/Documents
```

This is a logical target reference, not a Drive object. Therefore the successful manifest validation must not be interpreted as proof that the destination exists.

An actual target Drive scope must be resolved through an explicit, case-scoped storage operation before physical migration can proceed.

## Human approval boundary

The preflight result is not authorization to mutate storage. The future executor must require a separate human-controlled approval record bound to:

- `case_id`;
- manifest identity/version;
- preflight result;
- intended operation;
- actor/approver;
- timestamp;
- authorization reference.

Without that approval, execution must remain blocked.

## Rollback boundary

Physical execution must record enough state to reverse every successful mutation or otherwise restore a known-safe state. A partial migration must never be reported as successful.

Rollback design must precede executor implementation.

## Verification boundary

After execution, verification must independently confirm:

- expected target objects exist;
- logical document identities remain linked to the intended documents;
- source objects have the expected post-migration state;
- no unexpected duplicates were introduced;
- case scope remains isolated;
- audit records cover the operation.

Only successful post-migration verification may permit retirement of the legacy compatibility alias.

## Tests

`tests/unit/test_case001_migration_preflight.py` covers:

- successful preflight for an actual empty target;
- rejection of a planned/non-actual target;
- rejection of a non-empty target;
- duplicate source-object rejection;
- duplicate logical-document rejection;
- empty-manifest rejection.

These are deterministic unit tests. They do not constitute authorization for physical Drive mutation and do not prove live target existence.
