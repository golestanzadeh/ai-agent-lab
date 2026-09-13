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

Repository cleanup and canonical-state consolidation completed on 2026-09-13.

Project Constitution v2 was explicitly ratified by the Project Owner / Human on 2026-09-13 and is now active in `CONSTITUTION.md`.

Agent Organization v1 was explicitly ratified by the Project Owner / Human on 2026-09-13 and is now the active organizational contract at `docs/agent-organization-v1-proposal.md`.

Current authorized continuation point:

1. Phase O1 is complete.
2. Phase O2 is complete and Human-accepted at exact contract-set commit `382a140e42496ad9edd92dc2016cfde51d091575`.
3. Phase O3 deterministic Orchestrator Kernel was implemented and technically verified at commit `d70a28b9b33710a81881855048baccb63f3fc176`.
4. Current state is `O3_TECHNICALLY_COMPLETE -> HUMAN_REQUIRED` for exact Phase O3 acceptance or amendment.
5. Phase O4, real Agent activation, high-risk permission issuance, protected-main action, production release, destructive action, tax submission, and external transfer remain unauthorized.

Future changes to the organizational model require explicit Project Owner / Human instruction or approval. The Master Project Orchestrator may request review and propose an exact change but cannot activate it.

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

- `CONSTITUTION.md` — ratified supreme Project Constitution v2.
- `AGENTS.md` — mandatory Agent behavior and governance.
- `CURRENT_STATE.md` — detailed verified/recovered current state.
- `docs/agent-organization-v1-proposal.md` — active Agent hierarchy, authority, communication, lifecycle, and execution path.
- `docs/o2-machine-readable-contracts.md` and `contracts/orchestrator/v1/` — Phase O2 design, schemas, policies, and acceptance evidence.
- `ROADMAP.md` — remaining work and registered future artifacts.
- `DECISIONS.md` — accepted decisions and authority.
- `docs/d027-tax-agent-runtime.md` — executable specialist runtime.
- `docs/d028-chief-tax-auditor.md` — historical Chief implementation and live-test checkpoint.
- `docs/agent-bridge-production.md` — development control plane.
- `docs/local-sync-agent.md` and `docs/windows-relay.md` — host-side operational bridge.

## Authority and safety

This checkpoint records state; it does not grant runtime authority. It does not authorize ELSTER submission, Finanzamt contact, irreversible mutation, secret/permission changes, protected-main merge, or bypass of any Human Gate.


## Repository cleanup checkpoint — 2026-09-13

The active branch was cleaned and canonicalized:

- removed completed bridge trigger/probe artifacts and placeholder write-test files;
- removed unnecessary `.gitkeep` files from populated directories;
- removed superseded D-024/D-025 progress snapshots after preserving durable tax-analysis rules in `docs/d025-tax-calculation-contract.md`;
- replaced accumulated historical content in `CURRENT_STATE.md` and `ROADMAP.md` with concise current-state and future-work records;
- refreshed `README.md`, `docs/README.md`, D-027 runtime documentation, D-028 Chief documentation, and Agent Bridge documentation;
- retained source code, regression tests, security/approval contracts, reusable architecture, verified lessons, and consequential migration/audit evidence.

Git history remains the recovery path for deleted material. No source code, tax evidence, private Drive data, approval data, or audit data was deleted.


## Constitution v2 ratification checkpoint — 2026-09-13

- The Project Owner / Human explicitly approved and ratified Project Constitution v2, including Article 1 and all 20 Articles.
- The ratified text is active at `CONSTITUTION.md` and supersedes the original twelve-principle Constitution.
- Exact Constitution activation commit: `ef935a4ba0493c1f2904d0983614b2b73e656254`.
- Article 1 establishes absolute external-data Default Deny and requires two separate Human approvals: exact-content release approval, followed by exact-recipient/channel transmission approval.
- No Agent, Master Orchestrator, automation, tool, or generic authorization may amend or bypass the Constitution.
- Any future constitutional change requires the exact proposed change, impact/risk disclosure, explicit Project Owner approval, a dedicated commit, Decision Log entry, and checkpoint update.
- The superseded proposal file was removed after activation; Git history remains its recovery path.
- Status: **RATIFIED / IN FORCE**.


