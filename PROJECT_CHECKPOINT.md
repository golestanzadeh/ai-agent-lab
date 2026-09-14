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
4. The Project Owner / Human explicitly accepted that exact O3 implementation on 2026-09-13 and authorized Phase O4.
5. Phase O4 resumed on 2026-09-14 and its bounded pilot was implemented and technically verified at commit `b81f4060c5973ad0e5b4ec88a385ce3e046f7ee3`.
6. The Project Owner / Human explicitly accepted that exact O4 implementation on 2026-09-14 and authorized Phase O5 with emphasis on token efficiency.
7. The Phase O5 readiness evaluator is implemented and verified at commit `9e00bcfccdddd04cda7195a907fbc3aaa9dd9772`. Windows Relay, Local Sync, monitoring, protected-main enforcement, and all three active Work automations are now verified against the main repository.
8. A fresh Phase O5 evaluation on 2026-09-14 returned `PASS` with all fourteen conditions verified and no blockers. The Project Owner / Human explicitly accepted the Phase O5 readiness result and exact readiness-record commit `d64da2588b18f548c877aed6044f8884e7644cdc` on 2026-09-14. Current state is `O5_ACCEPTED / PHASE COMPLETE`.
9. At acceptance, the Project Owner reported that only approximately 9% of the current five-hour token allowance remained. Work must pause at the completed O5 boundary; Phase P1, production Agent activation, high-risk permission issuance, protected-main action, production release, destructive action, tax submission, and external transfer remain unauthorized pending separate explicit instruction.
10. On 2026-09-14, the Project Owner requested a live plan-limit stop/resume controller before further project work. The account service reported 99% five-hour remaining (UI rounded to 100%) and 62% weekly remaining. The documented controller and active same-task heartbeat `plan-limit-continuation-guard` now enforce caution, durable token pause, and guarded continuation thresholds. This operational controller grants no Phase P1 or production authority.
11. The Project Owner then explicitly authorized Phase P1 only for non-production design and implementation with synthetic data and no real ELSTER or Finanzamt transmission. Phase P1 package 1 is implemented and technically verified at commit `aaf5bec86e103480ef5d36cedca29cfbfb607862` as a deterministic ERiC 41.2 / UFA 10 / tax-year 2024 dry-run boundary; exact official XML mapping remains blocked until separately governed developer documentation is available. Current status is `P1_PACKAGE_1_TECHNICALLY_COMPLETE -> HUMAN_REQUIRED`.

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
- Human acceptance: the Project Owner explicitly accepted implementation commit `d70a28b9b33710a81881855048baccb63f3fc176` on 2026-09-13 and authorized Phase O4.
- Status: **O3_ACCEPTED / PHASE COMPLETE**.


## Organized pause before Phase O4 — 2026-09-13

- Phase O4 is authorized but intentionally deferred until 2026-09-14 at the Project Owner's instruction because approximately 25% of the current five-hour token allowance remained.
- No Phase O4 design, artifact registration, implementation, pilot execution, or Agent activation began in this session.
- Resume state: `O4_AUTHORIZED_BUT_DEFERRED`.
- Exact next action after resumption: read this checkpoint, inspect the active branch and PR head, then design the bounded Phase O4 pilot and register any future files in `ROADMAP.md` before creating them.
- O4 scope remains one low-risk, reversible, non-tax-private work package that verifies multi-session continuation, bounded retries, independent acceptance, recovery, cost reporting, and concise Human interaction.
- Token-efficient execution: use progressive context loading, one bounded work package, one implementation owner, targeted tests first, and broader regression only when integration risk or phase acceptance requires it.
- This pause grants no real Agent, credential, A6, private case-data, production, protected-main, destructive, tax-submission, or external-transfer authority.


## Phase O4 resumed — 2026-09-14

- The Project Owner instructed continuation from the checkpoint at 09:40 Europe/Berlin with a scheduled stop at 11:30 Europe/Berlin.
- The bounded pilot is a deterministic local consistency check of explicitly allowlisted public governance documents.
- Planned artifacts were registered in `ROADMAP.md` before creation.
- The pilot may use only local synthetic Kernel state and temporary JSON evidence. It may not access tax-case data, network services, credentials, protected `main`, production, or any external destination.
- Resume status: `O4_RESUMED / DESIGN_REGISTERED`.


