# Document Identity

**Status:** Design baseline approved for implementation planning
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

A deterministic internal identifier such as:

`DOC-CASE-001-00000001`

is assigned by the case-scoped Document Identity registry. It represents the logical source document within one case.

It is not derived from the filename and is not exposed as a substitute for the source provider object ID.

### 2. Source Object Identity

The initial provider locator is:

```text
case_id
provider
provider_object_id
```

For Google Drive, `provider_object_id` is the Drive file ID. The exact case scope remains authoritative through the Case Registry and Case-Scoped Resolver.

A provider object ID must never be accepted without validating that it belongs to the requested case scope.

### 3. Source Version Identity

A source document can change while retaining the same provider object ID. Therefore each meaningful observed version must be distinguishable.

Before content access is available, the system may record a **metadata observation** containing the stable provider object ID and relevant metadata. This is not a cryptographic content identity.

After authorized content access is introduced, the system should additionally calculate a content fingerprint for the exact bytes when technically appropriate. The content fingerprint identifies the observed content, not the legal meaning of the document.

## Initial metadata identity record

The first implementation should support at least:

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

`source_status` should distinguish at least:

- `ACTIVE`
- `MISSING`
- `TRASHED`
- `REPLACED`
- `UNRESOLVED`

The first implementation should not infer `REPLACED` merely from a changed filename. Replacement requires stronger evidence, such as a provider-level object change, content fingerprint difference, or explicit source observation rules.

## Identity resolution rules

### Rule A — Existing source object

If the same `(case_id, provider, source_object_id)` is observed again within the same case, resolve it to the existing `document_id`.

### Rule B — Same name, different object

A different provider object ID with the same filename is a **new candidate document**, not an update to the old document.

### Rule C — Renamed object

A changed filename on the same provider object ID does not create a new document. The logical document remains the same, while metadata history records the observation change.

### Rule D — Different case

The same provider object ID must never be assumed to belong to another case. Case scope must be resolved independently. A cross-case access attempt fails closed.

### Rule E — Migration/provider change

If a source document is migrated from Google Drive to another storage provider, the new provider locator is not automatically a new logical document. A future migration process may explicitly link the new source record to the old `document_id`, with provenance and audit evidence. Automatic cross-provider merging is prohibited.

### Rule F — Content duplicate

Two different source objects with identical bytes are not automatically one document. They may be duplicate copies, and their independent provenance must be preserved. A future duplicate-analysis layer may identify them as content-equivalent without collapsing their source identities.

## Inventory relationship

The metadata-only inventory currently produces provider object metadata. Document Identity should consume those observations after scope validation:

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

The existing Inventory Evidence record remains a snapshot/evidence object. It must not become the primary document identity registry.

## Provenance relationship

The minimum provenance chain should eventually be:

```text
Evidence / Fact
   ↓
Document Identity
   ↓
Source Version / Observation
   ↓
Provider + Object ID + Case Scope
   ↓
Original Source Document
```

A derived artifact such as OCR text, parsed JSON, or a normalized fact must reference the source document identity and the processing run that produced it.

## Immutability and history

The source file itself is not modified by identity management.

Identity metadata should be treated as historical state rather than repeatedly overwriting the only record. At minimum, changes to name, MIME type, parent scope, source status, and content fingerprint must be attributable to an observation/run.

The system should eventually maintain a source-observation history so an auditor can answer:

- When was this document first seen?
- In which case?
- Under which provider object ID?
- What metadata was observed at each run?
- Did the object change?
- Which derived artifacts were produced from which observed version?
- Which evidence and calculations depend on it?

## Collision and ambiguity policy

The following must never silently merge:

- same filename, different object ID;
- same content, different source object;
- different provider object IDs after migration;
- ambiguous cross-case references;
- an object whose ancestry cannot be validated;
- an object observed as trashed/missing and a newly discovered object with the same name.

When identity cannot be established deterministically, the record enters `UNRESOLVED` and the workflow escalates rather than guessing.

## Security boundary

Document Identity is downstream of case isolation, not a replacement for it.

The resolver must receive a validated `case_id`, and every source object lookup must pass through the case-scoped storage boundary. A global document search by filename, content, taxpayer name, or hash is prohibited in the initial architecture.

## Idempotency

Repeated observation of the same source object in the same case must be idempotent:

```text
same case + same provider + same object ID
        ↓
existing document_id
```

A repeated inventory run may create a new observation record and a new inventory evidence snapshot, but it must not create a second logical document solely because the run is new.

## What Document Identity does not decide

Document Identity does not determine:

- whether a document is tax-relevant;
- which person owns an expense;
- which tax category applies;
- whether an expense is deductible;
- the legal qualification of a document;
- the final tax calculation;
- whether two documents are legally equivalent.

Those decisions belong to later evidence, attribution, research, analysis, and calculation layers.

## Implementation sequence

1. Define deterministic `DocumentRecord` and source-observation models.
2. Implement a case-scoped in-memory Document Identity Registry.
3. Resolve inventory items by `(case_id, provider, source_object_id)`.
4. Record metadata observations without reading document content.
5. Add idempotency and collision tests.
6. Add cross-case isolation tests.
7. Connect Document Identity to Inventory Evidence.
8. Only after this baseline is verified, introduce controlled document-content access and content fingerprints.

## Acceptance criteria for the first implementation

- one logical `document_id` per source object within a case;
- repeated observations are idempotent;
- same-name/different-object documents remain separate;
- renamed same-object documents remain the same logical document;
- cross-case access fails closed;
- source provider and object locator are retained;
- observation/run provenance is retained;
- no document content is required for the metadata-only phase;
- no global Drive search is used;
- ambiguous identity is represented explicitly rather than guessed;
- original source documents remain untouched;
- tests demonstrate all material identity rules.

## Current boundary

This is a design baseline. The Document Identity runtime is **not yet implemented or verified**.
