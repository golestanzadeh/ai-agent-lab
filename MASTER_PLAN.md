# AI Agent Lab — Master Plan

## 1. Final destination

The project will produce a real, reproducible, evidence-driven Agentic AI system that solves one clearly defined complex real-world problem from end to end. The system must demonstrate controlled agentic behavior rather than merely calling an LLM repeatedly.

The final system should be:

- useful for a defined user and set of use cases;
- modular, observable, testable, and reproducible;
- grounded in authoritative evidence where evidence matters;
- explicit about uncertainty and limitations;
- capable of using tools under defined permissions;
- able to coordinate multiple specialized roles only where justified;
- protected by deterministic validation and human approval for consequential actions;
- auditable from input through evidence, tool calls, decisions, outputs, and approvals;
- evaluated against representative, edge, failure, and adversarial cases;
- packaged so another person can understand, run, test, and critique it;
- strong enough to serve as a credible portfolio demonstration of practical Agentic AI engineering.

## 2. Learning destination

The build itself is the course. By project completion, the learner should understand and be able to apply:

1. LLM applications versus agentic systems.
2. Agent roles, boundaries, prompts, tools, and stop conditions.
3. Orchestration and control loops.
4. State management and memory.
5. Tool calling and permission boundaries.
6. Retrieval, research, evidence extraction, and provenance.
7. Deterministic code around probabilistic models.
8. Structured outputs and validation.
9. Human-in-the-loop design.
10. Evaluation, benchmarks, regression testing, and error analysis.
11. Safety, security, privacy, and prompt-injection resistance.
12. Observability, tracing, auditability, and reproducibility.
13. Cost, latency, reliability, and model-selection trade-offs.
14. Deployment, maintenance, versioning, and operational failure handling.
15. How to improve an agentic system from measured evidence rather than intuition.

## 3. Domain and problem selection

The initial candidate is a complex document-heavy, evidence-driven workflow. Tax assistance is a candidate domain, not a locked decision.

Domain selection must be based on explicit criteria including:

- real-world usefulness;
- learning value;
- availability and quality of evidence/data;
- feasibility for a solo project;
- technical depth;
- safety and legal/ethical risk;
- ability to evaluate objectively;
- demonstrability;
- cost and operational complexity;
- privacy requirements;
- potential for meaningful agent/tool orchestration.

The final domain and problem must be recorded as a decision before implementation.

## 4. Lifecycle: Phase 0 to Phase 100

### Phase 0 — Foundation and project governance
Status: complete.

Establish the repository as source of truth, project constitution, project definition, roadmap, current state, decisions, anti-hallucination rules, repository structure, and future-file registry.

Exit criteria: project can be resumed from GitHub without relying on chat history.

### Phase 10 — Problem discovery and domain selection

Compare candidate domains and select one concrete problem.

Define:
- target user;
- user pain/problem;
- scope and non-scope;
- actors;
- inputs and outputs;
- constraints;
- risks;
- evidence requirements;
- measurable success criteria;
- minimum viable workflow;
- representative scenarios.

Deliverables: requirements, domain selection, use cases, decision record.

Exit criteria: one problem is explicitly approved and testable.

### Phase 20 — Workflow decomposition

Map the selected problem from input to final outcome.

Determine:
- which steps are deterministic;
- which steps need reasoning;
- where tools are needed;
- where evidence enters;
- where uncertainty exists;
- where decisions branch;
- where human approval is required;
- where failure can occur;
- which parts should not be autonomous.

Exit criteria: an end-to-end workflow exists independently of agent implementation.

### Phase 30 — Architecture and contracts

Design the system before significant implementation.

Define:
- components and boundaries;
- orchestrator/control loop;
- agent roles;
- agent inputs/outputs;
- tool contracts;
- permissions;
- state model;
- memory model;
- evidence/provenance model;
- structured schemas;
- human approval gates;
- error handling;
- termination/stop conditions;
- retry and recovery behavior.

Explicitly decide what is NOT an agent.

Exit criteria: architecture is reviewable and implementation-ready.

### Phase 40 — Evaluation and safety specification

Define how the system will be judged before optimizing it.

Build:
- evaluation rubric;
- golden/expected cases where feasible;
- representative cases;
- edge cases;
- failure cases;
- adversarial cases;
- regression policy;
- safety threat model;
- misuse cases;
- privacy rules;
- prompt-injection/tool-abuse defenses;
- approval policy.

