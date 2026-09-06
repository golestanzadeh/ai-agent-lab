# Architecture

Status: **approved baseline architecture; detailed implementation evolves by phase**

Last verified: 2026-09-06

This document defines the architectural baseline for the German tax-assistance system. Detailed components, contracts, and implementation decisions may be refined through the project phases, but the boundaries and safety principles below are now the governing baseline.

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

## 2. High-level system boundary

```text
                         ┌─────────────────────────┐
                         │       User / Taxpayer   │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │      Case Orchestrator  │
                         │   / Workflow Controller │
                         └────────────┬────────────┘
                                      │
             ┌────────────────────────┼────────────────────────┐
             │                        │                        │
             ▼                        ▼                        ▼
      ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
      │ Drive        │        │ Tax Research │        │ Calculation  │
      │ Connector    │        │ / Law Layer  │        │ Engine       │
      └──────┬───────┘        └──────┬───────┘        └──────┬───────┘
             │                       │                       │
             ▼                       ▼                       ▼
      ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
      │ Document     │        │ Rules +      │        │ Validated    │
      │ Inventory    │        │ Sources      │        │ Calculations │
      └──────┬───────┘        └──────┬───────┘        └──────┬───────┘
             │                       │                       │
             └───────────────┬───────┴───────────────┬───────┘
                             ▼                       │
                    ┌─────────────────┐              │
                    │ Evidence /     │◄─────────────┘
                    │ Provenance      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Tax Analysis &  │
                    │ Optimization    │
                    └────────┬────────┘
                             │
                 ┌───────────┴───────────┐
                 ▼                       ▼
        ┌─────────────────┐     ┌─────────────────┐
        │ Challenge /     │     │ Auditor / QA    │
        │ Devil's Advocate│     │                 │
        └────────┬────────┘     └────────┬────────┘
                 └───────────┬───────────┘
                             ▼
                    ┌─────────────────┐
                    │ Human Approval  │
                    │ Gate            │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ Final Reports / │
                    │ Controlled      │
                    │ Submission      │
                    └─────────────────┘

Cross-cutting layers:
  Case State | Party/Household Context | Audit/Observability |
  Security/Permissions | Evaluation
```

This diagram is a logical architecture, not a claim that every box will become an independent agent.

## 3. Data architecture

### 3.1 Private case storage

```text
Google Drive/
└── AI-Tax-Agent/
    └── Cases/
        └── CASE-001/
            ├── Documents/      <- immutable source boundary
            ├── Evidence/       <- derived, source-linked evidence
            ├── Calculations/   <- deterministic/validated calculation artifacts
            ├── Reports/        <- generated human-readable outputs
            └── Audit/          <- audit trail, run records, approvals
```

`Documents/` is the source-document boundary. The system must not silently modify those source files.

### 3.2 Case state

The logical case state must distinguish at minimum:

- case identity and tax period;
- parties, household relationships, and temporal status;
- source documents;
- document-to-party attribution;
- extracted evidence;
- normalized facts;
- reconciled facts;
- assumptions;
- legal/rule references;
- calculations;
- optimization opportunities;
- challenges and unresolved conflicts;
- approvals;
- final outputs;
- audit events.

No single unstructured LLM context is the authoritative case state.

## 4. Case Party / Household Context layer

A natural-person tax case must establish its relevant people and relationships before substantive analysis can safely proceed.

The minimum conceptual model distinguishes:

- primary taxpayer/case owner;
- spouse/registered partner;
- children;
- other relevant persons;
- organizations and external parties separately.

For each relevant person, the case may contain tax-year-specific attributes such as marital/family status, residence, employment, income, Steuerklasse/ELStAM, child-related relationships, and economic burden of expenses.

The system must explicitly determine or mark unknown:

- whether the case concerns one person or a family;
- spouse/partner identity where relevant;
- whether joint or individual assessment is legally available and selected;
- each spouse's tax class/ELStAM where applicable;
- children and relevant child facts;
- which documents, income, and expenses belong to which person;
- which facts are shared household facts;
- who economically bore each material expense.

### 4.1 Tax class is not the final tax liability

Steuerklasse/ELStAM is retained as evidence about wage-tax withholding and payroll circumstances. It must not be confused with the final income-tax assessment calculation.

The architecture therefore separates:

```text
Person A ELStAM / Steuerklasse ─┐
                               ├→ Wage-tax withholding evidence
Person B ELStAM / Steuerklasse ─┘
                                      ↓
                               Lohnsteuer withheld
                                      ↓
                           Income-tax assessment
                                      ↓
                         Final tax / refund / payment
```

For married couples, the system must capture the relevant tax class of each spouse independently, including changes during the year. The applicable legal consequences must be evaluated for the relevant tax year.

### 4.2 Joint versus individual assessment

Where spouses/registered partners are involved, assessment mode is explicit case state:

- `JOINT_ASSESSMENT` / Zusammenveranlagung;
- `INDIVIDUAL_ASSESSMENT` / Einzelveranlagung;
- `NOT_APPLICABLE`;
- `UNKNOWN_PENDING_VERIFICATION`.

The system must establish legal eligibility before comparing alternatives for tax optimization. Under individual assessment, attribution of costs to the person who legally/economically bears them becomes especially important.

### 4.3 Document-to-party attribution

Every material document and extracted fact must support attribution to one or more parties, or explicitly to the household/shared context.

Attribution may use names, addresses, tax identifiers where appropriate, employer/insurer data, invoice data, dates, form fields, explicit relationships, and cross-document consistency. Filename alone is never sufficient for material attribution.

