# D-019: Controlled Agent-Assisted Development Workflow

**Status:** Accepted
**Type:** Development Governance / Workflow Decision
**Scope:** Software development process
**Does not alter:** Application architecture, domain contracts, security model, or business rules

## 1. Decision

The project may use an AI coding agent, including OpenAI Codex, as a controlled development and execution assistant.

Use of an AI coding agent is **not mandatory, permanent, or exclusive**.

The project must remain fully understandable, maintainable, testable, and continuable without an AI coding agent.

## 2. Primary Objective

The primary objective of using an AI coding agent is to improve the efficiency and reliability of the software-engineering execution cycle by:

- reducing repetitive manual development operations;
- executing local development and test commands;
- analyzing test failures;
- implementing approved changes;
- repeating the implementation/test/fix cycle;
- maintaining Git traceability;
- reducing manual synchronization between development, testing, and version control.

The purpose is **not** to delegate architectural authority or project governance to the agent.

## 3. Human Authority

Architectural decisions, domain rules, contracts, stage acceptance, migration authorization, destructive operations, and other governance decisions remain under human control.

The agent may implement an approved design but must not independently redefine an approved contract or architectural boundary.

A successful test result does not constitute architectural or stage approval by itself.

## 4. Controlled Development Cycle

1. Identify the current approved D-stage and governing documents.
2. Read `AGENTS.md` and applicable project governance documents.
3. Inspect the relevant existing implementation.
4. Identify the exact implementation boundary.
5. Implement only the approved change.
6. Run required local commands and tests.
7. Analyze failures.
8. Correct implementation or tests where justified.
9. Repeat testing until acceptance criteria are satisfied.
10. Inspect `git diff` and `git status`.
11. Create a traceable commit.
12. Push to the designated branch when authorized.
13. Verify the remote result.
14. Record implementation and test outcomes.
15. Obtain human review/acceptance where required.

## 5. Agent Authority Boundaries

The agent may, when explicitly authorized:

- read repository files;
- inspect project documentation, source code, and tests;
- create or modify implementation files;
- execute PowerShell, Python, and project test commands;
- analyze test failures and repeat tests;
- create Git branches and commits;
- push authorized branches;
- report implementation and test results.

The agent must not independently:

- redefine project architecture;
- change an accepted contract without authorization;
- declare a D-stage accepted solely because tests pass;
- perform a physical Google Drive migration without explicit authorization;
- perform destructive or irreversible operations without explicit authorization;
- modify `main` outside the approved workflow;
- bypass project governance;
- conceal failed tests, unexpected changes, or environmental limitations.

## 6. Git and Branching Principle

Agent-generated changes must remain traceable through Git.

For non-trivial implementation work, development should preferably occur on a dedicated branch rather than directly on `main`.

Before commit, the agent must inspect the resulting diff and status and confirm that unrelated files have not been changed.

## 7. Testing Principle

Testing remains mandatory. Where applicable, the agent should execute PowerShell/local project commands, Python checks, targeted tests, the relevant pytest suite, and project-specific validation required by the current D-stage.

A passing test suite demonstrates technical test success only. It does not replace human approval of architecture, governance, or migration boundaries.

## 8. Operational Independence

All project documentation, source code, tests, contracts, and decisions must remain usable without Codex.

Codex-specific instructions are a development aid, not a runtime dependency. The project must not require Codex to execute the application, interpret its domain model, or recover its governing decisions.

## 9. Known Environment Constraints

The initial Codex capability assessment established:

- PowerShell 7.6.5 available.
- Python 3.14.2 available.
- Git 2.41.0.windows.1 available.
- Project-local Python virtual environment creation works.
- pytest 9.1.1 installed successfully in the project-local environment.
- Local Python execution and pytest execution work.
- Local Git operations work when the repository ownership restriction is explicitly handled.
- Codex execution identity and directory ownership identity differed, producing Git `dubious ownership` protection.
- Direct HTTPS Git authentication encountered credential-store and non-interactive-terminal limitations.
- Connected GitHub access through Codex successfully supported branch creation, commit, and push.
- Free-plan Codex usage reached its usage limit during the project continuation test.

These are observations of the tested environment at the time of evaluation, not permanent guarantees of product behavior or service limits.

## 10. Evidence From Initial Capability Test

The controlled GitHub write test used `ai-agent-lab` and successfully demonstrated:

- branch `codex-github-test` creation;
- creation of `codex_github_test.txt` containing `CODEX_GITHUB_WRITE_TEST`;
- commit `02236f4696cc5761e0ac00f0edf1e32a8ac4bcdc`;
- successful push;
- clean final branch state;
- no modification of `main`;
- no pull request creation.

The test therefore established that the tested Codex environment can perform a complete authorized GitHub write workflow.

## 11. Current Project Boundary

D-017 has been implemented.

D-018 has been accepted and implemented.

No physical Google Drive migration has occurred as part of the D-017/D-018 implementation state.

The next implementation boundary is construction of the D-017 approval context from:

1. the exact real migration manifest; and
2. the artifact identities of the successful live-target-preflight artifacts.

## 12. Review

This decision may be revised if the project workflow, Codex capabilities, security/governance requirements, or demonstrated project needs change.

The existence of this decision does not create a permanent dependency on Codex.