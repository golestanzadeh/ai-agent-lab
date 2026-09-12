# Codex Agent Workflow and Agent Execution Protocol

## Purpose

This document is the operational execution protocol for AI coding agents used during development of this project, including Codex.

Codex is optional. The repository, contracts, tests, and Git history remain authoritative and the project must remain continuable without Codex.

## Optimization objective

Optimize for **minimum tokens per accepted implementation**, not minimum tokens per individual prompt.

Context reduction must never weaken correctness, acceptance criteria, test coverage required by the task, security, auditability, traceability, or human-governance boundaries. Reading additional context is correct when it materially reduces implementation risk or rework.

## Progressive Context Loading

Agents must load the minimum sufficient context and expand only when the current level is insufficient for safe execution.

```text
Level 0 — current task, constraints, CURRENT_STATE.md, AGENTS.md
    ↓ only if required
Level 1 — directly relevant contracts, interfaces, tests, acceptance criteria
    ↓ only if required
Level 2 — direct implementation dependencies and adjacent state/decision records
    ↓ only if required
Level 3 — broader repository/history inspection
```

Rules:

- Do not scan the entire repository by default.
- Prefer exact file paths, symbols, tests, and governing contracts over broad searches.
- Do not reread historical material already summarized by an authoritative current-state or decision record unless verification is required.
- Expand context immediately when ambiguity, architecture risk, security impact, conflicting documentation, or a failing test requires it.
- Never guess missing project history or contracts to save tokens.

## Standard Task Workflow

```text
Inspect minimum sufficient context
        ↓
Implement bounded approved change
        ↓
Run targeted tests
        ↓
Analyze and repair failures
        ↓
Run relevant acceptance/regression suite
        ↓
Run full suite when justified
        ↓
Inspect diff/status
        ↓
Commit and push when authorized
        ↓
Return compact report
```

One agent should normally own inspect → edit → test → repair → commit for a bounded task. Do not create separate agents for routine substeps unless parallelism or specialist isolation provides demonstrated value.

## Implementation discipline

- Implement only the approved task boundary.
- Reuse existing contracts and abstractions before introducing new ones.
- Avoid unrelated refactoring, speculative production code, and documentation duplication.
- Stop for genuine human-authority boundaries defined by project governance; ordinary coding, test repair, local commands, and authorized Git operations are not reasons to stop.

## Testing policy

Testing remains mandatory. Use the least expensive sequence that still proves the required behavior:

1. targeted tests for the changed boundary;
2. relevant acceptance/regression suite;
3. full suite when justified by task acceptance criteria, integration risk, cross-cutting changes, release/stage validation, or governing documentation.

A full suite is not automatically required after every trivial edit, but token/time optimization never overrides explicit acceptance criteria. Failed tests must be analyzed and repaired or reported, never hidden or bypassed.

Project-specific commands must come from repository documentation or verified project configuration rather than being invented.

## Change review and Git

Before commit, inspect `git status` and `git diff`. Confirm only intended files changed, generated/private artifacts are excluded, no secrets or private IDs were introduced, and the change matches the approved boundary.

For non-trivial work, use the authorized development branch. Commit and push only when authorized. Do not rewrite history or modify `main` outside the approved workflow.

## Completion reporting

Successful routine tasks should return a compact report by default:

```text
STATUS: PASS
Changed: <files or concise summary>
Tests: targeted PASS; relevant PASS; full PASS/NOT REQUIRED
Commit: <hash>
Branch: <branch>
Next: <next boundary>
```

Expand the report only for failures, unresolved risks, architecture/contract decisions, security issues, unexpected environment limitations, or a human-authority boundary. Do not repeat large task prompts, repository history, or unchanged governance in completion reports.

## Human authority

Architectural decisions, domain rules, accepted contracts, stage acceptance, migration authorization, destructive operations, and other consequential governance decisions remain under human control as defined by D-019 and related decisions. Passing tests does not itself constitute stage or architectural acceptance.

## Security and case isolation

All existing security, privacy, case-isolation, approval, and migration restrictions remain in force. Token efficiency is never justification for broad Drive searches, weakened validation, omitted provenance, hidden failures, private-data commits, or bypassing fail-closed behavior.

## Enforcement

Prompt instructions are not the sole enforcement mechanism. Where practical, stable rules should be enforced by tests, CI checks, deterministic scope checks, acceptance criteria, and repository contracts.

Repository documents contain durable rules; task prompts should primarily specify the current mission, boundary, and acceptance criteria.

## Measuring effectiveness

Evaluate this protocol over multiple suitable tasks. The useful metric is accepted implementation efficiency, considering:

- unnecessary context loaded;
- repair iterations;
- execution time;
- test/acceptance quality;
- token consumption per accepted implementation.

If the protocol adds documentation overhead without improving execution behavior or accepted-implementation efficiency, revise or remove the ineffective parts.

## Known environment constraints

Environment observations are not permanent product guarantees. The tested Windows/Codex environment has required a per-command Git `safe.directory` override because sandbox execution identity differs from repository ownership. Direct HTTPS Git credential persistence has also been unreliable in some runs. Never paste credentials or access tokens into chat or commit them to the repository.

## Operational principle

The coding agent is an execution accelerator inside the governed engineering process. It is not the project owner, architectural authority, source of truth, approval authority, or runtime dependency.
