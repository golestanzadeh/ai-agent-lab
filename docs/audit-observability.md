# Durable Audit and Observability Boundary

Status: **foundational contract; runtime implementation introduced**

## 1. Purpose

The Audit/Observability layer makes each execution reconstructable without relying on LLM conversation history.

For a material execution, the system must be able to answer:

- who or what initiated the action;
- which `case_id` and `run_id` were involved;
- which agent/component executed it;
- what operation/tool was invoked;
- what data or references were used;
- which decision was made;
- which evidence/provenance references supported it;
- what result was produced;
- what error or block occurred;
- whether human approval was requested or granted.

## 2. Boundary

```text
Case Registry / Case State
          |
          | case_id + run_id
          v
   Audit Event Recorder
          |
          +--> durable Audit Store (future)
          |
          +--> observability/export adapters (future)
```

Audit is separate from Case State, source documents, evidence, and LLM context.

## 3. Core invariant

> Every audit event is bound to exactly one `case_id`; execution events are additionally bound to exactly one `run_id`.

No global or unscoped tax-case audit event is permitted.

Cross-case contamination in audit data is a security and correctness failure.

## 4. Event model

The foundational event contains:

- `event_id`: deterministic runtime-generated unique identifier;
- `case_id`: mandatory case scope;
- `run_id`: mandatory for execution events;
- `event_type`: controlled event classification;
- `occurred_at`: timezone-aware timestamp;
- `actor_type`: human, agent, system, or tool;
- `actor_id`: stable actor/component identifier;
- `operation`: action being performed;
- `status`: success, failure, blocked, or informational outcome;
- `input_refs`: references to data/evidence, never raw sensitive payloads by default;
- `decision_ref`: optional decision identifier;
- `evidence_refs`: optional provenance/evidence identifiers;
- `output_refs`: optional output identifiers;
- `error_code`: optional normalized error classification;
- `approval_ref`: optional human-approval reference;
- `metadata`: bounded non-authoritative diagnostic metadata;
- `schema_version`.

The event model is intentionally reference-oriented. Raw tax documents, credentials, tokens, and unnecessary personal data must not be copied into audit events.

## 5. Event types

Initial controlled vocabulary:

- `RUN_CREATED`
- `RUN_STARTED`
- `RUN_COMPLETED`
- `RUN_FAILED`
- `RUN_BLOCKED`
- `RUN_CANCELLED`
- `TOOL_CALLED`
- `TOOL_COMPLETED`
- `TOOL_FAILED`
- `DECISION_RECORDED`
- `EVIDENCE_LINKED`
- `APPROVAL_REQUESTED`
- `APPROVAL_GRANTED`
- `APPROVAL_REJECTED`
- `STATE_CHANGED`
- `OUTPUT_CREATED`
- `ERROR_RECORDED`

The vocabulary may grow, but new event types must be intentional and documented.

## 6. Audit versus observability

**Audit** answers: what happened and why can it be reconstructed later?

**Observability** answers: how is the running system behaving operationally?

They share event identity and correlation fields but are not the same data product. Operational metrics/logging may be sampled or aggregated; consequential audit records must not be silently sampled away.

## 7. Immutability and ordering

Audit events are append-only at the contract boundary. Existing events are never edited in place.

Corrections are represented by new events referencing the affected event.

`occurred_at` provides event time. The durable implementation must also preserve insertion/sequence ordering sufficient to reconstruct an execution when timestamps are equal or clocks differ.

The first runtime does not claim cryptographic tamper evidence or distributed total ordering.

## 8. Case and run validation

The recorder must reject:

- missing or blank `case_id`;
- unknown case IDs;
- missing `run_id` for execution-bound events;
- unknown runs;
- runs belonging to another case;
- malformed event identity;
- attempts to mutate an existing event.

Validation must use the authoritative Case Registry and Case State/Run model where applicable.

## 9. Privacy and security

Audit data is potentially sensitive. Therefore:

- store references instead of document contents whenever possible;
- never store credentials, access tokens, or secrets;
- avoid copying tax identifiers or personal data unless strictly required for reconstruction;
- keep audit storage case-scoped;
- apply retention and access-control policy before production use;
- fail closed on scope violations.

## 10. Deterministic runtime first

The first implementation is an in-memory append-only recorder behind a small interface. It establishes validation and event semantics before choosing a database, telemetry platform, or event-sourcing framework.

A future durable adapter must preserve the same contract and make storage replaceable without changing `case_id`/`run_id` identity semantics.

## 11. What this does not implement yet

- durable database storage;
- distributed event ordering;
- cryptographic audit chaining/signatures;
- OpenTelemetry integration;
- retention/deletion policy implementation;
- multi-user authorization;
- full evidence/provenance schema;
- production log aggregation.

## 12. Acceptance criteria

1. Every event has a validated `case_id`.
2. Execution events have a validated `run_id` belonging to that case.
3. Unknown cases and cross-case runs fail closed.
4. Events are append-only.
5. Event identity is unique and deterministic at runtime.
6. Event type and outcome are explicit.
7. Actor and operation are explicit.
8. Evidence/input/output references can be recorded without copying raw payloads.
9. Errors and approval events are reconstructable.
10. Audit records are independent of LLM conversation context.
11. Sensitive data is minimized.
12. A durable backend can replace the first runtime without changing the event contract.
