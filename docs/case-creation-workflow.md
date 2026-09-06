# Case Creation Workflow Contract

## Status

Foundational workflow contract. Runtime implementation is not yet complete.

## Purpose

The Case Creation Workflow creates a new tax case as a durable, uniquely identifiable, isolated unit of work.

The workflow connects persistent taxpayer/entity identity to one tax period and one `case_id`, establishes the exact storage scope, initializes the Case Registry record, and records an auditable creation event.

The workflow is designed for long-term multi-case and multi-year operation. CASE-001 migration is explicitly outside this workflow.

## Design principles

1. `case_id` is the mandatory operational scope after case creation.
2. Persistent `person_id` / `entity_id` identifies the taxpayer or legal entity across tax periods.
3. `tax_period` is explicit and must not be inferred only from a case identifier.
4. Identity resolution must be deterministic or explicitly unresolved; the workflow must never guess.
5. Storage location is a routing detail, not the identity of the case.
6. Case creation must be idempotent.
7. Failure must not leave a falsely usable or ambiguously scoped case.
8. All material creation decisions and state changes must be auditable.
9. Case data access remains prohibited without a validated case scope.
10. Generic creation and legacy CASE-001 migration are separate workflows.

## Input contract

A Case Creation Request must provide enough information to identify the intended owner and tax period.

Minimum conceptual input:

```text
request_id
owner_type                 # PERSON or ENTITY
owner_reference            # existing persistent ID or information for identity resolution
 tax_period
case_type
assessment_mode            # where applicable
requested_by
requested_at
schema_version
```

`owner_reference` may resolve to an existing `person_id` / `entity_id` or result in creation of a new persistent identity when identity evidence is sufficient.

For natural-person income-tax cases, `assessment_mode` may be:

```text
JOINT_ASSESSMENT
INDIVIDUAL_ASSESSMENT
NOT_APPLICABLE
UNKNOWN_PENDING_VERIFICATION
```

The workflow must not infer final tax treatment from `Steuerklasse` alone.

## Validation

Before any durable case creation, the workflow validates:

- request structure and schema version;
- owner type;
- owner identity resolution state;
- tax period validity and explicitness;
- case type compatibility with owner type;
- assessment mode applicability where relevant;
- authorization to create the case;
- uniqueness/idempotency conditions;
- availability of the target storage root and required scope guarantees.

Invalid or materially ambiguous requests do not proceed.

## Identity resolution

The workflow uses the Person/Entity Registry as the persistent identity layer.

```text
Case Creation Request
        ↓
Identity Resolution
        ├── CONFIRMED existing identity → use persistent ID
        ├── sufficient evidence for new identity → create persistent ID
        └── CANDIDATE / UNRESOLVED / ambiguous → stop or escalate
```

A display name, filename, or other weak lookup attribute is not by itself sufficient to select an existing identity when multiple candidates remain plausible.

The workflow must never silently merge two persistent identities.

## Tax period and case identity

`tax_period` is stored as a structured value.

Initial calendar-year form:

```text
{
  "type": "CALENDAR_YEAR",
  "year": 2025
}
```

A generated `case_id` must be globally unique. The recommended human-readable format is:

```text
CASE-YYYY-NNNN
```

The year portion is for readability only. Business logic must use the explicit `tax_period` field.

## Idempotency

The workflow must accept a stable `request_id` or equivalent idempotency key.

Repeated execution of the same creation request must not create duplicate cases.

Conceptually:

```text
same request + same effective creation parameters
                 ↓
        same case identity
```

If a prior attempt completed, the existing case is returned.

If a prior attempt failed, the workflow must detect whether a recoverable partial creation exists and either safely resume or cleanly fail. It must never create a second case merely because the first attempt was incomplete.

## Creation sequence

The deterministic creation sequence is:

```text
1. Validate request
2. Resolve or create persistent Person/Entity identity
3. Validate tax period and case parameters
4. Check idempotency and existing case candidates
5. Generate unique case_id
6. Create exact case storage scope
7. Create required case subfolders
8. Create Case Registry record
9. Link persistent identity ↔ case
10. Initialize case state and creation run metadata
11. Record audit event
12. Mark case as CREATED / ready for subsequent workflow
```

The implementation may use transactional or compensating mechanisms appropriate to the storage backend, but the externally observable result must satisfy the invariants below.

## Storage scope

For the initial Google Drive implementation, the target structure is:

```text
AI-Tax-Agent/
└── Tax_Years/
    └── <tax year>/
        └── Cases/
            └── <case_id>/
                ├── Documents/
                ├── Evidence/
                ├── Tax_Categories/
                ├── Calculations/
                ├── Reports/
                └── Audit/
```

The workflow must create and retain an exact storage-scope reference for the case root.

The Case Registry must not rely on later Drive searches to rediscover this root.

