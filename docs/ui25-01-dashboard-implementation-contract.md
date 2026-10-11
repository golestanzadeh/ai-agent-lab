# UI25-01 — Professional real-case dashboard implementation contract

Status: IMPLEMENTATION STARTED / NOT ACCEPTED
Date: 2026-10-11
Owner priority: polished, modern, pleasant, low-friction interface without compromising trustworthy state.

## Verified baseline
The existing `src/agent_lab/ui_app.py` is a loopback-only synthetic FastAPI/Jinja/HTMX UI; `build_synthetic_registry()` seeds fabricated cases. `CaseRegistry` in `src/agent_lab/case_registry.py` is explicitly in-memory and cannot itself prove restart persistence. The current `GET /health` reports `synthetic-local-only`. Do not show synthetic cases as live cases or imply a real CASE-001 record is available merely because the 2024 checkpoint exists.

## Product UX (desktop first, functional mobile)
- Visual hierarchy: clean app shell with calm navigation, concise page heading, year/case selector, one primary next action, and clear case-status badge.
- Dashboard content: overview of authorized cases and years, last verified state, current stage, open questions, documents and next action; cards show only grounded counts, never synthetic placeholders in live mode.
- Explicit source indicator: LIVE VERIFIED, DEMO, or CONNECTION UNAVAILABLE. An unverified source is an honest empty/error state, not a silent demo fallback.
- Progressive disclosure: keep Kernel internals, technical IDs, agent logs and audit trail available in a detail drawer/advanced section, not the primary workspace.
- Responsive layout: desktop grid, mobile single column; Persian RTL and German LTR, keyboard navigation, accessible contrast, reduced motion, no inaccessible icon-only actions.
- Clear disabled states for gated operations, especially submission; no external transfer control active without the existing two Owner approvals.

## Integration sequence
1. Inspect existing authoritative case/evidence/persistence resolver and exact owner-scoped read permission on the current implementation branch. OI-0002's blocked acceptance must not be bypassed.
2. Define read-only DashboardCaseSummary and an adapter that returns only verifiably authorized case metadata. No taxpayer content or opaque private storage IDs in HTML, URLs, logs or public GitHub.
3. Add a distinct live app factory/configuration; preserve `create_app()` synthetic mode and its tests. Do not mutate the Kernel or invent a second registry/database.
4. Implement polished dashboard shell, real empty/blocked/loading states, year/case navigation and source indicator. Render unverified counts as unavailable, not zero.
5. Test case isolation, missing/ambiguous lookup, restart continuity, inaccessible provider, keyboard/mobile behavior, Persian/German presentation and no submission/network side effects.
6. Owner visually verifies actual desktop/mobile dashboard; record evidence and acceptance separately.

## Gate
Until an authoritative case metadata source and permissions are verified, only synthetic-mode UI design and read-only integration contracts may proceed. A passing synthetic UI test is not a live Dashboard PASS. No production real-data mode is enabled by this document.

## Next executable step
Identify the canonical protected case metadata resolver and its read-only authorization contract in the existing Kernel/persistence modules; then implement a narrow adapter and a live/empty-state UI on the active branch with tests. Do not change or merge the Owner's other local worktrees without checking branch/working tree ownership.
