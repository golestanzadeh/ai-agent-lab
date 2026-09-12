# AGENTS.md

## Mission

AI Agent Lab is a practical, long-running learning project. Work must improve both the software and the user's understanding of Agentic AI.

## Source of truth

Treat the repository as the durable project memory. Before making architectural or project-level claims, inspect the relevant repository documents. Never invent prior decisions, completed work, files, experiments, or requirements.

## Documentation hierarchy

- `CONSTITUTION.md`: highest-level project principles.
- `PROJECT.md`: scope and goals.
- `ROADMAP.md`: planned phases and future artifacts.
- `CURRENT_STATE.md`: verified present state.
- `DECISIONS.md`: historical decisions and rationale.
- `docs/`: detailed technical knowledge.

When documents conflict, flag the conflict and do not silently choose a version.

## Agent execution protocol

Before executing a development task, follow `docs/codex-agent-workflow.md` as the Agent Execution Protocol. Use progressive context loading: read the minimum sufficient context and expand only when required for safe execution. Prefer targeted tests before broader suites, and keep routine completion reports compact. Token efficiency must never weaken correctness, required testing, auditability, security, or governance.

## Case and data isolation

- `case_id` is mandatory for every operation that reads or writes tax-case data.
- Resolve case identity through the Case Registry before accessing case storage.
- Never perform broad/unscoped Drive searches for tax-case data.
- A component processing one case must never inspect, infer from, or retrieve another case's documents.
- Case isolation must be enforced deterministically by application/connector code, not by prompt instructions alone.
- Fail closed when case identity or scope cannot be validated.
- Cross-case contamination is a security and correctness failure and requires tests.

## Change discipline

1. Read the relevant documentation before changing architecture or behavior.
2. Keep changes small and traceable.
3. Update documentation when a decision, state, roadmap item, or architecture changes.
4. Do not create speculative production code before the relevant design is agreed.
5. Prefer tests and measurable evaluation over claims of success.
6. Never store secrets, tokens, credentials, or private personal data in the repository.
7. Use explicit source references for consequential external facts.

## Verification

For code changes, run appropriate tests and checks. Report what was actually run and the result. Do not claim a test passed unless it was executed.

## Future-file rule

`ROADMAP.md` is the authoritative register of files that are intentionally planned but not yet created. When a future file becomes necessary, create it according to the roadmap and update `CURRENT_STATE.md` and/or `ROADMAP.md` as appropriate.

## Working style

Prefer simple, observable, reproducible designs. Avoid unnecessary frameworks and abstractions until an experiment demonstrates the need for them.
