# Controlled Physical Migration Executor

## Status

Implementation work package started after human acceptance of the Durable Approval stage on 2026-09-10. This document defines the bounded executor contract. It does **not** authorize real CASE-001 execution.

## Purpose

The executor moves the exact Google Drive objects already bound by the accepted CASE-001 migration manifest from one explicit source parent to one explicit target parent while preserving provider object IDs and logical document IDs.

It is downstream of:

1. Case Registry and case-scoped source identity;
2. Document Identity and Inventory Evidence;
3. deterministic migration manifest;
4. successful live target preflight;
5. Durable Approval exact binding.

It never discovers documents by taxpayer name, filename, folder name, or Drive-wide search.

## Modes

### DRY_RUN

Default mode. It performs zero storage mutations and zero approval consumption. It checks the explicit manifest, current source placement, target emptiness, duplicate object IDs, and execution parameters. A successful dry-run is evidence only, never execution authority.

### LIVE

Live mode is fail-closed and requires all of the following:

- explicit `live_enabled=True` at the caller boundary;
- a durable approval identifier;
- an exact `ApprovalExecutionContext`;
- the durable store validating that approval as `APPROVED` against that context;
- every expected object currently located under the explicit source parent;
- the explicit target parent still empty immediately before mutation.

No condition may be inferred from prose, exported review data, chat history, GitHub comments, or remembered IDs.

## Storage mutation port

The executor depends on an injected storage mutation port with three narrow capabilities:

- `list_children(parent_id)` returns direct child object IDs;
- `get_parent(object_id)` returns the object's current single parent ID;
- `move(object_id, new_parent_id, expected_old_parent_id=...)` performs one guarded parent move.

The executor contains no credentials, no Drive authentication, and no global search implementation. A live Google Drive adapter may only be injected by a separately controlled runtime boundary.

## Pre-mutation invariants

Execution fails closed unless:

- manifest is CASE-001 / 2024;
- manifest contains at least one document;
- every mapping uses the manifest source provider and exact source/target scope references;
- source object IDs and logical document IDs are unique;
- every expected object is directly under the explicit source parent;
- the target parent is empty;
- source and target parent IDs differ.

These checks are repeated at execution time to detect stale preflight state.

## Mutation and rollback

Objects are moved in manifest order. After each successful move, the object ID is appended to an in-memory applied-operation list.

If any later move, post-migration verification, or durable approval consumption fails, already-applied moves are rolled back in reverse order from target to source.

Rollback itself is guarded by the expected current parent. If any rollback step fails, the executor raises an explicit rollback failure containing the affected object IDs. It never reports success when final state is uncertain.

Because Google Drive and the local SQLite approval database cannot participate in one distributed transaction, the executor deliberately consumes approval **after** successful post-migration verification. If approval consumption then fails, it rolls the storage moves back. A crash outside this Python control flow can still create an uncertain external state; on restart the pre-mutation source/target checks fail closed and require human recovery rather than silently re-running.

## Post-migration verification

Before approval consumption, the executor verifies:

- target direct-child set equals exactly the manifest source-object set;
- no expected source object remains under the source parent;
- each moved object reports the target as its current direct parent.

Only after this verification succeeds may `DurableApprovalStore.consume()` be called.

A successful result therefore means both physical placement and durable one-time approval consumption succeeded in the same controlled attempt. It does not imply legacy alias retirement; that remains a later commit/verification concern.

## Idempotency and retries

- Successful live execution consumes the durable approval, so a replay fails before mutation with `APPROVAL_ALREADY_CONSUMED`.
- A failed attempt with complete rollback leaves the approval unconsumed and may be retried only after the preconditions are revalidated.
- An incomplete rollback or uncertain external state is terminal for automation and requires human intervention.

## Real CASE-001 Human Gate

This work package may implement and test the executor only with synthetic/injected storage and temporary durable approval databases.

Before real CASE-001 execution, a separate consequential Human Gate must explicitly authorize:

1. the exact authoritative manifest and successful live target preflight identities;
2. a newly created durable approval request and human grant;
3. the exact source and target object IDs/parents;
4. the live execution attempt.

The historical process-local `APP-00000001` is not executable durable authority and must never be upgraded or imported.
