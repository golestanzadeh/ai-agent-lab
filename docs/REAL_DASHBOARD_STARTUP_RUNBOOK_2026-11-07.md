# AI-Tax-Agent — Real Dashboard Startup Runbook
Date: 2026-11-07 (Europe/Berlin)
Status: REAL CASE READ + DRIVE INVENTORY VERIFIED; upload/write and restart persistence not retested in this session.
Scope: Windows laptop DESKTOP-HVRUQB7, owner-local UI. Do not confuse this with the unrelated residence/citizenship booklet dashboard or the synthetic UI.

## 1. Authoritative locations
- Active source worktree: `C:\Users\rezag\ai-agent-lab-c09-continuation`
- Git branch at verification: `c09-witness-hardening`
- Source application: `src\agent_lab\local_case_host.py`; ASGI object `app = create_local_case_app()`
- UI composition: `src\agent_lab\ui_dashboard.py`; templates in `src\agent_lab\ui_templates`.
- Canonical local case store (from local_root()): `%LOCALAPPDATA%\AI-Tax-Agent\Cases\cases.sqlite`; DPAPI key `case-integrity.dpapi` in same folder. NEVER replace/recreate these.
- Case scope storage: existing Google Drive API via `google_drive_auth.py`, `google_drive_provisioning.py`, and `LocalCaseHost`.
- Browser: `http://127.0.0.1:8766/?tab=cases&lang=fa-IR`; local loopback only.

## 2. Why the other launchers are WRONG
- `C:\Users\rezag\ai-agent-lab\scripts\start_local_ui.cmd` starts `agent_lab.ui_app:app` on 8000: synthetic-only, no real case.
- `agent_lab.ui_product_app:app` on 8766 is the DEFAULT no-source composition: health `source=unavailable`. This was the mistaken 2026-11-07 launch.
- `scripts\start_dashboard_preview.cmd` on 8765 is explicitly read-only preview, not the operational host.
- Another server on 8768 belongs to a different project (residence/citizenship digital booklet). Do not use it.
- Correct launch module is **`agent_lab.local_case_host:app`**, NOT `agent_lab.ui_product_app:app`.

## 3. Safe startup (PowerShell)
First confirm Windows user session is the same authorized owner and the repository directory exists. Do not run as SYSTEM, a different Windows user, or a service identity: owner SID and DPAPI key are tied to identity.
Do not kill an unknown process just because a port is occupied. Identify it first:
```powershell
Get-NetTCPConnection -LocalPort 8766 -State Listen -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort,OwningProcess
Get-CimInstance Win32_Process -Filter "ProcessId=<PID>" | Select-Object ProcessId,CommandLine
```
Replace <PID> with the actual process ID. If the correct real dashboard is already running, reuse it; if the wrong no-source dashboard is running, stop ONLY that verified process.

Launch in a PowerShell window:
```powershell
Set-Location 'C:\Users\rezag\ai-agent-lab-c09-continuation'
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -m uvicorn agent_lab.local_case_host:app --host 127.0.0.1 --port 8766
```
Keep the terminal/process running. To stop gracefully, use Ctrl+C in that terminal. If Python dependencies are missing, diagnose the existing environment before installing/changing anything. No new launcher, database, registry, or service is required.

## 4. Verification: do not trust HTTP 200 alone
1. `http://127.0.0.1:8766/health` must return HTTP 200 and `"source":"configured"`. Observed 2026-11-07: `{"status":"ok","mode":"read-only-dashboard","source":"configured"}`. The mode label does NOT by itself mean no operational routes: LocalCaseHost explicitly attaches document routes; test them separately.
2. Open `http://127.0.0.1:8766/?tab=cases&lang=fa-IR` and confirm real authorized cases, not placeholder records.
3. Verify actual document inventory without writing:
```powershell
curl.exe -s -G --data-urlencode 'case_id=CASE-2025-0001' --data-urlencode 'tax_year=2025' 'http://127.0.0.1:8766/cases/documents/inventory'
```
2026-11-07 observed: `ready=true`, `registry_complete=true`, correct case/year, SIX real files (including 2025 bank CSV, wage certificate, school, union, and building-cost evidence). Drive inventory was actually read; file IDs are deliberately omitted from this runbook.
4. Do not declare upload operational until a specifically authorized real PDF upload, readback/hash check and restart-readback are performed. Current session performed NO upload or deletion.

## 5. Existing real functionality and boundaries
- `local_case_host.py` has `/cases/documents/inventory`, `/cases/documents/upload`, `/cases/documents/view`, and guarded delete routes.
- Upload uses multipart fields `case_id`, `tax_year`, `document`; max 20 MiB; write endpoints check Origin and Host `http://127.0.0.1:8766` / `127.0.0.1:8766`. Do not bypass browser security checks.
- Case creation uses canonical `LocalCaseHost` / `CaseCreationWorkflow`; local SQLite with DPAPI integrity and direct Google Drive API. No Google Drive Desktop.
- ELSTER/Finanzamt submission remains separately gated by Owner approvals. Launching the dashboard grants no submission authority.
- Do not modify existing Owner-uncommitted UI changes merely to start the server.

## 6. Historical proof and checkpoints
- `PROJECT_CHECKPOINT.md` is canonical project status. At 2026-11-07 top entries record Phase4 partial real-case work, independent checks, and unresolved publication gates.
- `docs\case-2025-0002-final-lifecycle-test.md` (2026-10-28) records real case creation, SQLite + Drive readback, case lifecycle, and actual Dashboard visibility; final evidence commit `11acda0d0611489f370f1772372cec3bbe1fc9d1`, implementation `691663ec01242a1547da0cdc51ec9762aedd2182`.
- `docs\dashboard-local-execution-handoff-20261026.md` describes an EARLIER incomplete no-source app; it is historical and must not override the later 2026-10-28 real-case evidence.
- 2026-11-07 real dashboard discovery: wrong `ui_product_app:app` process on 8766 stopped after verification; correct `local_case_host:app` launched on 8766; /health returned source=configured; actual CASE-2025-0001 document inventory succeeded.
- At documentation time, Git status had pre-existing modifications to `ui_dashboard.py`, `dashboard.css`, `dashboard.html`, and untracked `case_confirmation.js`. They were not changed during recovery.

## 7. Failure diagnosis
- 8766 connection refused: check terminal/process, Python import errors, port ownership; do not switch to 8000/8765/8768.
- Health source=unavailable: wrong ASGI module `ui_product_app:app`; stop verified wrong process, start `local_case_host:app`.
- 403 Origin rejected: use exact browser URL `http://127.0.0.1:8766` (not file://, localhost alias, proxy, or another port).
- Missing case / 409 inventory: verify same Windows owner SID, existing canonical SQLite and DPAPI key, Drive OAuth and case authorization; do not initialize new SQLite or key.
- Google OAuth failure: use existing documented OAuth recovery process, never Drive Desktop or alternate credentials.
- If user sees case but upload fails, record exact route/status and investigate without blind retries or duplicate document creation.

## 8. Next acceptance gate
For CASE-2025-0001: upload the actual spouse 2025 payroll PDF only on explicit authorized execution, verify Drive file identity/size/hash and case inventory, restart same app and verify the document remains available. No fabricated intervening payslips and no financial conclusion from net bank payments alone.

## 9. One-line recovery command
From PowerShell in the authorized Windows session:
`cd C:\Users\rezag\ai-agent-lab-c09-continuation; $env:PYTHONPATH=(Join-Path (Get-Location) 'src'); python -m uvicorn agent_lab.local_case_host:app --host 127.0.0.1 --port 8766`