## Agent Organization v1 ratification checkpoint — 2026-09-13

- The Project Owner / Human explicitly approved the redefined ten-section Agent Organization v1 model as the governing basis for continued project work.
- Defined Human, independent control, Master/PMO, Engineering, and Tax Operations layers.
- Preserved the existing seven tax-runtime Agent identifiers.
- Accepted 20 permanent Agent roles plus three inactive case-selected domain role templates.
- Accepted role responsibilities, reporting lines, access tiers A0–A6/AX, task-mediated communication, deterministic kernel boundaries, lifecycle, separation of duties, and phases O0–P4.
- Future organizational changes require explicit Project Owner / Human instruction or approval. The Master may request review and propose exact changes but cannot approve or activate them.
- Ratification authorizes Phase O2 machine-readable contract work only.
- No Agent instance, credential, permission expansion, protected-main action, production release, destructive action, tax submission, or external transfer was authorized.
- Activation commit: `15c0f9855f361ade1133d22f20cee21f75a812fc`.
- Status: **RATIFIED / ACTIVE ORGANIZATIONAL CONTRACT**.


## Phase O2 acceptance checkpoint — 2026-09-13

- Created the exact-version `ORCHESTRATOR_CONTRACT_SET_V1` under `contracts/orchestrator/v1/`.
- Defined the 20 permanent roles, three inactive templates, Agent manifest, Permission Matrix, task/response schemas, lifecycle, Human Gates, conflict rules, budgets, retries, loop controls, and kill switch.
- Added a deterministic offline validator and 12 positive/fail-closed tests.
- Targeted result: `12 passed`.
- Full regression: `337 passed, 1 skipped`.
- Implementation and verification commit: `382a140e42496ad9edd92dc2016cfde51d091575`.
- No Agent was activated; no permission, credential, private case access, merge, release, destructive action, tax submission, or external transfer occurred.
- Human acceptance: exact contract-set commit `382a140e42496ad9edd92dc2016cfde51d091575` explicitly accepted on 2026-09-13.
- Acceptance record commit: `bd18777cf00cade02abfa58869417948742a7e28`.
- Status: **O2_ACCEPTED / PHASE COMPLETE**.
- Exact next action: Phase O3 designs and implements the deterministic Orchestrator Kernel against the accepted O2 contracts, without activating Agents or crossing any later Human Gate.


## Phase O3 technical completion checkpoint — 2026-09-13

- Implemented the SQLite-backed deterministic control plane at `src/agent_lab/orchestrator_kernel.py`.
- Covered task/dependency and Human Gate registration; Agent manifest validation; Default-Deny permission decisions; case/run scope; lifecycle; independent acceptance; budget, retry, and loop controls; fail-closed kill switch; hash-chained audit; checkpoint/recovery; read-only inspection; and exact Agent Bridge binding.
- Bound runtime loading to the canonical digest of the Human-accepted O2 contract set.
- O2 validator: `PASS`.
- O3 targeted suite: `26 passed`.
- Relevant O2/O3/Agent Bridge suite: `44 passed`.
- Full regression: `363 passed, 1 skipped`.
- Implementation commit: `d70a28b9b33710a81881855048baccb63f3fc176`.
- All tests used synthetic local state. No real Agent, credential, A6 permission, private tax-case data, production service, protected-main action, release, destructive action, tax submission, or external transfer was used or activated.
- Status: **O3_TECHNICALLY_COMPLETE -> HUMAN_REQUIRED**.
- Exact next action: Human reviews and explicitly accepts the exact O3 implementation or requests exact amendments. Only acceptance may authorize Phase O4.
