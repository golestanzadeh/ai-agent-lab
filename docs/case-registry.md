# Case Registry Contract

## Status

Foundational contract. Runtime implementation is not yet complete.

## Purpose

The Case Registry is the authoritative identity and lookup layer for tax cases. It separates persistent taxpayer/entity identity from individual tax cases and from physical storage locations.

The registry must allow reliable retrieval by person/entity, tax period, case ID, and approved lookup identifiers without broad Drive scanning.

## Identity model

### Persistent identity

A taxpayer or legal entity receives one persistent internal identity:

- `person_id` for a natural person;
- `entity_id` for a legal entity.

The identity persists across tax periods.

### Case identity

A `case_id` identifies exactly one concrete tax case for one taxpayer/entity and one defined tax period.

Recommended format:

```text
CASE-YYYY-NNNN
```

The identifier is opaque to business logic except for uniqueness and human readability. The tax period must also be stored as a separate field and must never be inferred solely from the ID string.

### Tax period

`tax_period` is a structured domain value. The first supported form is a calendar tax year:

```text
{
  "type": "CALENDAR_YEAR",
  "year": 2025
}
```

The model must remain extensible for future fiscal-period variants.

## Case record

Minimum conceptual record:

```text
case_id
owner_type                 # PERSON or ENTITY
owner_id                   # person_id or entity_id
tax_period
case_type                  # e.g. INDIVIDUAL or LEGAL_ENTITY
assessment_mode            # where applicable
lifecycle_status
storage_scope_reference
generation/schema version
created_at
updated_at
last_run_id
```

### Required invariants

1. `case_id` is globally unique within the system.
2. A case has exactly one primary `owner_id` and `owner_type`.
3. `tax_period` is explicit.
4. `storage_scope_reference` resolves to exactly one case root.
5. A case cannot be resolved to multiple unrelated storage roots.
6. Case identity does not depend on a filename.
7. A case remains identifiable even if its storage location changes.
8. Deleting or renaming a Drive folder must never silently create a new case identity.
9. Registry records must not contain private document content.
10. Ambiguous identity resolution must not return an arbitrary case.

## Lifecycle status

Initial status vocabulary:

```text
CREATED
ACTIVE
PROCESSING
REVIEW_REQUIRED
COMPLETED
ARCHIVED
BLOCKED
```

The vocabulary can evolve, but state transitions must be explicit and auditable.

## Case type

Initial conceptual values:

```text
INDIVIDUAL
LEGAL_ENTITY
```

Future case types may be added through an explicit decision and schema evolution process.

## Assessment mode

Assessment mode is optional at the generic registry level because it is not applicable to every case type. For natural-person income-tax cases it may include:

```text
JOINT_ASSESSMENT
INDIVIDUAL_ASSESSMENT
NOT_APPLICABLE
UNKNOWN_PENDING_VERIFICATION
```

This field is not a substitute for detailed Case Party / Household Context.

## Storage scope

`storage_scope_reference` identifies the exact case root in the storage layer. The reference is intentionally abstract in the registry contract so the storage implementation can evolve beyond Google Drive.

For Google Drive, the runtime resolver will map this reference to the exact case folder ID and enforce descendant-only access.

The registry must never require an Agent to search Drive to discover the case root.

## Lookup model

Supported lookup paths include:

```text
case_id
person_id + tax_period
entity_id + tax_period
approved name/display name + tax_period
approved tax identifier + tax_period
```

A lookup can return zero, one, or multiple candidates. A candidate must be resolved deterministically before case-scoped access begins.

If multiple cases remain plausible, the resolver must return an explicit ambiguity state rather than guessing.

## Cross-year retrieval

A person's or entity's history is resolved through persistent identity:

```text
PERSON-00042
      ↓
Case Registry
      ↓
2020 → CASE-2020-....
2021 → CASE-2021-....
...
2026 → CASE-2026-....
```

The resulting case IDs are then processed independently under their own case scopes.

## Case isolation contract

Every case-data API must require `case_id` or an already validated case-scope object.

Allowed conceptual operations:

```text
resolve_case(...)
list_documents(case_id)
get_document(case_id, document_id)
read_evidence(case_id, evidence_id)
write_report(case_id, ...)
```

Prohibited conceptual operations for tax-case data:

```text
list_all_cases_and_documents_for_agent()
search_all_drive_tax_documents()
list_documents_without_case_scope()
```

Registry lookup is not permission to read all matching cases. The caller must receive an explicit case scope for each case it is authorized to process.

## Security and failure behavior

The resolver must fail closed when:

- no case can be resolved;
- identity is ambiguous;
- tax period is ambiguous when required;
- the storage scope is missing or inconsistent;
- the requested object is outside the case scope;
- registry and storage metadata disagree materially.

No model-generated guess may override these failures.

## Versioning and audit

The registry schema must be versioned. Material changes to identity, ownership, tax period, lifecycle status, assessment mode, or storage scope must produce auditable events.

Every processing run is linked to a `run_id`, and every `run_id` is linked to exactly one case at the processing boundary.

## Relationship to other models

```text
Person / Entity Registry
          ↓
      Case Registry
          ↓
 Case Resolver / Scope
          ↓
 Case State
          ↓
Documents / Evidence / Calculations / Reports / Audit
```

The Case Registry does not replace:

- Case Party / Household Context;
- Document Inventory;
- Evidence / Provenance;
- Case State;
- Audit records.

It provides the identity and routing foundation for them.

## Implementation acceptance criteria

The first implementation is accepted only when automated tests demonstrate:

- unique case IDs;
- explicit tax periods;
- persistent person/entity mapping across multiple years;
- deterministic lookup;
- ambiguous lookup does not guess;
- exact storage-scope resolution;
- no unscoped case-data access path;
- cross-case access is rejected;
- cross-year retrieval returns the correct case set;
- changing storage location does not change case identity;
- registry state can be reconstructed and validated from durable data.
