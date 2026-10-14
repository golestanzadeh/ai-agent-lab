# UI25-01 lifecycle-status localization — 2026-10-14

Status: **BOUNDED TECHNICAL PASS / UI25-01 PARTIAL**

Baseline: `7f031f8497f39ee4baf654e14b24702bbf631f66`

## Admission and scope

Authenticated Codex telemetry reported 79% five-hour and 84% weekly remaining. The existing deterministic `BOUNDED (15/5)` Limit Guard returned `RUN_OPERATION_FITS`, preserving its mandatory reserve. C09 remains OPEN / NOT ACCEPTED but is not a dependency of this read-only presentation correction.

The dashboard accepted seven canonical lifecycle states but rendered their raw English codes in both German and Persian product modes. This was a reproducible bilingual usability defect. The correction:

- maps every allowed state to reviewed German and Persian product text;
- uses the localized value in overview statistics, the case list and scoped tab context;
- retains the exact canonical state in a diagnostic `data-status-code` attribute;
- changes no source authority, case identity, persistence or lifecycle transition;
- keeps approval and ELSTER transmission inert.

## Verification

- Focused dashboard suite: `17 passed`, exit 0.
- Relevant UI and local-launcher regression: `91 passed`, exit 0.
- A proposed case-selection tab-persistence assertion failed because the case list exists only on the overview page. That unsupported scope was removed rather than changing product behavior without a valid defect.
- An initial relevant-suite command referenced a nonexistent launcher test filename and executed no tests. The corrected command used `test_local_ui_launcher.py` and produced the recorded `91 passed` result.

## Remaining boundary

This increment is not full UI25-01 acceptance. Real persisted case status still requires the approved durable resolver and its independent persistence/IPC prerequisites. No real taxpayer data, protected persistence, Kernel transaction, external service or submission path was activated.
