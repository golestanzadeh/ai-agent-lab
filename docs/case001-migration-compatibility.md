# CASE-001 Migration / Compatibility Layer

**Status:** Implemented design baseline; no physical Drive migration performed
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

The compatibility layer exists to bridge these layouts without changing the case identity or source-document identity. It deliberately separates **migration planning** from **physical Drive mutation**.

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
10. Physical Drive writes are outside this first implementation.

## Compatibility model

The layer treats the legacy scope as a temporary alias for the same registered case. It does not create a second `CaseRecord`.

```text
Legacy CASE-001 scope
        │
        │ compatibility mapping
        ▼
     CASE-001
     tax_period=2024
        │
        ▼
Target 2024 CASE-001 scope
```

The mapping is case-scoped and explicit. It is not a Drive-wide discovery mechanism.

## Migration phases

### Phase 0 — Design

Define source scope, target scope, invariants, object-identity rules, failure behavior, and rollback requirements.

### Phase 1 — Prepare

Create a deterministic migration plan from explicit scope references. No Drive mutation occurs.

### Phase 2 — Validate

Validate the plan and its object mappings before any future write operation. The current implementation supports deterministic validation of the plan structure and identity invariants.

### Phase 3 — Execute

Future implementation only. Physical Drive create/move/rename operations require an explicit migration command and separate verification. They are not part of the current layer.

### Phase 4 — Verify

Future live verification must prove that every expected source object remains reachable, every document identity is preserved, and the target structure is correct.

### Phase 5 — Commit / Retire Legacy Alias

Only after successful verification may the legacy compatibility alias be retired.

## Rollback principle

The first implementation is intentionally non-mutating, so its rollback is trivial: discard the generated migration plan. A future physical migration must be designed so that a failed partial operation cannot be mistaken for a completed migration.

## Document Identity relationship

Migration must operate on source object identity, not filenames.

For each source document:

```text
provider + original object ID
          ↓
existing document_id
          ↓
new target parent/scope
```

A copied object with a new provider object ID is not automatically the same source object. Such a mapping requires explicit migration provenance and must preserve the old logical `document_id` only when the migration process can prove the relationship.

## Current runtime

`src/agent_lab/case001_migration.py` implements a deterministic preparation/validation layer using opaque storage-scope references.

It:

- requires explicit source and target scope references;
- requires the expected `case_id` and tax period;
- produces a deterministic migration plan;
- validates that the plan does not change case identity or tax period;
- validates object mappings when supplied;
- rejects duplicate source-object mappings;
- rejects mappings that attempt to change a logical document ID;
- performs no Drive reads or writes;
- performs no global search;
- does not copy or move source documents.

## Object mapping contract

A future execution manifest may contain mappings such as:

```text
source_provider
source_object_id
logical_document_id
source_scope_ref
target_scope_ref
```

The compatibility layer accepts these as identity assertions to validate, not as permission to mutate Drive.

The following are invalid:

- one source object mapped to multiple logical documents;
- one logical document mapped from multiple unrelated source objects;
- source case scope different from the plan source scope;
- target case different from `CASE-001`;
- empty provider/object/document identifiers;
- filename-only identity claims.

## Security boundary

The migration layer is downstream of the Case Registry and must remain case-scoped. It must never discover CASE-001 by searching Drive for a taxpayer name, filename, or folder name.

A future executor must require explicit authorization and a human-controlled consequential-action gate before any physical mutation.

## Acceptance criteria

The compatibility baseline is accepted when unit tests prove:

- correct CASE-001 / 2024 plan creation;
- source and target scope are explicit;
- case identity is preserved;
- tax period is preserved;
- document logical identity is preserved;
- duplicate/ambiguous mappings fail closed;
- no physical storage mutation is performed.

Physical migration remains a separate, later stage and is not implied by successful unit tests.
