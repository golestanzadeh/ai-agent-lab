# Durable / Reloadable Approval Lifecycle

## Status

Architecture **human-accepted on 2026-09-10** as the first Step-11 AI-Tax-Agent work package after Agent Bridge production acceptance.

This extends D-017 from process-local approval state to durable/reloadable executable authority. It does **not** authorize physical migration or consumption of the real CASE-001 approval.

## Design goals

The durable implementation must preserve all existing D-017 semantics while surviving process restart and concurrent consumers:

- exact case/run/manifest/preflight/operation/actor binding;
- immutable approval values and explicit lifecycle transitions;
- deterministic fail-closed validation;
- one-time terminal `CONSUMED` state;
- human-only grant authority;
- durable lifecycle audit evidence;
- no executable authority reconstructed from review exports, chat, GitHub comments, or prose.

## Initial durable backend

The initial backend is **SQLite** using Python's standard `sqlite3` module.

Rationale:

- the current production runtime is local/single-host;
- SQLite provides crash-safe transactions without introducing a network database or new service dependency;
- `BEGIN IMMEDIATE` plus a single transaction gives a simple deterministic serialization boundary for lifecycle changes and one-time consumption;
- WAL mode may be enabled for normal operation, while correctness depends on transaction semantics, not WAL alone.

A later database backend may replace SQLite only if it preserves the same domain contract and passes equivalent concurrency/recovery tests.

## Durable authority boundary

The authoritative executable approval is the validated row in the durable approval database. The database path is runtime configuration/private operational state and must not be committed with live case data.

Each durable approval row contains:

- schema version;
- approval ID;
- complete D-017 binding;
- approver and authorization reference;
- timezone-aware approval timestamp serialized canonically in UTC;
- lifecycle status;
- authoritative audit reference;
- integrity digest over the canonical approval payload.

Unknown schema versions, malformed enum values, invalid timestamps, missing fields, or integrity mismatches fail closed.

## Integrity model

Each stored approval carries a SHA-256 digest over a canonical JSON representation of all executable approval fields except the digest itself.

The digest is an integrity/corruption detector, **not** a digital signature and not proof against a malicious administrator with database write access. Unexpected digest mismatch prevents reload/validation/consumption.

Database file permissions and host security remain separate operational controls.

## Durable audit boundary

Approval lifecycle events remain part of the existing audit model. For the durable approval backend, the approval row transition and its corresponding approval lifecycle audit event are persisted inside the **same SQLite transaction**.

The durable event uses the existing `AuditEvent` field contract and existing approval lifecycle event types:

- `APPROVAL_REQUESTED`
- `APPROVAL_GRANTED`
- `APPROVAL_REJECTED`
- `APPROVAL_REVOKED`
- `APPROVAL_EXPIRED`
- `APPROVAL_CONSUMED`

No approval state transition is committed without its durable audit event, and no durable approval event is committed without the corresponding state transition.

This is a persistence implementation of the existing audit contract, not a second independent audit authority.

## Transaction and concurrency model

Every lifecycle mutation uses one SQLite write transaction:

```text
BEGIN IMMEDIATE
  -> read and validate current approval row
  -> validate requested transition/binding
  -> allocate durable audit event identity
  -> write replacement approval row
  -> append durable audit event
COMMIT
```

If any step fails, the transaction rolls back.

For `consume()` this means concurrent or sequential consumers cannot both succeed. Once one transaction commits `CONSUMED`, every later consumer reloads a terminal state and receives `APPROVAL_ALREADY_CONSUMED`.

## Reload semantics

A newly constructed durable store opens the same database, verifies schema compatibility, loads the requested approval from SQLite, verifies its integrity digest and domain values, and then applies the existing `ApprovalGate` binding validation.

There is no process-memory authority requirement after creation. Restarting Python does not invalidate a valid durable approval.

## Crash and partial-failure behavior

SQLite transaction commit is the durable atomic boundary. A process failure before commit leaves neither the new lifecycle state nor its audit event committed. A successful commit makes both visible on reload.

If the database reports corruption, schema uncertainty, transaction failure, or an unrecognized record, the approval operation fails closed. Recovery does not guess a state from an exported review file.

## IDs and schema version

The initial durable schema version is `1`.

Approval and audit IDs are allocated transactionally from durable integer sequences so restart cannot reuse an existing identifier.

Existing in-memory IDs remain compatible in textual form (`APP-00000001`, `AUDIT-00000001`) but an in-memory/exported record is not automatically imported as executable authority.

## Legacy / current D-021 state

The process-local APPROVED state produced for CASE-001 before this architecture is **not durable authority** and must not be silently imported.

The existing private review export may be used only as review evidence. To obtain future executable durable authority, the system must reconstruct the exact context from authoritative artifacts, run the required preflight, create a new durable approval request, and obtain a new explicit human grant under the durable store.

This prevents historical prose or exported JSON from becoming authority merely because the persistence layer now exists.

## Compatibility boundary

- `MigrationApproval`, `ApprovalExecutionContext`, enums and `ApprovalGate` remain the shared D-017 domain contract.
- Existing `ApprovalStore` remains available for unit/backward compatibility and is explicitly process-local.
- `DurableApprovalStore` is the reloadable executable implementation.
- Durable approval persistence does not make Manifest or Preflight approval-aware and does not introduce a physical migration executor.

## Acceptance tests

Before this work package can be accepted, tests must demonstrate at minimum:

1. create/grant survives close/reopen;
2. exact binding still passes and mismatch still fails closed;
3. consume survives restart and cannot be reused;
4. two concurrent consumers produce exactly one success;
5. failed state/audit write rolls back both sides;
6. corrupt integrity digest fails closed;
7. unknown schema version fails closed;
8. malformed durable records fail closed;
9. durable event is present for every committed lifecycle transition;
10. exported legacy/review data is never treated as executable authority;
11. existing in-memory D-017 tests continue to pass;
12. full regression suite passes.

## Explicit non-goals

This work package does not:

- consume the current real CASE-001 approval;
- copy/move/rename/delete Drive documents;
- implement physical migration;
- authorize release/merge by an agent;
- claim protection against a malicious host/database administrator;
- select a distributed/cloud database.
