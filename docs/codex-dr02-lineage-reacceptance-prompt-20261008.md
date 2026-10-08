# Codex dispatch — OWNER-AUTHORIZED bounded DR-02 lineage re-acceptance (2026-10-08)

OWNER AUTHORIZATION: On 2026-10-08, the Owner explicitly approved the second option in `docs/dr02-lineage-reacceptance-plan-20261008.md`: bounded DR-02 lineage re-acceptance. This is NOT permission to invent or self-accept canonical identities, change tax amounts, bypass independent acceptance, transmit externally, or begin DR-05.

START: Read authoritative GitHub `PROJECT_CHECKPOINT.md` on branch `d022-supervisor-loop-design`, `AGENTS.md`, `docs/codex-agent-workflow.md`, `docs/dr02-lineage-reacceptance-plan-20261008.md`, DR-02 and DR-04 acceptance records and directly relevant code/tests. The local checkpoint was intentionally deleted; do NOT recreate it. Preserve all existing uncommitted/untracked changes.

CAPACITY: Starting quota is exactly 23% five-hour remaining and 68% weekly remaining, supplied by Owner. Before work, estimate the full task and apply the Limit Guard to these supplied values; do NOT make an initial quota measurement. After work, measure actual ending quota and append the verified exact readings and reset times at the END of the existing local `.runtime/work-bridge/WORK_RESULT.md` as specified below. Preserve the existing bridge state and reporting contract.

MISSION (only bounded DR-02 identity gate):
1. Inventory exact, authorized CASE-001/2024 accepted DR-02 case-scoped artifacts and immutable provenance, without broad searches or changing existing accepted data. Record reproducible request reference, prior-result reference, complete canonical XML SHA256, DR-02 result artifact identity and run scope, or explicitly mark each unrecoverable.
2. If accepted identities cannot be recovered, construct a proposed re-acceptance candidate from authorized original inputs, with reproducible deterministic replay and source/XSD checks. Clearly distinguish NEW proposed identity from previously accepted identity; no retroactive claim.
3. Test case/run/year/source binding and negative substitution of request, prior result, unrelated non-VOR XML and XML digest. Do not promote a candidate without independent review.
4. Prepare independent DR-02 lineage acceptance dossier with evidence, expected identity pins, reproducibility and exact Human Gate. Request independent acceptance under existing project mechanism; never self-certify.
5. On actual independent PASS only, durably record newly accepted identities and checkpoint; otherwise mark HUMAN_REQUIRED and exact continuation. Do not resume DR-04 until DR-02 identity is accepted and capacity permits.
6. Keep GitHub `PROJECT_CHECKPOINT.md` authoritative and update in same governed change set. Preserve non-transmitting boundary. Do not change tax calculations or the 32.00/134.00 approved successor. Do not merge, release, submit, sign, use certificates, run Wake, or touch DR-05.

CONTINUOUS EXECUTION: solve ordinary failures, run focused tests, document, and stop only for real authority/capacity blocker. Return concise status, live quota, artifacts, tests, commit, and exact next action.


## CAPACITY HANDOFF CONTRACT — OWNER-APPROVED (2026-10-08)

The supervisor supplies the exact **remaining** Codex quota in this prompt. For this FIRST handoff, Owner-provided starting values are **23% remaining in the 300-minute window and 68% remaining in the 10080-minute window**. These are the authoritative handoff inputs for this package, not a fresh Codex measurement. For later prompts, the supervisor reads the previous task's **verified end-of-task** `.runtime/work-bridge/WORK_RESULT.md` quota appendix and passes its exact values and timestamp into the new prompt. Do not replace the supplied starting quota with an unnecessary pre-task `account/rateLimits/read` query.

BEFORE starting implementation, estimate this entire bounded task's quota cost conservatively, including tests, repair, evidence, documentation and independent review plus a safety reserve. Apply the existing deterministic Limit Guard to the supplied values, with any established age/reset rules. If the supplied values are stale, their reset window cannot be determined, the guard rejects the package, or the estimate exceeds available headroom, STOP before implementation with a precise capacity-blocked report; request updated capacity evidence rather than guessing. Do not pretend the supplied starting values are a live measurement.

