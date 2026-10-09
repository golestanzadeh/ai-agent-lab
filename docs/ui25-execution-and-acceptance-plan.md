# UI25 — UI-led Product Completion and 2025 End-to-End Acceptance

Date: 2026-10-09
Status: OWNER-APPROVED PLAN / NOT EXECUTED
Owner direction: complete and test the existing UI tab by tab, connect it to existing real project components, fix discovered implementation or architectural defects in the same workstream, and then validate a full 2025 case through the UI.
Authorizations: docs/ui25-owner-internal-development-testing-authorization-20261009.md (including its bounded Gemini API exception).

## Working method
For each package: inspect existing implementation -> implement only gaps -> run focused technical and regression tests -> demonstrate in the actual UI -> Owner hands-on test -> fix -> Owner acceptance. Track technical PASS, Owner UI PASS and E2E PASS separately. Never infer one from another. Start 2025 intake once the necessary UI is operational; do not wait for every tab.

No replacement Kernel, scheduler, case registry, database or checkpoint. Reuse the Deterministic Orchestrator Kernel, existing Gemini extraction boundary, specialist/Chief agents, persistence, existing UI and approved project storage. Changes to backend, agent contracts, persistence and workflow are in scope when required by a real product defect, subject to existing security gates.

## Work packages and acceptance evidence
| ID | Scope | Minimum acceptance |
| --- | --- | --- |
| UI25-00 | Existing UI inventory and launch | Run existing UI, identify functional vs synthetic screens, map real service connections and gaps, preserve existing UI-1..UI-19 evidence. |
| UI25-01 | Dashboard/workspace | Show case list and real persisted status, not fabricated status. |
| UI25-02 | Case and tax year | Create/reopen a 2025 case; verify case isolation and restart persistence. |
| UI25-03 | Family and annual carryover | Review effective-dated 2024-to-2025 carryover, changes and explicit annual confirmation, without reopening accepted 2024 facts; honor existing identity/carryover gates. |
| UI25-04 | Documents | Upload documents incrementally at any time; verify hash/identity, duplicates, corrections, metadata, classification and protected storage. |
| UI25-05 | Agent execution | Auto-dispatch ready Kernel tasks on intake, show genuine state and safe pause/retry/restart behavior; no second scheduler. |
| UI25-06 | Issues/questions | Generate precise requests for clarification or evidence, allow replies, unblock dependencies while unrelated tasks continue. |
| UI25-07 | Analysis/evidence | Show provenance, extracted fields, translations, specialist/Chief findings and uncertainty; Gemini performs only authorized initial analysis/translation/interpretation and no tax-use decisions. |
| UI25-08 | Tax calculation | Calculate with versioned inputs; verify deterministic recomputation of affected dependencies after new or contradictory evidence. |
| UI25-09 | Result/declaration | Show versioned results, comparisons, supporting evidence and a non-transmitting declaration preview. |
| UI25-10 | Approval/export | Validate distinct human content approval and separate outbound destination/ELSTER authorization; PDF/export only where separately allowed, never auto-submit. |
| UI25-11 | Bilingual/mobile | Validate German/Persian terminology, RTL/LTR, accessibility, ordinary phone and desktop workflows. |
| UI25-12 | End-to-end acceptance | Owner exercises 2025 case creation -> staged PDF intake -> agent analysis -> questions -> corrections -> late evidence -> final calculation and report through the UI; verify restart, duplicate, privacy and case isolation. |

## Incremental evidence invariant
A tax-year case remains open to later evidence, including after an earlier result is approved. New documents cause scoped re-extraction and dependency-aware versioned reanalysis; preserve accepted historical snapshots, explain changed figures, and require a new Owner approval where affected. Never silently modify a submitted declaration or automatically file an amendment.

## Evidence and issue tracking
- ROADMAP.md is the only roadmap of incomplete UI25 packages.
- CURRENT_STATE.md reports verified actual progress and the next package.
- PROJECT_CHECKPOINT.md records material accepted stages and exact durable continuation point.
- OPEN_ITEMS.md is reserved for genuinely unresolved acceptance blockers/Human Gates; do not copy all UI25 packages there.
- DECISIONS.md records the Owner-approved method and scope.
- Package acceptance requires actual test evidence and Owner signoff; this plan is not proof that a package has passed.

## Boundaries
All project Constitution and existing gates remain in force. No taxpayer data/secrets in public GitHub. No new unapproved external endpoint or publication. Existing registered Gemini API is authorized only for its previously approved initial analysis/translation/interpretation prompt, subject to provider privacy/retention verification for protected real data. ELSTER/ERiC/Finanzamt submission requires both independent Owner approvals. No implicit production, real-data or blocked-gate release.

## Next step
UI25-00: inspect and launch the actual existing UI, inventory each tab and its service bindings, and produce a short evidence-based gap list. No product functionality is asserted complete by this planning document.
