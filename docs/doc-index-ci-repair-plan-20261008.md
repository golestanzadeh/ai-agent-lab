# DOC-INDEX-CI-REPAIR — GitHub documentation-index CI notification remediation

Status: OWNER-PRIORITIZED / TRACKED / NOT EXECUTED
Date: 2026-10-08
Branch: d022-supervisor-loop-design
Authority: PROJECT_CHECKPOINT.md; independent CI and acceptance evidence.
Scope: bounded documentation-index / CI repair; independent of CASE-001 DR-01–DR-04.

## User-visible problem
The Owner reports repeated GitHub Inbox email notifications. Prior discussion identified a failing focused documentation-index test `test_every_focused_document_is_registered_in_the_index`, indicating a possible mismatch between focused documentation files and the authoritative index. This is a **reported diagnosis, not yet a fresh reproduction**. Do not assume that every incoming GitHub email has the same cause without inspecting the actual workflow runs/notifications.

## Six-step bounded repair package
1. **Identify failures**: inspect recent GitHub Actions workflow runs and reproduce the exact focused test; record offending documentation paths and workflow/commit IDs.
2. **Decide index eligibility**: inspect existing documentation-index contract, discover which files are required to be indexed and which are excluded, without weakening governance.
3. **Apply minimal correction**: update the authoritative documentation index or its legitimate file registration only where justified. Do not delete/skip/disable tests or broadly change CI notification settings.
4. **Rerun exact failing test**: verify `test_every_focused_document_is_registered_in_the_index` passes with real command/output evidence.
5. **Run related checks**: execute relevant documentation and CI regression tests and confirm no new breakage; inspect workflow run status where feasible.
6. **Record independent acceptance**: capture before/after CI evidence, changed paths, commit IDs, tests, remaining notification sources and independent review; update this plan and PROJECT_CHECKPOINT.md to PASS only after verification.

## Constraints
- No blanket muting of GitHub emails or hiding red CI as a substitute for fixing failures.
- Do not alter accepted tax data, CASE-001 artifacts, DR gates, Constitution, or unrelated files.
- No private inbox access or deletion/archiving of emails is authorized by this plan.
- Before Codex dispatch, use authenticated live quota and Limit Guard with reserve; bounded scope and Human Gates apply.
- A green focused test alone does not prove every GitHub notification is resolved; compare actual failing workflow history and distinguish unrelated emails.

## Next action
Run a read-only CI/documentation-index diagnosis and estimate a minimal correction; then execute only with valid task authorization and quota. If the original failure is no longer reproducible, record the current evidence and inspect other notification sources rather than forcing unnecessary changes.

## Persistence
Required reference from PROJECT_CHECKPOINT.md and the CASE-001 recovery plan. Keep OPEN until independent acceptance PASS or explicit Owner cancellation. Update both references after material status changes.

## Execution evidence — 2026-10-08

- Step 1: inspected current remote branch and prior DR-04 acceptance evidence. Historical full regression: 1068 passed, 5 skipped, 4 failed; documentation index and three Constitution v2 marker failures were reported. Current GitHub Actions live run listing was not available via connected tools; email-frequency outcome remains unverified.
- Step 2: compared tracked `docs/*.md` against `docs/README.md` on remote HEAD. 98 focused Markdown files vs 96 indexed, with exactly two missing: `case001-dr04-recovery-execution-plan-20261008.md` and `doc-index-ci-repair-plan-20261008.md`; no stale index entries. These two newly added plans were eligible for the index.
- Step 3: registered only those two entries in `docs/README.md`, commit `b850a33c0c598c9ecf8e882bd6c576a189ec4ce4`. No test or CI configuration disabled.
- Step 4: on isolated clean worktree at that commit, `python -m pytest -q tests/unit/test_documentation_index.py` returned **10 passed in 0.41s**.
- Step 5: related test command `PYTHONPATH=src python -m pytest -q tests/unit/test_documentation_index.py tests/unit/test_orchestrator_pilot.py` returned **12 passed, 3 failed**. All three failures arise from `src/agent_lab/orchestrator_pilot.py` requiring the obsolete literal `# Project Constitution v2` in `CONSTITUTION.md`, while Constitution v3 is ratified. This is a **separate governance-validator compatibility defect**, not an index entry defect. First attempt without PYTHONPATH failed test collection (missing agent_lab module); corrected environment produced the authoritative results.
- Step 6: **PARTIAL / NOT ACCEPTED**. Index-specific verification PASS, but live GitHub Actions result and independent acceptance are pending; repeated GitHub notification cessation not established. A separate governed bounded change is needed to reconcile the pilot validator with ratified Constitution v3 without weakening markers or authority. No mailbox accessed and no email settings changed.

**Exact continuation:** inspect authoritative Constitution v3 and pilot governance validator contract, approve and apply a narrow version-aware validator fix, rerun relevant tests, verify GitHub Actions run outcomes, then independent acceptance. Preserve this plan OPEN until confirmed.

## Constitution v3 compatibility fix — 2026-10-08

- Verified ratified `CONSTITUTION.md` starts `# Project Constitution v3` and retains `## Article 10 — Human Gates`.
- Narrowly changed only the obsolete Constitution title marker in `src/agent_lab/orchestrator_pilot.py`; retained Article 10 marker and other allowlisted governance requirements. Commit `b6731183afc634d8eac4a4818b34a827f95a09ed`.
- Isolated clean worktree at that commit: `PYTHONPATH=src python -m pytest -q tests/unit/test_documentation_index.py tests/unit/test_orchestrator_pilot.py` → **15 passed in 3.73s**. All three previously failing pilot tests now PASS.
- Local targeted verification PASS; **live GitHub Actions status, broader regression, and independent acceptance not yet verified**. Do not infer that all notification emails have stopped.
