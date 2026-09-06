# Current State

## Project status

The project is in the foundational architecture and Phase 1 preparation stage. CASE-001 is the first real validation case, but the architecture is being built for long-term multi-case, multi-year operation for natural persons and legal entities.

## Established architecture

- GitHub is the source of truth for code, docs, tests, decisions, and verified state.
- Google Drive is private source-document storage and working-case storage; it is not the system brain.
- Local Python/Docker runtime is the execution environment.
- Source documents under a case's `Documents/` boundary are immutable.
- Tax categories are a dynamic retrieval/organizational layer, not the source of truth.
- Evidence, provenance, calculations, reports, and audit data are case-scoped.
- Party/household context is explicit and ambiguity must not be silently guessed.
- Document processing is deterministic-first.

## Foundational multi-case architecture

The system is designed around three identities:

- `case_id`: identity of one tax case for one tax period and mandatory processing scope.
- `person_id` / `entity_id`: persistent taxpayer/entity identity across years.
- `tax_period`: explicit tax period, initially supporting calendar years and designed to support future fiscal-period variants.

Target Drive organization:

```text
AI-Tax-Agent/
├── Tax_Years/
│   ├── 2020/Cases/
│   ├── 2021/Cases/
│   ├── ...
│   ├── 2024/Cases/
│   ├── 2025/Cases/
│   └── 2026/Cases/
├── Case_Registry/
├── Person_Registry/
├── Entity_Registry/
├── Templates/
└── System/
```

Each case is internally isolated with:

```text
CASE-YYYY-NNNN/
├── Documents/
├── Evidence/
├── Tax_Categories/
├── Calculations/
├── Reports/
└── Audit/
```

The exact migration of the currently existing CASE-001 layout is not yet implemented.

## Mandatory isolation rule

No Agent, pipeline component, model, or data-access tool may access case data without a validated `case_id`. Access must resolve through the Case Registry to the exact case folder reference. Unscoped broad Drive searches for case data are prohibited.

Case isolation is a deterministic security/correctness boundary, not merely an Agent prompt instruction. Failure to resolve a case or an out-of-scope object must fail closed.

Cross-year summaries resolve cases through persistent `person_id`/`entity_id` and the Case Registry, then access each case separately. They must not scan unrelated Drive content and guess ownership.

## Case Registry foundation

`docs/case-registry.md` defines the first Registry contract. It establishes `case_id`, persistent person/entity identity, structured `tax_period`, case type, lifecycle state, storage scope reference, lookup behavior, invariants, failure-closed rules, versioning, and acceptance criteria.

The Registry contract is designed so the physical storage implementation can evolve beyond Google Drive without changing the case identity contract.

## Person/Entity Registry foundation

`docs/person-entity-registry.md` defines the foundational persistent identity model for natural persons and legal entities. It establishes explicit PERSON versus ENTITY identity, immutable persistent IDs, controlled lookup attributes, identity resolution states, identity-to-case mapping, lifecycle status, auditability, historical identity changes, and separation from case-scoped tax data.

Runtime implementation, identity matching, merge/split logic, and migration are not yet implemented.

## Case Creation Workflow contract

`docs/case-creation-workflow.md` defines the foundational contract for creating new tax cases. It establishes request validation, Person/Entity identity resolution, explicit tax-period validation, case identity generation, idempotency, exact storage-scope creation, Case Registry initialization, Person/Entity linkage, initial `CREATED` state, creation run identity, audit events, failure/compensation behavior, and mandatory case isolation.

The workflow is a generic case-creation contract. It explicitly excludes migration or restructuring of the existing CASE-001 layout.

Runtime implementation and automated acceptance tests for this workflow are not yet complete.

## Completed environment work

- Google Drive API enabled.
- Desktop OAuth client configured.
- Metadata-only Drive smoke test passed against the AI-Tax-Agent root.
- Python environment and Google Drive libraries verified.
- Docker Desktop verified.
- CASE-001 `Tax_Categories` default directories created in private Drive.
- Document Processing Contract created.
- Case Party / Household Model created.
- Foundational Case Management and Isolation architecture created.
- Case Registry contract created.
- Person/Entity Registry model created.
- Case Creation Workflow contract created.

## Next implementation priorities

1. Implement the deterministic Case Registry model from `docs/case-registry.md`.
2. Implement the Person/Entity Registry runtime model from `docs/person-entity-registry.md`.
3. Implement Case Creation workflow using both Registry models and the contract in `docs/case-creation-workflow.md`.
4. Implement case-scoped Drive Resolver and access boundary.
5. Implement case-scoped state and execution/run IDs.
6. Add isolation and cross-case contamination tests.
7. Define migration/compatibility handling for existing CASE-001.
8. Implement deterministic metadata-only Document Inventory using the case-scoped connector.
9. Run the live inventory against CASE-001/Documents only after the scope boundary is verified.
