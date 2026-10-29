# A-02:UI-03 — Increment 1: Document Registry

Date: 2026-10-29. Authority: Owner execution attachment a843d914-08ac-4324-b323-52df41608899. Branch: c09-witness-hardening. Starting HEAD: 7d7f3068850b77d0e7e5ecb8591b8e45e46e56a2.

Target: `A-02:UI-03 / DOCUMENT_REGISTRY_IMPLEMENTED / TESTED`, bounded to backend registry correctness. Full UI-03, analysis acceptance, movement, financial impact, restore workflow and Owner live UI acceptance are not implied.

Final verified status: `A-02:UI-03 / DOCUMENT_REGISTRY_IMPLEMENTED / TESTED`.

## Implementation

- LocalCaseHost.list_case_documents remains the pending Documents projection consumed by existing upload/preview/readiness routes. list_case_document_registry separately observes Documents, Tax_Categories (including category subfolders) and optional Deleted_Documents within the exact owner/case/year/root. It never creates a folder or moves a file. Missing/duplicate required folders, incorrect parents, repeated pages, duplicate file identities, malformed metadata and partial listings fail before reconciliation.
- The existing case_document_index retains the same case/Drive-file primary key. Metadata observations distinguish PENDING, ACTIVE_ANALYZED and DELETED_ANALYZED. Existing ACTIVE/UNRESOLVED source-status meanings distinguish physical availability from logical activity; unknown or absent files are retained with UNRESOLVED source status. A folder listing's absence is never a deletion receipt.
- Every material observation preserves prior metadata/state in append-only history_json. Unchanged observations do not append duplicate history. Per-row registry_mac and existing case_audit DOCUMENT_REGISTRY_UPDATED commitments detect row/history rewriting and silent record deletion. The existing canonical key, database, audit and anchor are reused; no parallel authority/store is introduced.
- These labels are verified storage/lifecycle observations, not an extraction result, legal classification or new acceptance grant. Existing extraction evidence is not modified or reinterpreted. Content extraction, content-version invalidation and Kernel-governed classification remain later increments.
- Only explicit, separately verified unanalyzed-document Trash success can remove its live index entry. Its existing audit chain retains PENDING_DOCUMENT_TRASHED evidence. An analyzed/inactive or historically analyzed document cannot be routed through pending Trash, even if an external actor returns it to Documents. No analyzed deletion/restoration operation is implemented.

## Minimal SQLite migration and compatibility

The document index was a lazily created, seven-column component, separate from core schema-v3 versioning. Its additive migration runs inside the same BEGIN IMMEDIATE reconciliation transaction. It adds only registry_state, source_status, parent_id, history_json and registry_mac; legacy rows start UNRESOLVED, empty-parent/history/MAC until verified scoped observation. Existing case keys, year, Drive IDs and old metadata remain. Global SQLite user_version stays3; no additional metadata table beyond the existing case_document_index, database, key, scheduler or orchestrator is introduced. A failed migration/update rolls back.

Whole-case snapshot restore accepts the original seven-column document rows and current extended rows. The current pending-row history survives legitimate whole-case Drive-ID remapping, with a recorded reference-remap observation and unresolved state until actual scoped readback. This is compatibility with the already accepted whole-case backup path, not a new analyzed-document Restore workflow. Backup preflight refuses analyzed/inactive/unresolved records that its pending-only snapshot engine cannot fully represent. Empty-case preflight and its durable deletion method reject retained/unresolved registry rows before treating an empty Documents listing as deletion eligibility. Existing pending-only cases retain the normal flow; complex lifecycle backup/deletion support is explicitly deferred.

## Required acceptance matrix

| Criterion | Executed evidence in tests/unit/test_case_document_registry.py | Result |
| --- | --- | --- |
| T1 registry preservation | Documents→Tax_Categories simulated move; original row and history prefix retained | PASS |
| T2 pending inventory | Categorized file absent from pending files/count, present in case registry | PASS |
| T3 inactive documents | Deleted_Documents file retained, excluded from active/pending projections | PASS |
| T4 identity stability | Same Drive ID, case, year and historical observations across transitions | PASS |
| T5 scope enforcement | Wrong owner/year and cross-case file reassignment rejected atomically | PASS |
| T6 existing functionality | Mock-backed actual LocalCaseHost upload/inventory/preview/pending Trash; legacy/current whole-case snapshot rollback compatibility | PASS |
| T7 fail closed | Unknown location preserved; duplicate folder/file, wrong parent, partial page, pending-only sync, invalid size, tampering, row deletion and injected audit failure rejected without silent loss | PASS |

Additional checks exercise additive legacy migration, restart persistence, idempotent unchanged reads, analyzed-Trash denial, incomplete-backup/empty-case guards, and audit/metadata rollback.

