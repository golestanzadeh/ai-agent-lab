# UI package 6 — synthetic review and form preview

Status: **IMPLEMENTED / LOCAL SYNTHETIC ONLY**

The immutable presentation contract binds allowlisted findings, the locally
validated E10/2024 XSD and six-rule-subset status, the still-unexecuted official
ERiC engine boundary, a nonnegative explicitly synthetic calculation summary,
and the existing preview identity to one validated synthetic case/run. Case
switching rebuilds the view and cannot retain stale state.

No free-form/private content, official-engine claim, authentication, persistence,
networking, receipt, production action, or transmission capability is present.

Verification: targeted UI-6/app `19 passed`; full regression
`548 passed, 1 skipped`; Python compile and loopback visual/accessibility
inspection passed. The existing TestClient deprecation warning is unchanged.
