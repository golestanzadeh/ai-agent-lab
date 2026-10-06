# UI package 10 — synthetic support and recovery diagnostics

Status: **IMPLEMENTED / DISPLAY ONLY**

UI-10 adds an immutable, case/run-bound support contract for the local synthetic
workspace. Its closed allowlist reports that read-only recovery diagnostics exist,
pause/resume/stop controls are not implemented, and no receipt exists because no
transmission occurred.

The panel cannot contain arbitrary text, real data, operational controls, receipts,
or network calls. It does not resume, stop, repair, replay, authenticate, invoke
ERiC, or transmit anything. Any such capability remains a separate Human Gate.

Verification: targeted UI/support `27 passed`; full regression
`653 passed, 1 skipped`. The known upstream Starlette TestClient deprecation
warning remains non-blocking.
