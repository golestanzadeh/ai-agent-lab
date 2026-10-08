# Roadmap

This file contains remaining work only. Completed evidence belongs in `PROJECT_CHECKPOINT.md`, `DECISIONS.md`, focused documents, and Git history.

Last reconciled: **2026-10-08**


## Supervisor loop validation — 2026-10-07

- Design contract: `docs/supervisor-loop-design.md`.
- Status: `G1 PASS / G2-G4 LOCAL VALIDATION REQUIRED`.
- G1 passed on the real Windows/ChatGPT account: authenticated `codex app-server` exposed unambiguous 300-minute and 10080-minute windows through `account/rateLimits/read`; the read-only normalized reader and ignored runtime snapshot are implemented and focused verification passes. Evidence: `docs/supervisor-loop-g1-validation-20261007.md`.
- Validate next in order: G2 MCP event delivery to one designated Work chat, G3 one-shot Work wake, then G4 synthetic end-to-end loop.
- No MCP callback server, scheduler binding, credentials, Telegram adapter, or autonomous continuation is authorized before the corresponding smoke test passes.
- The existing Deterministic Orchestrator Kernel remains execution authority; this work may close the recorded `NO_AUTHORITATIVE_SCHEDULER` boundary but must not introduce a second orchestrator.

## Current position

- OI-0002 second independent review of `ad263284` is `FAIL`: F01/F04 pass, while F02/F03/F05/F06/F07 require bounded second remediation and another independent review. OI-0002 remains OPEN and OI-0003 remains blocked.
- Infrastructure reconciliation R1-R6 is independently accepted at implementation commit `9355f81`. DR-03 is independently accepted. DR-04 Part 1 preserves the Owner-approved EUR 32.00 credit / EUR 134.00 refund successor. The ten-rule candidate passed focused and relevant tests but failed Independent Acceptance because the exact accepted DR-02 predecessor identity was never durably recorded and cannot be safely invented. DR-04 is `HUMAN_REQUIRED`; DR-05 stays blocked. No external notification or transmission is active.

- O1-O5, P1 local synthetic packages 1-7, the four-role local runtime, and UI-1 through UI-19 are complete.
- ELSTER developer access, private Human authentication, Release 44 license acceptance, and local retrieval of the official 44.3.6.0 documentation/schema packages are complete.
- No real ELSTER/Finanzamt submission has occurred.
- Autonomous execution authority remains `AGENT_LED_CONTINUOUS_EXECUTION_ACTIVE`, but execution is fail-closed at `NO_AUTHORITATIVE_SCHEDULER`. The logical identity `plan-limit-continuation-guard` is reserved for one local-project ChatGPT Work Scheduled Task; the Codex trigger is paused/non-authoritative and no current schedule or Work object exists. Migration requires a real wake test and never uses five-minute polling.
- Owner authority `MILESTONE-A-20260927-001` is fully exercised. MA-01 through MA-05 are independently accepted; the complete local synthetic golden journey, failure matrix, clean setup, and read-only CI proof pass. External and production capabilities remain blocked.
- Owner authority for declaration remediation DR-01 through DR-05 is active. DR-01, DR-02 and DR-03 are `PASS`, but DR-02's exact accepted package identity was not durably captured. DR-04 is open at the resulting Human Gate after two independent-review failures. DR-05 is dependency-blocked.
- Infrastructure repairs for deterministic capacity governance and manifest-pinned indexed official knowledge are independently accepted; no CASE-001 declaration package advanced.

## Track 1 — Autonomous project control

Status: **milestone authority, deterministic queue control, and bounded two-package synthetic continuity proof verified; provider/production activation gated**

Remaining goals:

- connect provider workers only after exact authority and security acceptance;
- retain independent QA/acceptance, deterministic lineage, budgets, retry limits, kill switch, and checkpoint recovery;
- demonstrate multi-session operation without chat memory.

## Track 2 — Controlled ERiC/Finanzamt integration

Status: **official 44.3.6.0 material retrieved; local mapping profile v14/XSD/thirty-nine-rule plausibility lineage integrated; external execution blocked**

Dependency path:

`Detailed material verification -> adapter/schema mapping -> plausibility tests -> exact preview -> Article 1 approval 1 -> Article 1 approval 2 -> authorized transmission -> receipt/recovery`

Remaining goals:

- expand later official field mapping and local plausibility coverage only from reviewed source evidence and explicit synthetic semantics;
- extend later real-operational binding only behind the existing Human Gates; MA-04 proves the local synthetic durable approval/submission/receipt path without external capability.

## Track 3 — User interface

Status: **local synthetic prototype complete through UI-19 with Persian states, semantic accessibility, concise dynamic announcements, fail-closed empty-state startup, loopback launch, and browser hardening; real operations gated**

Remaining goals:

- add governed real case creation and document intake without weakening isolation;
- implement the real Human decision lifecycle only after its authority and persistence design are accepted;
- add authenticated protected-access and transmission controls only after Track 2 gates;
- expose receipt, pause/resume/stop, recovery, and support diagnostics;
- complete hands-on ordinary-phone validation without GitHub or terminal knowledge; deterministic phone-width and keyboard-accessibility safeguards plus one-click Windows startup are implemented.

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

