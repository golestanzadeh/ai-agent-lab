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
