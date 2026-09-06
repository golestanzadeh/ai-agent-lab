# Roadmap

This is the authoritative plan for the project. Planned files are registered here before they are created so future work is not reconstructed from memory.

## Phase 0 — Initialization

Status: **complete**

- Establish repository as source of truth.
- Create operating principles and project definition.
- Create anti-hallucination rules.
- Establish this roadmap and future-file registry.

## Phase 1 — Problem and requirements

Status: **next**

Goals:
- compare candidate real-world domains;
- select one problem using explicit criteria;
- define users, inputs, outputs, constraints, risks, and success metrics;
- define the minimum viable workflow before adding agent complexity.

Planned files:
- `docs/requirements.md` — problem statement, actors, inputs/outputs, constraints, acceptance criteria.
- `docs/domain-selection.md` — candidate domains, scoring, rejected alternatives, final choice.
- `docs/use-cases.md` — concrete scenarios and expected outcomes.

## Phase 2 — System architecture

Status: planned

Goals:
- define control loop and state model;
- decide which tasks require agents versus deterministic code;
- define tool interfaces and evidence flow;
- define human approval points.

Planned files:
- `docs/architecture.md` — system architecture and component boundaries.
- `docs/agent-design.md` — agent roles, responsibilities, inputs, outputs, tools, and stop conditions.
- `docs/tool-contracts.md` — tool schemas, permissions, failure behavior, and safety constraints.
- `docs/state-and-memory.md` — working state, persistent memory, provenance, and retention rules.

## Phase 3 — Evaluation and safety design

Status: planned

Goals:
- define what good performance means;
- build representative cases and adversarial cases;
- define failure taxonomy and safety boundaries.

Planned files:
- `docs/evaluation.md` — metrics, test strategy, benchmark design, and regression policy.
- `docs/safety.md` — threat model, approval gates, misuse cases, and containment.
- `docs/failure-modes.md` — known and expected failure classes.
- `tests/fixtures/README.md` — structure and provenance of evaluation fixtures.

## Phase 4 — First executable prototype

Status: planned

Goals:
- implement the smallest useful end-to-end workflow;
- keep orchestration observable;
- test deterministic components independently.

Planned files/directories:
- `src/agent_lab/` — application package.
- `src/agent_lab/orchestrator.py` — initial control loop.
- `src/agent_lab/state.py` — case state model.
- `src/agent_lab/tools/` — tool adapters.
- `src/agent_lab/agents/` — agent implementations.
- `tests/unit/` — unit tests.
- `tests/integration/` — workflow tests.

## Phase 5 — Evidence, observability, and auditability

Status: planned

Goals:
- make every consequential output traceable;
- capture tool calls and decisions;
- support post-run analysis.

Planned files:
- `docs/observability.md` — logs, traces, events, and debugging strategy.
- `docs/provenance.md` — source/evidence lineage.
- `src/agent_lab/audit.py` — audit event model and recorder.
- `tests/evaluation/` — automated evaluation suites.

## Phase 6 — Adversarial testing and improvement

Status: planned

Goals:
- challenge the system deliberately;
- measure regressions;
- improve weak components based on evidence.

Planned files:
- `experiments/README.md` — experiment protocol.
- `experiments/` — dated experiment records.
- `docs/red-team.md` — adversarial testing strategy.
- `tests/adversarial/` — adversarial cases.

## Phase 7 — Packaging and portfolio quality

Status: planned

Goals:
- reproducible setup;
- clear documentation;
- architecture diagrams;
- demonstration workflow;
- credible limitations and evaluation results.

Planned files:
- `pyproject.toml` — Python project metadata and dependencies, once implementation language/framework is confirmed.
- `README` expansion — installation, usage, architecture, evaluation summary.
- `docs/demo.md` — reproducible demonstration.
- `docs/limitations.md` — known limitations and non-goals.

## Future-file registry rule

A file listed as planned is **not** considered created or implemented until it exists in GitHub. A future file may be added, renamed, split, or cancelled only through an explicit update to this roadmap and, for significant changes, a decision record.

## Ordering rule

Do not jump directly to Phase 4 because coding feels productive. Phases 1–3 define what we are building and how we will know whether it works. That prevents the usual human tradition of constructing a magnificent solution to the wrong problem.