Exit criteria: a failing system can be distinguished from a successful one using repeatable evidence.

### Phase 50 — Minimum executable prototype

Implement the smallest useful end-to-end workflow.

Requirements:
- real inputs;
- real outputs;
- minimal justified agent count;
- deterministic validation;
- observable execution;
- automated tests for deterministic components;
- no premature infrastructure complexity.

Exit criteria: one complete workflow runs reproducibly from input to output.

### Phase 60 — Evidence, tools, state, and orchestration maturity

Add and harden:
- real tool integrations;
- retrieval/research where justified;
- evidence extraction and citation/provenance;
- state transitions;
- memory where justified;
- agent delegation/routing;
- structured tool results;
- permission enforcement;
- human approval flows.

Exit criteria: agentic behavior is controlled, useful, and traceable.

### Phase 70 — Evaluation, observability, and auditability

Build the measurement and inspection layer.

Measure as appropriate:
- task success;
- factual/evidence correctness;
- citation/source quality;
- completeness;
- failure rate;
- unsafe-action rate;
- tool-call accuracy;
- latency;
- token/model cost;
- human intervention rate;
- repeatability.

Implement logs, traces, audit events, provenance, and run summaries.

Exit criteria: every important run can be inspected and compared with previous runs.

### Phase 80 — Adversarial testing and systematic improvement

Attack the system deliberately.

Test:
- ambiguous inputs;
- missing evidence;
- conflicting evidence;
- malformed documents;
- tool failures;
- stale information;
- prompt injection;
- instruction conflicts;
- hallucination pressure;
- excessive delegation;
- loops and runaway execution;
- unsafe requests;
- unexpected outputs.

For each important failure: reproduce, classify, measure, fix, retest, and record.

Exit criteria: major known failure modes have mitigations or explicit documented limitations.

### Phase 90 — Reliability, deployment, and operational readiness

Harden the system for repeatable use.

Address:
- configuration management;
- secrets handling;
- dependency management;
- model/version pinning where appropriate;
- reproducible environment;
- error recovery;
- timeouts and rate limits;
- cost controls;
- data retention;
- privacy;
- monitoring;
- backup/recovery considerations;
- upgrade strategy;
- operational documentation.

Exit criteria: the system can be run repeatedly without manual archaeology.

### Phase 95 — Portfolio and demonstration quality

Prepare the project for external technical review.

Deliver:
- clear README;
- architecture diagram;
- end-to-end demo;
- setup instructions;
- evaluation summary;
- example runs;
- known limitations;
- design decisions;
- failure analysis;
- explanation of what was learned.

Exit criteria: a technically literate outsider can understand why the system exists, how it works, how it was evaluated, and where it fails.

### Phase 100 — Final release and project retrospective

Freeze a documented release state and perform a complete review.

Verify:
- requirements satisfied;
- architecture matches implementation;
- tests pass;
- evaluation results are recorded;
- safety boundaries are explicit;
- provenance is intact;
- known limitations are documented;
- setup is reproducible;
- repository contains no secrets or accidental private data;
- final demo works;
- major decisions are recorded;
- learning objectives are mapped to concrete project evidence.

Create a final retrospective covering what worked, what failed, what changed from the original plan, and what should be built next.

## 5. Cross-cutting work that spans all phases

These are not optional end-stage features. They are maintained throughout the lifecycle:

- documentation and decision records;
- current-state updates;
- source/evidence discipline;
- testing;
- security/privacy;
- cost awareness;
- observability;
- reproducibility;
- version control;
- failure tracking;
- learning notes;
- scope control;
- explicit uncertainty.

## 6. Change management

The initial plan is a baseline, not a prison. The project is expected to evolve.

Changes must be evidence-driven and recorded. Significant changes require an update to the roadmap and/or a decision record. The current state must always describe what is actually implemented, not what was originally intended.

A planned file is not a created file. A proposed component is not an implemented component. A successful demo is not proof of reliability.

## 7. Definition of done for the whole project

Phase 100 is reached only when the project has a working system plus the evidence needed to judge it. Code alone is insufficient.

The final repository must allow a new session, agent, or human reviewer to reconstruct:

- why the project exists;
- what problem it solves;
- what was chosen and rejected;
- how the system works;
- what data/evidence it uses;
- what agents and tools exist and why;
- what controls exist;
- how it is evaluated;
- what failed;
- what changed;
- how to reproduce it;
- what its limitations are;
- what was learned.
