# Document Identity

**Status:** Implemented and unit-verified baseline
**Last updated:** 2026-09-06

## Purpose

Document Identity defines how the system recognizes one source document across repeated inventories, processing runs, category assignments, evidence records, and future content-processing stages.

The goal is to prevent a filename, Drive object ID, or processing run from becoming an accidental identity. A document must remain traceable to its exact source object while allowing the physical storage provider, metadata, and derived representations to evolve.

## Core principles

1. **Source identity is not filename identity.** Names can change and are not unique.
2. **Provider object ID is not sufficient as the long-term identity.** It is a provider-specific locator and may not survive migration or replacement.
3. **Case scope is mandatory.** A document identity is meaningful only inside a validated `case_id` unless a future global document registry explicitly defines otherwise.
4. **Original source remains immutable.** Derived content, OCR, normalized facts, classifications, and reports never replace the source document.
5. **Identity must support repeated observation.** The same source object observed in multiple runs should resolve to the same logical document identity.
6. **Replacement must be detectable.** A new file with the same name is not automatically the same document.
7. **Evidence requires provenance.** Every extracted fact must be traceable through the document identity to the source observation.
8. **Ambiguity fails closed.** The system must not merge documents merely because they look similar.

## Three-level identity model

The design separates three concepts:

```text
Document Identity
    │
    ├── Source Object Identity
    │     ├── provider
    │     ├── provider_object_id
    │     └── case_id / exact scope
    │
    ├── Source Version Identity
    │     ├── observed metadata
    │     ├── content fingerprint when content is available
    │     └── observation timestamp / run_id
    │
    └── Derived Representation Identity
          ├── extraction version
          ├── OCR/parser/model version
          └── derived artifact reference
```

### 1. Logical Document ID

A deterministic internal identifier such as `DOC-CASE-001-00000001` is assigned by the case-scoped Document Identity registry. It represents the logical source document within one case.

It is not derived from the filename and is not exposed as a substitute for the source provider object ID.

### 2. Source Object Identity

The initial provider locator is `case_id + provider + provider_object_id`. For Google Drive, `provider_object_id` is the Drive file ID. The exact case scope remains authoritative through the Case Registry and Case-Scoped Resolver.

A provider object ID must never be accepted without validating that it belongs to the requested case scope.

### 3. Source Version Identity

A source document can change while retaining the same provider object ID. Therefore each meaningful observed version must be distinguishable.

Before content access is available, the system records metadata observations containing the stable provider object ID and relevant metadata. This is not a cryptographic content identity.

After authorized content access is introduced, the system should additionally calculate a content fingerprint for the exact bytes when technically appropriate. The content fingerprint identifies the observed content, not the legal meaning of the document.

## Initial metadata identity record

The implementation supports:

```text
DocumentRecord
├── document_id
├── case_id
├── source_provider
├── source_object_id
├── source_scope_ref
├── current_name
├── mime_type
├── parent_ids
├── is_folder
├── first_seen_run_id
├── last_seen_run_id
├── first_seen_at
├── last_seen_at
├── source_status
├── content_fingerprint (optional until content access exists)
└── schema_version
```

`source_status` distinguishes `ACTIVE`, `MISSING`, `TRASHED`, `REPLACED`, and `UNRESOLVED`.

The current metadata-only implementation does not infer `REPLACED` from a filename change. Replacement requires stronger evidence and remains a later lifecycle concern.

## Identity resolution rules

### Rule A — Existing source object

If the same `(case_id, provider, source_object_id)` is observed again within the same case, resolve it to the existing `document_id`.

### Rule B — Same name, different object

A different provider object ID with the same filename is a new candidate document, not an update to the old document.

### Rule C — Renamed object

A changed filename on the same provider object ID does not create a new document. The logical document remains the same, while metadata observations record the change.

### Rule D — Different case

The same provider object ID must never be assumed to belong to another case. Case scope must be resolved independently. A cross-case access attempt fails closed.

### Rule E — Migration/provider change

A migrated source is not automatically merged across providers. A future migration process may explicitly link the new source record to the old `document_id`, with provenance and audit evidence.

### Rule F — Content duplicate

Two different source objects with identical bytes are not automatically one document. Their independent provenance must be preserved.

## Implemented runtime

`src/agent_lab/document_identity.py` implements the deterministic, case-scoped in-memory registry.

It assigns stable logical IDs, resolves repeated observations by `(case_id, provider, source_object_id)`, preserves identity across filename changes, separates different source objects with the same name, records source observations with `run_id` provenance, validates case/run ownership, and updates the case's `documents_ref` state reference. It does not read document content or perform global discovery.

## Inventory relationship

The verified pipeline boundary is:

```text
Case Registry
    ↓
Case-Scoped Drive Resolver
    ↓
Google Drive Metadata Adapter
    ↓
Document Inventory
    ↓
Document Identity Resolver
    ↓
Document Registry / Source History
    ↓
Inventory Evidence
```

Inventory Evidence now accepts stable Document Identity references. It remains a snapshot/evidence object and does not become the primary document identity registry.

## Provenance relationship

```text
Inventory Evidence
   ↓
Document Identity
   ↓
Source Observation
   ↓
Provider + Object ID + Case Scope
   ↓
Original Source Document
```

Future extracted facts and derived artifacts must reference the relevant document identity and processing run.

## Immutability and history

The source file itself is not modified by identity management. Each inventory observation produces a `SourceObservation`, retaining metadata and run provenance. The logical `DocumentRecord` maintains current metadata while observation history preserves prior observed states.

## Collision and ambiguity policy

The following must never silently merge:

- same filename, different object ID;
- same content, different source object;
- different provider object IDs after migration;
- ambiguous cross-case references;
- an object whose ancestry cannot be validated;
- an object observed as trashed/missing and a newly discovered object with the same name.

When identity cannot be established deterministically, the workflow must escalate rather than guess.

## Security boundary

Document Identity is downstream of case isolation, not a replacement for it. The resolver receives a validated `case_id`, validates the associated run, and operates only on inventory observations supplied within that case scope. Global document search by filename, content, taxpayer name, or hash is prohibited in the initial architecture.

## Idempotency

Repeated observation of the same source object in the same case is idempotent at the logical identity level:

```text
same case + same provider + same object ID
        ↓
existing document_id
```

A repeated observation creates a new source observation, but not a second logical document solely because the run is new.

## Verification

The implementation was locally verified on 2026-09-06 with:

```text
13 passed in 0.28s
```

The combined suite covered the Document Identity registry and Inventory Evidence integration, including logical identity idempotency, same-name/different-object separation, rename preservation, cross-case rejection, case/run scoping, case-state linkage, audit linkage, and inventory-evidence idempotency.

This is unit verification only. It does not prove durable persistence, production authorization, content extraction, legal qualification, or final tax correctness.

## What Document Identity does not decide

Document Identity does not determine tax relevance, person ownership of expenses, tax category, deductibility, legal qualification, final tax calculation, or legal equivalence of documents. Those decisions belong to later evidence, attribution, research, analysis, and calculation layers.

## Next boundary

After this verified baseline, the next architecture task is controlled migration/compatibility handling for the existing CASE-001 structure. Content access and content fingerprints remain downstream of that boundary.
