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
- anchor CASE-001 migration validation to Document Identity and Inventory Evidence;
- implement the deterministic human approval boundary for consequential actions.

### Preserved detailed Phase-2 register

Accepted architecture/storage/migration documents include:
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
- `docs/approval-gate.md`
- `docs/artifact-identity.md`
- `docs/case001-approval-context.md`

Implemented runtime foundations include:
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
- `src/agent_lab/case001_migration_manifest.py`
- `src/agent_lab/case001_live_target_preflight.py`
- `src/agent_lab/approval.py`
- `src/agent_lab/artifact_identity.py`
- `src/agent_lab/case001_approval_context.py`
- D-021 provisioning/approval-preparation implementation on `d021-agent-case-provisioning`.

Historical verification recorded before Agent Bridge productionization includes the accepted case-isolation, storage-adapter, identity, migration, approval and artifact-identity suites. The latest branch-wide Step-10 verification is **252 passed, 1 skipped**.

### Google Drive Storage Adapter

Status: **complete through Stage 6**

The provider-neutral contract, case-scoped resolver integration, metadata-only adapter, deterministic scope enforcement, unit/live isolation verification, and documentation gate are complete. Live storage access remains bounded by accepted case-isolation and authorization rules.

### CASE-001 inventory / identity / migration work package

Status: **metadata inventory verified; identity/evidence foundation implemented; migration compatibility and live target preflight implemented; approval gate implemented; physical migration not implemented**

- Metadata-only CASE-001 inventory: 15 PDFs, 0 folders.
- Document Identity and Inventory Evidence: implemented and verified.
- CASE-001 migration compatibility, deterministic Manifest, Live Target Preflight, D-017 Approval Gate, D-018 Artifact Identity, and D-020 Approval Context Composition: implemented.
- D-021 standard target provisioning and approval preparation: implementation complete on its branch.
- Physical Drive migration: deliberately not implemented.
- Durable/reloadable approval lifecycle is the active Step-11 work package.

Still required before any physical migration executor is accepted:
- durable/reloadable approval lifecycle implementation and verification;
- controlled physical migration executor;
- rollback and post-migration verification;
- a separate consequential Human Gate for execution.

## Phase 3 — Evaluation and safety design

Status: planned

Planned files include `docs/evaluation.md`, `docs/safety.md`, `docs/failure-modes.md`, and `tests/fixtures/README.md`.

## Phase 4 — First executable prototype

Status: planned

The smallest useful end-to-end workflow must remain observable and case-scoped, with deterministic components independently testable.

## Phase 5 — Evidence, observability, and auditability

Status: planned

Consequential outputs must remain traceable with case/run provenance and post-run analysis support.

## Phase 6 — Adversarial testing and improvement

Status: planned

Challenge scope boundaries, identity resolution, tool permissions, and regressions deliberately.

## Phase 7 — Packaging and portfolio quality

Status: planned

Reproducible setup, clear documentation, architecture diagrams, demonstration workflow, limitations, and evaluation evidence.

## D-020 approved integration boundary

D-020 is accepted and integrated into main. Its composition layer binds exact Manifest and successful Live Target Preflight artifact identities into D-017 execution context. It does not grant/consume approval or perform migration.

## Agent Bridge Production Migration — approved sequential plan

Status: **production accepted; Step 11 active**

1. Baseline + Durable Documentation + Canonical State Cleanup — **complete**.
2. Production Architecture and Governance — **human accepted 2026-09-10**.
3. Protocol Contract — **defined**.
4. Production Security Model — **defined**.
5. Passive / Observe-only Bridge — **complete**.
6. Codex Bounded Execution — **complete**.
7. GitHub → Work Response Wake-up and independent review — **complete**.
8. Controlled Continuation for low-risk bounded tasks only — **complete**.
9. Deliberate Human Gate validation — **complete; HUMAN_REQUIRED terminal behavior proved**.
10. Production acceptance, rollback drill, audit and kill-switch verification — **complete; production human-accepted 2026-09-10**.
11. Resume AI-Tax-Agent development at the durable/reloadable approval lifecycle blocker — **active; architecture human-accepted 2026-09-10**.

Agent Bridge is a **development control plane only**. It does not replace D-017, authorize approval consumption, or authorize physical migration.

### Agent Bridge production files

- `docs/agent-bridge-production.md`
- `.github/workflows/agent-bridge-passive.yml`
- `.github/workflows/agent-bridge-codex.yml`
- `.github/workflows/agent-bridge-response.yml`
- `scripts/agent_bridge_validate.py`
- `tests/unit/test_agent_bridge_validate.py`

Temporary probe trigger files and disposable test branches are validation artifacts, not long-term production interfaces, and should be removed or left unmerged when no longer needed.

### Durable/reloadable approval lifecycle — Step 11 future-file registry

Architecture accepted by the human on 2026-09-10. The following files are registered before implementation:

- `docs/durable-approval-lifecycle.md` — durable authority model, SQLite transaction boundary, schema/versioning, reload, crash recovery, audit linkage, tamper/fail-closed behavior, and migration boundary from the in-memory store.
- `src/agent_lab/durable_approval.py` — SQLite-backed durable approval authority preserving D-017 binding/lifecycle semantics.
- `tests/unit/test_durable_approval.py` — persistence/reload, exact binding, one-time consumption, concurrency, rollback, corruption, schema-version and legacy-export rejection tests.

Existing files expected to receive bounded integration changes:
- `src/agent_lab/approval.py` — shared domain value/validation reuse only; in-memory store remains available for compatibility unless explicitly superseded.
- `src/agent_lab/audit.py` — only if required to preserve one durable transactional boundary without introducing a second audit subsystem.
- `docs/approval-gate.md` — durable extension and compatibility boundary.
- `DECISIONS.md` and `CURRENT_STATE.md` — accepted decision/evidence state.

Implementation constraints:
- SQLite is the initial durable backend for the local single-host runtime.
- Approval and its authoritative approval-lifecycle audit event must commit in one SQLite transaction for durable lifecycle transitions.
- Executable authority is reconstructed only from validated durable records, never from exported review JSON/text or chat/GitHub prose.
- Unknown schema version, integrity mismatch, partial/corrupt state, case/run mismatch, or transaction uncertainty fails closed.
- `CONSUMED` remains terminal and exactly-once across process restart and concurrent consumers.
- No physical Drive mutation or approval consumption of the real CASE-001 approval is authorized by this work package.

## Future-file registry rule

A file listed as planned is **not** considered created or implemented until it exists in GitHub. A future file may be added, renamed, split, or cancelled only through an explicit update to this roadmap and, for significant changes, a decision record.

## Ordering rule

Do not jump directly to executable Agent implementation because coding feels productive. Case/identity/scope, evidence/evaluation, governance, protocol, and security boundaries must exist before automation is trusted.
