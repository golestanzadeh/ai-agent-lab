# AI Agent Lab — Master Plan

## 1. Final destination

The project will produce a real, reproducible, evidence-driven Agentic AI system for tax work in Germany, ultimately supporting natural persons and legal entities across defined tax workflows.

The target system should be capable of performing supported tax matters to a senior tax-expert standard, from user-supplied documents and information through validated analysis, preparation of final tax documents, and controlled electronic submission where an official and lawful technical path exists.

A golden objective applies across the entire system: **Maximize Legally Achievable Tax Benefit** by minimizing legally payable tax and maximizing legally recoverable/refundable tax. This is a continuous optimization objective, not merely a final reporting feature.

The system must demonstrate controlled agentic behavior rather than merely calling an LLM repeatedly. It must remain grounded in authoritative German tax sources and must verify the rules applicable to the relevant tax year and case at execution time.

The final system should be:

- useful for defined German tax users and use cases;
- modular, observable, testable, and reproducible;
- grounded in authoritative and current German tax evidence;
- explicit about effective dates, tax years, uncertainty, and limitations;
- capable of using tools under defined permissions;
- able to coordinate multiple specialized roles only where justified;
- continuously alert to lawful tax-optimization opportunities and able to feed validated opportunities back into the workflow;
- protected by deterministic validation and human approval for consequential actions;
- auditable from input through evidence, research, calculations, decisions, outputs, and approvals;
- capable of producing complete printable and submission-ready outputs for supported workflows;
- capable of controlled electronic submission where technically and legally supported;
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
16. How to design and evaluate a continuous tax-optimization control loop without sacrificing legality, evidence, or auditability.

## 3. Domain and problem selection

**German tax assistance is selected as the primary domain.** The final destination covers tax workflows for natural persons and legal entities, while the first executable workflow must be narrowed to a concrete, testable use case during Phase 10.

Phase 10 must define the first supported tax problem, target user, jurisdiction details, tax year(s), scope/non-scope, inputs, outputs, authoritative evidence requirements, current-law verification strategy, measurable success criteria, optimization objectives/metrics, and representative cases.

The first workflow should be narrow enough to evaluate rigorously but rich enough to exercise document understanding, retrieval/research, evidence grounding, structured reasoning, calculations, validation, optimization, challenge, auditability, and human-in-the-loop control.

## 4. Lifecycle: Phase 0 to Phase 100

### Phase 0 — Foundation and project governance
Status: complete.

Establish the repository as source of truth, project constitution, project definition, roadmap, current state, decisions, anti-hallucination rules, repository structure, and future-file registry.

Exit criteria: project can be resumed from GitHub without relying on chat history.

### Phase 10 — Problem discovery and requirements

Define the first concrete German tax workflow and its requirements.

Define:
- target user: natural person or legal entity, or a deliberately limited subset;
- tax jurisdiction and relevant tax authority context;
- tax year(s) and effective-date requirements;
- user pain/problem;
- scope and non-scope;
- actors and approval responsibilities;
- input documents/data;
- expected outputs and official forms/documents;
- current-law verification and authoritative source requirements;
- calculations and validation requirements;
- **tax-optimization objective, opportunity categories, financial-impact model, and measurable optimization metrics**;
- privacy/security constraints;
- submission requirements and technical/legal boundaries;
- measurable success criteria;
- minimum viable workflow;
- representative scenarios.

Deliverables: requirements, domain/scope record, use cases, decision records.

Exit criteria: one first workflow is explicitly approved and objectively testable.

### Phase 20 — Workflow decomposition

Map the selected problem from input to final outcome.

Determine:
- which steps are deterministic;
- which steps need reasoning;
- where tools are needed;
- where current-law evidence enters;
- how source freshness/effective dates are checked;
- where optimization opportunities are detected;
- how the Tax Optimization Supervisor can challenge, redirect, or request rework;
- where uncertainty exists;
- where decisions branch;
- where human approval is required;
- where filing/submission is allowed;
- where failure can occur;
- which parts should not be autonomous.

Exit criteria: an end-to-end workflow exists independently of agent implementation.

### Phase 30 — Architecture and contracts

Design the system before significant implementation.

Define:
- components and boundaries;
- orchestrator/control loop;
- agent roles, including whether a dedicated **Tax Optimization Supervisor** is justified;
- agent inputs/outputs;
- tool contracts;
- permissions;
- state model;
- memory model;
- current-law/source model;
- evidence/provenance model;
- structured schemas;
- calculation and validation boundaries;
- optimization opportunity and scenario schemas;
- human approval gates;
- submission controls;
- error handling;
- termination/stop conditions;
- retry and recovery behavior.

