# DR-02 lineage re-acceptance: supervisor initial evidence audit — 2026-10-08

## Verified inspection
- Authoritative `PROJECT_CHECKPOINT.md` records `HUMAN_REQUIRED / DR02-ACCEPTED-IDENTITY-NOT-RECOVERED` and owner approval of bounded re-acceptance.
- Local worktree `C:\Users\rezag\ai-agent-lab-d022` was inspected; it has an intentionally deleted local checkpoint and three pre-existing untracked scripts/tests. These must be preserved.
- `docs/case001-dr02-acceptance-2024.json` has DR-02 `PASS`, case/year, official source and XSD SHA256, fields and declared values, 12 focused tests, independent source review PASS, and historic refund EUR 133.83. It **does not** contain canonical accepted request reference, prior-result reference, complete XML digest or result identity.
- Existing local `.runtime/work-bridge/BRIDGE_STATE.json` is schema_version 1, last task `DR04-PART1-20261008`, status COMPLETED at `2026-10-08T07:37:05.167Z`. It has no capacity fields. `.runtime/work-bridge/BRIDGE_REPORT_CONTRACT.md` explicitly governs Work report transport and prohibits competing checkpoint or unsafe overwrites.
- Owner's first quota handoff is 23% five-hour remaining, 86% weekly remaining. These are supplied planning inputs, not observed ending telemetry.

## Safe technical decision
1. Preserve existing `BRIDGE_STATE.json` task/status fields. Do not overwrite it with a synthetic capacity reading.
2. Extend the existing bridge contract only with a backward-compatible optional `codex_capacity` object written atomically **after** Codex obtains an actual end-of-task reading. Suggested fields: `measured_at`, `source`, `five_hour.{used_percent,remaining_percent,reset_at}`, `weekly.{used_percent,remaining_percent,reset_at}`, `readback_verified`. Confirm compatibility with the actual writer and any consumers before implementation.
3. Supervisor computes next-task quota and reset arithmetic from the last verified ending snapshot, with uncertainty handling for intervening use.
4. For DR-02, inventory accepted case-scoped request, prior-result, complete XML and result artifact from authoritative existing runtime evidence. Mark absent fields `UNRECOVERED`, never fill them with hashes of newly fabricated artifacts.
5. If old identities cannot be recovered, perform the **owner-authorized** bounded deterministic replay as a NEW re-acceptance candidate, and seek genuinely independent review before marking it accepted. DR-04 remains OPEN; DR-05 BLOCKED.

## Current status
`INITIAL_AUDIT_COMPLETE / REACCEPTANCE_PENDING`. No identity pins have been recovered or independently accepted by this inspection. No Codex dispatched, no private data committed, no ERiC execution or external transmission.
