# OPEN_ITEMS â€” Active Unaccepted Gates

<!-- CURRENT_PROJECT_STAGE: SYNTHETIC_UI_ACCEPTED_REAL_PRODUCT_GATED -->
<!-- CURRENT_NEXT_ACTION: C09_R3_HG01_F01_F04_REMEDIATION_AND_INDEPENDENT_REREVIEW -->
<!-- CURRENT_ACTIVE_OPEN_ITEMS: OI-0002..OI-0008,OI-0010,OI-0012 -->

Owner-proposed tracking design, active inventory reconciled after OI-0001 Owner closure (2026-10-08). This file is a **read-only projection** of existing Kernel acceptance, authoritative plans and `PROJECT_CHECKPOINT.md`; it is not a second checkpoint, queue, scheduler or execution authorization.

## Lifecycle (proposal recorded, automatic enforcement not implemented)

At every governed recovery and package boundary, reconcile active gates with the **latest** independent evidence, not historical checkpoint labels. Register only the **unresolved part** with a stable ID, exact next action, dependencies and acceptance authority. A later accepted PASS supersedes an earlier FAIL; do not reopen it. On formal independent PASS, first commit evidence and update checkpoint/plan, then remove the row from this active list in a committed change; Git history preserves the record. New unresolved gates get new sequential IDs. Every future stage transition must assess and synchronize both `PROJECT_CHECKPOINT.md` and this file in the same governed change set; when no active row is resolved, preserve the rows and explicitly record that result. An unattended periodic schedule requires separate authorization; none is created here. Protected taxpayer facts and credentials never belong in Git.

## Verified active items

2026-10-27 F07 mission status is `BLOCKED_SPEC_GAP`: exact operational Identity request/proof fields, digest/signature preimages/construction order, operation-specific read result schemas and golden vectors require clarification in the existing contract before operational implementation. Recovered client composition `77fd630ffad62e97515c69e384b51387e77262fd` has independent PASS only for development-contract validation/correlation (232 focused, 366 expanded); no live SCM or operational Identity acceptance exists. Existing host entrypoints remain unavailable by default; timeout/cancellation and real-principal deployment evidence remain required. No active row closes. See checkpoint and `docs/f07-runtime-activation-preparation-20261026.md`.

2026-10-26 local dashboard discovery documented in `docs/dashboard-local-execution-handoff-20261026.md` and linked from `PROJECT_CHECKPOINT.md`: port 8766 is the no-source read-only product app in the c09-continuation worktree; existing F06 runtime and F07 readiness code must be reused. The operational service client/dispatcher and SCM composition remain missing, and protected case creation / Drive mutation remain gated. This is documentation only; no active row closes, no acceptance or stage transition occurs.


F07 preparation resumed 2026-10-26: configuration/gate/readiness code is a candidate pending independent review. The exact service integration prerequisite is the existing SCM host's `unavailable_runtime` composition and absent operational client/dispatcher; no synthetic adapter was promoted. No active row closes. See `docs/f07-runtime-activation-preparation-20261026.md`.

F07 preparation final `de0ef2ee1bd612c173774b54902b0070c5d557be` received `INDEPENDENT_PASS` (41 focused tests plus adversarial configuration probes); constructor-validation finding is resolved. Overall operational service integration remains prerequisite-blocked, not accepted: the existing-role client/dispatcher and SCM composition are absent. All protected gates, operational C09/OI-0002, OI-0003 evidence-bound registration and provider/Owner Human Gates remain active. No row closes.

F06 independently accepts `5f2547a2707a785f34766361ab22148535725086` for the existing production runtime's read-only composition, fresh authorized multi-case/year state/Run/storage display and audited disabled provider/activation boundaries. Independent tests: 37 UI/runtime and 91 relevant persistence/Identity; storage-integrity fail-open finding is resolved. The trusted operational host/configuration, OI-0002/C09 service/finality acceptance, protected OI-0003 registration and provider deployment gates remain outstanding. No active row closes; this is not operational activation.

