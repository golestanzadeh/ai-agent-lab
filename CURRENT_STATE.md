# Current State

Last reconciled: **2026-09-27**

## Authoritative status

- CASE-001 / tax year 2024 analytical preparation is complete and Chief-approved by explicit Human recovery confirmation.
- No ELSTER submission or Finanzamt transmission has occurred.
- Unrecovered post-D-028 details remain `NOT_RECOVERED` and must not be fabricated.
- `PROJECT_CHECKPOINT.md` is the mandatory cross-session entry point.

## Completed foundations

- Deterministic case/person/tax-period identity, case isolation, scoped storage, evidence, audit, and durable approval boundaries.
- Controlled CASE-001 migration, document processing, six-role tax runtime, and Chief review.
- Agent Bridge, Local Sync, Windows Relay, and Orchestrator phases O1-O5; O5 was Human-accepted at `d64da2588b18f548c877aed6044f8884e7644cdc`.
- Owner approval `ORCH-CONT-20260927-001` is active. Milestone-authority contract v1 and its Kernel controls now fail closed on authority amplification, select ready packages in durable dependency order, permit only bounded queue-exhaustion replanning, and persist complete non-token STOP diagnostics. Contract validation and the focused Kernel suite pass (`41 passed`).
- Owner authority `MILESTONE-A-20260927-001` is active. The exact five-package envelope is pinned to `sha256:2a6d89b6c350b5a1b653bfb7b8b1ddf472188785104389967786e23d97249d09`. MA-01 implements the closed twelve-stage golden-journey coverage manifest and is independently accepted; full unit regression passes (`876 passed, 1 warning`). Kernel checkpoint `sha256:9c7f5a28521d82ac70ffd2dd8c9d5de74b8c9e6512ac977380508ac50656625b` makes MA-02 ready.
- The bounded `SYNTHETIC_LOCAL_V1` continuity proof passed with two dependency-ordered packages, three dispatch attempts, one recoverable failure, two independent acceptances, one bounded replan, durable close/reopen checkpoint recovery, simulated capacity pause, audit integrity `PASS`, and final kill switch `HALTED`. Focused verification passes (`31 passed`); the complete unit regression passes (`863 passed, 1 warning`).
- Phase P1 local synthetic ERiC boundary through package 7.
- Local E10/2024 mapping profile version 14 for the bounded Anlage N employment subset, including the reviewed wage-tax, professional-association, work-equipment, home-office workroom/day, training, ferry-or-flight, domestic-travel, single business-travel transport-cost item, employer-reimbursement, commuting-benefit/subsidy, and other-expense fields; omitted optional values remain absent and are never inferred.
- Complete synthetic E10/2024 declaration assembly and local validation against the exact hash-pinned official `E10-2024.xsd`; protected schema contents remain outside Git and official ERiC plausibility execution remains blocked.
- Source-evidenced local plausibility profile version 11 evaluates thirty-nine official Anlage N rules, including bounded single-item professional-association, work-equipment, home-office workroom, training, home-office-day, ferry-or-flight, domestic-travel, and other-expense completeness contracts.
- A fresh complete unit regression, including the formerly order-sensitive Windows Google Drive provisioning tests, passes: `693 passed, 1 warning`. This verifies the current local unit surface; it does not prove the earlier intermittent environment behavior permanently resolved.
- Historical package-2 adapter and synthetic-preview documentation now explicitly defer current mapping/XSD/plausibility claims to the separately versioned E10 readiness pipeline; immutable upstream status names are no longer presented as current blockers.
- A current-state readiness artifact now binds the exact mapping, official-XSD declaration, and passing local plausibility identities. Historical package blockers remain historical; the live residual boundary is official ERiC-engine execution, real-data authority, both Article 1 approvals, and a transmitter.
- Local four-role Agent Runtime Activation Layer at `cb41d13`; verification: `537 passed, 1 skipped`.
- Read-only Agent Runtime recovery inspection classifies intact planned/completed boundaries and interrupted mid-resume state with exact durable completed-stage evidence; automatic replay remains forbidden.
- The Human-authorized local synthetic repair/replay policy, versioned evaluator, and bounded continuation executor are implemented. Every permitted remaining-stage boundary is covered; completed stages are not replayed, and partial/extra traces fail closed. Targeted runtime verification: `34 passed`.
- The complete local unit regression after runtime repair integration passes: `712 passed, 1 warning`.
- The profile-v3 E10 expansion passes its targeted suite (`109 passed`), both exact official-XSD probes, and the complete local regression (`718 passed, 1 skipped, 1 warning`).
- The profile-v4 professional-association expansion passes its focused suite (`122 passed`), exact official-XSD probe, and complete local regression (`733 passed, 1 skipped, 1 warning`).
- The profile-v5 work-equipment expansion passes its focused E10/UI/documentation suite (`166 passed, 1 warning`), exact official-XSD probe, and complete local regression (`748 passed, 1 skipped, 1 warning`).
- The profile-v6 home-office workroom expansion passes its focused E10/UI/documentation suite (`181 passed, 1 warning`), exact official-XSD probe, and complete local regression (`763 passed, 1 skipped, 1 warning`).
- The profile-v7 training expansion passes its focused E10/UI/documentation suite (`196 passed, 1 warning`), exact official-XSD probe, and complete local regression (`778 passed, 1 skipped, 1 warning`).
- The profile-v8 home-office-day expansion passes its focused E10/UI/documentation suite (`208 passed, 1 warning`), exact official-XSD probe, and complete local regression (`790 passed, 1 skipped, 1 warning`).
- Plausibility profile v9 adds the two reviewed other-expense completeness rules without changing mapping profile v8. Its focused E10/UI/documentation suite passes (`209 passed, 1 warning`), and the complete local unit regression passes (`795 passed, 1 warning`).
- Mapping profile v9 and plausibility profile v10 add one paired synthetic ferry-or-flight item and reviewed rule `121361`. The generated declaration passes the exact official XSD, the focused E10/UI/documentation suite passes (`218 passed, 1 warning`), and the complete local unit regression passes (`804 passed, 1 warning`).
- Combined other-expense boundary hardening proves that the derived aggregate rejects twelve-digit overflow and that rule `100200002` uses the combined `Sonst` plus ferry-or-flight total at the exact tolerance boundary. Focused verification passes (`155 passed`), and the complete local unit regression passes (`807 passed, 1 warning`).
- Ferry-or-flight omission and identity hardening proves explicit zero is distinct from omission, preserves the derived aggregate, and changes the cryptographic lineage. Focused mapping verification passes (`86 passed`), and the documentation guard passes (`8 passed`).
- Mapping profile v10 and plausibility profile v11 add the domestic travel day/reduction subset and three reviewed rules. The generated declaration passes the exact official XSD, the focused E10/UI/documentation suite passes (`232 passed, 1 warning`), and the complete local unit regression passes (`818 passed, 1 warning`).
- Domestic-travel hardening covers the exact `366/367` combined-day boundary, both `14`-euro partial-day categories, and cryptographic lineage changes. Focused verification passes (`178 passed`).
- Mapping profile v11 adds the official employer tax-free travel reimbursement field `E0205108` with whole-euro, non-negative, twelve-digit fail-closed validation. The generated declaration passes the exact official XSD, the focused E10/UI/documentation suite passes (`240 passed, 1 warning`), and the complete local unit regression passes (`826 passed, 1 warning`).
- Employer-reimbursement hardening proves explicit zero is distinct from omission, accepts the exact twelve-digit maximum, binds the field into request/result identity, and rejects every superseded mapping profile. Focused mapping/documentation verification passes (`110 passed`).
- Mapping profile v12 adds the official optional Jobcenter/Agentur travel-cost subsidy field `E0204004` with non-negative whole-euro twelve-digit validation, explicit-zero preservation, identity binding, and exact `N/Wk/EP/Fahrtk_Ersatz` placement. The generated declaration passes the exact official XSD and the focused E10/documentation suite passes (`228 passed`).
- Mapping profile v13 adds official tax-free and flat-taxed employer commuting-benefit fields `E0204103` and `E0203901`, preserving the official field order alongside `E0204004`, with the same whole-euro, omission, boundary, and identity guarantees. The generated declaration passes the exact official XSD and the focused E10/documentation suite passes (`238 passed`).
- Mapping profile v14 adds one synthetic business-travel transport-cost item with exact official fields `E0205003` and `E0205004`, enforcing reviewed pairing rule `100200074`, lexical boundaries, official order, omission/explicit-zero distinction, and identity binding. The generated declaration passes the exact official XSD and the focused E10/readiness/UI/documentation suite passes (`287 passed`).
- Local FastAPI + Jinja/HTMX Persian UI through UI-19; closed Persian labels are joined by semantic accessibility, concise dynamic case announcements, and fail-closed startup when no scoped synthetic case exists.

