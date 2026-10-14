# Codex handoff: C09 nonblocking and project continuation

Date: 2026-10-14
Status: OWNER_AUTHORIZED_POLICY / IMPLEMENTATION_NOT_YET_RUN

## On entry

1. Identify the active local branch and remote SHA; do not overwrite a different checkout or merge unrelated work.
2. Read `PROJECT_CHECKPOINT.md`, `AGENTS.md`, `CURRENT_STATE.md`, `DECISIONS.md`, `docs/decisions/c09-nonblocking-local-development-20261014.md`, `docs/oi-0002-final-closure-matrix-20261012.md`, `docs/ui25-execution-and-acceptance-plan.md` and `docs/codex-agent-workflow.md` as needed.
3. Check the authenticated five-hour and weekly limit guard and mandatory reserve before any execution. Stop safely if admission fails; do not assume stale October 12 percentages are current.
4. Reconcile the new decision into the canonical checkpoint with a small, non-destructive prepend or insertion and verify the exact diff. Do not create a second checkpoint. The ChatGPT GitHub connector's large-file update was blocked; no checkpoint write is claimed.
5. Distinguish the active `d021-agent-case-provisioning` Windows checkout from `oi0002-identity-persistence` GitHub policy branch. Use approved branch integration, no silent branch switch or force push.

## Work admission

C09_NOT_ACCEPTED != PROJECT_EXECUTION_BLOCKED. C09 remains OPEN / NOT ACCEPTED. Independently safe and authorized UI25 synthetic/navigation/localization tests and bounded IPC ADR work may proceed, but no full OI-0002 closure, OI-0003 release, production deployment, protected real-data binding or outbound ELSTER submission is authorized by this policy. All other gates remain.

## First bounded execution

Perform a read-only prerequisite inventory for UI25-00/01/11 and the approved IPC ADR. Select the smallest already-authorized C09-independent task, implement only the proven gap, run focused tests then relevant regression, document actual evidence, and update canonical checkpoint and current state. Never claim owner visual PASS without owner testing. Maintain deterministic Kernel as sole orchestrator and no new DB, scheduler or external service.

## Proof to return

Branch, before/after SHAs, changed paths, exact tests and outcomes, remaining gates, quota admission, next bounded task. Do not claim a task was triggered or Codex was woken merely because this handoff exists in GitHub.