## Phase O4 technical completion checkpoint — 2026-09-14

- Implemented the deterministic governance-document consistency pilot at commit `b81f4060c5973ad0e5b4ec88a385ce3e046f7ee3`.
- Verified separate start/resume Kernel instances, durable pause/recovery, allowlisted document hashing, evidence-drift rejection, independent acceptance, budget reporting, bounded retry enforcement, audit integrity, final checkpoint, and final `HALTED` kill-switch state.
- Targeted O4 suite: `5 passed`.
- Relevant O2/O3/O4/Agent Bridge suite: `49 passed`.
- Full regression: `368 passed, 1 skipped`.
- Local two-invocation demonstration: `COMPLETED`; audit `PASS`; 2 tasks, 2 manifests, 1 response, 1 independent acceptance, 2 checkpoints, and 21 audit events.
- Recorded pilot cost: 0 model tokens, 12 bounded local tool operations, USD 0 external cost.
- Generated SQLite and JSON evidence remained in a local temporary directory outside version control.
- Completion time was approximately 09:47 Europe/Berlin, before the scheduled 11:30 stop.
- No tax-case data, network, credential, external service, LLM dispatch, protected-main action, production operation, or external transfer was used.
- Status: **O4_TECHNICALLY_COMPLETE -> HUMAN_REQUIRED**.
- Exact next action: Human reviews and explicitly accepts implementation commit `b81f4060c5973ad0e5b4ec88a385ce3e046f7ee3` or requests exact amendments. Phase O5 may not begin before that acceptance.


## Phase O4 acceptance and Phase O5 start — 2026-09-14

- The Project Owner explicitly accepted Phase O4 implementation commit `b81f4060c5973ad0e5b4ec88a385ce3e046f7ee3` and authorized Phase O5.
- O4 status: **O4_ACCEPTED / PHASE COMPLETE**.
- O5 resumed under the existing 11:30 Europe/Berlin scheduled stop and an explicit token-efficiency constraint.
- Initial read-only evidence: Local Sync scheduled task exists but is disabled; Windows Relay scheduled task is not installed; no local Codex automation record proving main-repository Work scope was found.
- Phase O5 readiness artifacts were registered in `ROADMAP.md` before creation.
- Current status: `O5_IN_PROGRESS / READINESS_BLOCKERS_PRESENT`.
- Exact next action: implement the deterministic readiness evaluator, verify the blockers, and stop at the applicable Human/operational gate without activating production authority.


## Phase O5 readiness checkpoint — 2026-09-14

- Implemented the deterministic fail-closed readiness evaluator at commit `9e00bcfccdddd04cda7195a907fbc3aaa9dd9772`.
- Verification: targeted `11 passed`; relevant O3/O4/O5/Bridge/Local Sync/Windows Relay `72 passed`; full regression `379 passed, 1 skipped`; compile check passed.
- Current evaluator outcome: `BLOCKED` with five blockers: Work automation repository scope, Work automation enabled state, monitoring, protected-main Human Gate, and disabled Local Sync.
- Status: **O5_BLOCKED -> HUMAN_REQUIRED**.
- Exact next action: obtain explicit authority for the local service changes, identify the exact Work automation, define monitoring, and verify protected-main enforcement; then collect fresh evidence and require evaluator `PASS`.
- No service, automation, credential, permission, repository protection, production authority, merge, release, or external transfer was changed.


## Phase O5 local service authorization result — 2026-09-14

- Human authorization covered enabling `AI-Tax-Agent Local Sync` and installing `AI-Tax-Agent Windows Relay` through the registered script.
- The two user-owned untracked files were added only to local `.git/info/exclude`; their contents and locations were not changed, and no repository commit contains them.
- Windows Relay installation succeeded. Task state: `READY`, enabled: `true`, run level: `Limited`, last task result: `0`.
- Local Sync activation failed with Windows `Access is denied`; it remains `Disabled`. No privilege or security boundary was bypassed.
- Manual Local Sync smoke result: `UP_TO_DATE`; local and remote SHA both `ef9078b7c853d2d920430632a8aecdc4c0ec3e17`.
- Refreshed readiness outcome: `BLOCKED` with five remaining blockers.
- At this checkpoint, the next action was elevated Local Sync activation; the later verification record below supersedes that blocker.


