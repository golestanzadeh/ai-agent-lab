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
- `src/agent_lab/durable_approval.py`
- `src/agent_lab/case001_physical_migration.py`
- `src/agent_lab/google_drive_mutation.py`
- D-021 provisioning/approval-preparation implementation on `d021-agent-case-provisioning`.

Latest branch-wide verification for the controlled migration work package is **279 passed, 1 skipped**.

### Google Drive Storage Adapter

Status: **complete through Stage 6**

The provider-neutral contract, case-scoped resolver integration, metadata-only adapter, deterministic scope enforcement, unit/live isolation verification, and documentation gate are complete. Live storage access remains bounded by accepted case-isolation and authorization rules.

### CASE-001 inventory / identity / migration work package

Status: **controlled physical migration executor and guarded Drive mutation adapter implemented and synthetically verified; controlled local execution harness is being completed; real CASE-001 execution is Human-Gated**

- Metadata-only CASE-001 inventory: last recorded 15 PDFs, 0 folders; fresh live reconstruction is required before execution.
- Document Identity and Inventory Evidence: implemented and verified.
- CASE-001 migration compatibility, deterministic Manifest, Live Target Preflight, D-017 Approval Gate, D-018 Artifact Identity, D-020 Approval Context Composition, durable/reloadable approval, controlled executor, and guarded Drive mutation adapter: implemented.
- D-021 standard target provisioning and approval preparation: implementation complete on its branch.
- Physical Drive migration against real CASE-001 data has **not** been executed.

Still required before real physical migration:
- fresh authoritative live inventory, manifest, and target preflight reconstruction;
- a newly created durable executable approval for that exact binding;
- explicit human grant and separate consequential Human Gate for the live attempt;
- post-execution evidence before any legacy alias retirement.

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

Status: **production accepted; Step 11 durable approval accepted; controlled migration executor verified; real execution Human-Gated**

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
11. Resume AI-Tax-Agent development at the durable/reloadable approval lifecycle blocker — **complete; architecture and stage human-accepted 2026-09-10**.

Agent Bridge is a **development control plane only**. It does not replace D-017, authorize approval consumption, or authorize physical migration.

### Agent Bridge production files

- `docs/agent-bridge-production.md`
- `.github/workflows/agent-bridge-passive.yml`
- `.github/workflows/agent-bridge-codex.yml`
- `.github/workflows/agent-bridge-response.yml`
- `scripts/agent_bridge_validate.py`
- `tests/unit/test_agent_bridge_validate.py`

Temporary probe trigger files and disposable test branches are validation artifacts, not long-term production interfaces, and should be removed or left unmerged when no longer needed.

### Durable/reloadable approval lifecycle — Step 11

Architecture and stage accepted by the human on 2026-09-10.

Implemented files:
- `docs/durable-approval-lifecycle.md`
- `src/agent_lab/durable_approval.py`
- `tests/unit/test_durable_approval.py`

Implementation constraints remain authoritative:
- SQLite is the initial durable backend for the local single-host runtime.
- Approval and its authoritative approval-lifecycle audit event commit in one SQLite transaction for durable lifecycle transitions.
- Executable authority is reconstructed only from validated durable records, never from exported review JSON/text or chat/GitHub prose.
- Unknown schema version, integrity mismatch, partial/corrupt state, case/run mismatch, or transaction uncertainty fails closed.
- `CONSUMED` remains terminal and exactly-once across process restart and concurrent consumers.

### Controlled physical migration executor — implemented and verified

Registered before implementation on 2026-09-10 and now present:
- `docs/physical-migration-executor.md`
- `src/agent_lab/case001_physical_migration.py`
- `tests/unit/test_case001_physical_migration.py`
- `src/agent_lab/google_drive_mutation.py`
- `tests/unit/test_google_drive_mutation.py`

Controlled harness registered before creation:
- `scripts/case001_controlled_migration.py` — local runtime entry point for fresh inventory/manifest/preflight reconstruction, dry-run, and separately Human-Gated live execution using a new durable approval.
- `tests/unit/test_case001_controlled_migration.py` — fail-closed mode/authorization and safe-summary tests without live Drive access.

Verification already recorded:
- CI run `34509462092`: executor tests **9 passed**, full suite **272 passed, 1 skipped**.
- CI run `34509683965`: executor **9 passed**, guarded Drive adapter **7 passed**, durable approval **11 passed**, Bridge validator **6 passed**, full suite **279 passed, 1 skipped**.
- CI run `34509914717`: all registered migration/durable/Bridge regression checks **success** after the Human-Gate state update.

Executor/harness constraints:
- dry-run is the default and performs zero mutations and zero approval lifecycle changes;
- live execution requires an exact newly created durable `APPROVED` authorization and separately explicit live enablement;
- creation/grant of the real durable approval and the live attempt occur only after the final consequential Human Gate;
- the executor operates only on explicit manifest object IDs and explicit source/target parent IDs, never names or Drive-wide search;
- each mutation preserves provider object ID and logical document identity;
- partial failure attempts reverse-order rollback of already-applied moves;
- incomplete rollback or unverifiable post-state fails closed and is never success;
- post-migration verification proves exact target placement before approval consumption;
- approval consumption occurs only after successful post-migration verification; consumption failure triggers storage rollback;
- real CASE-001 execution, new durable grant, and approval consumption remain behind the separate consequential Human Gate.

## Future-file registry rule

A file listed as planned is **not** considered created or implemented until it exists in GitHub. A future file may be added, renamed, split, or cancelled only through an explicit update to this roadmap and, for significant changes, a decision record.

## Ordering rule

Do not jump directly to executable Agent implementation because coding feels productive. Case/identity/scope, evidence/evaluation, governance, protocol, and security boundaries must exist before automation is trusted.
