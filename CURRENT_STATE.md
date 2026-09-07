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

Local verification passed: `tests/unit/test_case_creation_workflow.py completed with 9 passed tests.`

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

## Live CASE-001 Document Identity Bootstrap

The read-only live bootstrap has now been executed successfully against the real CASE-001 Documents scope.

Verified output:

- `inventory_document_count`: **15**
- `inventory_folder_count`: **0**
- `identity_count`: **15**
- `run_id`: `RUN-00000001`
- local identity snapshot: `artifacts\\case001\\document_identity.json`
- `drive_mutation`: **false**

All 15 observed PDF source objects received a stable logical `document_id`. The bootstrap performed no Google Drive mutation. The local snapshot remains local and must not be committed because it may contain private provider object IDs.

The bootstrap initially exposed a constructor-call mismatch in the harness: `GoogleDriveMetadataAdapter` requires keyword-only constructor arguments. The harness was corrected in commit `771db7b1d7de895d05bc2e4c745414a60efbc8ef` and then executed successfully.

## Pre-Manifest Safety Gate

The pre-manifest gate is now satisfied for the live CASE-001 inventory:

- local restart-safe Document Identity snapshot persistence;
- authoritative registered-source-scope enforcement;
- deterministic migration manifest generator;
- live metadata-only inventory of 15 documents;
- live identity bootstrap resolving all 15 documents to logical identities;
- no physical Drive mutation.

## D-017 Human Approval Gate

D-017 is now implemented at `src/agent_lab/approval.py` with unit coverage at `tests/unit/test_approval.py` and implementation documentation at `docs/approval-gate.md`.

The implementation establishes:

- immutable `MigrationApproval` values with controlled lifecycle states;
- `ApprovalStore` as the lifecycle and one-time consumption owner;
- `ApprovalGate` as the deterministic fail-closed binding validator;
- exact case/run, manifest identity/version/reference, preflight identity/reference/result, intended-operation, actor, approver, authorization, timestamp, and audit bindings;
- explicit `APPROVAL_CONSUMED` audit evidence through the existing `AuditStore`;
- process-local atomic consistency for state transition plus audit publication;
- rollback of approval state and audit sequence/event publication on failure;
- exactly one successful concurrent consumption and deterministic `APPROVAL_ALREADY_CONSUMED` on reuse;
- no Drive mutation, manifest generation, preflight generation, or physical migration execution.

`CaseState.approvals_ref` remains only a case-state reference. Approval lifecycle authority is not moved into CaseState.

The atomicity guarantee is intentionally limited to process-local consistency. The implementation makes no claim of crash durability, persistent transactional durability, or distributed atomicity.

The D-017 unit suite was expanded to **13 tests**. The assistant also performed a separate local deterministic reconstruction of the D-017 implementation boundary with **13 passed tests in 0.20s**. Repository-hosted GitHub Actions execution was attempted through a temporary verification workflow, but the repository reported **zero workflow runs**, so no GitHub-hosted execution result is claimed.

## D-018 Deterministic Migration Artifact Identity

D-018 is accepted and implemented at `src/agent_lab/artifact_identity.py`, with artifact identity exposure added to the CASE-001 migration Manifest and Preflight result.

The identity contract is:

- controlled artifact `kind`;
- explicit identity/schema `version`;
- `sha256:<digest>` reference over deterministic canonical payload;
- identity payload excludes the identity itself, avoiding circular hashing;
- equivalent payloads produce the same reference;
- changing a hashed field produces a different reference.

Current artifact kinds are `CASE001_MIGRATION_MANIFEST` and `CASE001_MIGRATION_PREFLIGHT`, both version `1`.

The Manifest identity covers its case, tax period, provider, source/target scopes, mapping sequence, and optional Inventory Evidence reference. The Preflight identity covers the complete deterministic preflight result.

Documentation: `docs/artifact-identity.md`.

Test suite: `tests/unit/test_artifact_identity.py` contains **8 tests** covering canonicalization, deterministic identity, content-change invalidation, Manifest identity, and Preflight identity.

