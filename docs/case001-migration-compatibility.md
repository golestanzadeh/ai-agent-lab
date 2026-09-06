# CASE-001 Migration / Compatibility Layer

**Status:** Implemented compatibility validation baseline; no physical Drive migration performed
**Last updated:** 2026-09-06

## Purpose

CASE-001 currently exists in the legacy Drive layout:

```text
AI-Tax-Agent/
└── Cases/
    └── CASE-001/
        └── Documents/
```

The target architecture places the same case under its explicit tax period:

```text
AI-Tax-Agent/
└── Tax_Years/
    └── 2024/
        └── Cases/
            └── CASE-001/
                ├── Documents/
                ├── Evidence/
                ├── Tax_Categories/
                ├── Calculations/
                ├── Reports/
                └── Audit/
```

The compatibility layer bridges these layouts without changing case identity or source-document identity. It deliberately separates **migration planning/validation** from **physical Drive mutation**.

## Non-negotiable invariants

A migration is valid only if all of the following remain true:

1. `case_id` remains `CASE-001`.
2. `tax_period` remains 2024.
3. The persistent owner identity does not change.
4. Every source object keeps its original provider object ID.
5. Every logical `document_id` remains unchanged.
6. Existing `SourceObservation` provenance remains valid.
7. No source document is deleted, overwritten, or silently duplicated.
8. Legacy and target scopes are never treated as two independent cases.
9. Any ambiguous mapping fails closed.
10. Physical Drive writes are outside this implementation.

## Compatibility model

The layer treats the legacy scope as a temporary alias for the same registered case. It does not create a second `CaseRecord`.

```text
Legacy CASE-001 scope
        │
        │ explicit migration mapping
        ▼
     CASE-001
     tax_period=2024
        │
        ▼
Target 2024 CASE-001 scope
```

The mapping is case-scoped and explicit. It is not a Drive-wide discovery mechanism.

## Validation chain

The current implementation can validate a migration plan against both the stable Document Identity registry and a previously recorded Inventory Evidence snapshot:

```text
Case Registry
     │
     ├──────────────┐
     ▼              ▼
Document Identity  Inventory Evidence
     │              │
     └──────┬───────┘
            ▼
   CASE-001 Migration Plan
            │
            ▼
     deterministic validation
```

When a `DocumentIdentityRegistry` is supplied, every mapping must resolve to an existing logical document in `CASE-001`, and all of these must match exactly:

- `source_provider`
- `source_object_id`
- `source_scope_ref`
- `logical_document_id`

When `InventoryEvidence` is supplied, the migration manifest must match the evidence snapshot's source object sequence and logical document sequence exactly. The evidence must belong to `CASE-001`, use the plan's source scope, and use the expected Google Drive provider.

This prevents a migration manifest from inventing document identities or silently omitting/reordering inventory objects.

## Migration phases

### Phase 0 — Design

Define source scope, target scope, invariants, object-identity rules, failure behavior, and rollback requirements.

### Phase 1 — Prepare

Create a deterministic migration plan from explicit scope references. No Drive mutation occurs.

### Phase 2 — Validate

Validate the plan against the Case Registry and, when connected, the Document Identity and Inventory Evidence layers. Duplicate, unknown, mismatched, or cross-scope mappings fail closed.

### Phase 3 — Execute

Future implementation only. Physical Drive create/move/rename operations require an explicit migration command, consequential-action approval, and separate verification. They are not part of the current layer.

### Phase 4 — Verify

Future live verification must prove that every expected source object remains reachable, every logical document identity is preserved, and the target structure is correct.

### Phase 5 — Commit / Retire Legacy Alias

Only after successful verification may the legacy compatibility alias be retired.

## Rollback principle

The current implementation is intentionally non-mutating, so its rollback is trivial: discard the generated migration plan. A future physical migration must be designed so that a failed partial operation cannot be mistaken for a completed migration.

## Document Identity relationship

Migration operates on source object identity, not filenames.

For each source document:

```text
provider + original object ID
          ↓
existing logical document_id
          ↓
new target parent/scope
```

The migration layer does not create or reassign logical document IDs. When the identity registry is connected, the existing record is authoritative and the mapping must agree with it.

A copied object with a new provider object ID is not automatically the same source object. Such a relationship requires explicit future migration provenance and must preserve the old logical `document_id` only when the migration process can prove the relationship.

## Inventory Evidence relationship

Inventory Evidence records the verified metadata-only source snapshot and can contain stable `document_identity_refs`. The migration layer can use that evidence as a preflight manifest boundary.

The current validation requires exact sequence equality between:

- migration `(source_provider, source_object_id)` mappings and evidence `item_refs`;
- migration `logical_document_id` mappings and evidence `document_identity_refs`.

Therefore a migration plan cannot silently migrate only part of the inventory when the full inventory evidence is supplied.

## Current runtime

`src/agent_lab/case001_migration.py` implements deterministic preparation and validation using opaque storage-scope references.

It:

- requires explicit source and target scope references;
- requires the expected `case_id` and tax period;
- produces a deterministic migration plan;
- validates case identity and tax period;
- validates explicit object mappings;
- rejects duplicate source-object mappings;
- rejects duplicate logical-document mappings;
- can validate each mapping against `DocumentIdentityRegistry`;
- can validate a complete mapping manifest against `InventoryEvidence`;
- performs no Drive reads or writes;
- performs no global search;
- does not copy, move, rename, delete, or overwrite source documents.

## Object mapping contract

A future execution manifest may contain mappings such as:

```text
source_provider
source_object_id
logical_document_id
source_scope_ref
target_scope_ref
```

These are identity assertions to validate, not permission to mutate Drive.

The following are invalid:

- one source object mapped to multiple logical documents;
- one logical document mapped from multiple unrelated source objects;
- source scope different from the plan source scope;
- target scope different from the plan target scope;
- unknown logical document when identity validation is enabled;
- provider/object/scope mismatch against Document Identity;
- inventory evidence from another case or source scope;
- migration mappings that do not exactly match the supplied inventory evidence;
- empty provider/object/document identifiers;
- filename-only identity claims.

## Security boundary

The migration layer is downstream of the Case Registry and remains case-scoped. It must never discover CASE-001 by searching Drive for a taxpayer name, filename, or folder name.

A future executor must require explicit authorization and a human-controlled consequential-action gate before any physical mutation.

## Tests

`tests/unit/test_case001_migration.py` contains the structural migration tests plus integration-boundary tests for Document Identity and Inventory Evidence.

The test suite covers:

- CASE-001 / 2024 plan creation;
- validated plan status;
- logical document preservation;
- duplicate and scope mismatch rejection;
- unregistered and wrong-year rejection;
- successful validation against registered Document Identity;
- rejection of unknown logical document IDs;
- rejection of source-object identity mismatch;
- successful validation against matching Inventory Evidence;
- rejection of Inventory Evidence from another source scope.

The tests are deterministic and non-mutating. They do not prove live Drive migration safety.

## Acceptance criteria

The compatibility baseline is accepted when unit tests prove:

- correct CASE-001 / 2024 plan creation;
- source and target scope are explicit;
- case identity is preserved;
- tax period is preserved;
- document logical identity is preserved;
- Document Identity is authoritative when connected;
- Inventory Evidence can act as an exact migration preflight boundary;
- duplicate/ambiguous mappings fail closed;
- no physical storage mutation is performed.

Physical migration remains a separate, later stage and is not implied by successful unit tests.