The model must support one-to-many and many-to-many relationships because a document can concern several people or a household, and a person's tax case can depend on several documents.

Each material attribution carries evidence references, attribution method, status/confidence, and unresolved alternatives where applicable.

### 4.4 Temporal facts

Party relationships and tax attributes are time-dependent. The case state must support effective intervals for marital status, permanent separation, tax class, employment, residence, child household membership, education/training, insurance coverage, and other material changes.

A dated document must not automatically establish a fact for the entire tax year.

The complete conceptual contract is defined in `docs/case-party-model.md`.

## 5. Intake and document pipeline

The first executable boundary is now explicitly defined as:

```text
Google Drive
   ↓
Drive Connector
   ↓
Case/Folder Resolver
   ↓
Case Party / Household Context
   ↓
Document Inventory
   ↓
Inventory Validation
   ↓
Document → Party Attribution
   ↓
Document Processing
   ↓
Evidence Extraction
   ↓
Fact Normalization / Reconciliation
```

Document Inventory is deterministic code, not an LLM agent. It reads only the approved case path and metadata required for inventory. It does not interpret tax content.

The detailed contract is recorded in `docs/document-inventory.md`.

Google Drive API supports parent-scoped queries such as `'folderId' in parents`, pagination through `nextPageToken`, and explicit field masks. The implementation will use those mechanisms to avoid scanning unrelated Drive content and to minimize data transfer. citeturn0search0turn0search1

## 6. Evidence and provenance

Every material extracted fact must ultimately be traceable to:

```text
Source Document
      ↓
Document Identity / Version
      ↓
Party Attribution
      ↓
Evidence Span / Extraction Record
      ↓
Normalized Fact
      ↓
Calculation / Rule Application
      ↓
Conclusion / Recommendation
```

Where the exact evidence span cannot yet be represented, the system must record the strongest available source reference and mark the provenance limitation explicitly.

## 7. Current-law layer

German tax law is a dynamic system dependency. The architecture must support:

- authoritative source retrieval;
- tax-year and effective-date awareness;
- source/version provenance;
- current-versus-historical rule distinction;
- supersession/change detection;
- citations for material legal conclusions;
- controlled failure when current authoritative information cannot be verified.

The LLM must not be treated as the authoritative source of current German tax law.

## 8. Agent boundary

Candidate agents remain hypotheses until workflow decomposition proves they are needed. Candidates include:

- Case/Orchestrator Agent;
- Tax Research Agent;
- Analysis/Calculation reasoning component;
- Tax Optimization Supervisor;
- Challenge/Devil's Advocate Agent;
- Auditor/QA Agent.

Other functions should remain deterministic code or controlled integrations when that is safer and simpler.

An agent is approved only after definition of role, inputs, outputs, tools, permissions, evidence requirements, stop conditions, failure behavior, and evaluation tests.

## 9. Tax Optimization Supervisor

The Tax Optimization Supervisor is a cross-cutting architectural role candidate aligned with the project's golden objective:

**Maximize Legally Achievable Tax Benefit**

It continuously reviews facts, evidence, calculations, research, and decisions for lawful opportunities to reduce tax or increase refund. It may challenge work and request additional evidence, research, or recalculation, but it does not silently alter source evidence or submit a tax filing.

Every optimization opportunity must carry legal basis, evidence requirements, effective-date awareness, financial impact where calculable, uncertainty, and approval requirements.

## 10. Permissions and safety

Capabilities must be permissioned by stage. The initial inventory stage is metadata-read-only for the approved case path.

No component may:

- access unrelated user Drive data without an explicit requirement and permission;
- mutate source documents without an explicit approved operation;
- fabricate evidence;
- silently omit material facts;
- submit consequential tax declarations without the required approval gate;
- expose credentials, tokens, or private case content through logs or GitHub.

## 11. Audit and observability

The system must maintain enough information to reconstruct a run:

- case identifier;
- workflow/run identifier;
- component/agent identity;
- input references;
- tool calls and outcomes;
- source/evidence references;
- party attribution records;
- calculations;
- decisions and challenges;
- approvals;
- final output references;
- failures and recovery events.

Sensitive content must be minimized in logs.

## 12. Evaluation architecture

Evaluation is part of the system, not a final afterthought. The project must maintain:

- golden cases;
- expected facts/results;
- party-attribution accuracy tests;
- household/relationship edge cases;
- expected assessment-mode decisions;
- expected document-to-person mappings;
- tax-optimization opportunity coverage;
- adversarial and failure cases;
- regression tests;
- evidence/citation correctness checks;
- reproducibility checks;
- safety and permission tests.

CASE-001 is the first Golden Test Case and must remain independently evaluated against the known real-world outcome without revealing that outcome to the system before its independent calculation is complete.

## 13. Implementation sequence

The next implementation stage is deliberately narrow:

1. Drive connector contract;
2. deterministic case-folder resolution;
3. **Case Party / Household Context contract**;
4. Document Inventory implementation;
5. mocked/unit tests;
6. live metadata-only test against `CASE-001/Documents`;
7. record the inventory snapshot and verified result;
8. only then design document-content processing and party attribution extraction.

This sequencing prevents early LLM complexity from contaminating the source-document boundary and makes party identity/ownership a first-class case-state concern.

## 14. Baseline security requirement

Before real document content is processed, the project must explicitly validate authentication, access scope, token handling, data minimization, logging, local caching, retention, and failure behavior. OAuth credentials and tokens remain outside GitHub.