- `docs/dr04-rounding-human-gate-20261006.json` records the fail-closed DR-04 Owner gate: authoritative taxpayer-favorable whole-euro declaration inputs imply a EUR 32.00 section-35a credit and a projected EUR 134.00 successor refund, while the accepted EUR 133.83 result remains frozen until an exact Owner decision.
- `src/agent_lab/owner_exception_notification.py`, `tests/unit/test_owner_exception_notification.py`, and `docs/owner-exception-notification-activation-20261005.json` are the authorized Constitution-v3 operational-exception sender boundary, deterministic validation tests, and privacy-minimized activation evidence. The sender accepts no arbitrary recipient, attachment, or free-form activation content.
- `docs/dr04-token-paused-after-owner-notification-repair-20261005.json` is the governed hard-threshold continuation capsule created after the accepted relay/notification repair; it preserves DR-04 as the exact next action and arms only the sole reset-aligned guard.
- `docs/work-scheduler-migration-stop-20261005.json` records the second missed wake, retirement of the non-authoritative Codex trigger, and the exact tooling prerequisite for a real local-project Work Scheduled Task wake test.

- `contracts/project-execution/v1/master-execution-graph.json`, `contracts/project-execution/v1/notification-contract.json`, `src/agent_lab/project_execution_graph.py`, `docs/master-execution-graph.md`, and `docs/repository-audit-20261004.json` form the authorized R1-R6 reconciliation surface. They project over the existing Kernel and controller and do not create another orchestrator, scheduler, authority store, or transmission channel.

- `docs/case001-reproduction-2024.md` is the privacy-safe durable execution record for Owner-authorized `RUN-CASE001-REPRO-20260928-001`. The 15-document Gemini run completed, but the formal Specialist/Chief result is `BLOCKED` by material source-evidence gaps; the historical refund cannot be numerically reproduced. Independent acceptance is `PASS`; sensitive source/provider artifacts remain outside Git.
- `docs/case001-independent-real-document-execution-2024.md` records completed corrected Owner run `RUN-CASE001-INDEPENDENT-20260928-002`: recursive discovery froze 16 taxpayer-source PDFs and excluded one official D026 form package; Gemini completed 16/16; all final Specialist roles, Chief, non-transmitting preview, and Independent Acceptance passed. The independent current result is z.v.E. EUR 27,928, Einkommensteuer EUR 700, and refund EUR 76; no historical target was used.
- `docs/case001-comparative-audit-2024.md` records the diagnostic-only comparison: the EUR 5.17 endpoint difference reconciles exactly through the reported EUR 37 tariff difference and EUR 31.83 historical section 35a credit, while missing historical deduction intermediates and a one-euro tariff inconsistency keep the rule-level result at `AUDIT_UNRESOLVED`. No current implementation defect or repair authority exists.
- `docs/case001-structured-financial-evidence-2024.md` records the completed canonical CSV intake: all 946 rows have stable terminal dispositions and exact candidate lineage; school fees and section 35a trigger a versioned successor refund of EUR 133.83 while the frozen EUR 76 result remains unchanged. Specialist, Chief and Independent Acceptance pass.
- `docs/case001-donation-evidence-2024.md` records the bounded EUR 60 Bjorn Steiger Stiftung reconciliation. The PDF/payment match is exact, but the recipient-produced document lacks three explicit section 50(4) EStDV particulars; status is `DONATION_EVIDENCE_INCOMPLETE` and the accepted EUR 133.83 result is unchanged.
- `docs/case001-declaration-readiness-2024.md` and its JSON companion freeze the accepted EUR 133.83 tax case. The bounded queue is already Owner-authorized; current continuation is DR-03 completion, DR-04 repair/acceptance, then DR-05.
- `docs/official-knowledge-index.md` defines the verified reusable official-knowledge index and precise protected-source-free normal lookup path.
- `docs/infrastructure-repair-20261004.md` records Repair A/B acceptance and the preserved CASE-001 continuation marker.
- `docs/case001-dr01-stop-diagnostic-20260929.md` and its JSON companion record the authorized queue's fail-closed DR-01 stop, exact protected-artifact identities, exhausted bounded recovery, capacity observations, and precise continuation after private ELSTER developer re-authentication.
- `docs/protected-official-source-store.md` records acceptance of the portable local ERiC 44.3.6.0 source store, registry/resolver, exact identities, minimal extraction, backup separation, and fail-closed tests.
- `docs/case001-dr01-acceptance-2024.md` and its JSON companion retain the historical, now-superseded DR-02 continuation recorded when DR-01 was accepted.

## Cleanup rule

- Keep this file limited to incomplete work and registered future artifacts.
- Remove temporary probes and generated outputs when they carry no unique audit or recovery value.
- Never remove reusable contracts, tests, security evidence, isolation controls, or consequential audit records merely to shorten the repository.
