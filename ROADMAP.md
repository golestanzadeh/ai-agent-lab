# Roadmap

This file contains remaining work only. Completed evidence belongs in `PROJECT_CHECKPOINT.md`, `DECISIONS.md`, focused documents, and Git history.

Last reconciled: **2026-09-20**

## Current position

- O1-O5, P1 local synthetic packages 1-7, the four-role local runtime, and UI-1 through UI-8 are complete.
- ELSTER developer access, private Human authentication, Release 44 license acceptance, and local retrieval of the official 44.3.6.0 documentation/schema packages are complete.
- No real ELSTER/Finanzamt submission has occurred.

## Track 1 — Autonomous project control

Status: **local synthetic runtime verified; provider/production activation gated**

Remaining goals:

- harden restart/recovery, including safe mid-resume recovery;
- connect provider workers only after exact authority and security acceptance;
- retain independent QA/acceptance, deterministic lineage, budgets, retry limits, kill switch, and checkpoint recovery;
- demonstrate multi-session operation without chat memory.

## Track 2 — Controlled ERiC/Finanzamt integration

Status: **official 44.3.6.0 material retrieved; contract migration and bounded E10/2024 Anlage N subset mapping implemented**

Dependency path:

`Detailed material verification -> adapter/schema mapping -> plausibility tests -> exact preview -> Article 1 approval 1 -> Article 1 approval 2 -> authorized transmission -> receipt/recovery`

Remaining goals:

- assemble a complete synthetic E10/2024 declaration around the verified Anlage N subset;
- validate the complete synthetic declaration locally against the recovered official XSD set;
- expand official field mapping and local plausibility coverage only from reviewed source evidence;
- bind payload, recipient, channel, expiry, idempotency, and retry to durable approvals;
- prevent silent, stale, duplicate, or cross-case filing and preserve recoverable receipts.

## Track 3 — User interface

Status: **local synthetic display prototype complete through UI-8; real operations gated**

Remaining goals:

- add governed real case creation and document intake without weakening isolation;
- implement the real Human decision lifecycle only after its authority and persistence design are accepted;
- add authenticated protected-access and transmission controls only after Track 2 gates;
- expose receipt, pause/resume/stop, recovery, and support diagnostics;
- validate ordinary phone and Windows use without GitHub or terminal knowledge.

## Track 4 — Product acceptance and release

Status: **blocked by remaining gated work in Tracks 1-3**

Required flow:

`Create Case -> Intake -> Process -> Specialist Review -> Chief Review -> Calculation -> Form Preview -> Human approval stages -> ELSTER submission -> Receipt`

Required checks include case isolation, privacy/security, restart/crash/retry/revocation/expiry, duplicate prevention, audit recovery, official-version evidence, protected-main review, release approval, monitoring, rollback, and kill switch.

## Scheduling and constraints

- Independent, prerequisite-ready, already authorized work may proceed in parallel.
- Dependency order remains mandatory where later work relies on an earlier foundation.
- Human Gates, testing, auditability, case isolation, protected-main rules, and plan-limit controls remain unchanged.
- Target: complete before 2026-10-05 where external dependencies and Human Gates permit.

## Future-file register

No future artifact is currently registered. Register a necessary file here before creating it, including purpose, dependencies, acceptance criteria, and Human Gate.

## Cleanup rule

- Keep this file limited to incomplete work and registered future artifacts.
- Remove temporary probes and generated outputs when they carry no unique audit or recovery value.
- Never remove reusable contracts, tests, security evidence, isolation controls, or consequential audit records merely to shorten the repository.
