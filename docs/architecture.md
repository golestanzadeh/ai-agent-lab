# Architecture

Status: **approved baseline architecture; detailed implementation evolves by phase**

Last verified: 2026-09-06

This architecture is designed for a long-lived German tax-assistance platform that starts with one user and CASE-001 but can grow to many natural persons, legal entities, tax periods, and concurrent cases without architectural replacement.

## 1. Architectural principles

- GitHub is the durable Source of Truth for code, documentation, tests, schemas, decisions, and verified development state.
- Google Drive is the initial private source-data store for real tax cases.
- Real taxpayer documents and unnecessary private data must never be committed to GitHub.
- Source documents are authoritative evidence; LLM output is never a source of truth by itself.
- Deterministic processing is preferred wherever the task can be made deterministic.
- Agents are introduced only where reasoning, planning, challenge, or coordination creates measurable value.
- Every consequential conclusion must be traceable to source evidence, applicable rules, calculations, and approvals.
- The system must fail closed when required evidence or current authoritative law cannot be verified.
- Human approval is mandatory for consequential external actions and other explicitly designated judgment points.
- The architecture must support reproducibility, auditability, privacy, and evaluation from the beginning.
- **Case isolation is a security and correctness boundary, not merely an Agent instruction.**

## 2. System boundary

```text
User / External Request
        ↓
Identity + Case Resolution
        ↓
Case-Scoped Orchestration
        ↓
Case-Scoped Data Access
        ↓
Document Inventory
        ↓
Document Processing / Evidence Extraction
        ↓
Fact Normalization / Reconciliation
        ↓
Tax Categorization
        ↓
Research / Analysis / Optimization
        ↓
Challenge / Audit / QA
        ↓
Human Approval Gate
        ↓
Reports / Controlled Submission
```

Cross-cutting layers:

```text
Case Registry | Person/Entity Registry | Case State
Evidence / Provenance | Calculations | Audit / Observability
Security / Permissions | Versioning / Reproducibility | Evaluation
```

Not every box becomes an independent Agent. Agent count is not an architectural objective.

## 3. Case-first identity architecture

The fundamental operational unit is a **case**, not a Drive folder and not a document.

Three identities are distinct:

```text
person_id / entity_id = persistent taxpayer or legal-entity identity
              ↓
tax_period = tax period to which a case belongs
              ↓
case_id = identity of one concrete case for that period
```

`case_id` is mandatory in every operation that reads or writes case data.

A person/entity can therefore have many cases:

```text
PERSON-00042
├── 2020 → CASE-2020-....
├── 2021 → CASE-2021-....
├── ...
└── 2026 → CASE-2026-....
```

The model must support natural persons and legal entities. `tax_period` is a domain concept, not merely a folder name, and must be capable of representing calendar years and future fiscal-period variants.

## 4. Multi-year Drive organization

The target long-term storage structure is:

```text
AI-Tax-Agent/
├── Tax_Years/
│   ├── 2020/
│   │   └── Cases/
│   │       ├── CASE-2020-0001/
│   │       └── ...
│   ├── 2021/Cases/
│   ├── 2022/Cases/
│   ├── 2023/Cases/
│   ├── 2024/Cases/
│   ├── 2025/Cases/
│   └── 2026/Cases/
├── Case_Registry/
├── Person_Registry/
├── Entity_Registry/
├── Templates/
└── System/
```

Each case remains internally isolated:

```text
CASE-YYYY-NNNN/
├── Documents/      <- immutable source boundary
├── Evidence/       <- derived, source-linked evidence
├── Tax_Categories/ <- dynamic organizational/retrieval layer
├── Calculations/   <- validated calculation artifacts
├── Reports/        <- generated outputs
└── Audit/          <- run records, decisions, approvals
```

Tax-year grouping is primarily for human organization and discovery. Registry-based identity is authoritative for resolving cases. Existing CASE-001 storage is not automatically migrated until a migration strategy is implemented and verified.

## 5. Registries

### Case Registry

