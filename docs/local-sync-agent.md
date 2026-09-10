# Local Sync Agent

**Status:** Architecture human-accepted 2026-09-10; implementation pending technical verification and stage acceptance.

## Purpose

Keep the authoritative GitHub branch and the Windows checkout at `C:\Users\rezag\ai-agent-lab` near-real-time synchronized without routine user intervention.

GitHub remains the durable source of truth. The local checkout is an execution workspace, not an independent authority.

## One-shot model

The synchronization engine performs one bounded reconciliation per invocation. Windows Task Scheduler invokes it every minute. This avoids a long-lived daemon and makes restart/recovery simple.

The synchronization decision is deterministic:

1. Verify that the configured path is the exact Git repository root.
2. Verify that HEAD is attached to the configured branch.
3. Refuse to proceed when staged or unstaged changes exist.
4. Fetch only the configured remote/branch.
5. Compare local HEAD, remote HEAD, and their merge base.
6. If equal, report `UP_TO_DATE`.
7. If local is strictly behind, execute only `git merge --ff-only origin/<branch>`.
8. If local is strictly ahead and branch is not `main`, push the already committed HEAD normally.
9. If histories diverge, fail closed without merge/rebase/reset/stash/force-push.
10. `main` is never auto-pushed.

## Explicit non-capabilities

The agent does not:

- create commits;
- stage files;
- stash local changes;
- rebase;
- reset;
- force-push;
- change branches;
- merge divergent histories;
- weaken protected-main rules;
- store credentials or tokens in the repository;
- inspect or synchronize ignored runtime data, OAuth credentials, tax documents, SQLite approval authority, or private Drive artifacts.

This means a developer or tool must first create an intentional Git commit before Local Sync can propagate an ahead local branch. Uncommitted work is treated as an unresolved human/tool workspace and blocks synchronization rather than being silently published.

## Failure behavior

The following states are terminal for the current one-shot run and cause no history rewrite:

- dirty working tree;
- wrong branch or detached HEAD;
- missing/unresolvable remote branch;
- divergent history;
- invalid repository root;
- failed Git command;
- attempt to auto-push `main`.

The next scheduled run retries only naturally recoverable conditions. It never repairs divergence automatically.

## Concurrency

Windows Task Scheduler is configured with `IgnoreNew` so overlapping scheduled instances are not launched. The CLI also places a lock under `.git/local-sync-agent.lock`; an obviously stale lock older than ten minutes is removed on the next run to recover from process crashes.

## Installation

The one-time bootstrap is:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_local_sync_task.ps1
```

Defaults:

- repository: `C:\Users\rezag\ai-agent-lab`
- branch: `d021-agent-case-provisioning`
- task name: `AI-Tax-Agent Local Sync`
- cadence: once per minute

The installer resolves the existing `python` executable on the Windows host and registers a bounded scheduled task. It does not install or write GitHub credentials. Existing Git authentication remains responsible for fetch/push authorization.

## Security boundary

Local Sync is development infrastructure only. It does not authorize physical migration, durable approval grant/consumption, tax submission, release, merge to `main`, or destructive operations.

The Local Sync Agent inherits the project's D-019 governance: routine synchronization may be automatic, while architecture changes, stage acceptance, protected-main merge/release, consequential runtime actions, and Human Gates remain separately controlled.

## Acceptance criteria

Technical implementation is ready for stage acceptance only when tests prove:

- no-op when local and remote match;
- fast-forward only when local is strictly behind;
- normal push only when a non-main branch is strictly ahead;
- no push for `main`;
- dirty tree blocks before fetch/merge/push;
- branch mismatch blocks;
- divergence blocks without mutation;
- remote-resolution failure blocks;
- no code path invokes commit, reset, rebase, stash, checkout/switch, or force-push.

Local installation and a live synchronization smoke test occur only after implementation verification and human stage acceptance.
