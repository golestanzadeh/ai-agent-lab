# Project Checkpoint

## Purpose

This file is the mandatory, session-independent entry point for AI-Tax-Agent. It exists so a change of ChatGPT conversation, Codex session, or Agent process never requires the human to reconstruct project history.

Chat history is working context only. GitHub documentation is durable project memory.

## Mandatory startup protocol

Before answering a project-status question, proposing work, or asking the human for project facts, every ChatGPT/Codex/Agent session must:

1. Read this file from the active development branch.
2. Read `AGENTS.md`.
3. Read every authoritative file listed under **Required references** that is relevant to the requested work.
4. Check the current branch/PR head and identify whether `main` is behind the active development branch.
5. Prefer the latest dated human-confirmed checkpoint over older technical checkpoints.
6. Never ask the human to repeat information already recorded in this checkpoint, its required references, or case current case evidence.
7. If records conflict, report the conflict and reconcile the durable documentation before continuing. Do not silently choose an older record and do not invent missing details.

## Authoritative recovered state

Recovery date: **2026-09-13**  
Authority: **explicit human confirmation in the current project session**  
Status: **CASE-001 / tax year 2024 analysis complete and Chief-approved**

The human confirmed the following final state from the preceding project conversation:

- CASE-001 for tax year 2024 completed its document, evidence, tax-analysis, opportunity, calculation-review, and Chief Agent review process.
- The Chief Agent approved the completed 2024 analytical result and closed that preparation process.
- Previously discussed CASE-001 facts and evidence—including driver/work information, EVG, spouse income/Minijob, school fees, household services and other reviewed items—must not automatically be reopened or requested again merely because an older D-024/D-025/D-028 document still labels them provisional or missing.
- The only remaining product boundaries are:
  1. design and implementation of the controlled ELSTER/Finanzamt submission path;
  2. design and implementation of the user interface.
- No ELSTER submission or Finanzamt transmission has occurred.
- The exact final Chief response, final calculation amount, final test count, stage identifier after D-028, and any uncommitted implementation details were not recoverable from GitHub or available cross-session history. They must be marked **not recovered**, never fabricated.

This recovered checkpoint supersedes the older D-028 `HUMAN_REQUIRED` state and the 2026-09-13 operational-readiness audit wherever they describe CASE-001 tax-analysis evidence gaps as currently open. Those older records remain historical evidence, not the current continuation point.

## Current continuation point

Do not restart CASE-001 evidence gathering or foundational multi-year testing.

Proceed in this order:

1. Reconcile older D-024 through D-028 status documents with this human-confirmed closure without inventing unrecovered details.
2. Define the safe ELSTER/Finanzamt integration contract, including preview/validation, explicit human approval, submission receipt, failure recovery, and prohibition on silent filing.
3. Design and implement the UI for case creation, document intake, Agent progress, evidence/status review, calculation/form preview, Human Gates, and submission authorization.
4. Run product-level end-to-end acceptance through the UI. This is not permission to repeat completed foundational architecture tests.
5. Preserve mandatory Human Gates for filing, destructive/irreversible actions, permission/security changes, protected-main merge/release, and governance changes.

## Cross-session update rule

Whenever a stage is accepted, closed, blocked, resumed, or materially changed, the same governed change set must update:

- this file;
- `CURRENT_STATE.md`;
- `ROADMAP.md` when future work or planned artifacts change;
- `DECISIONS.md` when authority, architecture, or governance changes;
- the relevant detailed document under `docs/`.

A stage is not durably handed off until the checkpoint states:

- what completed;
- what was actually verified;
- what remains;
- the exact next action;
- applicable Human Gates;
- branch, PR, and commit reference when known;
- unknown or unrecovered facts explicitly labeled as such.

## Required references

- `AGENTS.md` — mandatory Agent behavior and governance.
- `CURRENT_STATE.md` — detailed verified/recovered current state.
- `ROADMAP.md` — remaining work and registered future artifacts.
- `DECISIONS.md` — accepted decisions and authority.
- `docs/d027-tax-agent-runtime.md` — executable specialist runtime.
- `docs/d028-chief-tax-auditor.md` — historical Chief implementation and live-test checkpoint.
- `docs/agent-bridge-production.md` — development control plane.
- `docs/local-sync-agent.md` and `docs/windows-relay.md` — host-side operational bridge.

## Authority and safety

This checkpoint records state; it does not grant runtime authority. It does not authorize ELSTER submission, Finanzamt contact, irreversible mutation, secret/permission changes, protected-main merge, or bypass of any Human Gate.