2026-10-26 Owner architecture decision for OI-0003: `OWNER_APPROVED / IMPLEMENTATION_PENDING`. Separate opaque successor internal Person A/B IDs, unmapped legacy owner preservation, explicit marriage relationship scope and existing SubjectFactEnvelope individual facts are approved. These are no longer Owner questions. Implementation, evidence-bound protected registration and independent operational acceptance remain required; no active row closes.

F05 final `7b1706ac2ccd75022f05aad42cfe9e595b663a4f` has `INDEPENDENT_PASS` for read-only committed storage references and OI-0003 schema/association code (74 independent focused tests plus Windows adversarial probes). Authority-row deletion completeness and rejected-startup handle cleanup findings are resolved. The architecture decision is approved and its bounded code implemented; actual protected successor/party/fact registration and operational acceptance remain pending. No active row closes and no unchanged fact requires reconfirmation.

The 2026-10-25 local operational-unblocking slice added an owner-scoped, explicit-allowlist, read-only CaseRegistry projection to the existing Dashboard and passed 33 focused tests with synthetic data. It resolves no active row below: OI-0002/OI-0003 remain the protected identity/persistence boundary, while C09/HG-01/GCS gaps do not globally block unrelated non-privileged UI development. See `docs/ui25-local-operational-unblocking-20261025.md`.

Continuation connected that reader and exact-scope read-only Kernel projection to the real local product launcher; startup/restart/configuration and isolation verification passes `69`. This still resolves no active row: the missing durable provider for the existing CaseRegistry/CaseState authorization composition is part of the OI-0002/OI-0003 protected boundary, not authorization to promote the test SQLite store or PostgreSQL PoC.

The durable provider code gap is now implemented as a one-database SQLite candidate with atomic case/state/authorization/audit registration, integrity verification and restart reconstruction (`65` focused tests). It is not independently accepted or activated for protected data, so OI-0002 remains active. OI-0003 still requires the exact Owner identity/role/subject-fact decision described in its row; no identity was inferred and no active row closes.

Independent review of `dd831b7` failed on rollback/deletion, empty-store key binding and missing durable state/run mutation. F01/F02 have a bounded audit-anchor remediation with `17` focused tests; F03 remains open pending exact-SHA re-review and a separately scoped mutation package. OI-0003 inventory recovered no authoritative Person A/B IDs or party bindings; prior Owner-confirmed facts and declaration hash remain valid without reconfirmation. No row closes.

Re-review of `50a0a7f` confirmed F01/F02 fixed but found F04 Windows handle leakage after rejected initialization. The narrow close-on-failure repair passes `18`; exact-SHA re-review remains required. F03 and coordinated DB+anchor rollback remain open, so OI-0002 does not close.

Final independent review of exact `e1410514295253bd1e171faba10cf7348ddf6c79` is PASS for immutable initial registration, restart reconstruction and read-only Dashboard only (`40` focused plus Windows rejected-open cleanup probes). F01/F02/F04 are resolved in that bounded scope. F03 durable state/run mutation and atomic Kernel/CaseCreationWorkflow integration remain open; coordinated DB+anchor rollback remains C09. OI-0002 and OI-0003 stay active and no row closes.

F03 durable state/Run mutation and exact registered-Kernel binding now have `INDEPENDENT_PASS` at `8d08f7a72465922e8878c326a1db286d61f5f774`. Independent verification passed `69` focused tests plus adversarial immutable-replay and task/request-collision probes. Versioned mutations, optimistic conflicts, idempotent results, exact owner/case/year/run scope, restart reconstruction, v1-to-v2 migration and multiple same-year/multi-year cases are accepted for this bounded code scope. This resolves the prior F03 implementation finding but does not close OI-0002: coordinated DB+anchor rollback/C09, privileged operational controls and external CaseCreationWorkflow storage/association compensation remain unaccepted. OI-0003 subject/case identity decisions also remain. No active row is removed.