The Case Registry is the authoritative mapping between persistent taxpayer/entity identity, tax period, case identity, lifecycle state, and exact storage scope.

Minimum conceptual fields:

```text
case_id
person_id / entity_id
tax_period
case_type
assessment_state
lifecycle_status
drive_case_folder_reference
last_run_id
system_version
schema_version
```

### Person / Entity Registry

Persistent identities allow reliable retrieval across tax years without relying on filenames or broad Drive searches. The registry may contain approved lookup identifiers, display information, and case mappings. Sensitive tax identifiers must only be retained where legally and technically appropriate.

Registries are indexes and identity maps. They do not replace source documents or evidence.

## 6. Case resolution and discovery

The resolution path is:

```text
request
  ↓
identity / tax-period lookup
  ↓
Case Registry
  ↓
validated case_id
  ↓
exact case-folder reference
  ↓
case-scoped connector
```

Cases must be discoverable by multiple controlled keys, such as:

- case ID;
- person/entity ID;
- approved name/display name;
- tax period;
- applicable tax identifiers where appropriate;
- case type;
- lifecycle status.

Names and sensitive identifiers are lookup keys, not folder-name conventions.

A request for a person's cases from 2020–2026 resolves that person's persistent ID through the registry, obtains the relevant case IDs, and then reads each case separately. It must never scan all Drive documents and ask a model to guess ownership.

## 7. Mandatory case isolation

No Agent, tool, pipeline stage, model, or connector may discover or access tax-case data outside its validated `case_id` scope.

Conceptually permitted APIs:

```text
list_documents(case_id)
get_document(case_id, document_id)
read_evidence(case_id, evidence_id)
write_report(case_id, ...)
```

Conceptually prohibited case-data APIs:

```text
list_all_tax_documents()
search_drive_for_taxpayer_name()
list_documents()
```

The deterministic application/connector layer must enforce the boundary. Prompts are not a security mechanism.

If case resolution fails, if scope is ambiguous, or if an object is outside the validated case scope, the operation must fail closed or enter an explicit unresolved state.

Cross-case contamination is a security and correctness failure and must have dedicated automated tests.

## 8. Case execution model

Every processing execution receives a unique `run_id` and is associated with exactly one `case_id` at the processing boundary.

A higher-level cross-year report may coordinate several case runs, but each underlying access remains independently case-scoped.

Processing should be idempotent where practical. Material state changes, classifications, attributions, decisions, approvals, and failures remain auditable.

## 9. Case state

Case state must distinguish at minimum:

- case identity and tax period;
- parties, household relationships, and temporal status;
- source documents;
- document-to-party attribution;
- extracted evidence;
- normalized and reconciled facts;
- assumptions;
- legal/rule references;
- calculations;
- optimization opportunities;
- challenges and unresolved conflicts;
- approvals;
- final outputs;
- audit events.

No unstructured LLM context is authoritative case state.

## 10. Case Party / Household Context

A natural-person case must establish relevant people and relationships before substantive analysis can safely proceed.

The system must explicitly determine or mark unknown:

- one-person versus family case;
- spouse/partner identity where relevant;
- joint versus individual assessment where applicable;
- each spouse's Steuerklasse/ELStAM where applicable;
- children and relevant child facts;
- ownership/attribution of income and expenses;
- shared household facts;
- economic bearer of material expenses.

Steuerklasse/ELStAM is evidence about wage-tax withholding and is not the final income-tax liability.

Document-to-party attribution may use names, addresses, identifiers where appropriate, employer/insurer data, invoice data, dates, explicit relationships, and cross-document consistency. Filename alone is never sufficient for material attribution.

Party relationships and tax attributes are temporal. A dated document does not automatically establish a fact for the entire tax year.

The detailed contract is defined in `docs/case-party-model.md`.

## 11. Intake and document pipeline

```text
Google Drive
   ↓
Drive Connector
   ↓
Case / Folder Resolver
   ↓
Case Party / Household Context
   ↓
Document Inventory
   ↓
Inventory Validation
   ↓
Document Processing
   ↓
Evidence Extraction
   ↓
Fact Normalization / Reconciliation
   ↓
Tax Categorization
   ↓
Provenance / Audit
```

