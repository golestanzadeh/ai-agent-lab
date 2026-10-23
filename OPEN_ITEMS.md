# OPEN_ITEMS â€” Active Unaccepted Gates

<!-- CURRENT_PROJECT_STAGE: SYNTHETIC_UI_ACCEPTED_REAL_PRODUCT_GATED -->
<!-- CURRENT_NEXT_ACTION: C09_R1_IMPLEMENT_AFTER_CAPACITY_RESET -->
<!-- CURRENT_ACTIVE_OPEN_ITEMS: OI-0002..OI-0008,OI-0010,OI-0012 -->

Owner-proposed tracking design, active inventory reconciled after OI-0001 Owner closure (2026-10-08). This file is a **read-only projection** of existing Kernel acceptance, authoritative plans and `PROJECT_CHECKPOINT.md`; it is not a second checkpoint, queue, scheduler or execution authorization.

## Lifecycle (proposal recorded, automatic enforcement not implemented)

At every governed recovery and package boundary, reconcile active gates with the **latest** independent evidence, not historical checkpoint labels. Register only the **unresolved part** with a stable ID, exact next action, dependencies and acceptance authority. A later accepted PASS supersedes an earlier FAIL; do not reopen it. On formal independent PASS, first commit evidence and update checkpoint/plan, then remove the row from this active list in a committed change; Git history preserves the record. New unresolved gates get new sequential IDs. Every future stage transition must assess and synchronize both `PROJECT_CHECKPOINT.md` and this file in the same governed change set; when no active row is resolved, preserve the rows and explicitly record that result. An unattended periodic schedule requires separate authorization; none is created here. Protected taxpayer facts and credentials never belong in Git.

## Verified active items

| ID | Unaccepted part (not the whole process) | Evidence / current status | Dependencies and next review | Governing reference |
| --- | --- | --- | --- | --- |
| OI-0002 | CASE-001 Identity & Family Persistence (stage 1; mandatory critical path) | Architecture exact SHA `2c66480` has independent PASS. R1 focused `9 passed` and relevant regression `337 passed`; capabilities exist with no role grant. Complete regression and independent implementation review remain pending; C09 OPEN. | Run complete unit regression, inspect exact diff/security boundaries, freeze candidate SHA, then obtain independent implementation review. Privileged grants, IAM/key/retention and live activation retain explicit Human Gates; keep OI-0003 blocked. | `docs/oi0002-c09-witness/R1_IMPLEMENTATION_TESTS_2026-10-23.md`; `docs/oi0002-c09-witness/KERNEL_IDENTITY_OPERATIONAL_ARCHITECTURE.md`; `docs/oi0002-c09-witness/R1_R4_FINAL_EXECUTION_REPORT.md` |
| OI-0003 | Package A protected Owner Facts Registration (stage 2) | `HUMAN_REQUIRED/SCHEMA_BLOCKED` at `f9a4b99`; existing declaration integrity PASS but registration not accepted. | OI-0002; subject-bound idempotent registration and independent PASS. | Recovery plan stage 2 |
| OI-0004 | DR-01 exact accepted declaration lineage reacceptance (stage 3) | Historical PASS superseded for current lineage; immutable request/result/XML identities unrecovered; subsequent independent FAIL. | OI-0002/0003; authoritative recovery/reconstruction, substitution tests, XSD, independent PASS. | Recovery plan stage 3; checkpoint DR-01 2026-10-08 |
| OI-0005 | DR-02 lineage independent reacceptance (stage 4) | Replay previously FAIL due to placeholders/preconstructed result and substitution risk. | OI-0004; pin exact identities, replay, independent PASS. | Recovery plan stage 4; checkpoint DR-02 2026-10-08 |
| OI-0006 | Package B annual carryover contract / Kernel gate (stage 5) | PLANNED, not accepted; Owner scheduling order ahead of DR-04. | Stages 1â€“4; versioned snapshot, annual change review, Kernel gate and independent PASS. | Recovery plan stage 5 |
| OI-0007 | Package C bilingual annual questionnaire / UI (stage 6) | PLANNED, not accepted. | OI-0006; German/Persian RTL/LTR change review, explicit Owner annual approval, Kernel integration and independent PASS. | Recovery plan stage 6 |
| OI-0008 | DR-04 final rounding/declaration acceptance (stage 7) | Part 1 successor EUR 134.00 implemented, historical EUR 133.83 preserved; ten rules, accepted-artifact lineage, full regression and independent PASS outstanding. | OI-0004/0005, Owner-ordered OI-0006/0007; execute rules, substitution tests, independent PASS. DR-05 downstream remains blocked. | Recovery plan stage 7; `docs/case001-dr04-acceptance-2024.md` |
| OI-0010 | Authoritative continuation scheduler migration and wake proof (optional enhancement; nonblocking) | Checkpoint `NO_AUTHORITATIVE_SCHEDULER / MIGRATION_BLOCKED_TOOLING_BOUNDARY`; retired Codex trigger missed wake. It does not block manual governed development. | **Owner selection/operational authority:** only if desired, inspect live Work state; establish one authorized scheduler and `WAKE_TEST_PASS`, no duplicate. | `docs/work-scheduler-migration-stop-20261005.json`; `CURRENT_STATE.md` |
| OI-0012 | DR-05 integrated CASE-001 declaration content proof (mandatory after stage 7) | `NOT_STARTED / DEPENDENCY_BLOCKED`. The governed definition requires all nine affirmative requirements to be case-bound, XSD-valid and locally plausible, with exclusions preserved and independent acceptance PASS. | OI-0003â€“OI-0008; after their accepted completion, execute the already authorized bounded integrated proof, recovery/isolation/regression tests and independent acceptance. Official ERiC/filing remains separately gated. | `docs/case001-declaration-readiness-2024.md` and JSON companion |

