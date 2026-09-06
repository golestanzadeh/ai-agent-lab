# Project Definition

## Mission

Build a real, traceable Agentic AI system for a defined tax-assistance workflow while using the build itself as a structured course in agent architecture, orchestration, tools, memory, evaluation, safety, and operations.

## Final objective

The final system should be able to take a defined tax case and its supporting documents, extract and reconcile relevant facts, research authoritative tax rules and evidence, identify applicable considerations and potential options, challenge its own reasoning, audit the resulting analysis, and produce a traceable report that clearly separates facts, evidence, assumptions, calculations, conclusions, uncertainty, and items requiring human review.

The system is an evidence-driven decision-support system, not an autonomous tax authority and not a replacement for a tax professional.

## Learning outcomes

By the end of the project, the user should be able to:

- explain the difference between an LLM application and an agentic system;
- design agent roles, tools, state, memory, and control loops;
- build deterministic components around probabilistic models;
- implement evidence and source tracing;
- evaluate agents with repeatable tests and failure cases;
- apply human approval to consequential actions;
- diagnose failures and improve an agent systematically;
- understand prompt injection, tool abuse, privacy, and operational risks;
- measure cost, latency, reliability, and quality trade-offs;
- present the resulting system as a credible portfolio project.

## Primary domain

**Tax assistance** is the selected primary project domain. The concrete tax problem, jurisdiction, user profile, and initial scope will be defined during Phase 10 before implementation.

The initial design should remain narrow enough to evaluate rigorously but rich enough to exercise document understanding, retrieval/research, evidence grounding, structured reasoning, specialist delegation, conflict resolution, validation, adversarial testing, auditability, and human-in-the-loop control.

## Initial architectural hypothesis

Potential components include:

- Case/Orchestrator Agent
- Specialist Agents selected according to the case
- Document Extraction Agent or deterministic document pipeline
- Evidence Matching / Reconciliation component
- Research Agent
- Analysis / Optimization Agent
- Devil's Advocate / Challenge Agent
- Auditor / QA Agent
- Human Approval Gate
- Shared case state
- Evidence/provenance layer
- Audit trail and observability layer

These remain hypotheses until workflow decomposition and architecture design justify each component. The project will explicitly decide what should be an agent and what should remain deterministic code.

## Success criteria

The project is successful when it demonstrates a useful end-to-end tax-assistance workflow with traceable evidence, controlled agent/tool use, deterministic validation where appropriate, measurable evaluation, documented failure modes, adversarial testing, human approval for consequential judgment, reproducible execution, and clear operational limitations.

## Explicit non-goals

- building a generic autonomous agent framework;
- maximizing the number of agents;
- replacing qualified tax professionals or official tax authorities;
- making unsupported legal/tax correctness claims;
- silently taking consequential external actions;
- adding tools merely because they are available;
- using personal or real taxpayer data unnecessarily in development;
- optimizing infrastructure before workflow and evaluation are understood.
