# Case creation confirmation, active selection, document removal and deletion
Date: 2026-10-27
Status: OWNER DECISIONS DOCUMENTED; IMPLEMENTATION OF NEW LIFECYCLE/DELETE FEATURES NOT AUTHORIZED
Scope: local Windows dashboard, canonical SQLite, direct Google Drive API, deterministic Kernel. No Google Drive Desktop.

## 1. Verified live baseline (read-only evidence)
- 2025 has CASE-2025-0001, CASE-2025-0002, CASE-2025-0003 in canonical SQLite: case_record, case_state, ui_case_authorization, storage_provisioning (three rows in each).
- Each storage_provisioning row is COMPLETE; each case exists in Google Drive under Tax_Years/2025/Cases and has Audit, Calculations, Documents, Evidence, Reports, Tax_Categories subfolders.
- Drive API provisioning journal contains all three case IDs and no pending operation.
- Owner tested and accepted the in-page creation confirmation modal. External JS asset is required by CSP script-src 'self'; do NOT relax CSP or reintroduce inline JS.
- CASE-2025-0001 must be preserved. CASE-2025-0002 and CASE-2025-0003 are candidates for later deletion ONLY after separate owner explanation and explicit authorization. No deletion is authorized by this document.

## 2. Creation confirmation: accepted UI behavior
- On selecting a tax year and requesting a new case, calculate the proposed ID from authoritative state; do not silently create before confirmation.
- For existing cases, modal title remains as currently accepted. Intro text in Persian: «برای سال 2025 قبلاً پرونده‌های زیر وجود دارد:» (year dynamic); list each existing case ID on its own line, then confirmation and cancel buttons. Equivalent correct German copy is required; RTL/LTR and mobile remain supported.
- If no existing case in the year, retain the current first-case confirmation/information behavior pending any explicit later change.
- Cancellation causes zero case creation. Confirmation must revalidate the authorized case list/snapshot and token server-side before creating. Do not trust browser-selected IDs alone. Existing signed confirmation token and fail-closed stale-state check must remain.
- Owner acceptance: modal opens on same dashboard and case IDs appear on separate lines. Current implementation changes are uncommitted at the time of this document; do not claim code acceptance equals independent acceptance.

## 3. Year selector and active case: requested, NOT implemented
- Case tab should display a combo box of tax years derived from authoritative persisted cases; selecting a year lists its cases.
- Explicit case selection sets one active case, displays «CASE-2025-0003 انتخاب و فعال است.» (dynamic ID), and scopes subsequent Documents, Analysis, Issues, Result, Declaration, Approval, Submission and other case operations to it.
- Active case selection is a UX session concept; server/Kernel must authorize and validate case_id, tax year and owner on every operation. Never silently fall back to a different case after deletion or refresh.
- Empty years should disappear from the selector only after authorized cleanup; historical ID reservation metadata, where needed, must remain outside deletable year folders.

## 4. Binding owner deletion rules (supersede earlier three-confirmation proposal)
- FINAL COMPLETION means the ENTIRE tax workflow has ended, not merely document analysis, result calculation or an intermediate approval.
- A fully completed case cannot be deleted under ANY number of confirmations. Its documents cannot be deleted either. Backend and Kernel must enforce; UI disabling is not sufficient. Ambiguous/unverifiable finality => fail closed.
- An unfinished case may add and remove documents assigned to that case. Removing a document must check ownership and invalidate/recompute any dependent analysis/evidence/results before they can be relied on.
- EMPTY CASE means an existing case with ZERO currently assigned tax documents, even if documents had previously been attached and then removed. Initial standard Drive folders and initial SQLite metadata are not tax documents.
- Empty unfinished case: one warning/confirmation; no mandatory backup; case may be deleted and its case number becomes eligible for reuse in the SAME tax year.
- Unfinished case WITH assigned tax documents: one warning/confirmation, then create and verify a restorable backup BEFORE deletion; abort deletion if backup fails. Case number must NEVER be reassigned in that tax year.
- A case that becomes empty after removing all documents follows empty-case deletion rules, including eligibility to reuse its number. This explicitly supersedes the earlier suggestion to permanently reserve all previously used IDs.
- For the last case in a tax year: an additional explicit warning that the year becomes empty and may be removed; remove the year folder ONLY after proving no other cases, protected data or references remain. The backup and permanently reserved ID metadata must NOT be removed with the year.
- Never delete a case or document belonging to a fully completed tax workflow. A submitted case is not automatically considered completed merely because of a submission event; determine finality from authoritative full-workflow state and evidence. Where official records impose additional protection, fail closed.

## 5. Implementation safeguards and unresolved design contracts
- Delete requires read-only inventory of case, document bindings, Drive objects, SQLite records, lineage, tasks, protected/official artifacts, and dependencies. Reject if ownership, finality, data completeness or scope cannot be established.
- For document-bearing cases, backup must be outside the deletion target and restorable: structured SQLite state plus Drive files, manifest/checksums and enough metadata to restore case relationships. Backup retention/location and restoration validation require design approval; do not invent a complex backup service.
- SQLite and Drive cannot share one atomic transaction: use a recoverable, journaled, idempotent state machine and verify each step. A partial deletion must not be presented as success.
- The rule allowing case-number reuse after empty-case deletion creates a potential conflict with existing immutable case_id, audit lineage and historical references. Design an explicit safe generation/identity separation and dependency cleanup; do not simply recycle identifiers in the current registry or rewrite historical audit events. Requires independent architecture/security review before implementation.
- Reserve non-reusable numbers for backed-up document-bearing deleted cases, including after DB recovery; selection of the smallest eligible ID is a PROPOSAL, not an owner-approved allocation policy.
- Document deletion semantics (permanent Drive removal versus detach, cross-case shared objects, historical evidence) require an explicit storage contract; avoid accidental deletion of shared or protected resources.
- Existing Kernel default-deny, independent acceptance, audit requirements, Human Gates and two owner approvals for any external ELSTER transmission remain unchanged.
- The owner requested design discussion before implementation. This documentation does NOT authorize creating delete endpoints, modifying case registry, performing backup/delete, or removing any real data.

