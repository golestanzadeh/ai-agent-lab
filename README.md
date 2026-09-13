# AI-Tax-Agent

A case-scoped, evidence-driven Agentic AI system for German tax workflows.

## Current position

CASE-001 for tax year 2024 completed its analytical preparation and was Chief-approved according to the recovered human checkpoint. No ELSTER/Finanzamt submission has occurred.

The remaining product tracks are:

1. controlled ELSTER/Finanzamt submission;
2. user interface;
3. operational automation toward supervised autonomous project execution.

Always read [PROJECT_CHECKPOINT.md](PROJECT_CHECKPOINT.md) before relying on historical status documents.

## Core architecture

- GitHub: durable source of truth for code, governance, tests, decisions, and checkpoint state.
- Google Drive: private case documents, evidence, calculations, reports, and audit artifacts.
- Windows/Python/Docker: controlled execution environment.
- ChatGPT Work + Agent Bridge + Codex: development orchestration and bounded implementation.
- Gemini-backed tax agents: case-scoped specialist analysis under deterministic validation.
- Human Gates: mandatory authority for filing and other consequential actions.

## Canonical documentation

- `PROJECT_CHECKPOINT.md` — current state and exact continuation point.
- `AGENTS.md` — mandatory Agent operating rules.
- `CONSTITUTION.md` — non-negotiable principles.
- `PROJECT.md` — product mission, domain, and success criteria.
- `MASTER_PLAN.md` — long-horizon destination and definition of done.
- `CURRENT_STATE.md` — concise operational state.
- `ROADMAP.md` — remaining work only.
- `DECISIONS.md` — accepted decisions and rationale.
- `docs/architecture.md` — system architecture.
- `docs/README.md` — detailed documentation index.

## Safety

No Agent may guess missing case facts, cross case boundaries, expose private case data in GitHub, or submit to ELSTER/Finanzamt without the required explicit Human Gate.