D-018 performs no Drive mutation and does not authorize or execute migration. The next boundary is to construct the D-017 approval context from the exact real Manifest and successful Live Target Preflight artifact identities.

## D-019 Controlled Agent-Assisted Development Workflow

D-019 is accepted and documented. Controlled agent-assisted development is now part of project governance: Codex remains optional, is not a runtime dependency, and does not replace required human authority for architecture, contracts, stage acceptance, migration authorization, destructive operations, or governance decisions. Passing tests does not itself constitute architectural or stage acceptance.

D-017 is implemented/completed and D-018 is accepted and implemented. No physical Google Drive migration has occurred. The next implementation boundary remains construction of the D-017 approval context from the exact real migration manifest and successful live-target-preflight artifact identities.

### D-019 integration validation

The authorized D-019 documentation was merged into main with a non-fast-forward merge. The first complete local suite reported 167 passed, 4 failed, and 1 skipped. These failures were pre-existing: the merge changed no runtime source or tests. Manifest-generator fixtures used an unqualified source scope, and the live-preflight test attempted to construct a wrong-case manifest that the existing constructor already rejects.

Test-only repairs use the registered `google_drive:legacy` scope and separately verify wrong-case constructor rejection and empty-manifest preflight rejection. No runtime contracts or governance were changed. A targeted run initially failed collection because `agent_lab` was not on the import path; process-local `PYTHONPATH=src` resolved it.

Verification using the existing project-local environment, with `$env:PYTHONPATH="src"`:
- `.\.venv\Scripts\python.exe -m pytest -q tests/unit/test_case001_migration_manifest.py tests/unit/test_case001_live_target_preflight.py`: **13 passed**.
- `.\.venv\Scripts\python.exe -m pytest`: **172 passed, 1 skipped**.

The live Drive integration harness skipped because its explicit test-root environment variables were absent. No live Drive verification or mutation occurred. These results establish local test success, not human stage acceptance. D-020 was not started.

## D-020 Approval Context Composition — branch implementation

D-020 is implemented on `d020-case001-approval-context`, pending human review and integration into main. `src/agent_lab/case001_approval_context.py` composes the generic D-017 execution context from an exact manifest and successful live preflight, preserving their existing D-018 references. Live preflight now records the manifest's exact `ArtifactIdentity`; missing or mismatched provenance fails closed. Identical manifest contents remain the same artifact identity; no attempt/run provenance was added.

The focused suite passed **51 tests**, required regression suites passed **104 tests**, and the complete suite passed **223 tests with 1 opt-in live test skipped**, using the project-local Python environment with `PYTHONPATH=src`. See `docs/case001-approval-context.md` for commands and semantics. D-017 lifecycle and D-018 structural identity payloads remain unchanged. No approval was granted or consumed by composition, no Drive mutation occurred, and no migration executor was created. Tests do not constitute stage acceptance.

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
- Document Identity local persistence baseline implemented and live-verified against 15 CASE-001 documents.
- CASE-001 Migration/Compatibility baseline implemented and unit-verified.
- Migration validation connected to Document Identity and Inventory Evidence.
- CASE-001 Migration Manifest Generator implemented and unit-verified: 6 passed in 0.17s.
- Live CASE-001 identity bootstrap completed successfully with 15/15 identity coverage and no Drive mutation.
- D-017 Human Approval Gate implemented with deterministic lifecycle, exact binding, one-time consumption, rollback semantics, and existing AuditStore integration.
- D-018 deterministic artifact identity implemented for CASE-001 Manifest and Preflight outputs.

## Next implementation priorities

1. Generate the real CASE-001 migration manifest from the live inventory and persisted logical identities.
2. Validate the generated manifest against the authoritative source scope and Inventory Evidence.
3. Run the read-only live target preflight and bind its exact artifact identity to the exact Manifest identity.
4. Construct and validate a D-017 approval record from those exact artifact identities before any physical migration design/execution.
5. Design the controlled physical migration executor, rollback, and post-migration verification. No physical Drive migration yet.
6. Continue toward controlled document-content access and evidence extraction.
