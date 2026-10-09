# OI-0002 security remediation — SEC-01 through SEC-04

Date: 2026-10-09  
Authorization: Owner task `OI-0002 Security Remediation | SEC-01 to SEC-04`  
Baseline: `28b0c1571c6026b7bfe996f68b52a30450d1f352`  
Implementation commit: `4c54c5cba6ef6e007012d035d59310e5dd2db3a9`  
Status: `REVIEW_READY / NOT INDEPENDENTLY ACCEPTED / NOT RELEASED`

## Recovery and admission

The clean `oi0002-identity-persistence` worktree and `origin/oi0002-identity-persistence` both resolved to the exact baseline. The authoritative checkpoint, `AGENTS.md`, `OPEN_ITEMS.md`, Agent Execution Protocol and current OI-0002 contracts were inspected. No repository document assigned existing meanings to `SEC-01` through `SEC-04`; this package therefore maps those labels, without inventing prior evidence, to the four adversarial cases expressly required by the Owner: unauthorized restore, unauthorized revocation, unauthorized initialization and truncated audit history.

Authenticated capacity at admission was 54 percent five-hour remaining (reset `2026-10-10T00:35:43Z`) and 55 percent weekly remaining (reset `2026-10-14T16:57:07Z`). The conservative whole-package estimate was 20 five-hour percentage points, leaving 34 percent and preserving the 15-point reserve.

## Independent pre-change reproduction

Each probe ran against the untouched baseline before implementation and exited zero only because the prohibited action was accepted:

| Finding | Baseline observation | Result |
| --- | --- | --- |
| SEC-01 | `OWNER-FORGED` satisfied the restore prefix check; the attacker-selected authorization was registered and consumed. | CONFIRMED |
| SEC-02 | `revoke("C1", actor_id="ATTACKER")` revoked protected evidence without an authorization. | CONFIRMED |
| SEC-03 | direct Kernel initialization created continuity state without task or manifest context. | CONFIRMED |
| SEC-04 | deleting the final audit event still allowed authority reopen and integrity verification. | CONFIRMED |

The reproduction used only temporary synthetic SQLite databases and `CASE-SYNTHETIC`; it performed no network, production, credential or taxpayer-data action.

## Corrections

- **SEC-01:** restore registration now requires an active, unexpired, exactly case/year/run/task-bound Kernel manifest and an exact approved `IDENTITY_RESTORE` Human Gate authority reference. Consumption also requires an active exact Kernel context and the manifest actor must equal the bound recovery operator. Prefix-shaped strings are not authority.
- **SEC-02:** revocation now requires an unused, unexpired, unrevoked `IDENTITY_AUTHORIZATION`, exact actor equality and exact case/year/subject/semantic-key/run/task/manifest scope. The authorization is consumed atomically with revocation, preventing replay.
- **SEC-03:** continuity initialization now uses the same active Kernel context validation as reservation/finalization, emits a Kernel audit event, and rejects reinitialization instead of silently ignoring it.
- **SEC-04:** the evidence audit has a keyed count/head anchor updated in the same SQLite transaction. Tail truncation, full history plus anchor deletion, row rewriting and key mismatch fail closed. Existing non-empty data without an anchor is not silently re-anchored.

No new Orchestrator, checkpoint, evidence database or authority was introduced.

## Verification evidence

| Command | Result | Exit |
| --- | --- | --- |
| `python -m pytest -q tests/unit/test_identity_continuity_authority.py tests/unit/test_identity_evidence_authority.py` | `18 passed` | 0 |
| relevant Kernel/continuity/evidence/persistence/custody/registry suite | `107 passed` | 0 |
| `python -m pytest -q tests/unit` | `1104 passed, 5 skipped` in 236.29s | 0 |

Negative tests explicitly cover unauthorized restore registration and consumption, forged Human Gate references, unauthorized and replayed revocation, unauthorized and repeated initialization, final-event truncation, and complete audit-plus-anchor deletion.

## Boundaries and handoff

This remediation worker does not independently accept the package. No real identity or taxpayer data, production principal, ACL, key, backup, external transmission, merge, release, gate release or OI-0003 execution occurred.

`E-03`, `C-02`, `C-06`, `REMEDIATION-02` and `OI-0003` remain `BLOCKED`. The exact next action is a separate independent read-only security and acceptance review of the published remediation SHA, including fresh adversarial reproduction of SEC-01 through SEC-04. Only later explicit Owner governance may change conditional-gate status.

## Capacity handoff

Authenticated at `2026-10-09T20:18:51.8115017Z`: five-hour 41 percent remaining, reset `2026-10-10T00:35:43Z`; weekly 53 percent remaining, reset `2026-10-14T16:57:07Z`. Source: signed-in Codex rate-limit service. No reset credit was used and the 15-point five-hour reserve remains intact.