IF the package is admitted, execute it through completion or a real Human Gate. At the END, query the actual authenticated Codex rate limits ONCE via the existing reader, record exact 300-minute and 10080-minute used/remaining percentages, reset timestamps, measured_at, and source into the existing local `.runtime/work-bridge/WORK_RESULT.md` as a clearly delimited FINAL appendix, using the established report writer and preserving unrelated fields. Read back and verify the persisted snapshot. If a package stops early, still record the ending quota when possible. If the measurement/write fails, report that the next task lacks a verified capacity handoff and fail closed. The supervisor must use this verified ending appendix in `WORK_RESULT.md` for the NEXT prompt. Do not rely on `BRIDGE_STATE.json` as the sole quota evidence. Do not create duplicate bridge files, invent values or confuse Work quota with Codex quota. No public commit of account-specific usage data unless project policy allows it.


### Supervisor owns reset-window arithmetic (Owner clarification 2026-10-08)

The supervisor, NOT Codex, reads the prior verified `WORK_RESULT.md` end-of-task capacity appendix, including measured_at and exact reset_at for each quota window, and computes effective available quota at the NEXT dispatch time. If a window's reset time has passed, the supervisor may use 100% remaining for that window **only if** no intervening usage is known and the handoff is otherwise trustworthy; if usage may have occurred, the supervisor must obtain new evidence or mark the capacity uncertain, not fabricate 100%. If the next task does not fit, the supervisor calculates the next eligible reset time (with timezone conversion), defers dispatch and supplies the computed quota and provenance in the next prompt. Codex's role remains estimating full task cost against the supervisor-supplied quota and writing/verifying the ending quota appendix in `WORK_RESULT.md`; no initial quota measurement.


## FINAL OWNER DIRECTIVE — WORK_RESULT IS THE QUOTA HANDOFF (2026-10-08)

This section supersedes all conflicting quota-report destinations above or in earlier documents. Owner-supplied START capacity for THIS dispatch is **23% five-hour remaining / 68% weekly remaining**, NOT 23/86 or 24/86. The 24/86 figures belong to a previous Work report, not the current Owner-supplied Codex capacity. Do not perform an initial live quota query; apply full-package conservative feasibility estimation and Limit Guard against 23/68.

At the END of every outcome (PASS, FAIL, HUMAN_REQUIRED, TOKEN_PAUSED, or safe early stop), obtain actual authenticated Codex quota evidence if available and **append the following exact block as the last section of the existing local `.runtime/work-bridge/WORK_RESULT.md`**. This is mandatory even if the task is blocked; when reading is impossible, record UNKNOWN and the specific reason rather than inventing numbers. Respect the existing Work bridge report contract, archive prior task state/report first if required, and write the new report atomically. Never overwrite unrelated task history, invent a parallel report, or commit private account quota to GitHub. If the established writer or contract does not permit Codex to update WORK_RESULT safely, stop with HUMAN_REQUIRED and report the incompatibility rather than overwriting a Work-owned report.

```text
## CODEX_CAPACITY_HANDOFF — FINAL
Task-ID: <exact task id>
Codex quota measured_at: <ISO-8601 timestamp or UNKNOWN>
Codex five_hour_remaining_percent: <exact value or UNKNOWN>
Codex five_hour_reset_at: <ISO-8601 timestamp or UNKNOWN>
Codex weekly_remaining_percent: <exact value or UNKNOWN>
Codex weekly_reset_at: <ISO-8601 timestamp or UNKNOWN>
Measurement source: <authenticated reader/source or failure reason>
Readback verified: <YES/NO>
Next dispatch quota status: <VERIFIED / UNVERIFIED>
```

Read the report back after the write, verify the appendix is the final section and its values match the measured source, and include the WORK_RESULT path in the final response. The supervisor owns reset-time arithmetic and next-dispatch decisions. The official GitHub `PROJECT_CHECKPOINT.md` remains the project recovery authority; `WORK_RESULT.md` is only the task and quota handoff, never a replacement checkpoint.

## DR-04 stop evidence and execution boundary

Work reported candidate ten-rule evaluator with 26 focused passed; 83 relevant passed and 5 skipped; full suite 1,068 passed, 5 skipped, 4 unrelated pre-existing failures; independent acceptance failed twice because DR-02 lacks accepted request/prior-result/XML digest/result identity. Candidate code was NOT pushed. Diagnostic commit `b45170801ac55524a0e228022471c7c2ebe95d9c` was reported. Treat this as reported evidence and verify against GitHub checkpoint before modifying code. DR-04 stays OPEN/HUMAN_REQUIRED, DR-05 BLOCKED. This dispatch is ONLY the Owner-authorized bounded DR-02 lineage re-acceptance; do not resume DR-04 without actual independent DR-02 acceptance and a separate authorized execution gate.