Document Inventory is deterministic code, not an LLM Agent. It reads only the approved case scope and required metadata. It does not interpret tax content.

The detailed contracts are defined in `docs/document-inventory.md` and `docs/document-processing.md`.

## 12. Evidence and provenance

Every material fact must ultimately be traceable through:

```text
Source Document
      ↓
Document Identity / Version
      ↓
Party Attribution
      ↓
Evidence / Extraction Record
      ↓
Normalized Fact
      ↓
Calculation / Rule Application
      ↓
Conclusion / Recommendation
```

No category or generated report becomes a substitute for authoritative source evidence.

## 13. Current-law layer

German tax law is a dynamic system dependency. The architecture must support authoritative source retrieval, tax-year/effective-date awareness, source/version provenance, historical-versus-current rule distinction, supersession/change detection, and citations for material legal conclusions.

The LLM is not an authoritative source of current German tax law.

## 14. Agent boundary

Candidate agents remain hypotheses until workflow decomposition proves their value. Candidates include Case/Orchestrator, Tax Research, Analysis/Calculation reasoning, Tax Optimization Supervisor, Challenge/Devil's Advocate, and Auditor/QA.

Each approved Agent must have a defined role, inputs, outputs, tools, permissions, evidence requirements, stop conditions, failure behavior, and evaluation tests.

## 15. Tax Optimization Supervisor

A cross-cutting Tax Optimization Supervisor supports the project's golden objective:

**Maximize Legally Achievable Tax Benefit.**

It reviews facts, evidence, calculations, research, and decisions for lawful opportunities to reduce tax or increase refund; may challenge work or request additional evidence/research/recalculation; and must not silently modify source evidence or submit a filing.

Optimization opportunities require legal basis, evidence requirements, effective-date awareness, financial impact where calculable, uncertainty, and approval requirements.

## 16. Permissions and safety

The initial inventory stage is metadata-read-only for the approved case scope.

No component may:

- access unrelated Drive data without an explicit requirement and permission;
- mutate source documents without an explicit approved operation;
- fabricate evidence;
- silently omit material facts;
- submit consequential tax declarations without the required approval gate;
- expose credentials, tokens, or private case content through logs or GitHub.

## 17. Audit and observability

The system must maintain enough information to reconstruct a run:

- case ID;
- run ID;
- component/Agent identity;
- input references;
- tool calls and outcomes;
- source/evidence references;
- party attribution;
- calculations;
- decisions/challenges;
- approvals;
- output references;
- failures and recovery events.

Sensitive content must be minimized in logs.

## 18. Evaluation architecture

Evaluation is part of development. The project must maintain golden cases, expected facts/results, party-attribution tests, household/relationship edge cases, assessment-mode tests, document-to-person mapping tests, tax-optimization coverage, adversarial cases, regression tests, evidence/citation correctness tests, reproducibility tests, and security/permission tests.

CASE-001 is the first Golden Test Case and must remain independently evaluated against the known real-world outcome without revealing that outcome to the system before independent calculation is complete.

## 19. Implementation sequence

Before serious document processing, the following foundational work must be completed:

1. Case Registry model;
2. Person/Entity Registry model;
3. Case Creation workflow;
4. case-scoped Drive Resolver;
5. case-scoped state and `run_id` model;
6. isolation and cross-case contamination tests;
7. migration/compatibility strategy for existing CASE-001;
8. only then deterministic metadata-only Document Inventory;
9. live inventory against CASE-001/Documents only after scope enforcement is verified;
10. subsequently document-content processing and party attribution extraction.

This sequence prevents CASE-001-specific code from becoming the architecture and prevents LLM complexity from bypassing deterministic safety boundaries.

## 20. Current implementation status

The multi-case, multi-year, registry, and isolation architecture is now defined. The corresponding runtime components and tests are not yet fully implemented. Existing CASE-001 private Drive storage remains unchanged until migration is explicitly designed and verified.
