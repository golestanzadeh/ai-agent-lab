# Document Inventory and Intake Architecture

Status: **approved baseline / first implementation ready**

Last updated: 2026-09-06

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
2. use the exact CASE-001 `Documents` scope registered for the case;
3. enumerate direct children of `Documents` that are not trashed;
4. retrieve metadata only;
5. produce an inventory snapshot;
6. stop before downloading or interpreting document content.

No Drive-wide search is permitted. The exact CASE-001 `Documents` folder ID must be supplied by the local case bootstrap/registry layer. It must not be discovered by searching Drive for a taxpayer or filename.

## Minimum metadata model

The first implementation uses the verified provider-neutral storage metadata contract:

- stable Drive object ID;
- filename;
- MIME type;
- parent IDs;
- folder/document flag.

The inventory additionally records:

- `case_id`;
- inventory timestamp;
- document count;
- folder count.

The schema deliberately separates source metadata from later classification and interpretation. Additional metadata such as size, created time, modified time, checksum, or Drive version may be added when justified by a later requirement.

## Runtime implementation

`src/agent_lab/document_inventory.py` implements `DocumentInventoryService` over the existing `CaseScopedStorageAdapter` contract.

It:

- requires a `case_id`;
- delegates enumeration to the case-scoped storage boundary;
- sorts inventory items deterministically by case-insensitive name and object ID;
- does not read document content;
- does not perform Drive-wide discovery;
- distinguishes documents from folders.

`tests/unit/test_document_inventory.py` provides the initial deterministic contract tests.

`scripts/case001_metadata_inventory.py` is the local CASE-001 execution harness. It requires the exact `CASE_001_DOCUMENTS_ROOT_ID` environment variable and uses the existing local OAuth flow. It prints the metadata-only inventory as JSON and does not modify Drive.

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
- later create or update an inventory record in the approved case artifact area once that artifact-storage contract is implemented;
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

The inventory stage must request only the metadata fields required for its task. The current Google Drive adapter therefore requests IDs, names, MIME types, parents, and trashed state only. Content, permissions, owners, and other sensitive metadata are not requested.

## Pagination and completeness

Inventory must be complete for the selected folder. The Google Drive adapter continues through every `nextPageToken` until none remains. A single page is not considered a complete inventory unless the API explicitly confirms no continuation token exists.

## Idempotency

Running inventory repeatedly against an unchanged folder should produce the same logical set of source items. Stable Drive object IDs, rather than filenames alone, are the primary identity key.

The current snapshot timestamp is intentionally run-specific, while the logical item set is deterministic.

## Failure states

The inventory stage must fail closed when:

- authentication is unavailable;
- the exact case scope cannot be resolved;
- Drive returns an authorization error;
- pagination cannot be completed;
- required metadata cannot be retrieved reliably.

A partial inventory must never be presented as a complete inventory.

## Current CASE-001 observation

On 2026-09-06, the user reported that the local Drive mirror contains 15 PDF files in `CASE-001/Documents`, totaling approximately 4.25 MB. This is a human-provided observation only. The authoritative machine inventory must be produced by the Drive API and must not assume the local filesystem listing is identical to the Drive API view.

## Acceptance criteria for the first implementation

The implementation is ready for live execution when it can:

- authenticate with the existing OAuth flow;
- use the exact registered CASE-001 `Documents` scope without scanning unrelated Drive content;
- enumerate all direct children using pagination;
- return deterministic metadata for every item;
- report total document and folder counts;
- perform no source-document mutation;
- perform no tax interpretation;
- pass automated unit tests;
- produce a structured inventory snapshot suitable for later evidence provenance.

The live CASE-001 inventory itself is **not yet verified**. The next verification is the local execution of `scripts/case001_metadata_inventory.py` against the exact CASE-001 `Documents` folder ID.
