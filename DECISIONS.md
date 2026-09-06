# Decision Log

Use this file for decisions that materially affect project scope, architecture, safety, or workflow.

## D-001 — Repository as source of truth

**Status:** accepted

**Decision:** GitHub is the durable source of truth. Chat is a working interface, not the canonical project memory.

**Reason:** The project is long-running and must survive large chat histories, context loss, and model mistakes.

## D-002 — Domain remains open during Phase 0

**Status:** accepted

**Decision:** Do not lock the project to the tax domain yet.

**Reason:** Tax is a strong candidate but the learning project should first compare candidate problems against explicit criteria.

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

**Reason:** OpenAI's Codex guidance emphasizes concise agent instructions and structured repository knowledge rather than a giant instruction file. citeturn0search5