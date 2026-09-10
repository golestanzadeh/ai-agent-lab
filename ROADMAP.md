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

Existing files include the accepted architecture/case/storage/migration/approval documents and their tested runtime foundations under `src/agent_lab/` and `tests/`.

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
- Durable/reloadable approval lifecycle remains required before physical execution can be designed or considered.

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

Status: **in progress**

1. Baseline + Durable Documentation + Canonical State Cleanup — **complete**.
2. Production Architecture and Governance — **human accepted 2026-09-10**.
3. Protocol Contract — **defined; implementation pending**.
4. Production Security Model — **defined; implementation pending**.
5. Passive / Observe-only Bridge — next implementation stage.
6. Codex Bounded Execution.
7. GitHub → Work Response Wake-up and independent review.
8. Controlled Continuation for low-risk bounded tasks only.
9. Deliberate Human Gate validation.
10. Production acceptance, rollback drill, audit and kill-switch verification.
11. Resume AI-Tax-Agent development at the durable/reloadable approval lifecycle blocker.

Agent Bridge is a **development control plane only**. It does not replace D-017, authorize approval consumption, or authorize physical migration.

### Agent Bridge future-file registry

The following files are registered before creation:

- `docs/agent-bridge-production.md` — accepted production architecture, protocol, Human Gate matrix, security model, rollback and operational boundaries.
- `.github/workflows/agent-bridge-passive.yml` — Step-5 observe-only REQUEST validation; no Codex execution or repository write authority.
- `.github/workflows/agent-bridge-codex.yml` — later bounded Codex execution workflow; must not be activated until Step 6 and its prerequisites are satisfied.
- `.github/workflows/agent-bridge-response.yml` — later response/wake-up path; must not be activated until Step 7 and its prerequisites are satisfied.
- `scripts/agent_bridge_validate.py` — deterministic protocol/parser/validation boundary.
- `tests/unit/test_agent_bridge_validate.py` — protocol, fail-closed, replay/idempotency and Human-Gate validation tests.

Registration does not authorize creation or activation before the corresponding sequential migration step.

## Future-file registry rule

A file listed as planned is **not** considered created or implemented until it exists in GitHub. A future file may be added, renamed, split, or cancelled only through an explicit update to this roadmap and, for significant changes, a decision record.

## Ordering rule

Do not jump directly to executable Agent implementation because coding feels productive. Case/identity/scope, evidence/evaluation, governance, protocol, and security boundaries must exist before automation is trusted.