## 6. Acceptance checklist for future authorized implementation
- Modal: existing case list one per line, correct year/title, Persian/German, cancellation no writes, stale token rejected, CSP-safe external JS.
- Selector: each persisted year and case shown correctly; explicit active case persists across tabs; all operations bound to authorized active case; no stale data leak.
- Empty unfinished case: single warning, safe deletion and ID reuse only when dependencies cleared.
- Document-bearing unfinished case: single warning, verified restorable backup, safe deletion, permanent ID reservation.
- Remove last document: case becomes empty; dependent analysis invalidated; empty-case rules apply.
- Fully completed case: deletion of case and any document always denied at UI, backend and Kernel.
- Last case of year: extra warning; protected references checked; year folder removal only when safe.
- Failure injection: Drive failure, SQLite failure, backup failure, stale selection, concurrent writes, restart/recovery; no false success.
- No tests may mutate real user cases or live Drive data; use isolated mocks/synthetic fixtures. Independent acceptance required.

## Implementation increment S1 (2026-10-27)
- Authorized staged implementation begins with year/case selection only. Added read-only year picker and case links to the existing Cases tab; selecting a case uses existing validated case_id route and tab links. External JS is used because CSP forbids inline handlers.
- No delete, backup, restore or document mutation endpoints are enabled in S1.
- Focused baseline tests: tests/unit/test_ui_dashboard.py and tests/unit/test_ui_app.py: 33 passed, 1 warning. Owner visual test and independent acceptance PENDING.
- Existing uncommitted source changes for case creation and Drive provisioning were preserved and excluded from this commit.
- S1 currently retains the existing default first-case selection when no case_id is supplied; changing that behavior requires a separate tested scope decision before deletion is enabled.

## Owner-reported 2026 creation loop: runtime investigation (2026-10-27)
- Root cause in case-create confirmation: an empty year yields empty snapshot string; an empty form field may be parsed as None, causing a repeated confirmation. Local backend comparison normalized to (confirmed_cases or '') while still requiring the signed token and current registry snapshot.
- The actual Uvicorn server on 127.0.0.1:8766 was started at 19:39, before the correction was loaded. Restarted server from the existing local source at 127.0.0.1:8766, confirmed startup.
- Read-only dashboard HTTP GET: 200 and four 2025 case options. Nonmutating 2026 confirmation preview: HTTP 200, requires_confirmation=true, empty snapshot, proposed CASE-2026-0001.
- Focused synthetic first-year confirmation regression: PASS (no live case created). Real Owner-confirmed creation remains pending Owner retest; no actual 2026 case created during this investigation.
- Backend source ui_dashboard.py contains other preexisting uncommitted edits; do not bundle them blindly. This log records operational correction, not full independent acceptance.


## Owner acceptance of S1 year/case creation (2026-10-27)
- Owner reports that first-year 2026 confirmation and creation succeeded, followed by a second case for 2026; both confirmation messages correct.
- Live dashboard readback HTTP 200 shows CASE-2025-0001..0004 and CASE-2026-0001..0002 (six total).
- Read-only canonical SQLite verification: both CASE-2026-0001 and CASE-2026-0002 present in ui_case_authorization; storage_provisioning status COMPLETE for both.
- No data mutated during verification. Direct Google Drive folder inspection and independent acceptance are separate, not yet claimed.
- S1 owner UI test: PASS for reported scenario; deletion stages remain disabled.

## Stage 1 closure and Stage 2 activation decision (2026-10-27)
- STAGE_1 CLOSED / OWNER_ACCEPTED: Owner confirmed successful 2026 creation twice with correct confirmation. Independent read-only SQLite readback showed both case IDs authorized and both storage intents COMPLETE. Six cases visible.
- STAGE_2 ACTIVE / IMPLEMENTATION_GATED: Owner authorized implementation of empty-case deletion, not deletion of any specific existing case. No destructive call is authorized by this instruction alone.
- Read-only canonical database check: schema v3, six CREATED cases, zero durable runs, storage provider google_drive and provisioning COMPLETE. This does NOT prove that any case's Drive subtree has no documents.
- Critical implementation gap: SQLiteCasePersistence exposes register/load and a chained integrity audit/anchor, but no authorized delete-case transaction. Direct SQL DELETE would bypass integrity/audit and leave provisioning references and Drive journal; prohibited. GoogleDriveStorageScopeCreator has create-only journal and no verified delete/reconciliation path.
- Before enabling the destructive button: add a bounded, audited deletion transaction to existing persistence; verify exact case/year ownership and empty Drive subtree via Google Drive API; check backup reservations and dependencies; revalidate on confirmation; implement recovery-safe Drive/SQLite cleanup and number reuse. Test with synthetic fixtures first. Until these checks pass, no real deletion endpoint is enabled.
- Preserve the Owner's existing six cases, local uncommitted work and default-deny external transmission.
