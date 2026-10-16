# UI25 Kernel read-only projection — 2026-10-16

## Result

Status: **TECHNICAL_PASS / SYNTHETIC_ONLY**.

The isolated functional Dashboard can display existing task state from the existing Deterministic Orchestrator Kernel for an exact synthetic `TEST-*` case, tax year and run. The projection uses a read-only SQLite URI and one consistent read transaction. It verifies the Kernel schema and audit hash chain, requires exactly one registration audit per projected task, and returns only task identity, role, lifecycle status, Kernel kill-switch state and the exact case/year/run binding.

The UI does not create or dispatch Kernel tasks. It does not activate manifests, agents, protected persistence, document processing, credentials, transport, networking or external communication. The functional launcher connects this projection only when `AI_TAX_UI_KERNEL_DB` explicitly identifies an existing Kernel database; production Dashboard construction rejects the test projection.

## Enforced boundaries

- `case_id` and `run_id` are bounded ASCII identifiers; only `TEST-*` case identities are accepted.
- `case_id`, `tax_year` and `run_id` must match the canonical task `case_context` exactly.
- Reuse of one run identity across another case or tax year is rejected.
- Missing run identity, unknown run, malformed context, unknown task state, invalid schema, incomplete task-registration audit or broken audit chain fails closed.
- The integrity check and scoped query share one read transaction to prevent a check/query race.
- Restart reads the same existing Kernel state; the projection creates no state store or registry.
- German LTR and Persian RTL views identify the data as genuine read-only Kernel state and state explicitly that no task was executed.

## Verification

Focused command:

`PYTHONPATH=src python -m pytest tests/unit/test_orchestrator_kernel.py tests/unit/test_ui_functional.py tests/unit/test_ui_dashboard.py -q`

Result: `54 passed`.

Coverage includes exact scope, missing run identity, cross-case access, cross-year mismatch, shared-run ambiguity, truncated registration audit, genuine registered status, read-only file behavior, bilingual rendering and UI/store/Kernel restart.

Relevant UI/Kernel/Case/documentation regression: `109 passed`.

Complete unit regression: `1366 passed, 5 skipped`.

Authenticated ending Codex telemetry at `2026-10-16T19:46:41.466940+00:00`: five-hour `50%` remaining (reset `2026-10-17T00:02:24+00:00`), weekly `90%` remaining (reset `2026-10-23T13:57:50+00:00`). The 15-point five-hour reserve remains intact.

## Acceptance boundary and continuation

This package advances UI25-01 visibility only. It does not satisfy UI25-02 real case creation or UI25-05 task execution, and it grants no OI-0002, C09, protected-persistence or operational IPC acceptance credit.

The next blocker toward the real 2025 end-to-end path is an accepted durable live case/run resolver and protected persistence boundary. Once that prerequisite is independently accepted, the next executable UI package is a read-only live resolver integration; automatic dispatch remains a separate UI25-05 package and is not authorized by this result.
