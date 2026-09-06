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
- define migration strategy for the existing CASE-001 structure.

Existing files:
- `docs/architecture.md`
- `docs/case-management.md`

Still planned:
- `docs/agent-design.md`
- `docs/tool-contracts.md`
- `docs/state-and-memory.md`

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
