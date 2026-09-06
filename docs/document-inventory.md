# Document Inventory and Intake Architecture

Status: **approved baseline**

Last verified: 2026-09-06

## Purpose

Document Inventory is the first controlled processing stage for a real tax case. Its job is to establish exactly which source documents are present in the approved case location before document content is interpreted for tax purposes.

It is an intake/inventory component, not a tax-analysis agent.

## Source of truth

For CASE-001, the private source documents remain in Google Drive:

```text
Google Drive/
└── AI-Tax-Agent/
    └── Cases/
        └── CASE-001/
            ├── Documents/      <- source documents
            ├── Evidence/       <- derived evidence, later stage
            ├── Calculations/   <- derived calculations, later stage
            ├── Reports/        <- generated reports, later stage
            └── Audit/          <- audit records, later stage
```

GitHub stores code, schemas, documentation, tests, and evaluation assets. Real taxpayer documents and extracted sensitive content must not be stored in GitHub.

## Intake boundary

The first inventory pass MUST:

1. authenticate using the approved local OAuth credential;
2. resolve the approved case folder and its `Documents` child folder;
3. enumerate direct children of `Documents` that are not trashed;
4. retrieve metadata only;
5. record an inventory snapshot;
6. detect obvious inventory anomalies such as unsupported file types, duplicate names, or unexpected subfolders;
7. stop before downloading or interpreting document content.

Google Drive API `files.list` supports parent-based queries such as `'folderId' in parents`, pagination through `nextPageToken`, and explicit field selection. The implementation must use these mechanisms rather than scanning the user's entire Drive. See the official Drive API documentation for search and partial-response behavior.

## Minimum metadata model

Each inventory item should have, where available:

- stable Drive file ID;
- filename;
- MIME type;
- size in bytes;
- created time;
- modified time;
- parent ID;
- trashed status;
- Drive version when available;
- checksum/hash when safely obtainable without unnecessary content exposure;
- inventory timestamp;
- case ID;
- source location identifier.

The exact schema must distinguish **source metadata** from any later classification or interpretation.

## Separation of concerns

The pipeline is intentionally separated:

```text
Drive Connector
      ↓
Case/Folder Resolver
      ↓
Document Inventory
      ↓
Inventory Validation
      ↓
Document Processing
      ↓
Evidence Extraction
      ↓
Fact Normalization/Reconciliation
      ↓
Tax Analysis
```

Document Inventory must not infer tax facts from filenames. For example, a filename containing `Spenden` is not by itself evidence that a deductible donation exists.

## Deterministic-first rule

Inventory is deterministic code, not an LLM agent.

An LLM may later assist with document classification or extraction, but only after the source document has been identified, retrieved under explicit permissions, and passed through the evidence/provenance pipeline.

## Read/write permissions

### Inventory stage may

- read Drive metadata for the approved case path;
- create or update an inventory record in the approved case artifact area once that artifact-storage contract is implemented;
- emit structured logs/audit events.

### Inventory stage must not

- modify, rename, move, delete, or upload source documents;
- submit anything to a tax authority;
- infer tax deductions;
- alter tax-case facts;
- silently access unrelated Drive content;
- store source-document contents in GitHub;
- expose OAuth credentials or tokens in logs.

## Privacy and minimization

The inventory stage must request only the metadata fields required for its task. Google recommends explicit field masks/partial responses to avoid unnecessary data transfer. The implementation must therefore avoid requesting file content, permissions, owners, or other sensitive metadata unless a later requirement explicitly justifies it.

## Pagination and completeness

Inventory must be complete for the selected folder. The implementation must continue through every `nextPageToken` until none remains. A single page is not considered a complete inventory unless the API explicitly confirms no continuation token exists.

The resulting inventory should record the number of enumerated items and the timestamp of the snapshot.

## Idempotency

Running inventory repeatedly against an unchanged folder should produce the same logical set of source items. Stable Drive file IDs, rather than filenames alone, are the primary identity key.

A renamed document therefore remains the same source item, while a new Drive file receives a new identity even if it has the same filename.

## Failure states

The inventory stage must fail closed when:

- authentication is unavailable;
- the approved case folder cannot be resolved;
- the `Documents` folder cannot be resolved uniquely;
- Drive returns an authorization error;
- pagination cannot be completed;
- required metadata cannot be retrieved reliably.

A partial inventory must never be presented as a complete inventory.

## Current CASE-001 observation

On 2026-09-06, the user verified the local Drive mirror contains 15 PDF files in `CASE-001/Documents`, totaling approximately 4.25 MB. This is a human-provided observation only. The authoritative machine inventory must be produced by the Drive API and must not assume the local filesystem listing is identical to the Drive API view.

## Acceptance criteria for the first implementation

The first implementation is accepted only when it can:

- authenticate with the existing OAuth flow;
- resolve `AI-Tax-Agent/Cases/CASE-001/Documents` without scanning unrelated Drive content;
- enumerate all direct child files using pagination;
- return deterministic metadata for every item;
- report total item count;
- distinguish folders from documents;
- perform no source-document mutation;
- perform no tax interpretation;
- pass automated tests using mocked Drive responses;
- produce a reproducible inventory snapshot suitable for later evidence provenance.
