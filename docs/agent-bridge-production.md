# Agent Bridge Production Architecture

Status: **architecture human-accepted 2026-09-10; implementation staged**

## Purpose

Agent Bridge is the development control plane connecting ChatGPT Work, GitHub and Codex. It is not runtime tax authority and cannot replace D-017 or any case/run-scoped authorization.

## Roles

- ChatGPT Work: Architect / Orchestrator / Reviewer. Creates bounded tasks, independently verifies GitHub evidence, and decides PASS, BLOCKED or HUMAN_REQUIRED.
- Codex: Implementation Engineer. Executes only authorized bounded tasks, runs tests, repairs within scope and reports evidence.
- GitHub: durable source of truth and event bridge for tasks, commits, diffs, tests and responses.
- Human: final authority wherever D-019, governance, security or consequential runtime contracts require it.

## Canonical loop

`Work → GitHub → Codex → tests/evidence → GitHub → Work → PASS/next bounded task`

Any required Human Gate terminates automatic continuation: `HUMAN_REQUIRED → STOP → Human`.

## Protocol v1

REQUEST requires: protocol_version, unique task_id, parent_id when applicable, sender, recipient, repository/ref, base_commit, status=REQUEST, bounded task, acceptance criteria, allowed scope, forbidden actions and risk class.

RESPONSE requires matching lineage plus result, response commit when applicable, changed paths, structured tests, authority used and human_required. Controlled outcomes are PASS, BLOCKED and HUMAN_REQUIRED.

Missing/malformed/mismatched repository, ref, base lineage, task identity or authority fails closed. A task_id may not execute/continue twice. Replay and stale responses are rejected. Work verifies GitHub commit/diff/test evidence independently instead of trusting response prose.

## Human Gate matrix

HUMAN_REQUIRED is mandatory for changes to accepted architecture/contracts/governance; stage acceptance where governance requires it; consequential runtime authorization; physical migration or approval consumption; source-document mutation; destructive/irreversible operations; Drive permission/OAuth-scope expansion; security/secret/permission/Human-Gate model changes; and ambiguity about authority.

Agent Bridge HUMAN_REQUIRED never substitutes for D-017 approval.

## Production security model

Least privilege is mandatory. No write-all. Default workflow permissions are empty/read-only and write authority is granted only to the exact bounded job requiring it. Codex writes only to dedicated non-main task branches. Main protection/rules are required before autonomous continuation is production-ready.

Secrets never enter repository files, prompts, comments, artifacts or logs. The PoC AGENT_BRIDGE_USER_TOKEN is not approved for production reuse. PAT is fallback only after identity design proves it unavoidable, and then must be repository-scoped and least privilege.

Third-party actions should be pinned by immutable commit SHA. Avoid secret exposure to forks and unsafe pull_request_target patterns. Use concurrency, timeouts, replay/idempotency controls, base/branch validation, allowed-path restrictions, sanitized logs/artifacts and a fail-closed kill switch.

Bridge payloads must not contain private Drive IDs, OAuth material, credentials, tax-document content/names or private evidence.

## Rollback

Before autonomous continuation, rollback must remain simple: disable Bridge workflows, discard unmerged task branches/PRs, preserve main, revoke/rotate any compromised credential, and return to the D-019 manual controlled workflow. Bridge rollback must never mutate Drive data, runtime approval records or tax documents.

A global fail-closed kill switch must stop dispatch and continuation. HUMAN_REQUIRED remains terminal until explicit human authorization creates/permits a new action.

## Sequential productionization

1. Baseline/canonical cleanup.
2. Architecture/governance acceptance.
3. Protocol contract.
4. Security model.
5. Passive observe-only validation.
6. Bounded Codex execution.
7. GitHub→Work response wake-up and independent review.
8. Controlled low-risk continuation.
9. Deliberate Human Gate stop test.
10. Production acceptance and rollback drill.
11. Resume AI-Tax-Agent development at durable/reloadable approval lifecycle.

Each stage must preserve all existing case isolation, audit, security, approval and human-authority boundaries.
