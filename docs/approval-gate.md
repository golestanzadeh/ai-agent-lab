# Human Approval Gate

## Status

Implemented for D-017. The original `ApprovalStore` remains process-local. A SQLite-backed `DurableApprovalStore` now implements the human-accepted durable/reloadable extension described in `docs/durable-approval-lifecycle.md`.

This document defines the Human Approval Gate before any consequential physical migration. Neither the process-local nor durable store authorizes physical migration by itself.

## Ownership

- `MigrationApproval` is an immutable approval artifact. Lifecycle transitions replace the stored immutable value rather than mutating the artifact in place.
- `ApprovalGate` owns deterministic binding and authorization validation.
- `ApprovalStore` owns the legacy/process-local approval lifecycle and one-time consumption semantics.
- `DurableApprovalStore` owns the SQLite-backed durable/reloadable lifecycle and persists its matching approval-lifecycle audit event in the same SQLite transaction.
- `CaseState` does not own approval state. Its `approvals_ref` remains a reference boundary only.
- Approval audit events continue to use the existing `AuditEvent` / `AuditEventType` contract. The durable backend persists the approval-lifecycle subset of that contract transactionally with the approval row; this is not an independent second audit authority.

## Approval binding

An executable approval is valid only when all of these match exactly:

- `case_id`
- `run_id`
- manifest identity, version, and reference
- preflight identity, reference, and successful result
- intended operation
- execution actor
- human approver
- authorization reference
- approval timestamp
- audit reference

The first supported intended operation is the controlled value `PHYSICAL_MIGRATION`. The preflight result token accepted by this implementation is `PASSED`.

Missing, malformed, unknown, revoked, expired, consumed, or mismatched values fail closed. No LLM/model judgment participates in validation or authorization.

## Lifecycle

```text
PENDING -> APPROVED -> CONSUMED
    |          |
    v          +-> REVOKED
 REJECTED      +-> EXPIRED
```

`CONSUMED` is terminal for execution and one-time. A sequential reuse attempt returns `APPROVAL_ALREADY_CONSUMED`.

The legacy in-memory `ApprovalStore` serializes concurrent attempts with its process lock. The durable store serializes write transactions with SQLite `BEGIN IMMEDIATE`, so independent store instances/processes cannot both commit the same consumption.

## Process-local atomic boundary

For `ApprovalStore`, consumption remains:

```text
APPROVED
  -> [ApprovalStore lock + existing AuditStore atomic_append boundary]
  -> CONSUMED + APPROVAL_CONSUMED
  -> success
```

The existing `AuditStore.atomic_append()` holds the audit lock while the Approval Store commits the state transition and before the audit event becomes externally visible. If the domain transition or audit publication fails, the Approval Store rollback restores the previous approval and the Audit Store removes the unpublished event and restores its sequence number.

This remains **process-local atomic consistency only**. The in-memory implementation makes no claim of crash durability, persistent transactional durability, or distributed atomicity.

## Durable SQLite boundary

For `DurableApprovalStore`, every lifecycle mutation uses one SQLite write transaction:

```text
BEGIN IMMEDIATE
  -> reload + integrity/schema/scope validation
  -> validate transition or exact execution binding
  -> allocate durable audit identity
  -> replace approval row with new immutable lifecycle value
  -> append matching durable approval audit event
COMMIT
```

If any operation fails before commit, SQLite rolls back approval state, audit event, and transactional counters together. A successful commit is reloadable after process restart.

The durable record includes a schema version and SHA-256 integrity digest over its canonical executable payload. Durable approval audit rows also carry an integrity digest over the existing AuditEvent-shaped payload. Unknown schema versions, malformed records, or integrity mismatches fail closed.

The integrity digest is corruption/tamper detection, not a digital signature and not protection against a malicious host administrator with database write access.

## Reload and executable authority

A durable approval becomes executable authority only when it is loaded from the configured durable SQLite database and passes:

1. durable schema validation;
2. record decoding and enum/timestamp validation;
3. integrity verification;
4. current case/run scope validation;
5. existing `ApprovalGate.validate_binding()` against the exact execution context.

An exported review record may document an APPROVED state produced during another process, but it is **never imported or interpreted as executable authority**. Chat text, GitHub comments, review JSON/text, and remembered identifiers are likewise not authority.

The historical CASE-001 process-local APPROVED result therefore remains **APPROVED / NOT CONSUMED / NON-DURABLE** and is not silently migrated. Future durable execution would require a newly created durable approval request and a new explicit human grant against the exact authoritative artifacts/context.

## Durable IDs and persistence

Durable approval IDs and durable audit IDs keep the established textual shapes (`APP-00000001`, `AUDIT-00000001`) but are allocated from transactionally persisted SQLite counters so restart does not reuse an identifier.

The database path is private runtime configuration/state. A live database containing case-bound approval authority must not be committed to GitHub.

## Audit events

Approval lifecycle actions use the existing event types:

- `APPROVAL_REQUESTED`
- `APPROVAL_GRANTED`
- `APPROVAL_REJECTED`
- `APPROVAL_REVOKED`
- `APPROVAL_EXPIRED`
- `APPROVAL_CONSUMED`

`APPROVAL_CONSUMED` is the authoritative audit evidence that the one-time authorization was successfully consumed.

`create_pending()` records `APPROVAL_REQUESTED` with the actual requester type. Its backward-compatible default is `HUMAN`; authorized agent preparation may pass `AGENT`. Only `HUMAN` and `AGENT` are valid requesters. `grant()` remains a human-authority action and records `APPROVAL_GRANTED` as `HUMAN`.

## Verification

The durable lifecycle unit suite covers restart/reload, exact binding, terminal one-time consumption across restart, independent concurrent consumers, rollback on durable audit insertion failure, approval/audit integrity corruption, unknown schema versions, lifecycle audit coverage, and rejection of legacy review export as authority.

The first CI run failed only because the newly targeted test was executed without the repository `src` import path. The workflow was corrected to set `PYTHONPATH=src` and rerun.

Verified CI run `34508255413`:

- Agent Bridge validator: **6 passed**;
- durable approval lifecycle: **11 passed**;
- full repository suite: **263 passed, 1 skipped**;
- job conclusion: **success**.

## Integration boundary

This implementation does not create or modify Manifest, Live Target Preflight, or a Physical Migration Executor. It performs no Drive mutation and did not consume the existing real CASE-001 approval.

`CaseState.approvals_ref` may point to an approval ID for case-level discoverability, but executable authority belongs to the selected Approval Store implementation and must pass the exact D-017 binding gate.