## Owner-deferred decisions (not active)

- `OI-0011` Outbound operational exception notification provider activation: **`OWNER_DEFERRED / OPTIONAL / NONBLOCKING`** on 2026-10-20 by explicit final Owner directive. This is not `TECHNICAL_PASS`, activation or delivery evidence. No development, acceptance or release stage depends on it. Existing fail-closed code, security contract and evidence remain unchanged. Reactivation requires a new explicit Owner directive; the ID is never reused.

## Closed items (not active)

- `OI-0001` DOC-INDEX-CI-REPAIR: `CLOSED / OWNER_ACCEPTED_ON_TECHNICAL_EVIDENCE` on 2026-10-08. Explicit Owner decision; 68 tests PASS and two GitHub Actions runs SUCCESS. This is **not** a claim of formal independent reviewer acceptance. Closure evidence: `docs/doc-index-ci-repair-plan-20261008.md`, commit `e3743e64ce65ea1f747949d30eb5e53e9b64c9cf`. ID is never reused.
- `OI-0009` Supervisor-loop G2 MCP event delivery proof: **`OWNER_TERMINATED / PERMANENTLY_OUT_OF_SCOPE`** on 2026-10-20 by explicit final Owner directive. This is not `TECHNICAL_PASS`, does not prove G2, and creates no acceptance evidence. G2 MCP Events are not an execution dependency. Historical design/G1 evidence is retained; reactivation requires a new explicit Owner directive. ID is never reused.
- `UI25-10` Analysis navigation and execution-conflict UX: `TECHNICAL_PASS / INDEPENDENT_PASS / OWNER_BROWSER_PASS / SYNTHETIC_ONLY` on 2026-10-20 for implementation `9b4cec532c97483cbf072c4fc90e8bcd3cf89538` and accepted case/run `TEST-2025-02` / `RUN-OWNER-UI25-08-004`. Closure covers only the seven Owner-observed scenarios recorded in `PROJECT_CHECKPOINT.md`: Documents â†’ Analysis navigation, selected-Run preservation, six synthetic fields, Persian/German switching, result preservation across language changes, completed-run Replay, and same-document/new-run conflict behavior. No active `OI-0002`â€“`OI-0011` row is resolved by this bounded UI acceptance; all listed dependencies, security gates and untested browser scenarios remain open or outside this acceptance.

## Superseded / intentionally excluded

- Documentation-index and Constitution v2-marker **technical** FAILs: fixed and green; Owner accepted closure of OI-0001; no technical defect remains open.
- DR-04 rounding-change Human Gate: Owner approved versioned successor; do not reopen.
- DR-03 old capacity deferral/registration: later accepted DR-03 continuation supersedes them.
- ERiC developer-access email pending: access received, license accepted.
- Historical O4/O5/UI package blocker labels and earlier wake incidents: later progress or consolidated under OI-0010.
- Official ERiC submission/production: future external Human Gates, not failed currently authorized work.
- Old checkpoint/plan lines saying DOC-INDEX-CI-REPAIR â€œNOT EXECUTEDâ€: superseded by verified commits/tests/Actions.

## Mandatory review

Read newest checkpoint and governing evidence; test each row against later accepted records; add genuinely new unaccepted gates; never dispatch work just because it appears here. Upon formal PASS, update plan and checkpoint with exact evidence and commit, then delete only the resolved active row. Every stage transition must assess and synchronize `PROJECT_CHECKPOINT.md` and `OPEN_ITEMS.md` together, including an explicit no-row-change result when applicable. No automated schedule or additional execution authority is created by this document.

The October bounded-increment labels UI25-05 through UI25-10 do not close the same-numbered formal UI25 plan packages. In particular, the accepted increment is not formal UI25-10 Approval/Export. Only the exact accepted increment scope may be treated as closed; formal real-data package gates remain governed by the UI25 plan and the dependencies above.

