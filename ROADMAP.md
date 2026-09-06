# Roadmap

This is the authoritative plan for the project. Planned files are registered here before they are created so future work is not reconstructed from memory.

## Phase 0 — Initialization

Status: **complete**

- Establish repository as source of truth.
- Create operating principles and project definition.
- Create anti-hallucination rules.
- Establish roadmap, future-file registry, and decision log.

## Phase 1 — Problem and requirements

Status: **in progress**

Goals:
- define the German tax-assistance domain and supported first workflow;
- define users, inputs, outputs, constraints, risks, and success metrics;
- define party/household context;
- define the minimum viable workflow before adding agent complexity;
- establish the first real Golden Test Case.

Existing files:
- `docs/requirements.md`
- `docs/use-cases.md`
- `docs/case-party-model.md`
- `docs/document-inventory.md`
- `docs/document-processing.md`

## Phase 2 — System architecture and case foundation

Status: **in progress**

Goals:
- define control loop and state model;
- define deterministic versus Agent boundaries;
- define tool interfaces and evidence flow;
- define human approval points;
- establish persistent multi-case and multi-year identity;
- establish Case Registry and Person/Entity Registry contracts;
- establish mandatory case-scoped access and isolation;
- define execution/run identity and idempotency;
- define case creation workflow;
- define migration strategy for the existing CASE-001 structure;
- anchor CASE-001 migration validation to Document Identity and Inventory Evidence.

Existing files:
- `docs/architecture.md`
- `docs/case-management.md`
- `docs/case-registry.md`
- `docs/person-entity-registry.md`
- `docs/case-creation-workflow.md`
- `docs/case-scoped-drive-resolver.md`
- `docs/state-and-memory.md`
- `docs/google-drive-storage-adapter.md`
- `docs/case001-migration-compatibility.md`
- `docs/document-identity.md`

Implemented runtime foundations:
- `src/agent_lab/case_registry.py`
- `src/agent_lab/person_entity_registry.py`
- `src/agent_lab/case_identity_association.py`
- `src/agent_lab/case_creation_workflow.py`
- `src/agent_lab/case_scoped_drive.py`
- `src/agent_lab/case_state.py`
- `src/agent_lab/storage.py`
- `src/agent_lab/google_drive_storage.py`
- `src/agent_lab/google_drive_auth.py`
- `src/agent_lab/document_inventory.py`
- `src/agent_lab/document_identity.py`
- `src/agent_lab/inventory_evidence.py`
- `src/agent_lab/case001_migration.py`

Verified unit-test suites:
- Case Registry: 10/10
- Person/Entity Registry: 11/11
- Case ↔ Identity Association: 9/9
- Case Creation Workflow: 9/9
- Case-Scoped Drive Resolver: 8/8
- Case State + Run ID: 12/12
- Audit: 9/9
- Case Isolation: 10/10
- Google Drive Storage Adapter: 8/8
- Document Identity + Inventory Evidence: 13/13
- CASE-001 Migration baseline: 8/8

### Google Drive Storage Adapter — six-stage work package

Status: **complete through Stage 6; CASE-001 metadata-only inventory gate open**

1. **Storage Adapter Contract** — provider-neutral case-scoped interface and normalized metadata model. **Complete.**
2. **Case-Scoped Resolver Integration** — adapter access must originate from the authoritative Case Registry through `CaseScopedDriveResolver`. **Complete.**
3. **Google Drive Metadata Adapter** — metadata-only Google Drive implementation using the currently verified metadata-read capability. **Complete.**
4. **Deterministic Scope Enforcement** — exact root and descendant containment; fail closed for unrelated, ambiguous, trashed, or malformed objects. **Complete.**
5. **Adapter and Scope Tests** — unit tests plus live integration verification of A/B isolation before opening real case data. **Complete.** Unit suite: 8 passed. Live scope harness: 1 passed in 4.55s.
6. **Documentation, Verification and Gate** — record evidence, limitations, decisions, and the release condition for CASE-001 inventory. **Complete.**

