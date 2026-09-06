# Project Definition

## Mission

Build a real, traceable Agentic AI system for tax work in Germany, using the build itself as a structured course in agent architecture, orchestration, tools, memory, evaluation, safety, and operations.

## Final objective

The target system is a Germany-focused tax-assistance system for **natural persons and legal entities**. It should be designed to perform, to a senior tax-expert standard, the end-to-end preparation of a defined tax matter from the documents and information supplied by the user.

For a supported case, the system should be able to:

- ingest and classify the user's tax documents and information;
- extract, normalize, reconcile, and validate relevant facts;
- identify missing, inconsistent, or suspicious information;
- determine the applicable German tax rules for the relevant tax year and case;
- verify that legal/tax information used by the system reflects the **latest applicable German rules available at the time of execution**;
- research and cite authoritative sources;
- calculate relevant tax figures with deterministic validation where possible;
- identify applicable deductions, allowances, obligations, options, risks, and deadlines;
- challenge its own reasoning and search for contrary interpretations or evidence;
- perform an independent audit/QA pass;
- produce complete, clear, evidence-backed tax documentation and submission-ready outputs;
- support both printable documents and, where technically and legally permitted, controlled electronic submission to the relevant German tax authority/system;
- maintain provenance and an audit trail from source document through evidence, reasoning, calculations, approvals, and final output.

The system must distinguish clearly between facts, evidence, assumptions, calculations, legal/tax interpretations, conclusions, uncertainty, and human approvals. It must never present an unverified or stale rule as current merely because an LLM produced a plausible answer.

"Senior tax-expert standard" is a **design and evaluation target**, not an unsupported claim of legal perfection. The project must establish measurable evidence for accuracy and completeness, and consequential submissions must remain subject to explicit controls and approval requirements defined during the project.

## Primary domain

**German tax assistance for natural persons and legal entities** is the selected primary project domain.

The project is deliberately broad at the final-goal level, but the first executable workflow must be narrowed during Phase 10 to a concrete, testable tax case and then expanded systematically. The system should eventually cover multiple tax workflows only after each is independently specified and evaluated.

## Core requirement: current-law alignment

Current German tax law is a first-class system dependency, not static background knowledge.

The architecture must therefore support:

- authoritative-source retrieval;
- effective-date and tax-year awareness;
- source version/provenance tracking;
- detection of changed or superseded rules;
- explicit distinction between current, historical, and uncertain information;
- re-validation of applicable rules for each relevant case/run;
- citations for material legal/tax conclusions;
- a controlled failure state when authoritative current information cannot be verified.

The system must not rely on model training data as the source of truth for current German tax law.

## Initial architectural hypothesis

Potential components include:

- Case/Orchestrator Agent
- Specialist Agents selected according to the case
- Document Extraction Agent or deterministic document pipeline
- Evidence Matching / Reconciliation component
- German Tax Research Agent
- Calculation / Tax Analysis Agent
- Optimization / Options Agent
- Devil's Advocate / Challenge Agent
- Auditor / QA Agent
- Human Approval Gate
- Current-law verification layer
- Shared case state
- Evidence/provenance layer
- Audit trail and observability layer
- Controlled submission layer

These remain hypotheses until workflow decomposition and architecture design justify each component. The project will explicitly decide what should be an agent and what should remain deterministic code or controlled integration logic.

## Output and submission target

Final outputs should be:

- factually and mathematically validated;
- legally/tax-evidence grounded;
- complete for the supported workflow;
- clearly structured and understandable;
- traceable to source evidence;
- suitable for printing;
- suitable for electronic submission where an official interface and lawful technical integration exist;
- accompanied by a machine-readable case/audit record where useful.

Automatic submission must be permissioned and controlled. The system must not silently submit consequential tax filings or declarations.

## Success criteria

The project is successful when it demonstrates one or more supported German tax workflows end to end with:

- verified current-law alignment;
- traceable authoritative evidence;
- accurate document/fact extraction and reconciliation;
- deterministic validation where appropriate;
- measurable tax-result correctness against trusted references;
- explicit handling of uncertainty and missing/conflicting evidence;
- controlled agent/tool use;
- independent challenge and audit stages;
- reproducible evaluation;
- documented failure modes and adversarial testing;
- human approval for consequential judgment/submission;
- printable and, where supported, controlled electronic outputs;
- complete auditability from input to final submission package.

## Explicit non-goals

- building a generic autonomous agent framework;
- maximizing the number of agents;
- treating LLM output as authoritative German tax law;
- claiming legal/tax perfection without measurable evidence;
- silently taking consequential external actions;
- bypassing official German tax authority requirements or authentication controls;
- adding tools merely because they are available;
- using personal or real taxpayer data unnecessarily in development;
- optimizing infrastructure before workflow and evaluation are understood.
