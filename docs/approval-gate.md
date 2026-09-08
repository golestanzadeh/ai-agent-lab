# Human Approval Gate

## Status

Implemented for D-017. This document defines the implementation boundary for the Human Approval Gate before any consequential physical migration.

## Ownership

- `MigrationApproval` is an immutable approval artifact. Lifecycle transitions replace the stored immutable value rather than mutating the artifact in place.
- `ApprovalStore` owns approval lifecycle and one-time consumption.
- `ApprovalGate` owns deterministic binding and authorization validation.
- `CaseState` does not own approval state. Its `approvals_ref` remains a reference boundary only.
- The existing `AuditStore` remains the only audit subsystem.

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

`CONSUMED` is terminal for execution and one-time. A sequential reuse attempt returns `APPROVAL_ALREADY_CONSUMED`. Concurrent attempts are serialized by the Approval Store lock, so exactly one matching attempt can consume an approval.

## Atomic consumption boundary

Consumption is not implemented as two independent operations such as `consume()` followed by `audit.append()`.

The boundary is:

```text
APPROVED
  -> [ApprovalStore lock + existing AuditStore atomic_append boundary]
  -> CONSUMED + APPROVAL_CONSUMED
  -> success
```

The existing `AuditStore.atomic_append()` holds the audit lock while the Approval Store commits the state transition and before the audit event becomes externally visible. Approval readers are protected by the Approval Store lock and audit readers by the Audit Store lock. Therefore callers cannot observe the committed approval transition without the corresponding audit event.

If the domain transition or audit publication fails, the Approval Store rollback restores the previous approval and the Audit Store removes the unpublished event and restores its sequence number. The operation is then unsuccessful.

This is **process-local atomic consistency only**. The current in-memory implementation makes no claim of crash durability, persistent transactional durability, or distributed atomicity.

## Audit events

Approval lifecycle actions use the existing audit boundary. The implementation adds the explicit event types needed by the lifecycle:

- `APPROVAL_REQUESTED`
- `APPROVAL_GRANTED`
- `APPROVAL_REJECTED`
- `APPROVAL_REVOKED`
- `APPROVAL_EXPIRED`
- `APPROVAL_CONSUMED`

`APPROVAL_CONSUMED` is the authoritative audit evidence that the one-time authorization was successfully consumed.

`create_pending()` records `APPROVAL_REQUESTED` with the actual requester type.
Its backward-compatible default is `HUMAN`; authorized agent preparation passes
`AGENT`. Only `HUMAN` and `AGENT` are valid requesters. `grant()` remains a
human-authority action and always records `APPROVAL_GRANTED` as `HUMAN`.

## Integration boundary

The implementation does not create or modify Manifest, Live Target Preflight, or a Physical Migration Executor. It performs no Drive mutation and cannot itself execute physical migration.

`CaseState.approvals_ref` may point to an approval ID for case-level discoverability, but ApprovalStore remains the lifecycle authority.