Tests load the actual LocalCaseHost module with only its final module-level ASGI startup assignment excluded. They instantiate the class without its operational constructor, bind temporary canonical SQLite and fake Drive/credentials/downloads, and never open the Owner's database or OAuth. No real document, case, Drive metadata or tax data is read/written by this verification. No actual app restart or live migration is claimed.

## Verification history

- Initial focused run:1 failed/17 passed; the wrong-year test expected CasePersistenceError, while the existing canonical boundary correctly returns PermissionError. Corrected the assertion without changing authorization.
- Focused and empty-case run then22 passed. The malformed-size case was subsequently added and must be included in final verification below.
- Initial relevant regression:1 failed/89 passed. The untouched provisioning fixture modeled an unrecorded Tax_Years ancestor without its metadata; that ancestor has an existing explicit adoption exception. The negative fixture now records the verified ancestor and tests an unrecorded child; it still requires rejection and zero creates. Production provisioning code is unchanged.
- Combined focused/related run before the final malformed-size test:112 passed, exit0.
- Initial final combined run:1 failed/130 passed; the sole failure found three existing governing/acceptance documents missing from the index. Those three directly relevant references were registered; no contract or earlier acceptance was changed.
- Final verification:131 passed in20.08s, exit0. This comprises20 new registry tests,3 existing empty-case checks,90 related persistence/provisioning/creation/backup/document-identity tests and18 documentation checks. No test is skipped, deselected or credited without execution in this final command.

Exact final command, with PYTHONPATH=src:

```powershell
C:\Users\rezag\ai-agent-lab\.venv\Scripts\python.exe -m pytest tests/unit/test_case_document_registry.py tests/unit/test_empty_case_preflight.py tests/unit/test_case_persistence.py tests/unit/test_case_persistence_f03.py tests/unit/test_storage_provisioning.py tests/unit/test_google_drive_provisioning.py tests/unit/test_case_creation_workflow.py tests/unit/test_case_backup_contract.py tests/unit/test_case_number_reservation_policy.py tests/unit/test_document_identity.py tests/unit/test_document_identity_persistence.py tests/unit/test_document_inventory.py tests/unit/test_documentation_index.py -q --tb=short
```

The legacy test_local_case_host.py is not imported: its module-level operational startup and obsolete Desktop-oriented setup are unsuitable for this no-live-data task. The new focused tests exercise the actual host methods safely without that startup. No broad/full-suite or live acceptance is claimed. Final diff hygiene passes.

## Changed files

- src/agent_lab/case_document_registry.py — same-table state/history, additive migration, validation, audit and legacy snapshot remapping.
- src/agent_lab/local_case_host.py — full registry versus pending projection; safe existing pending-operation compatibility.
- src/agent_lab/case_backup_restore.py — old/new index column compatibility; no analyzed restore workflow.
- src/agent_lab/case_backup_preflight.py — reject incomplete lifecycle snapshots.
- src/agent_lab/empty_case_preflight.py and case_persistence.py — retained/unknown rows cannot be mistaken for empty-case deletion eligibility.
- tests/unit/test_case_document_registry.py — T1–T7 and compatibility/failure/restart evidence.
- tests/unit/test_empty_case_preflight.py and test_google_drive_provisioning.py — necessary fixture compatibility; provisioning production code remains unchanged.
- This report, docs/README.md, PROJECT_CHECKPOINT.md, OPEN_ITEMS.md, CURRENT_STATE.md and ROADMAP.md — governed evidence/status/index updates. The three pre-existing governing/acceptance documents were indexed, not changed.

## Delivery and remaining scope

The pre-existing ui_dashboard.py, dashboard.css, dashboard.html and untracked case_confirmation.js changes are excluded from this increment's commits. No Analysis UI changes, Gemini, tax computation, Drive mutation workflow, analyzed restore/delete, Human Gate change or ELSTER activation occurred. No independent or Owner live acceptance is claimed.

Surviving legacy records are preserved. Records already erased by older destructive reconciliation cannot be reconstructed from nothing; this increment does not fabricate their history or backfill real cases. Live schema migration, deployment and real-case observation were not performed.

Recommended next increment (not executed): separately authorized, Kernel-governed document-movement intent/readback/reconciliation with real scope/version guards and lazy holding-folder handling. Preserve the explicit separate acceptance gates in the Owner plan.

Ending authenticated quota handoff2026-10-29T12:17:11Z via signed-in Codex app: five-hour80% remaining/reset2026-10-29T16:47:24Z, weekly93%/reset2026-11-04T12:52:37Z. Initial usage was read concurrently with opening the attachment before its no-initial-check instruction was known; this was disclosed, not used to defer work, and no repeat initial check was performed. No next increment is dispatched.
