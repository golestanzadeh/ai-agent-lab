# UI25 — UI-led Product Completion and 2025 End-to-End Acceptance

## Current truth overlay — 2026-10-20

The package table below remains the formal UI25 scope. October execution-order labels `UI25-05` through `UI25-10` were used for smaller bounded synthetic increments and are not full-package acceptance. The independently accepted UI25-05 synthetic worker is not automatic intake dispatch; the Owner-accepted UI25-10 navigation/conflict increment is not UI25-10 Approval/Export. Formal Approval/Export remains disabled and unaccepted.

The bounded bilingual shell (UI25-11) is Owner-accepted, and the seven UI25-10 increment browser scenarios are Owner-accepted for exact synthetic scope. Real case creation, protected documents, provider extraction, tax analysis, calculation, declaration, approval/export and end-to-end 2025 acceptance remain open. Exact operational prerequisite is OI-0002/OI-0003; OI-0002 first requires `OWNER_SELECT_PORTABLE_FRESHNESS_AUTHORITY`, revised ADR independent PASS and the frozen C01–C13 campaign.

Date: 2026-10-09
Status: OWNER-APPROVED PLAN / PARTIALLY EXECUTED (synthetic-only increments)
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

Current bounded evidence: UI25-01 now includes a synthetic-only, strictly read-only projection of genuine existing Kernel case/run/task status. It does not accept the live resolver, protected persistence, automatic dispatch or real 2025 workflow. See `docs/ui25-kernel-read-only-projection-20261016.md`.

UI25-05 bounded evidence: one explicit user action can execute one fixed deterministic synthetic worker through the existing Kernel and display its durable response. The implementation has independent PASS (`93` focused, `148` related regression), but this is not automatic intake dispatch, real-case execution or formal package acceptance. Owner browser evidence is limited to the later seven UI25-10 increment scenarios. See `docs/ui25-05-synthetic-kernel-execution-20261016.md` and `PROJECT_CHECKPOINT.md`.

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

The UI25-00 inventory is complete. Current mandatory dependency action is Owner selection of a portable independently non-rollbackable freshness/restore authority, followed by revised operational ADR independent PASS and OI-0002 C01–C13 implementation/acceptance. Separately authorized synthetic usability work may continue because C09 is not a global stop, but it cannot be promoted to formal real-data package acceptance.