## Phase O5 Local Sync elevated activation result — 2026-09-14

- The Project Owner reported executing the approved Local Sync activation commands from an elevated PowerShell session.
- Independent verification: task state `READY`, enabled `true`, run level `Limited`, latest task result `0`.
- Local and remote `d021-agent-case-provisioning` heads match at `bc1749317450c449e8446bdf813bf13afa885715`.
- Refreshed readiness evaluation verified both Local Sync and Windows Relay and returned `BLOCKED` with four remaining conditions.
- Remaining blockers: Work automation repository scope, Work automation enabled state, monitoring, and protected-main Human Gate verification.
- Status remains **O5_BLOCKED -> HUMAN_REQUIRED**.
- Exact next action: identify and govern the Work automation update, then define monitoring and verify protected-main enforcement.


## Phase O5 scheduled-task window fix — 2026-09-14

- The Project Owner reported repeated command windows opening during the one-minute scheduled runs.
- Root cause: Windows Relay used console `python.exe`, was visible, and Windows subprocesses lacked no-window creation flags.
- Fix commit: `345cadb83ce0fd6b30b851c394cebdc891037672`.
- Local Sync and Windows Relay now start subprocesses with `CREATE_NO_WINDOW`; the Relay installer uses `pythonw.exe` and registers a hidden task.
- Windows Relay was reinstalled and verified enabled, hidden, `READY`, using `C:\Python314\pythonw.exe`, with last result `0`.
- Regression verification: Local Sync and Windows Relay targeted suite `27 passed`.
- At this checkpoint, O5 still had Work automation, monitoring, and protected-main blockers; the later verification record below resolves the latter two.


## Phase O5 monitoring and protected-main verification — 2026-09-14

- GitHub ruleset `22799423` is active and targets `main`.
- Its bypass list is empty; pull requests are required before merging; force pushes are blocked.
- Monitoring evidence: Agent Bridge Passive Validation run `34821613554` completed successfully, and both Local Sync and Windows Relay report latest task result `0`.
- A fresh readiness evaluation verified twelve conditions and returned `BLOCKED` only for Work automation repository scope and enabled state.
- Current status: **O5_BLOCKED -> WORK_AUTOMATION_EVIDENCE_REQUIRED**.
- Exact next action: identify the existing ChatGPT Work automation, change its repository scope from `golestanzadeh/agent-bridge-poc` to `golestanzadeh/ai-agent-lab`, verify it is enabled, and rerun readiness.


## Phase O5 Work automation resolution and readiness PASS — 2026-09-14

- The Project Owner explicitly authorized changing the three active ChatGPT Work Agent Bridge automations from `golestanzadeh/agent-bridge-poc` to `golestanzadeh/ai-agent-lab`.
- `Bridge PR Wake-up`, `Agent Bridge Human Gate`, and `Agent Bridge Continuation` were each inspected before change. All three were active, but both their GitHub Repository condition and prompt still referenced the PoC repository.
- Each existing automation was updated in place so its Repository condition and prompt reference `golestanzadeh/ai-agent-lab`. Titles, event filters, exact Agent Bridge markers, Human Gate behavior, duplicate prevention, no-merge rules, and other safety restrictions were preserved.
- Each automation was independently reopened after update and verified active with the exact main-repository scope. No automation was run during the update, and no GitHub data, plugin permission, credential, branch, file, pull request, merge, or release was changed.
- Fresh supporting evidence: branch and remote synchronized at `bac8a4cf279952fab92fc4ab0cb54fe7fdfea2c8`; draft PR #1 still targets `main`; GitHub ruleset `22799423` remains active with no bypass, required pull requests, and blocked force pushes; Agent Bridge Passive Validation run `34821985936` completed successfully; Local Sync and Windows Relay are enabled, `READY`, and have latest result `0`.
- The deterministic readiness evaluator ran against a fresh non-secret snapshot collected at `2026-09-14T10:49:00+02:00` and returned `PASS`, `ready: true`, fourteen verified conditions, and zero blockers.
- Status: **O5_TECHNICALLY_READY -> HUMAN_REQUIRED**.
- Exact next action: the Project Owner reviews and explicitly accepts the Phase O5 readiness result or requests exact amendments. Phase P1 and any production activation remain unauthorized until separately approved.


