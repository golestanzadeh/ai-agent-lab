# OPEN_ITEMS — Active Unaccepted Gates

Owner-proposed tracking design, active inventory reconciled after OI-0001 Owner closure (2026-10-08). This file is a **read-only projection** of existing Kernel acceptance, authoritative plans and `PROJECT_CHECKPOINT.md`; it is not a second checkpoint, queue, scheduler or execution authorization.

## Lifecycle (proposal recorded, automatic enforcement not implemented)

At every governed recovery and package boundary, reconcile active gates with the **latest** independent evidence, not historical checkpoint labels. Register only the **unresolved part** with a stable ID, exact next action, dependencies and acceptance authority. A later accepted PASS supersedes an earlier FAIL; do not reopen it. On formal independent PASS, first commit evidence and update checkpoint/plan, then remove the row from this active list in a committed change; Git history preserves the record. New unresolved gates get new sequential IDs. An unattended periodic schedule requires separate authorization; none is created here. Protected taxpayer facts and credentials never belong in Git.

## Verified active items

| ID | Unaccepted part (not the whole process) | Evidence / current status | Dependencies and next review | Governing reference |
| --- | --- | --- | --- | --- |
| OI-0002 | CASE-001 Identity & Family Persistence (stage 1) | Durable subject/person-role binding absent; independent HUMAN_REQUIRED/FAIL. | Compatible effective-dated identity schema, protected persistence, deterministic readback, tests, independent PASS. | `docs/case001-dr04-recovery-execution-plan-20261008.md` stage 1; checkpoint latest 2026-10-08 |
| OI-0003 | Package A protected Owner Facts Registration (stage 2) | `HUMAN_REQUIRED/SCHEMA_BLOCKED` at `f9a4b99`; existing declaration integrity PASS but registration not accepted. | OI-0002; subject-bound idempotent registration and independent PASS. | Recovery plan stage 2 |
| OI-0004 | DR-01 exact accepted declaration lineage reacceptance (stage 3) | Historical PASS superseded for current lineage; immutable request/result/XML identities unrecovered; subsequent independent FAIL. | OI-0002/0003; authoritative recovery/reconstruction, substitution tests, XSD, independent PASS. | Recovery plan stage 3; checkpoint DR-01 2026-10-08 |
| OI-0005 | DR-02 lineage independent reacceptance (stage 4) | Replay previously FAIL due to placeholders/preconstructed result and substitution risk. | OI-0004; pin exact identities, replay, independent PASS. | Recovery plan stage 4; checkpoint DR-02 2026-10-08 |
| OI-0006 | Package B annual carryover contract / Kernel gate (stage 5) | PLANNED, not accepted; Owner scheduling order ahead of DR-04. | Stages 1–4; versioned snapshot, annual change review, Kernel gate and independent PASS. | Recovery plan stage 5 |
| OI-0007 | Package C bilingual annual questionnaire / UI (stage 6) | PLANNED, not accepted. | OI-0006; German/Persian RTL/LTR change review, explicit Owner annual approval, Kernel integration and independent PASS. | Recovery plan stage 6 |
| OI-0008 | DR-04 final rounding/declaration acceptance (stage 7) | Part 1 successor EUR 134.00 implemented, historical EUR 133.83 preserved; ten rules, accepted-artifact lineage, full regression and independent PASS outstanding. | OI-0004/0005, Owner-ordered OI-0006/0007; execute rules, substitution tests, independent PASS. DR-05 downstream remains blocked. | Recovery plan stage 7; `docs/case001-dr04-acceptance-2024.md` |
| OI-0009 | Supervisor-loop G2 MCP event delivery proof | Latest checkpoint: G1 PASS, G2 unproven; no later accepted G2 proof identified in reviewed checkpoint. | Inspect current runtime/branch evidence before implementation; bounded end-to-end proof and acceptance. | Checkpoint “Supervisor-loop G1 usage telemetry” |
| OI-0010 | Authoritative continuation scheduler migration and wake proof | Checkpoint `NO_AUTHORITATIVE_SCHEDULER / MIGRATION_BLOCKED_TOOLING_BOUNDARY`; retired Codex trigger missed wake. | First inspect live Work task/trigger state to avoid stale conclusion; one authorized scheduler and `WAKE_TEST_PASS`, no duplicate. | `docs/work-scheduler-migration-stop-20261005.json`; `CURRENT_STATE.md` |
| OI-0011 | Outbound operational exception notification provider activation | Sender activation FAILED due to protected provider configuration/permission; underlying contract and independent acceptance PASS. **Unrelated to incoming GitHub emails.** | Only if capability remains desired: authorized provider setup and bounded real delivery proof, preserving Article 1. | Checkpoint “Owner operational exception notification amendment”; `DECISIONS.md` |

## Closed items (not active)

- `OI-0001` DOC-INDEX-CI-REPAIR: `CLOSED / OWNER_ACCEPTED_ON_TECHNICAL_EVIDENCE` on 2026-10-08. Explicit Owner decision; 68 tests PASS and two GitHub Actions runs SUCCESS. This is **not** a claim of formal independent reviewer acceptance. Closure evidence: `docs/doc-index-ci-repair-plan-20261008.md`, commit `e3743e64ce65ea1f747949d30eb5e53e9b64c9cf`. ID is never reused.

## Superseded / intentionally excluded

- Documentation-index and Constitution v2-marker **technical** FAILs: fixed and green; Owner accepted closure of OI-0001; no technical defect remains open.
- DR-04 rounding-change Human Gate: Owner approved versioned successor; do not reopen.
- DR-03 old capacity deferral/registration: later accepted DR-03 continuation supersedes them.
- ERiC developer-access email pending: access received, license accepted.
- Historical O4/O5/UI package blocker labels and earlier wake incidents: later progress or consolidated under OI-0010.
- Official ERiC submission/production: future external Human Gates, not failed currently authorized work.
- Old checkpoint/plan lines saying DOC-INDEX-CI-REPAIR “NOT EXECUTED”: superseded by verified commits/tests/Actions.

## Mandatory review

Read newest checkpoint and governing evidence; test each row against later accepted records; add genuinely new unaccepted gates; never dispatch work just because it appears here. Upon formal PASS, update plan and checkpoint with exact evidence and commit, then delete only the resolved active row. No automated schedule or additional execution authority is created by this document.