## Live external status

- The ELSTER developer-access email was received and the Human authenticated privately on 2026-09-16.
- After explicit Human acceptance, the official ERiC Release 44 software-manufacturer license was accepted.
- Official `44.3.6.0` documentation and schema-documentation ZIPs were retrieved locally and hash-verified. They remain outside Git.
- The official page states ERiC 41 and 42 can no longer transmit after the 2026-04-27 minimum-version increase. The Project Owner authorized the local non-production migration, and adapter contract version `2` now binds ERiC `44.3.6.0`, procedure `UFA10`, tax year `2024`, and the E10/2024 material categories. The adapter itself remains inert; the separate local E10 pipeline provides mapping profile v14, exact official-XSD validation, and a thirty-nine-rule local plausibility subset while official ERiC-engine execution remains fail-closed.

## Active boundaries

- Development remains on `d021-agent-case-provisioning`; `main` is behind and protected.
- Current work is limited to authorized local, synthetic, non-production, architecture-compatible changes.
- Real data, credentials, protected access before Human login, provider/network activation, external transfer, production, ELSTER/Finanzamt action, merge/release, and destructive action remain Human Gates.
- Article 1 exact-content and exact-recipient/channel approvals are separate and both remain `NOT_APPROVED`.
- Plan-limit continuation must stop at its documented thresholds.
- Execution governance remains `AGENT_LED_CONTINUOUS_EXECUTION_ACTIVE`, while scheduler `plan-limit-continuation-guard` is intentionally `PAUSED` under terminal condition (3). The latest end-of-package observation reported five-hour `66%` and weekly `95%` remaining after proof commit `adbba53d284fe38aa3ccb5af0a38df0a7972b921`; capacity is not the stopping reason.
- The Project Owner reaffirmed continuous autonomous progression on 2026-09-20 with no routine reporting. The active plan-limit guard uses a five-minute cadence, reflects completed developer access, and may execute sequential authorized bounded packages while each end-of-package check remains safe, retaining all token thresholds and Human Gates.
- The plan-limit controller document is reconciled with that active state; its former package-7 Human-Gate pause is retained only as history, not current status.
- The guard checks limits after every completed/pushed package and must immediately start the next bounded authorized package while safe. A pre-first-package check is only a fallback when the current execution window has no reliable live observation; routine heartbeat-start checks are disabled.
- The focused documentation index now includes the current runtime recovery, E10 mapping/declaration/plausibility/readiness, and UI records through UI-19; a deterministic test prevents future silent index drift.
- Canonical-state tests also require the checkpoint, current state, and roadmap to agree on the latest UI package, active branch, and continuous-execution state.
- Canonical-state tests now also require every active record to retain mapping profile v14 and reject superseded current-profile summaries.

## Remaining product work

1. Execute registered synthetic packages MA-02 through MA-05 in dependency order without duplicating existing components.
2. After synthetic Milestone A passes, verify the exact real-data/Gemini authority boundary before any controlled CASE-001 reproduction operation.
3. Expand official E10/2024 field mapping only from separately reviewed exact source evidence and explicit synthetic semantics.
4. Keep external submission, official ERiC execution, product release, and production controls behind their existing Human Gates.

## Exact next action

State is `TOKEN_PAUSED` because the post-MA-01 five-hour window has `12%` remaining. At or after `2026-09-27T23:41:49Z`, read only live limits; if resume thresholds pass, run the Recovery Gate before ending the pause, then execute dependency-ready `MA-02-COMPOSITION-AND-STORE`. Real CASE-001/Gemini processing remains a separate post-synthetic authorization check.

## Non-negotiable constraints

- Never reopen completed CASE-001 questions solely from superseded historical reports.
- Require `case_id` for every tax-case operation; never mix cases or tax years.
- Never store credentials, private Drive IDs, private tax documents, or protected material in GitHub.
- Never treat tests as Human acceptance or a displayed approval state as authority.
- Never submit, sign, transmit, release, merge protected `main`, or expand permissions without the applicable explicit Human Gate.
