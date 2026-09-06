# Document Processing & Tax Categorization Contract

## Status

Approved architecture contract for CASE-001 and future tax cases.

This document defines how source documents move from deterministic intake into evidence extraction and tax-category organization. It does not authorize substantive tax conclusions before evidence, party attribution, tax-year attribution, and applicable-law verification are complete.

## 1. Purpose

The document-processing layer transforms an immutable source-document inventory into structured, traceable evidence and a dynamic tax-category index that makes relevant material easy to retrieve for later analysis, optimization, calculation, and audit.

The design is deterministic-first. An LLM may assist with interpretation where necessary, but source identity, references, provenance, state transitions, and storage boundaries must remain explicit and machine-checkable.

## 2. Source boundary

Original tax documents are stored under the case `Documents/` directory and are treated as immutable source material.

The processing system must not silently:

- rename source files;
- move source files;
- overwrite source files;
- delete source files;
- replace a source document with an extracted or generated artifact.

Every downstream record must retain a stable reference to its source document.

## 3. Processing pipeline

```text
Document Inventory
      ↓
Document Identity & Metadata
      ↓
Content Processing
      ↓
Evidence / Fact Extraction
      ↓
Fact Normalization
      ↓
Party Attribution
      ↓
Tax-Year Attribution
      ↓
Tax-Relevance Analysis
      ↓
Candidate Tax Categories
      ↓
Classification Decision
      ↓
Category Index / Record
      ↓
Provenance + Audit
```

No stage may be skipped merely because a filename appears informative.

## 4. Tax categories

The following categories are default starting categories, not a closed taxonomy:

1. `Einkommensnachweise`
2. `Werbungskosten`
3. `Haushaltsnahe_Dienstleistungen`
4. `Sonderausgaben_Versicherungsbeitraege`
5. `Aussergewoehnliche_Belastungen`
6. `Kinder`

The system may create additional categories when the case requires them. Category creation must be explicit and auditable.

Examples of possible future categories are illustrative only; they must not be created merely because they are listed in documentation.

## 5. Category semantics

A tax category is an organizational and retrieval construct. It is not itself a legal qualification or a final deduction decision.

Therefore:

```text
Category ≠ Tax Deduction
Category ≠ Legal Qualification
Category ≠ Final Tax Decision
```

A document classified into a category means that the document is relevant or potentially relevant to that area and should be available for subsequent tax analysis.

## 6. Many-to-many classification

A document may belong to multiple categories.

Example:

```text
Document A
 ├── Werbungskosten
 └── Haushaltsnahe_Dienstleistungen
```

The system must not force every document into exactly one category.

Category membership is represented by references/records rather than by moving the original file between folders.

## 7. Category confidence and decision state

Each classification must have an explicit state:

- `CONFIRMED` — sufficient evidence supports the classification for its stated purpose.
- `CANDIDATE` — plausible relevance exists, but evidence or legal context is insufficient for confirmation.
- `UNRESOLVED` — conflicting, missing, or ambiguous evidence prevents a reliable classification.

An unresolved classification must not be silently converted into a confirmed one.

## 8. Party attribution

Every material document or extracted fact must be attributable to one of:

- a specific case party;
- multiple case parties;
- shared household context;
- `UNKNOWN_PENDING_VERIFICATION`.

Filename-based attribution alone is insufficient.

Shared expenses must not automatically be assigned 50/50.

Where party attribution is material and ambiguous or contradictory, the affected workflow must stop or escalate rather than silently choosing a party.

## 9. Tax-year attribution

Tax-year relevance is an explicit attribute.

A document date does not automatically establish that the document applies to the entire tax year.

The system must support:

- explicit tax-year attribution;
- effective intervals where relevant;
- unknown/pending verification states;
- conflicting temporal evidence.

## 10. Category record

A category record should contain, at minimum:

```json
{
  "document_id": "stable-source-document-id",
  "category_id": "Werbungskosten",
  "party_refs": ["party-id"],
  "tax_year": 2024,
  "classification_state": "CANDIDATE",
  "confidence": 0.94,
  "reason": "Document evidence indicates a potentially deductible employment-related expense.",
  "evidence_refs": ["evidence-id"],
  "source_refs": ["document-id"],
  "created_at": "timestamp",
  "classifier": "component-or-agent-identifier",
  "review_required": true
}
```

The exact schema is implementation work and must be versioned when finalized.

## 11. Evidence and provenance

Every material classification must be traceable to evidence.

At minimum the lineage must support:

```text
Category Record
    ↓
Evidence / Fact
    ↓
Source Document
    ↓
Original File Metadata
```

A model-generated statement without a source reference is not sufficient evidence for a consequential tax decision.

## 12. Drive organization

The case Drive structure contains:

```text
CASE-001/
├── Documents/
├── Evidence/
├── Tax_Categories/
├── Calculations/
├── Reports/
└── Audit/
```

`Documents/` is the immutable source boundary.

`Evidence/` stores structured extracted facts and their provenance.

`Tax_Categories/` provides a human- and machine-accessible organization layer for category-specific records/references.

`Calculations/`, `Reports/`, and `Audit/` remain downstream outputs and must not be treated as substitutes for source evidence.

## 13. No unnecessary PDF duplication

The system should not create redundant copies of source PDFs merely to represent category membership.

Category membership should normally point to the original document through stable IDs/references. Generated category-specific artifacts are allowed only when they provide a concrete operational value and are themselves traceable.

## 14. Dynamic category creation

When processing reveals a tax-relevant area not represented by the current category set, the system may propose or create a new category.

The event must record:

- category identifier;
- reason for creation;
- triggering evidence/documents;
- creator component/agent;
- timestamp;
- whether human review is required.

A category must not be created solely because a model invents a plausible tax concept without supporting case evidence.

## 15. Audit requirements

The following events are consequential and should be auditable:

- classification created;
- classification changed;
- classification removed;
- category created;
- category renamed or deprecated;
- party attribution changed;
- tax-year attribution changed;
- human review requested;
- human decision recorded.

Audit records must preserve enough information to reconstruct what was known and why a decision was made at that time.

## 16. Human control

Human approval is required whenever classification uncertainty could materially affect a tax calculation, filing position, or optimization recommendation and the available evidence does not justify an automated confirmation.

The system must prefer an explicit unresolved state over fabricated certainty.

## 17. Non-goals

This contract does not yet define:

- OCR implementation;
- PDF parsing implementation;
- LLM/provider selection;
- final legal-tax classification rules;
- final calculation formulas;
- final category JSON schema;
- production orchestration;
- electronic submission.

Those decisions belong to later implementation and architecture stages and must be based on evidence and tests.

## 18. Acceptance criteria for this contract

The design is considered correctly implemented only when the system can demonstrate that:

1. source documents remain unchanged;
2. every processed document has a stable source reference;
3. one document can have multiple category memberships;
4. categories can be extended without changing the source-document structure;
5. classification state and confidence are explicit;
6. party and tax-year attribution are explicit;
7. material classifications have evidence/provenance links;
8. ambiguous material cases are escalated rather than silently resolved;
9. category changes are auditable;
10. category organization does not become the source of truth for legal conclusions.

## 19. Implementation order

The next executable work remains:

1. complete the deterministic Drive Connector and Document Inventory;
2. validate the live CASE-001 source inventory;
3. define the concrete document/evidence schemas;
4. implement content processing on controlled test fixtures;
5. implement classification and category indexing;
6. add party/tax-year attribution validation;
7. add provenance and audit events;
8. run the first controlled CASE-001 categorization test.
