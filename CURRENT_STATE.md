# Current State

## Project status

The project is in the foundational architecture and Phase 2 implementation stage. CASE-001 is the first real validation case, but the architecture is being built for long-term multi-case, multi-year operation for natural persons and legal entities.

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

## Mandatory isolation rule

No Agent, pipeline component, model, or data-access tool may access case data without a validated `case_id`. Access must resolve through the Case Registry to the exact case folder reference. Unscoped broad Drive searches for case data are prohibited.

Case isolation is a deterministic security/correctness boundary, not merely an Agent prompt instruction. Failure to resolve a case or an out-of-scope object must fail closed.

Cross-year summaries resolve cases through persistent `person_id`/`entity_id` and the Case Registry, then access each case separately. They must not scan unrelated Drive content and guess ownership.

## Case Registry implementation

`docs/case-registry.md` remains the authoritative contract. The deterministic runtime model is implemented at `src/agent_lab/case_registry.py`, with acceptance-oriented unit tests at `tests/unit/test_case_registry.py`.

Local verification passed: `tests/unit/test_case_registry.py` completed with 10 passed tests.

## Person/Entity Registry foundation and runtime

`docs/person-entity-registry.md` defines the persistent identity model for natural persons and legal entities. The deterministic runtime implementation is at `src/agent_lab/person_entity_registry.py`, with tests at `tests/unit/test_person_entity_registry.py`.

Local verification passed: `tests/unit/test_person_entity_registry.py` completed with 11 passed tests.

## Case ↔ Identity Association runtime

The deterministic association boundary is implemented at `src/agent_lab/case_identity_association.py`, with tests at `tests/unit/test_case_identity_association.py`.

It enforces identity-type compatibility, exact owner-ID matching, existence of both identity and case, idempotent association, and registry consistency. It introduces no document or Drive access.

Local verification passed: `tests/unit/test_case_identity_association.py` completed with 9 passed tests.

## Case Creation Workflow

`docs/case-creation-workflow.md` defines the foundational creation contract. The deterministic runtime is implemented at `src/agent_lab/case_creation_workflow.py`, with tests at `tests/unit/test_case_creation_workflow.py`.

Local verification passed: `tests/unit/test_case_creation_workflow.py` completed with 9 passed tests.

The runtime remains storage-provider-neutral and does not migrate CASE-001 or perform document processing.

## Case-Scoped Drive Resolver and Access Boundary

`docs/case-scoped-drive-resolver.md` defines the mandatory boundary between validated case identity and storage access.

The deterministic runtime is implemented at `src/agent_lab/case_scoped_drive.py`, with tests at `tests/unit/test_case_scoped_drive.py`.

The resolver requires a validated `case_id`, resolves storage only through the Case Registry, returns the exact registered `StorageScopeReference`, fails closed for unknown cases, rejects out-of-scope objects, and does not scan Drive or infer ownership.

Local verification passed: `tests/unit/test_case_scoped_drive.py` completed with 8 passed tests.

## Case State + Run ID Model and Runtime

`docs/state-and-memory.md` defines the foundational case-state and execution identity contract.

The deterministic runtime is implemented at `src/agent_lab/case_state.py`, with acceptance-oriented tests at `tests/unit/test_case_state.py`.

The runtime establishes structured case-scoped operational state, unique deterministic `run_id` generation, exactly one `case_id` per run, request-ID idempotency, case-scoped run lookup, explicit run lifecycle transitions, immutable terminal status, state references, registry validation, and fail-closed cross-case access protection.

The current runtime is intentionally in-memory. Durable persistence, workflow queues, checkpoint/resume, durable audit storage, and full tax-domain state schemas remain separate future layers.

Local verification passed: `tests/unit/test_case_state.py` completed with 12 passed tests.

## Durable Audit / Observability Boundary

`docs/audit-observability.md` defines the foundational audit contract. The deterministic runtime is implemented at `src/agent_lab/audit.py`, with acceptance-oriented tests at `tests/unit/test_audit.py`.

The audit layer establishes exactly one validated `case_id` per event, validated `run_id` for execution-bound events, explicit event type/actor/operation/timestamp, reference-based links, append-only semantics, case-scoped retrieval, fail-closed cross-case protection, independence from LLM conversation context, and minimization of sensitive/raw payload storage.

The first runtime is intentionally in-memory. Durable database storage, distributed ordering, cryptographic tamper evidence, retention policy, and OpenTelemetry integration remain future layers.

Local verification passed: `tests/unit/test_audit.py` completed with 9 passed tests in 0.20s.

## Isolation and Cross-Case Contamination Tests

`docs/case-isolation-tests.md` defines the foundational isolation acceptance contract. The acceptance suite is implemented at `tests/unit/test_case_isolation.py`.

The suite verifies the deterministic chain across Case Registry, Case State/Run ID, Case-Scoped Storage Resolver, and Audit Boundary.

Local verification passed: `tests/unit/test_case_isolation.py` completed with 10 passed tests in 0.14s.

## Google Drive Storage Adapter — six-stage rollout

`docs/google-drive-storage-adapter.md` is the authoritative implementation contract for Decision D-013.

The six stages are complete and verified as defined by D-013. The adapter is metadata-only and case-scoped. The live A/B scope-isolation harness was read-only and did not modify CASE-001.

Verification evidence:

