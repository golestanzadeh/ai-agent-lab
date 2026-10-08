# Codex dispatch — OWNER-AUTHORIZED bounded DR-02 lineage re-acceptance (2026-10-08)

OWNER AUTHORIZATION: On 2026-10-08, the Owner explicitly approved the second option in `docs/dr02-lineage-reacceptance-plan-20261008.md`: bounded DR-02 lineage re-acceptance. This is NOT permission to invent or self-accept canonical identities, change tax amounts, bypass independent acceptance, transmit externally, or begin DR-05.

START: Read authoritative GitHub `PROJECT_CHECKPOINT.md` on branch `d022-supervisor-loop-design`, `AGENTS.md`, `docs/codex-agent-workflow.md`, `docs/dr02-lineage-reacceptance-plan-20261008.md`, DR-02 and DR-04 acceptance records and directly relevant code/tests. The local checkpoint was intentionally deleted; do NOT recreate it. Preserve all existing uncommitted/untracked changes.

CAPACITY: Starting quota is exactly 23% five-hour remaining and 86% weekly remaining, supplied by Owner. Before work, estimate the full task and apply the Limit Guard to these supplied values; do NOT make an initial quota measurement. After work, measure actual ending quota and persist it in BRIDGE_STATE.json as specified below.

MISSION (only bounded DR-02 identity gate):
1. Inventory exact, authorized CASE-001/2024 accepted DR-02 case-scoped artifacts and immutable provenance, without broad searches or changing existing accepted data. Record reproducible request reference, prior-result reference, complete canonical XML SHA256, DR-02 result artifact identity and run scope, or explicitly mark each unrecoverable.
2. If accepted identities cannot be recovered, construct a proposed re-acceptance candidate from authorized original inputs, with reproducible deterministic replay and source/XSD checks. Clearly distinguish NEW proposed identity from previously accepted identity; no retroactive claim.
3. Test case/run/year/source binding and negative substitution of request, prior result, unrelated non-VOR XML and XML digest. Do not promote a candidate without independent review.
4. Prepare independent DR-02 lineage acceptance dossier with evidence, expected identity pins, reproducibility and exact Human Gate. Request independent acceptance under existing project mechanism; never self-certify.
5. On actual independent PASS only, durably record newly accepted identities and checkpoint; otherwise mark HUMAN_REQUIRED and exact continuation. Do not resume DR-04 until DR-02 identity is accepted and capacity permits.
6. Keep GitHub `PROJECT_CHECKPOINT.md` authoritative and update in same governed change set. Preserve non-transmitting boundary. Do not change tax calculations or the 32.00/134.00 approved successor. Do not merge, release, submit, sign, use certificates, run Wake, or touch DR-05.

CONTINUOUS EXECUTION: solve ordinary failures, run focused tests, document, and stop only for real authority/capacity blocker. Return concise status, live quota, artifacts, tests, commit, and exact next action.


## CAPACITY HANDOFF CONTRACT — OWNER-APPROVED (2026-10-08)

The supervisor supplies the exact **remaining** Codex quota in this prompt. For this FIRST handoff, Owner-provided starting values are **23% remaining in the 300-minute window and 86% remaining in the 10080-minute window**. These are the authoritative handoff inputs for this package, not a fresh Codex measurement. For later prompts, the supervisor reads the previous task's **verified end-of-task** `BRIDGE_STATE.json` snapshot and passes its exact values and timestamp into the new prompt. Do not replace the supplied starting quota with an unnecessary pre-task `account/rateLimits/read` query.

BEFORE starting implementation, estimate this entire bounded task's quota cost conservatively, including tests, repair, evidence, documentation and independent review plus a safety reserve. Apply the existing deterministic Limit Guard to the supplied values, with any established age/reset rules. If the supplied values are stale, their reset window cannot be determined, the guard rejects the package, or the estimate exceeds available headroom, STOP before implementation with a precise capacity-blocked report; request updated capacity evidence rather than guessing. Do not pretend the supplied starting values are a live measurement.

IF the package is admitted, execute it through completion or a real Human Gate. At the END, query the actual authenticated Codex rate limits ONCE via the existing reader, record exact 300-minute and 10080-minute used/remaining percentages, reset timestamps, measured_at, and source into the existing authoritative `BRIDGE_STATE.json` using its established schema/writer, preserving unrelated fields. Read back and verify the persisted snapshot. If a package stops early, still record the ending quota when possible. If the measurement/write fails, report that the next task lacks a verified capacity handoff and fail closed. The supervisor must use this persisted ending snapshot for the NEXT prompt. Do not create duplicate bridge files, invent values or confuse Work quota with Codex quota. No public commit of account-specific usage data unless project policy allows it.
