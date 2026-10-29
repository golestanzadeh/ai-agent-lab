# A-02:UI-03 — Owner-approved incremental analysis and document lifecycle
Date: 2026-10-29
Status: OWNER_APPROVED REQUIREMENTS / IMPLEMENTATION PLANNED / NOT TECHNICALLY ACCEPTED
Authority: Owner instructions in conversation, following A-02:UI-02 acceptance commit 3454f4d.

## Non-negotiable boundaries
Deterministic Orchestrator Kernel remains the sole execution authority. Use existing Gemini extraction, CSV parser, specialist agents, Google Drive API, canonical SQLite, case/year/owner scoping, permission gates, evidence lineage and audit. Do not introduce Drive Desktop, parallel orchestration, another database, implicit external submission or fabricated monetary effects. Preserve preexisting working-tree changes. This document authorizes bounded engineering, NOT real-case destructive operations or bypass of Human Gates.

## Document states and storage
- Documents = active incoming documents awaiting accepted extraction/classification. The top Analysis count and format breakdown are specifically the current Documents inventory.
- Tax_Categories = active analyzed/classified documents, moved (not copied) from Documents only after successful extraction, validation and authorized specialist decision, or Kernel decision only where existing authority permits. An uncertain classification requires review. Do not invent legal conclusions from Gemini candidate tax_category.
- Deleted_Documents = lazily provisioned, case-scoped recoverable holding folder for analyzed documents after approved deletion. Not Google Drive Trash. The bottom Analysis section lists these items with prior category, deletion date, recorded financial impact or unknown-impact override, and Restore action.
- Restore moves the original file ID from Deleted_Documents back to Documents, removes it from the current deleted-items display, and sets operational state to pending reanalysis; never automatically returns it to Tax_Categories. Historical extraction/deletion/restore audit and evidence are retained but not treated as current accepted extraction.
- Unanalyzed documents may be moved to Google Drive Trash after the existing scoped confirmation. Analyzed documents MUST NOT go to Drive Trash via the normal document delete action.
- The Analysis page has three distinct views: pending Documents (formats/counts), active analyzed Tax_Categories (category/counts), deleted analyzed Deleted_Documents (items/restore). Do not confuse physical folder inventory with immutable case-wide registry.

## Incremental extraction and lineage
- Reconcile authoritative case-wide document registry across all three folders, not merely the Documents listing; preserve file ID, original scope, parent, content digest SHA-256, version, extraction contract/model version, accepted result, dependency edges and audit history.
- NEW and CHANGED content, FAILED/INCOMPLETE attempts, restored pending documents, and explicit invalidation require processing; accepted UNCHANGED documents must not be resent to Gemini solely because their folder changed.
- A new 21st document after 20 accepted documents triggers extraction of only that new document; invalidate/recompute only provably affected downstream results, retaining prior immutable run evidence. The complete specialist reanalysis decision remains Kernel-governed.
- A restored document must pass the extraction/acceptance lifecycle again even if historical extraction bytes are unchanged.
- A failed classification/move leaves a durable recoverable pending state, not a false completed count. Drive move and SQLite update are not atomic: journal, idempotency, independent Drive readback and restart reconciliation are required.

## Financial-impact-gated deletion of analyzed documents
- Before mutation, Kernel calculates the tax result with and without the selected document, considering dependencies, duplicates, deductions and other interactions. Show current result, projected result and exact delta ONLY when a validated deterministic comparison is available. A document's face value is not its tax refund effect.
- If impact cannot be computed, ordinary delete is blocked but an explicit separate Owner-authorized override permits deletion despite unknown impact; never fabricate a number. This override does not waive owner/case scope, version, finality, audit or retention protections.
- Both paths bind Owner confirmation to exact document ID, case/year, content digest, run/result version, financial preview or unknown status and expiry; reject stale state and replay. No file move before confirmation.
- On confirmed analyzed deletion, move file to Deleted_Documents, retain audit and invalidate affected results. If no valid recomputation is available mark RECALCULATION_REQUIRED, distinguish historical amount from valid current result, and block submission until valid recalculation and required approvals.
- Restore is a distinct audited authorization with scope/readback/recovery guards. Deleted list is a current-state view; restored items disappear from it while historical audit persists.

## Empty-case exception and existing case deletion contract
- If Documents count=0 AND Tax_Categories active count=0, the case has zero active tax documents even if Deleted_Documents contains 20 items. The existing empty-case deletion eligibility checks then apply, including protected/final case prohibition, active identity, backup reservations and other dependencies. Zero active documents alone never authorizes case deletion.
- Before full case deletion, define and test treatment of Deleted_Documents as part of the case deletion/backup lifecycle; do not leave orphan folders or silently destroy recoverable evidence. Follow the previously Owner-accepted case deletion/backup contract and deferred finalized-case protection.

## Existing code findings and incompatibilities to fix
- local_case_host.list_case_documents enumerates only Documents and _sync_document_index deletes index rows absent from that folder. This would wrongly forget moved documents; replace the destructive reconciliation with case-wide state-aware registry before enabling moves.
- local_case_host.trash_case_document scopes to Documents and sets trashed=True. Retain this only for proven unanalyzed documents; never route analyzed document IDs through it.
- Analysis readiness endpoint currently counts Documents only, which is correct for pending count; add separate active and deleted counters sourced from verified scoped state.
- case_creation_workflow.REQUIRED_SUBFOLDERS, local case host and empty_case_preflight currently expect six standard folders. Deleted_Documents should be lazily provisioned and existing-case compatibility maintained, with explicit deletion/restore inventory rules.
- Existing case deletion/backup flows are Owner-accepted in docs/case-document-bearing-deletion-owner-acceptance-2026-10-28.md. Do not regress their observed behavior; finalized-case prohibition is deferred and must not be falsely claimed as implemented.

## Ordered implementation increments and acceptance gates
1. Inventory and freeze existing Kernel/extraction/Drive/backup/empty-case contracts and tests; confirm mutation permissions and finality guards. No real-case changes.
2. Add backward-compatible canonical SQLite document lifecycle state/lineage and migration; deterministic case-wide reconciliation, content/version identity and failure recovery. Synthetic tests including move without re-extraction, duplicate name, changed bytes and empty pending folder.
3. Implement Drive API scoped folder resolution, lazy Deleted_Documents creation, atomic-intent/idempotent move/readback/reconcile and restore. Test wrong case, concurrent move, crash and retry. Never trash analyzed documents.
4. Implement Kernel-controlled incremental extraction + classification acceptance and dependency invalidation; reuse Gemini and existing CSV pipeline, enforce permissions and budget. Test 20 accepted + one new -> one new extraction; restore -> pending reanalysis.
5. Implement deterministic financial-impact preview and two distinct Owner confirmations (exact delta / unknown-impact override), stale-preview rejection, audit, RECALCULATION_REQUIRED and submission guard.
6. Add bilingual fa-IR/de-DE mobile-friendly Analysis three-section view, disabled/ready start button, per-document delete/restore and live execution identity; rename old 'شروع تحلیل واقعی' / 'Echte Analyse starten' label as requested in UI-02 acceptance.
7. Regression across empty-case deletion, backup/restore, category folder inventory, file permissions, finality, audit, 2025 synthetic cases and no-ELSTER guard. Independent acceptance, then Owner live UI acceptance before closing UI-03.

## Explicit non-claims
This document does not mean incremental extraction, category moves, deletion preview, restore, full-case cleanup, or real Gemini/Kernel execution has been implemented or tested. No real Drive file, SQLite record, case or tax result is mutated by this documentation change.