- adapter unit suite: **8 passed in 0.25s**;
- live Google Drive scope-isolation harness: **1 passed in 4.55s**.

This does not verify CASE-001 document processing, PDF extraction, tax calculations, production authorization, durable storage security, or electronic filing.

## CASE-001 Metadata-Only Document Inventory

The metadata-only inventory implementation is present and has been live-verified against the CASE-001 `Documents` scope.

- `src/agent_lab/document_inventory.py` provides deterministic metadata-only inventory;
- `tests/unit/test_document_inventory.py` provides the unit contract;
- `scripts/case001_metadata_inventory.py` is the local live execution harness;
- `docs/document-inventory.md` is the inventory/intake contract.

The live inventory produced **15 documents and 0 folders**. All 15 observed items were PDFs and direct children of the selected CASE-001 Documents scope. No source-document mutation was performed.

Private Drive object IDs are not recorded in GitHub.

## Document Identity

`docs/document-identity.md` and `src/agent_lab/document_identity.py` define the stable logical identity layer between source-object observations and downstream evidence/processing.

The runtime is metadata-only and case-scoped. It preserves logical identity across repeated observations and renames while keeping different provider objects distinct.

Local verification passed: the combined Document Identity + Inventory Evidence unit suites completed with **13 passed tests in 0.28s**.

A versioned local JSON snapshot boundary is implemented through `export_snapshot()`, `save_snapshot()`, `load_snapshot()`, and `import_snapshot()`. The snapshot is intended for local use only because it may contain private provider object IDs. `docs/document-identity-persistence.md` defines this boundary.

## Inventory Evidence

`src/agent_lab/inventory_evidence.py` records an immutable, case-scoped metadata inventory snapshot and can link inventory items to stable logical Document Identity references. It also updates case state and emits a case/run-bound audit event.

## CASE-001 Migration / Compatibility Layer

`docs/case001-migration-compatibility.md` defines the compatibility contract between the legacy CASE-001 layout and the target 2024 case layout.

`src/agent_lab/case001_migration.py` implements non-mutating deterministic migration preparation and validation.

The migration layer is connected to Document Identity and Inventory Evidence. Source scope is authoritative: the migration plan must use the exact registered CASE-001 storage scope. Provider, source object ID, source scope, and logical document ID must match exactly; supplied Inventory Evidence must match source-object and logical-document sequences exactly; cross-case, cross-scope, unknown-identity, and identity-mismatch conditions fail closed.

Local verification passed: the latest combined persistence + migration + authoritative source-scope suite completed with **18 passed tests in 0.29s**.

## CASE-001 Migration Manifest Generator

`src/agent_lab/case001_migration_manifest.py` defines the deterministic manifest-generation boundary.

The generator derives one migration mapping for each non-folder inventory item by resolving the logical `document_id` from `DocumentIdentityRegistry`. It rejects missing identity, source-scope mismatch, and inactive identity records, and can bind the manifest to matching `InventoryEvidence` before passing the result through migration compatibility validation.

`tests/unit/test_case001_migration_manifest.py` has been executed by the user: **6 passed in 0.17s**.

No physical Drive migration has occurred. The manifest generator does not create, move, rename, delete, overwrite, or copy Drive objects.

## Pre-Manifest Safety Gate

Before generating the real CASE-001 manifest from the live 15-document inventory, the following safety work is implemented:

- local restart-safe Document Identity snapshot persistence;
- a read-only live bootstrap harness at `scripts/case001_identity_bootstrap.py`;
- authoritative registered-source-scope enforcement in migration compatibility validation;
- `ERRORS_AND_LESSONS.md` for verified failures and architectural lessons.

The persistence/migration/source-scope tests are now green. The live bootstrap has **not yet been executed against CASE-001**, so persistence against the live 15-document inventory remains the next verification gate.

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
- Case Registry contract, runtime, and tests created and verified.
- Person/Entity Registry model, runtime, and tests created and verified.
- Case ↔ Identity Association runtime and tests created and verified.
- Case Creation Workflow contract, runtime, and tests created and verified.
- Case-Scoped Drive Resolver contract, runtime, and tests created and verified.
- Case State + Run ID contract, runtime, and tests created and verified.
- Durable Audit / Observability contract, runtime, and tests created and verified.
- Case Isolation and Cross-Case Contamination acceptance tests created and verified.
- Six-stage Google Drive Storage Adapter rollout completed and live scope gate verified.
- CASE-001 metadata-only inventory implemented and live-verified: 15 documents, 0 folders.
- Document Identity and Inventory Evidence foundations implemented and unit-verified.
- Document Identity local persistence baseline implemented; live bootstrap verification pending.
- CASE-001 Migration/Compatibility baseline implemented and unit-verified.
- Migration validation connected to Document Identity and Inventory Evidence.
- CASE-001 Migration Manifest Generator implemented and unit-verified: 6 passed in 0.17s.

## Next implementation priorities

1. Execute `scripts/case001_identity_bootstrap.py` against the live CASE-001 Documents scope and confirm inventory/identity counts are both 15, with no Drive mutation.
2. Inspect the generated local identity snapshot and verify stable logical identities for all 15 source objects.
3. Only then generate the real CASE-001 migration manifest from the live inventory.
4. Design the controlled physical migration preflight, human approval gate, executor, rollback, and post-migration verification. No physical Drive migration yet.
5. Continue toward controlled document-content access and evidence extraction.
