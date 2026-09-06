# Decision Log

Use this file for decisions that materially affect project scope, architecture, safety, or workflow.

## D-001 — Repository as source of truth

**Status:** accepted

**Decision:** GitHub is the durable source of truth. Chat is a working interface, not the canonical project memory.

**Reason:** The project is long-running and must survive large chat histories, context loss, and model mistakes.

## D-002 — Domain remains open during Phase 0

**Status:** superseded by D-006

**Decision:** During Phase 0, the domain was intentionally left open while the project structure was established.

**Reason:** The initial architecture should not be forced by an untested domain assumption.

## D-003 — Anti-hallucination project memory

**Status:** accepted

**Decision:** Verified state, decisions, and planned future files must be recorded in the repository. Unknown information must not be reconstructed as fact.

**Reason:** The user explicitly requires protection against later answers based on model memory or speculation.

## D-004 — Agent count is not an objective

**Status:** accepted

**Decision:** Use the minimum number of agents necessary to solve demonstrated coordination problems.

**Reason:** Multi-agent systems add complexity, latency, cost, and failure modes. More agents do not automatically mean a better system.

## D-005 — AGENTS.md is a map, not the encyclopedia

**Status:** accepted

**Decision:** Keep `AGENTS.md` concise and place detailed project knowledge in structured repository documents.

**Reason:** OpenAI's Codex guidance emphasizes concise agent instructions and structured repository knowledge rather than a giant instruction file.

## D-006 — Tax assistance is the primary project domain

**Status:** accepted

**Decision:** The AI Agent Lab will use a tax-assistance workflow as its primary real-world problem domain and will carry this domain through the project unless later evidence justifies a formally recorded change.

**Scope:** The goal is not to build an autonomous tax authority or replace a tax professional. The project will build an evidence-driven agentic system that can analyze a defined tax case, extract and reconcile information from documents, research authoritative tax rules, identify applicable considerations and potential options, challenge its own conclusions, audit the result, and present a traceable output with explicit uncertainty and human approval where consequential judgment is involved.

**Reason:** Tax work provides a strong learning environment for document understanding, retrieval/research, evidence grounding, structured reasoning, specialist delegation, conflict resolution, validation, adversarial testing, auditability, and human-in-the-loop control.

**Important constraint:** Legal/tax correctness must never be claimed merely because an LLM produced a plausible answer. Authoritative sources, deterministic checks where possible, evaluation evidence, and appropriate human review are required.
