# DR-02 identity gate: next bounded execution plan — 2026-10-08

Owner-reported remaining capacity: five-hour 23%, weekly 86% (not independently verified via app-server). The 5-hour window is binding. Do not dispatch a long Codex task at this capacity.

Current authoritative state: DR-04 HUMAN_REQUIRED / DR02-ACCEPTED-IDENTITY-NOT-RECOVERED. Independent acceptance failed twice; the ten-rule evaluator is uncommitted. DR-05 BLOCKED. See PROJECT_CHECKPOINT.md and docs/case001-dr04-acceptance-2024.json.

## Gate A: Owner authorization needed

The owner or independent authority must either supply/confirm canonical accepted DR-02 request reference, prior-result reference, complete XML digest and result identity, OR explicitly authorize a bounded DR-02 lineage re-acceptance. This plan does NOT constitute that approval and does not invent identifiers.

## Low-capacity plan

1. At start, inspect latest authoritative GitHub checkpoint, branch, dirty worktree, and read current real Codex 300/10080-minute telemetry; do not use historical snapshots as live authorization. Respect existing Limit Guard.
2. If Gate A not approved, do only read-only source/lineage gap inventory and stop at Human Gate; no candidate promotion.
3. Once authorized, reconstruct DR-02 identities from exact accepted case-scoped artifacts only, with reproducible hashes, case/run/2024 binding, and no unscoped searches. If impossible, produce an independent re-acceptance dossier and request acceptance; do not substitute invented hashes.
4. On independent PASS, freeze DR-02 accepted identity in canonical acceptance record with independent reviewer evidence, then resume DR-04 candidate and add request/prior/non-VOR substitution negative tests.
5. Run focused, relevant, then justified full regression. Resolve four previously observed non-DR04 failures only within approved scope, otherwise record separate blockers.
6. Repeat independent DR-04 acceptance. On PASS update official index, DR-04 acceptance docs, and GitHub PROJECT_CHECKPOINT.md together. Only then unblock DR-05.
7. On limit threshold, checkpoint precise results and stop safely; never bypass the five-hour guard or run unapproved Codex/Work.

No ELSTER/ERiC transmission, signing, release, merge, scheduler, wake, or private data in GitHub.

Execution split: (A) identity re-acceptance only, (B) DR-04 completion after independent PASS and adequate fresh capacity. Never bundle A+B into one 23%-capacity Codex dispatch.