Current implementation artifacts:
- `docs/google-drive-storage-adapter.md`
- `src/agent_lab/storage.py`
- `src/agent_lab/google_drive_storage.py`
- `src/agent_lab/google_drive_auth.py`
- `tests/unit/test_storage.py`
- `tests/unit/test_google_drive_storage.py`
- `tests/integration/test_google_drive_scope_live.py`

### CASE-001 inventory / identity / migration work package

Status: **metadata inventory verified; identity/evidence foundation implemented; migration compatibility validation integrated; physical migration not implemented**

- Metadata-only CASE-001 inventory: implemented and live-verified with 15 PDF documents and 0 folders.
- Document Identity: implemented and unit-verified.
- Inventory Evidence: implemented and unit-verified, including stable Document Identity references.
- CASE-001 Migration/Compatibility Layer: implemented and baseline unit-verified.
- Migration ↔ Document Identity validation: implemented.
- Migration ↔ Inventory Evidence exact-manifest validation: implemented.
- Physical Drive migration: deliberately not implemented.

Current artifacts:
- `docs/document-inventory.md`
- `docs/document-identity.md`
- `docs/case001-migration-compatibility.md`
- `src/agent_lab/document_inventory.py`
- `src/agent_lab/document_identity.py`
- `src/agent_lab/inventory_evidence.py`
- `src/agent_lab/case001_migration.py`
- `tests/unit/test_document_inventory.py`
- `tests/unit/test_document_identity.py`
- `tests/unit/test_inventory_evidence.py`
- `tests/unit/test_case001_migration.py`
- `scripts/case001_metadata_inventory.py`

Still planned before physical migration:
- `docs/agent-design.md`
- `docs/tool-contracts.md`
- stronger live CASE-001 migration manifest/preflight generation;
- human approval gate for consequential migration;
- physical migration executor with rollback and post-migration verification.

## Phase 3 — Evaluation and safety design

Status: planned

Goals:
- define what good performance means;
- build representative cases and adversarial cases;
- define failure taxonomy and safety boundaries;
- test case isolation and cross-case contamination;
- test identity resolution and multi-year retrieval.

Planned files:
- `docs/evaluation.md`
- `docs/safety.md`
- `docs/failure-modes.md`
- `tests/fixtures/README.md`

## Phase 4 — First executable prototype

Status: planned

Goals:
- implement the smallest useful end-to-end workflow;
- keep orchestration observable;
- test deterministic components independently;
- implement the case-scoped Drive connector before live document processing.

Planned files/directories:
- `src/agent_lab/`
- `src/agent_lab/orchestrator.py`
- `src/agent_lab/state.py`
- `src/agent_lab/case_registry.py`
- `src/agent_lab/case_resolver.py`
- `src/agent_lab/tools/`
- `src/agent_lab/agents/`
- `tests/unit/`
- `tests/integration/`
- isolation and cross-case test suites.

## Phase 5 — Evidence, observability, and auditability

Status: planned

Goals:
- make every consequential output traceable;
- capture tool calls and decisions;
- support post-run analysis;
- preserve case/run provenance.

Planned files:
- `docs/observability.md`
- `docs/provenance.md`
- `src/agent_lab/audit.py`
- `tests/evaluation/`

## Phase 6 — Adversarial testing and improvement

Status: planned

Goals:
- challenge the system deliberately;
- measure regressions;
- improve weak components based on evidence;
- attack scope boundaries, identity resolution, and tool permissions.

Planned files:
- `experiments/README.md`
- `experiments/`
- `docs/red-team.md`
- `tests/adversarial/`

## Phase 7 — Packaging and portfolio quality

Status: planned

Goals:
- reproducible setup;
- clear documentation;
- architecture diagrams;
- demonstration workflow;
- credible limitations and evaluation results.

Planned files:
- `pyproject.toml`
- README expansion
- `docs/demo.md`
- `docs/limitations.md`

## Future-file registry rule

A file listed as planned is **not** considered created or implemented until it exists in GitHub. A future file may be added, renamed, split, or cancelled only through an explicit update to this roadmap and, for significant changes, a decision record.

## Ordering rule

Do not jump directly to executable Agent implementation because coding feels productive. The project must first establish the case/identity/scope boundaries and the evidence/evaluation contracts that make later automation safe and testable.
