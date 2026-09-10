# Windows Relay

## Status

Architecture human-accepted on 2026-09-10. This document defines the bounded bridge from GitHub project state to the authoritative Windows checkout at `C:\Users\rezag\ai-agent-lab`.

## Purpose

The existing Agent Bridge can coordinate Work, GitHub, GitHub Actions, and Codex, but GitHub-hosted Codex runs execute on ephemeral GitHub runners, not on the user's Windows host. Windows Relay closes only that local-runtime gap.

The relay is intentionally not a general remote shell. It accepts a tiny, versioned, fail-closed request contract and maps an allowlisted task type to hard-coded local behavior.

## Trust and transport model

GitHub remains the durable control-plane source of truth. Relay requests are stored at:

`.github/windows-relay/request.json`

Relay responses are stored at:

`.github/windows-relay/response.json`

The relay reads only the configured `origin/d021-agent-case-provisioning` ref after a safe fetch. A request is executable only when every contract field validates exactly.

The initial protocol is:

```json
{
  "protocol_version": 1,
  "task_id": "LOCAL-SYNC-LIVE-001",
  "task_type": "LOCAL_SYNC_BOOTSTRAP",
  "repository": "golestanzadeh/ai-agent-lab",
  "branch": "d021-agent-case-provisioning",
  "requested_by": "work"
}
```

Unknown fields are rejected. No command, script body, path override, environment payload, credential, Drive identifier, or arbitrary argument is accepted from GitHub.

## Initial allowlisted task

`LOCAL_SYNC_BOOTSTRAP` is the only initially executable task type. Its implementation is fixed locally and may only:

1. validate that execution is on Windows and the exact authoritative repository root;
2. validate the expected branch and clean working tree;
3. reconcile the branch using the existing Local Sync Agent safe semantics;
4. run the targeted Local Sync and Windows Relay tests;
5. install/update the approved `AI-Tax-Agent Local Sync` scheduled task using `scripts/install_local_sync_task.ps1`;
6. run one immediate Local Sync reconciliation smoke test;
7. verify the scheduled task exists;
8. write a bounded response and push only that response commit to the approved non-main branch.

The relay never interprets request text as shell commands.

## Local bootstrap

The relay itself requires one local bootstrap because nothing can execute on a Windows machine before some trusted local process exists there. The bootstrap installs `AI-Tax-Agent Windows Relay` in Windows Task Scheduler with a one-minute cadence. After that point, ordinary relay requests do not depend on the user opening a terminal.

The bootstrap does not install a GitHub self-hosted Actions runner. This is deliberate: attaching an unrestricted self-hosted runner to a public repository would unnecessarily expose the host to workflow-code risk.

## Git safety

The relay:

- operates only on the exact configured repository root and branch;
- never pushes `main`;
- never force-pushes, rebases, resets, stashes, switches branches, or merges divergent history;
- refuses a dirty working tree before task execution;
- stages only `.github/windows-relay/response.json` when publishing a result;
- verifies the staged path before committing;
- uses a normal non-force push;
- leaves divergence or unexpected state blocked for review.

The existing Local Sync Agent remains responsible for ordinary Git reconciliation and still never auto-commits arbitrary local changes.

## Idempotency and replay

Processed task state is stored outside the working tree under `.git/windows-relay-state.json`. A task ID already recorded as terminal is not executed again. `IN_PROGRESS` state fails closed after an interrupted run rather than blindly replaying local operations.

The durable GitHub response also records the task ID and result, allowing Work to verify completion independently.

## Security boundaries

Windows Relay is a development-control component only. It does not:

- access Google Drive or tax-document contents;
- read or mutate OAuth tokens, PAT values, API keys, or private keys;
- create, grant, consume, or bypass Durable Approval authority;
- perform CASE-001 physical migration;
- merge PRs, release software, or modify protected `main`;
- execute arbitrary code supplied in relay requests;
- weaken D-017, D-019, D-020, Agent Bridge Human Gates, or case isolation.

Existing Git authentication on the Windows host is responsible for authenticated fetch/push. Credentials are never placed in repository files or relay output.

## Failure behavior

Any malformed request, unknown protocol field, unknown task type, wrong OS, wrong path, wrong branch, dirty tree, divergence, test failure, installer failure, scheduled-task verification failure, Git failure, replay ambiguity, or response-publication uncertainty returns or records `BLOCKED` and performs no broader recovery action.

The relay never converts uncertainty into PASS.

## Observability

Successful execution produces a compact response containing only non-sensitive facts such as task ID, PASS/BLOCKED, local test result, Local Sync smoke status, and scheduled-task status. Provider IDs, credentials, private paths beyond the already-approved repository root, tax data, and shell output that may contain secrets are excluded.
