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

## Case Registry implementation

`docs/case-registry.md` remains the authoritative contract. The first deterministic runtime model has been implemented at `src/agent_lab/case_registry.py`, with acceptance-oriented unit tests at `tests/unit/test_case_registry.py`.

The implementation currently provides:

- explicit `CaseRecord`, `TaxPeriod`, and `StorageScopeReference` models;
- controlled enums for owner type, case type, assessment mode, lifecycle status, and lookup status;
- globally unique `case_id` registration;
- explicit owner + tax-period lookup;
- deterministic ambiguity handling with no arbitrary case selection;
- persistent cross-year lookup by owner ID;
- lifecycle, storage-scope, and run-ID updates;
- request-ID idempotency for registration;
- registry invariant validation, including one storage root per case;
- no Drive/document access inside the registry layer.

Local verification passed: `tests/unit/test_case_registry.py` completed with 10 passed tests.

## Person/Entity Registry foundation and runtime

`docs/person-entity-registry.md` defines the foundational persistent identity model for natural persons and legal entities. It establishes explicit PERSON versus ENTITY identity, persistent IDs, controlled lookup attributes, identity resolution states, identity-to-case mapping, lifecycle status, auditability, and separation from case-scoped tax data.

The deterministic runtime implementation is at `src/agent_lab/person_entity_registry.py`, with acceptance-oriented unit tests at `tests/unit/test_person_entity_registry.py`.

Local verification passed: `tests/unit/test_person_entity_registry.py` completed with 11 passed tests.

## Case ↔ Identity Association runtime

The deterministic association boundary is implemented at `src/agent_lab/case_identity_association.py`, with tests at `tests/unit/test_case_identity_association.py`.

It enforces identity-type compatibility, exact owner-ID matching, existence of both identity and case, idempotent association, and registry consistency. It introduces no document or Drive access.

Local verification passed: `tests/unit/test_case_identity_association.py` completed with 9 passed tests.

## Case Creation Workflow contract

`docs/case-creation-workflow.md` defines the foundational contract for creating new tax cases. It establishes request validation, Person/Entity identity resolution, explicit tax-period validation, case identity generation, idempotency, exact storage-scope creation, Case Registry initialization, Person/Entity linkage, initial `CREATED` state, creation run identity, audit events, failure/compensation behavior, and mandatory case isolation.

The workflow is a generic case-creation contract. It explicitly excludes migration or restructuring of the existing CASE-001 layout.

## Case Creation Workflow runtime

The deterministic runtime is implemented at `src/agent_lab/case_creation_workflow.py`, with acceptance-oriented unit tests at `tests/unit/test_case_creation_workflow.py`.

The current runtime coordinates:

- request validation;
- deterministic existing-identity resolution;
- case-type and assessment-mode validation;
- duplicate and request-id idempotency checks;
- unique `CASE-YYYY-NNNN` generation;
- exact storage-scope creation through an injected storage adapter;
- Case Registry initialization with lifecycle `CREATED`;
- Person/Entity ↔ Case association;
- creation run identity;
- auditable creation event recording.

The initial storage implementation is deliberately in-memory/test-oriented. Google Drive creation is not yet part of this runtime, preserving a replaceable storage abstraction and preventing premature coupling to an external backend.

Local verification passed: `tests/unit/test_case_creation_workflow.py` completed with 9 passed tests.

The runtime does not yet implement the durable Case State store, production Run store, production Audit store, Google Drive storage adapter, or CASE-001 migration. Those remain separate steps.

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
- Case Registry contract and runtime created and verified.
- Person/Entity Registry model and runtime created and verified.
- Case ↔ Identity Association runtime created and verified.
- Case Creation Workflow contract, runtime, and unit tests created and verified.

## Next implementation priorities

1. Implement case-scoped Drive Resolver and access boundary.
2. Implement case-scoped state and execution/run IDs.
3. Define durable audit/observability boundary.
4. Add isolation and cross-case contamination tests.
5. Define migration/compatibility handling for existing CASE-001.
6. Implement deterministic metadata-only Document Inventory using the case-scoped connector.
7. Run the live inventory against CASE-001/Documents only after the scope boundary is verified.
8. Continue toward evidence extraction, research, analysis, optimization, challenge, audit, and final-output workflows.