F04 durable storage intent and recovery integration now has `INDEPENDENT_PASS` at `abda1c8579710c1e90537cb1d73ae036f63273a1` (`93` focused tests plus typed-failure adversarial probes). It accepts only synthetic non-privileged reconciliation around the existing Google Drive creator; it does not activate real Drive credentials or protected data. Runtime credential/ACL/privacy/retention/isolation evidence, an authorized uncertain-outcome reconciliation procedure, C09 and OI-0003 remain open. No active row is removed.

| ID | Unaccepted part (not the whole process) | Evidence / current status | Dependencies and next review | Governing reference |
| --- | --- | --- | --- | --- |
| OI-0002 | CASE-001 Identity & Family Persistence (stage 1; mandatory critical path) | R1/R2/base R3 and HG-01/02/03 preparation have bounded independent PASS. HG01 BP-01/I01/I02/synthetic-I03/I05 are implemented locally; I04 has a later exact-reproducibility PASS at f1af82f (75/75 identical A/B manifest entries, zero differences), with full regression 1558 passed / 6 skipped; original 97adcca failure remains historical evidence. Artifacts are unsigned and not deployment eligible. Independent Codex review returned INDEPENDENT_FAIL (F01/F02 HIGH, F03/F04 MEDIUM); remediation and exact-SHA re-review required. HG-03 and operational Custodian remain separately blocked. | Next: independent exact-SHA implementation/build security review, remediate findings and repeat review, then assess nonprivileged synthetic service composition/R1 and R2. HG-01 activation remains a separate Owner gate. Never deploy/install current artifacts. | `docs/oi0002-c09-witness/HG01_IMPLEMENTATION_2026-10-24.md`; `config/c09-r3/hg01-build-evidence.json`; `config/c09-r3/hg01-signing-profile.json` |
| OI-0003 | Package A protected Owner Facts Registration (stage 2) | Owner architecture `OWNER_APPROVED`; schema/association code bounded `INDEPENDENT_PASS` at `7b1706ac2ccd75022f05aad42cfe9e595b663a4f`. Legacy owner remains unmapped; protected successor/party/fact registration is not executed or accepted. Prior declaration integrity and unchanged confirmation remain valid. | Accepted operational OI-0002 Identity execution boundary; then evidence-bound internal successor allocation, explicit subject/case associations and confirmed individual/relationship fact registration, followed by independent acceptance. No architecture reconfirmation required. | Recovery plan stage 2; checkpoint F05 2026-10-26; existing Identity authority |
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


## HG01 reviewer handoff reconciliation - 2026-10-24

Independent Codex reviewer package and ready-to-send prompt prepared in docs/oi0002-c09-witness/HG01_CODEX_INDEPENDENT_REVIEW_HANDOFF_2026-10-24.md and HG01_CODEX_REVIEW_PROMPT_2026-10-24.txt. No review has run; OI-0002 remains active and no active row was resolved. Reviewer must establish separate read-only context, capacity admission and exact-SHA findings before independent acceptance.

## HG01 independent review FAIL reconciliation - 2026-10-24

Reviewer returned INDEPENDENT_FAIL for F01 VERIFY_WITNESS semantics, F02 Kernel proof verification, F03 stale build/service evidence, F04 canonical marker regression. Evidence and corrective requirements: docs/oi0002-c09-witness/HG01_INDEPENDENT_FAIL_AND_REMEDIATION_2026-10-24.md. OI-0002 stays OPEN; no active item resolved.

## HG01 F01-F04 containment - 2026-10-24

F01/F02 unsafe accept path now denies both Custodian operations, but frozen functional contract remains NOT IMPLEMENTED. F03 historical evidence preserved and separate current baseline snapshots added. F04 markers synchronized; focused 30 passed. Full regression pending. No OI-0002 closure, no independent PASS; see docs/oi0002-c09-witness/HG01_F01_F04_REMEDIATION_PROGRESS_2026-10-24.md.
