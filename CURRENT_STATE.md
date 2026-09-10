# Current State

## CURRENT_STAGE

**D-021 complete; Agent Bridge productionization has reached the Step-10 production acceptance gate.**

D-021 implementation remains complete on branch `d021-agent-case-provisioning`. Standard case-storage provisioning is not physical document migration.

Human authorization issued on 2026-09-08 produced an **APPROVED** state in the process-local `ApprovalStore`; it was **not consumed**. Physical migration was **not started** and source documents remain unchanged. The approval is not durable/reloadable after process exit and the private review export is not executable authority.

## LAST_ACCEPTED_STAGE

**D-020 — CASE-001 Approval Context Composition: accepted, integrated, and closed.**

Canonical main remains `ee59dadbc2c7f2433e8291f849fef3048b574a9c` until PR #1 is separately accepted and merged through the protected-main workflow.

## AGENT BRIDGE PRODUCTION MIGRATION — 2026-09-10

1. Baseline/canonical cleanup — **COMPLETE**.
2. Production architecture/governance — **HUMAN ACCEPTED**.
3. Protocol contract — **DEFINED**.
4. Security model — **DEFINED**.
5. Passive/observe-only Bridge — **PASS**.
6. Controlled Codex connection — **PASS**.
7. GitHub → Work owner-identity response path — **PASS**.
8. Controlled low-risk continuation — **PASS**.
9. Full Human Gate test — **PASS; HUMAN_REQUIRED terminal stop proved**.
10. Final verification/rollback hardening — **TECHNICAL VERIFICATION PASS; HUMAN PRODUCTION ACCEPTANCE REQUIRED**.
11. Resume AI-Tax-Agent development at durable/reloadable approval lifecycle — **NOT STARTED**.

## STEP-10 VERIFIED EVIDENCE

- Repository ruleset `22799423` is active and targets exactly `refs/heads/main`.
- Main requires pull-request based changes, blocks non-fast-forward updates, has no bypass actors, and the current user cannot bypass the rule.
- Final passive verification workflow uses pinned checkout/setup-python actions, read-only repository permission, non-persisted checkout credentials, concurrency control and timeout.
- Fail-closed rollback state is `BRIDGE_ENABLED=false`.
- Bounded Codex and controlled continuation jobs now require repository variable `BRIDGE_ENABLED` to equal the exact string `true`; absent/false therefore skips agent execution.
- Rollback drill evidence: Codex workflow run `34507216155` concluded **skipped** with the fail-closed switch not explicitly enabled.
- Step-10 passive verification run `34507007733`: Agent Bridge validator **6 passed**; full suite **252 passed, 1 skipped**.
- Finalized passive workflow run `34507288461`: **success**, including kill-switch check, validator tests and full regression suite.
- Controlled continuation now independently reruns the six validator tests and verifies no tracked worktree changes before emitting PASS.
- All tested Bridge actions are pinned to immutable SHAs.
- Temporary Step-10 probe/checkpoint files were removed after verification.

## PRODUCTION SAFETY BOUNDARY

Agent Bridge remains a **development control plane only**. It is not runtime tax authority.

It does not authorize or perform:
- physical Google Drive migration;
- D-017 approval consumption;
- source-document mutation;
- destructive or irreversible operations;
- autonomous merge/release/stage acceptance;
- direct autonomous write to `main`.

`HUMAN_REQUIRED` is terminal until explicit human authorization permits a new action. Bridge rollback must not touch Drive data, tax documents or runtime approval records.

## NEXT_BOUNDARY

The technical portion of Step 10 is complete. Under D-019 and the proved Step-9 Human Gate, **production stage acceptance is reserved to the human**. No merge/release occurs automatically.

After explicit production acceptance, Step 11 resumes AI-Tax-Agent development at the existing blocker: design and separately accept a **durable/reloadable approval lifecycle architecture** before any physical migration executor or approval consumption is considered.

## VERIFIED_RUNTIME_STATE

- GitHub is the durable source of truth; local Python/Docker is the execution environment; Google Drive holds private case data.
- Multi-case architecture requires mandatory `case_id`, persistent `person_id`/`entity_id`, and explicit `tax_period`.
- Real CASE-001 source inventory: **15 PDFs, 0 folders**.
- Real CASE-001 / 2024 target tree: six standard subfolders provisioned; target Documents verified empty at the recorded D-021 checkpoint.
- Real run: `RUN-00000001`; approval identifier: `APP-00000001`.
- Approval: **APPROVED / NOT CONSUMED / NON-DURABLE**.
- Physical Google Drive migration: **NOT STARTED**.

## ACTIVE_CONSTRAINTS

- Source documents are immutable.
- No broad/unscoped Drive search for case data.
- Every case-data operation requires validated case scope and fails closed on ambiguity.
- Private Drive IDs, OAuth tokens, credentials, client secrets and private document information must never be committed.
- Human authority remains required wherever D-019 or a consequential-action contract requires it.

## AUTHORITATIVE_REFERENCES

- `AGENTS.md`
- `CONSTITUTION.md`
- `DECISIONS.md`
- `ROADMAP.md`
- `docs/agent-bridge-production.md`
- `docs/codex-agent-workflow.md`
- `docs/d-019-controlled-agent-assisted-development-workflow.md`
- `docs/approval-gate.md`
