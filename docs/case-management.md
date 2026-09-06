# Case Management and Isolation

## Status

Foundational architecture decision for long-term multi-case operation.

## Purpose

The system must support many tax cases across multiple tax periods for both natural persons and legal entities. CASE-001 is the first real validation case, not a one-off architecture.

## Core identity model

The system uses three distinct identities:

- `case_id`: immutable identity of one tax case for one tax period.
- `person_id` / `entity_id`: persistent identity of the taxpayer or legal entity across tax periods.
- `tax_period`: the period to which the case belongs. The model must support calendar-year cases and future fiscal-period variants.

`case_id` is the mandatory operational scope for processing.

## Drive organization

The conceptual long-term structure is:

```text
AI-Tax-Agent/
├── Tax_Years/
│   ├── 2020/
│   │   └── Cases/
│   │       ├── CASE-2020-0001/
│   │       └── ...
│   ├── 2021/
│   ├── 2022/
│   ├── 2023/
│   ├── 2024/
│   ├── 2025/
│   └── 2026/
├── Case_Registry/
├── Person_Registry/
├── Entity_Registry/
├── Templates/
└── System/
```

Each case remains internally isolated:

```text
CASE-YYYY-NNNN/
├── Documents/
├── Evidence/
├── Tax_Categories/
├── Calculations/
├── Reports/
└── Audit/
```

This is the target architecture. Existing CASE-001 storage is not automatically migrated until an explicit migration implementation is designed and verified.

## Discovery and retrieval

A user must be able to find cases by multiple reliable keys, including:

- tax period;
- case ID;
- persistent person/entity ID;
- taxpayer/entity name or approved display name;
- applicable tax identifiers where legally and technically appropriate;
- case type and status.

Names and sensitive tax identifiers must not be used as the primary Drive folder name. Registries provide the mapping from human/business identifiers to internal IDs and case IDs.

A person/entity may have many cases across years:

```text
PERSON-00042
├── 2020 → CASE-2020-....
├── 2021 → CASE-2021-....
├── ...
└── 2026 → CASE-2026-....
```

This enables cross-year summaries without scanning unrelated Drive content.

## Registry responsibilities

### Case Registry

The Case Registry maps `case_id` to:

- persistent taxpayer/entity ID;
- tax period;
- case type;
- assessment state where applicable;
- lifecycle status;
- exact Drive case-folder reference;
- current processing/run metadata;
- system/schema version metadata needed for reproducibility.

### Person/Entity Registry

These registries maintain persistent identities and map them to cases across tax periods. They are indexes and identity maps, not substitutes for source documents or evidence.

## Mandatory case-scoped access

No Agent, pipeline component, or data-access tool may access tax-case data without a validated `case_id`.

The intended access contract is conceptually:

```text
list_documents(case_id)
get_document(case_id, document_id)
read_evidence(case_id, evidence_id)
write_report(case_id, ...)
```

A generic unscoped operation such as `list_documents()` is prohibited for case data.

The Case Resolver must resolve:

```text
user/request
    ↓
case resolver
    ↓
validated case_id
    ↓
exact case folder reference
    ↓
case-scoped connector
```

Drive is storage, not the system's source of identity or workflow state.

## Isolation rule

An Agent processing `CASE-2025-0317` must only be able to access that case and explicitly permitted descendants. It must never search, inspect, infer from, or retrieve documents from another case merely because they are in the same year, belong to the same person/entity, or are nearby in Drive.

Case isolation must be enforced by deterministic application/connector logic, not merely by prompts or Agent instructions.

Cross-case contamination is a security and correctness failure.

## Cross-year summaries

Cross-year reporting is an explicit higher-level operation. It starts from a persistent `person_id` or `entity_id`, resolves the requested tax periods through the registry, and then accesses each resolved case separately under its own case scope.

It must not be implemented as a broad Drive search followed by model-based guessing.

## Lifecycle and reproducibility

Every processing execution should carry an execution/run ID associated with the `case_id`. Processing should be idempotent where practical, and case state must remain isolated between runs.

Future requirements include:

- Case Registry implementation;
- Case creation workflow;
- case-scoped Drive resolver;
- case-scoped state;
- execution/run IDs;
- idempotency;
- isolation tests;
- cross-case contamination tests;
- multi-year retrieval tests;
- migration strategy for the existing CASE-001 structure.

## Security boundary

The system must fail closed when a case cannot be resolved or when a requested document/evidence object is outside the validated case scope. Ambiguous identity or scope must result in an explicit unresolved state rather than best-effort guessing.