Explicitly decide what is NOT an agent.

Exit criteria: architecture is reviewable and implementation-ready.

### Phase 40 — Evaluation and safety specification

Define how the system will be judged before optimizing it.

Build:
- evaluation rubric;
- trusted reference cases;
- representative cases;
- edge cases;
- failure cases;
- adversarial cases;
- current-law freshness/effective-date tests;
- **tax-optimization opportunity coverage tests**;
- **missed-opportunity, false-positive, and financial-impact accuracy metrics where trusted references permit**;
- regression policy;
- safety threat model;
- misuse cases;
- privacy rules;
- prompt-injection/tool-abuse defenses;
- approval and submission policy.

Exit criteria: a failing system can be distinguished from a successful one using repeatable evidence.

### Phase 50 — Minimum executable prototype

Implement the smallest useful end-to-end workflow.

Requirements:
- real inputs;
- real outputs;
- minimal justified agent count;
- deterministic validation;
- authoritative evidence retrieval for the supported case;
- observable execution;
- automated tests for deterministic components;
- no premature infrastructure complexity.

The prototype must demonstrate the optimization loop for the supported workflow, even if the first implementation uses a narrow set of optimization rules.

Exit criteria: one complete workflow runs reproducibly from input to output.

### Phase 60 — Evidence, tools, state, and orchestration maturity

Add and harden:
- real tool integrations;
- authoritative German tax retrieval/research;
- current-law and effective-date verification;
- evidence extraction and citation/provenance;
- state transitions;
- memory where justified;
- agent delegation/routing;
- structured tool results;
- calculation engines and deterministic checks;
- permission enforcement;
- **continuous optimization supervision, opportunity detection, and alternative-scenario evaluation**;
- human approval flows;
- controlled submission integrations where justified.

Exit criteria: agentic behavior is controlled, useful, current-law-aware, and traceable.

### Phase 70 — Evaluation, observability, and auditability

Build the measurement and inspection layer.

Measure as appropriate:
- task success;
- factual/evidence correctness;
- current-law correctness and freshness;
- citation/source quality;
- completeness;
- calculation correctness;
- **tax-optimization opportunity recall/coverage**;
- **missed-opportunity rate**;
- **false-positive optimization rate**;
- **financial-impact estimation accuracy**;
- failure rate;
- unsafe-action rate;
- tool-call accuracy;
- submission accuracy where applicable;
- latency;
- token/model cost;
- human intervention rate;
- repeatability.

Implement logs, traces, audit events, provenance, source snapshots/identifiers where lawful and practical, and run summaries. Optimization decisions and feedback loops must be auditable.

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
- changed tax rules;
- incorrect effective dates;
- **optimization opportunities hidden in new evidence or rule changes**;
- **tempting but legally invalid deductions/claims**;
- prompt injection;
- instruction conflicts;
- hallucination pressure;
- excessive delegation;
- loops and runaway execution;
- unsafe requests;
- unauthorized submission attempts;
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
- source availability/failure handling;
- upgrade strategy;
- operational documentation;
- controlled submission/authentication handling.

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
- representative final tax-document package;
- current-law evidence demonstration;
- **tax-optimization demonstration showing baseline versus optimized lawful outcome**;
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
- current-law verification is demonstrably effective;
- **tax optimization is demonstrably systematic, lawful, evidence-backed, and measurable for supported workflows**;
- safety boundaries are explicit;
- provenance is intact;
- known limitations are documented;
- setup is reproducible;
- repository contains no secrets or accidental private data;
- final demo works;
- supported final documents are print-ready;
- controlled submission path works where supported and authorized;
- major decisions are recorded;
- learning objectives are mapped to concrete project evidence.

Create a final retrospective covering what worked, what failed, what changed from the original plan, and what should be built next.

## 5. Cross-cutting work that spans all phases

These are not optional end-stage features. They are maintained throughout the lifecycle:

- documentation and decision records;
- current-state updates;
- source/evidence discipline;
- current-law verification;
- **lawful tax-benefit optimization**;
- testing;
- security/privacy;
- cost awareness;
- observability;
- reproducibility;
- version control;
- failure tracking;
- learning notes;
- scope control;
- explicit uncertainty;
- controlled human approval for consequential actions.

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
- how current German tax law is verified;
- **how the system searches for and validates lawful tax-optimization opportunities**;
- what agents and tools exist and why;
- what controls exist;
- how final documents are generated and submitted;
- how it is evaluated;
- what failed;
- what changed;
- how to reproduce it;
- what its limitations are;
- what was learned.
