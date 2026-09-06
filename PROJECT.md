# Project Definition

## Mission

Build a real, traceable Agentic AI system while using the build itself as a structured course in agent architecture, orchestration, tools, memory, evaluation, safety, and operations.

## Learning outcomes

By the end of the project, the user should be able to:

- explain the difference between an LLM application and an agentic system;
- design agent roles, tools, state, memory, and control loops;
- build deterministic components around probabilistic models;
- implement evidence and source tracing;
- evaluate agents with repeatable tests and failure cases;
- apply human approval to consequential actions;
- diagnose failures and improve an agent systematically;
- present the resulting system as a credible portfolio project.

## Candidate system

A multi-agent system for a complex, document-heavy, evidence-driven process is the current candidate. Tax assistance is one candidate domain because it naturally exercises research, document extraction, evidence matching, reasoning, optimization, auditing, and human approval. The domain remains uncommitted until Phase 1 evaluation.

## Initial architectural hypothesis

Potential components include:

- Case/Orchestrator Agent
- Specialist Agents created or selected according to the case
- Document Extraction Agent
- Evidence Matching Agent
- Research Agent
- Analysis/Optimization Agent
- Devil's Advocate / Challenge Agent
- Auditor / QA Agent
- Human Approval Gate
- Shared case state and audit trail

These are hypotheses, not implementation commitments.

## Success criteria

The project is successful when it demonstrates a useful end-to-end workflow, traceable evidence, controlled agent/tool use, measurable evaluation, documented failure modes, and reproducible execution.

## Explicit non-goals for the early phases

- building a generic autonomous agent framework;
- maximizing the number of agents;
- adding tools merely because they are available;
- claiming legal or tax correctness without authoritative evidence and human review;
- optimizing infrastructure before the workflow and evaluation are understood.