The storage abstraction must remain replaceable so the case identity contract does not become dependent on Google Drive.

## Case Registry initialization

The minimum conceptual Case Registry record created by this workflow is:

```text
case_id
owner_type
owner_id
 tax_period
case_type
assessment_mode
lifecycle_status = CREATED
storage_scope_reference
schema_version
created_at
updated_at
last_run_id
```

The record must satisfy the Case Registry invariants, including one primary owner, one exact storage root, explicit tax period, unique case identity, and no private document content.

## Person/Entity Registry linkage

The workflow creates or updates the persistent identity-to-case relationship without moving case-scoped financial data into the Person/Entity Registry.

Conceptually:

```text
PERSON-0001
    ↓
Case Registry
    ├── CASE-2024-....
    ├── CASE-2025-....
    └── CASE-2026-....
```

The relationship must be auditable and must preserve the distinction between persistent identity and individual case data.

## Initial case state

A newly created case enters:

```text
CREATED
```

It must not be represented as `ACTIVE`, `PROCESSING`, or `COMPLETED` merely because the folder was successfully created.

Subsequent state transitions belong to the Case State / execution model and must be explicit and auditable.

## Run identity

Case creation must have its own execution identity, such as `creation_run_id`.

The run is linked to exactly one case at the processing boundary once the case identity exists.

Run metadata must support:

- idempotency;
- audit reconstruction;
- failure diagnosis;
- correlation of Registry and storage operations.

## Failure and rollback behavior

Case creation is a multi-resource operation. Failures must be handled explicitly.

Examples:

- identity cannot be resolved → no case created;
- tax period invalid → no case created;
- duplicate case detected → return existing case or explicit conflict;
- storage root cannot be created → case must not become usable;
- required subfolder creation fails → case remains non-ready or is safely compensated;
- Registry write fails after storage creation → workflow must execute a defined compensation/recovery path and must not report successful creation;
- identity linkage fails → workflow must not report a fully created case.

Partial state must be detectable and recoverable. Silent orphaned cases are prohibited.

The implementation must define compensation boundaries without pretending that external storage operations are inherently transactional.

## Isolation boundary

After `case_id` is established, all subsequent case operations are scoped to that case.

No Agent or generic data-access operation may use the creation workflow as permission to access unrelated cases.

The following are prohibited:

```text
search_all_drive_tax_documents()
list_documents_without_case_scope()
resolve_case_by_broad_drive_scan()
```

Allowed conceptual access begins from the validated case scope:

```text
case_id
  ↓
Case Registry
  ↓
exact storage root
  ↓
case descendants only
```

## Audit event

Successful creation must produce an auditable event containing, at minimum:

```text
creation_run_id
request_id
case_id
owner_type
owner_id
 tax_period
case_type
creation outcome
created_at
schema_version
```

Audit records must not unnecessarily duplicate private source-document content.

Failed and compensated creation attempts must also leave sufficient audit information to reconstruct what happened.

## Explicit exclusions

This workflow does not perform:

- CASE-001 migration;
- document ingestion;
- OCR or document extraction;
- tax-law research;
- tax calculation;
- tax optimization;
- final legal qualification;
- electronic tax submission;
- broad cross-case document access.

Those are separate workflows and contracts.

## CASE-001 relationship

CASE-001 is the first real validation case, but its existing physical Drive structure is legacy state.

Generic Case Creation must not silently migrate, rename, or restructure CASE-001.

A separate migration/compatibility workflow must first define discovery, mapping, validation, rollback, and verification for CASE-001.

## Acceptance criteria

The first runtime implementation is accepted only when automated tests demonstrate:

- valid requests create exactly one unique `case_id`;
- persistent Person/Entity identity is correctly reused or safely created;
- ambiguous identity resolution stops without guessing;
- tax period is explicit and validated;
- case type and assessment mode are validated;
- repeated identical requests are idempotent;
- duplicate case creation is rejected or deterministically resolved;
- exact case storage scope is created;
- all required case subfolders are created within that scope;
- Case Registry is initialized consistently with the storage scope;
- Person/Entity Registry linkage is correct;
- initial lifecycle state is `CREATED`;
- creation run identity is recorded;
- successful and failed attempts are auditable;
- partial failures do not produce falsely usable cases;
- no unscoped case-data access path is introduced;
- cross-case access is rejected;
- changing physical storage later does not change `case_id`;
- CASE-001 remains untouched by generic case creation.

## Relationship to existing contracts

```text
Person/Entity Registry
          ↓
Case Creation Workflow
          ↓
Case Registry
          ↓
Case Resolver / Scope
          ↓
Case State + Run Identity
          ↓
Documents / Evidence / Calculations / Reports / Audit
```

This workflow operationalizes the existing Case Registry and Person/Entity Registry foundations. It does not replace either contract.