## Phase O5 acceptance checkpoint — 2026-09-14

- The Project Owner / Human explicitly accepted the Phase O5 technical-readiness result and exact readiness-record commit `d64da2588b18f548c877aed6044f8884e7644cdc`.
- Accepted evidence: deterministic `PASS`, `ready: true`, fourteen verified conditions, zero blockers, and successful GitHub validation run `34824845788` at the accepted commit.
- Status: **O5_ACCEPTED / PHASE COMPLETE**.
- Token constraint at acceptance: the Project Owner reported approximately 9% remaining in the current five-hour allowance.
- Exact continuation point: pause at the O5 boundary and await separate explicit Project Owner instruction for Phase P1 or any other next work.
- This acceptance does not authorize Phase P1, production activation, credentials or permission expansion, protected-main mutation or merge, release, destructive action, tax submission, ELSTER/Finanzamt contact, or external transfer.


## Plan-limit continuation controller — 2026-09-14

- The Project Owner requested that Codex inspect live five-hour and weekly account limits, stop early enough to preserve a durable checkpoint, and automatically return to this task after capacity recovers.
- Live service evidence at design time: five-hour 99% remaining (`usedPercent: 1`; UI rounded to 100%), weekly 62% remaining (`usedPercent: 38`), primary reset `2026-09-14 23:47:38 +02:00`, and weekly reset `2026-09-20 13:48:09 +02:00`.
- The accepted operational thresholds are: caution at five-hour 25% or weekly 20%; hard token pause at five-hour 15% or weekly 10%; guarded resume only at five-hour at least 80% and weekly above 10%.
- Design: `docs/plan-limit-continuation-controller.md`.
- Active same-task heartbeat: `Plan Limit Continuation Guard`, automation id `plan-limit-continuation-guard`, five-hour cadence.
- Status: **PLAN_LIMIT_CONTROLLER_ACTIVE**.
- Exact next action: obtain or identify explicit authority for the next project phase before starting it. The controller may resume only an exact action already authorized and durably recorded as `TOKEN_PAUSED`; it cannot create authority.


## Phase P1 package 1 technical completion — 2026-09-14

- The Project Owner explicitly authorized Phase P1 design and implementation only in a non-production environment, using synthetic data and without real transmission to ELSTER or Finanzamt.
- Official ELSTER evidence identifies ERiC as the third-party software integration route. The official availability schedule identifies ERiC `41.2` for unlimited income tax (`UFA 10`) for tax year 2024.
- Exact XML schemas, plausibility rules, and developer API details are not publicly recovered in the repository and must not be invented. Developer registration, account access, manufacturer ID, ERiC download, credentials, certificates, endpoints, and live connectivity remain outside current authority.
- Registered package 1 artifacts: `src/agent_lab/elster_dry_run.py`, `tests/unit/test_elster_dry_run.py`, and `docs/p1-controlled-elster-path.md`.
- Implementation: a synthetic-only immutable envelope, ordered two-stage approval binding, and a dry-run result that can never permit or perform transmission.
- Verification: targeted `23 passed`; full regression `405 passed, 1 skipped`; Python compile check passed.
- Implementation commit: `aaf5bec86e103480ef5d36cedca29cfbfb607862`.
- The first full-suite invocation completed all test cases but hit a Windows pytest temporary-link cleanup error. The suite was rerun with an isolated temporary base and completed successfully; no test failure was hidden or reclassified.
- Status: **P1_PACKAGE_1_TECHNICALLY_COMPLETE -> HUMAN_REQUIRED**.
- Exact next action: the Project Owner reviews and explicitly accepts package 1 or requests exact amendments. Package 2, developer registration/access, official ERiC package retrieval, credentials, live connectivity, and any real transmission remain unauthorized.
