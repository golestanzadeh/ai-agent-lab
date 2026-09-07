# Codex Agent Workflow and Operational Record

## Purpose

This document records how an AI coding agent, particularly OpenAI Codex, may be used during development of this project.

Codex is an optional development tool. The project does not depend on its continued availability.

## Standard Workflow

### Phase 1: Understand

Before implementation, Codex must:

1. identify the current D-stage;
2. read `AGENTS.md`;
3. read applicable governance and design documents;
4. inspect the relevant implementation;
5. identify the exact implementation boundary;
6. identify required tests and acceptance criteria.

No implementation should begin when the governing contract is materially ambiguous.

### Phase 2: Implement

Codex implements only the approved scope. Unrelated refactoring and silent scope expansion are prohibited.

### Phase 3: Execute

Codex may execute local development commands through the available PowerShell/terminal environment.

Typical commands include:

```powershell
python --version
git --version
python -m pytest
```

Project-specific commands must come from project documentation rather than being invented.

### Phase 4: Test

The normal cycle is:

```text
Implement
   ↓
Run targeted test
   ↓
Run relevant project tests
   ↓
Analyze failure
   ↓
Correct
   ↓
Run tests again
```

A failed test is an input to the development cycle, not something to hide or bypass.

### Phase 5: Review the Change

Before committing:

```powershell
git status
git diff
```

The agent must verify that only intended files changed, no temporary/generated files are unintentionally included, no secrets were introduced, and the implementation corresponds to the approved scope.

### Phase 6: Git

When authorized:

```text
Create/use appropriate branch
        ↓
Commit intended changes
        ↓
Push authorized branch
        ↓
Verify remote state
```

Direct modification of `main` is not the default workflow.

### Phase 7: Report

Every completed agent task should report:

- what changed;
- files changed;
- tests executed;
- test results;
- failures encountered;
- corrections performed;
- commit hash;
- branch;
- push result;
- unexpected environmental limitations.

# Initial Codex Capability Test

## Environment

The initial local execution test established:

```text
PowerShell: 7.6.5
Python:     3.14.2
Git:        2.41.0.windows.1
pytest:     9.1.1
```

A project-local virtual environment was used for pytest.

## Local Execution Test

Codex successfully:

1. created a writable project-local test directory;
2. created a Python test file;
3. executed Python locally;
4. created a Git repository;
5. staged and committed a file;
6. executed pytest;
7. observed a real failing assertion;
8. analyzed the failure;
9. modified the test as instructed;
10. reran pytest and obtained a passing result.

The demonstrated cycle was:

```text
Failure
   ↓
Analysis
   ↓
Code correction
   ↓
pytest
   ↓
Pass
```

No commit was created for the deliberate pytest repair test.

# Git Environment Findings

## Repository Ownership

The Codex PowerShell environment executed under:

`DESKTOP-HVRUQB7\codexsandboxonline`

The tested repository directory was owned by:

`DESKTOP-HVRUQB7\CodexSandboxOffline`

Git therefore produced `fatal: detected dubious ownership`.

A per-command `safe.directory` override allowed repository operation without changing global Git configuration.

This is an environment/sandbox constraint, not a project defect.

## Direct HTTPS Authentication

A direct `git ls-remote https://github.com/...` test reached GitHub but encountered the `wincredman` credential-store persistence limitation and a non-interactive terminal error.

Direct Git HTTPS credential handling from the tested sandbox must therefore not be assumed to be reliable.

Credentials and access tokens must never be pasted into ChatGPT conversation text.

# GitHub Integration Test

The controlled write test used repository `ai-agent-lab`.

It successfully demonstrated:

```text
Create branch
      ↓
Create one file
      ↓
Commit
      ↓
Push
      ↓
Verify
```

Branch: `codex-github-test`

File: `codex_github_test.txt`

Content: `CODEX_GITHUB_WRITE_TEST`

Commit: `02236f4696cc5761e0ac00f0edf1e32a8ac4bcdc`

The test confirmed that the authorized Codex environment could create a branch, commit, and push to the connected GitHub repository without modifying `main`.

# Usage Limitation

During the continuation test, Codex reported:

```text
You've hit your usage limit.
```

The displayed continuation time was `October 7, 2026, 1:02 PM`.

This is recorded as an observation of the tested Free-plan environment at that time. It must not be treated as a permanent product limit because service limits and reset policies may change.

Practical conclusion:

```text
Codex capability: demonstrated
Codex continuous capacity: limited by available usage quota
```

# Operational Principle

Codex is an execution accelerator inside the project's existing engineering process.

It is not:

- the project owner;
- the architectural authority;
- the source of truth;
- the approval authority;
- a mandatory runtime dependency.

The project's source of truth remains the repository's governed documentation, contracts, source code, tests, Git history, and explicit human decisions.

# Current Project State at Documentation Time

- D-017: Implemented.
- D-018: Accepted and implemented.
- Physical Google Drive migration: Not performed.
- Next implementation boundary: exact real migration manifest + successful live-target-preflight artifact identities → D-017 approval context.
