# Local case creation launch (Windows)

Status: REAL LOCAL CASE CREATION AND REOPEN WORKING. NOT FULL TAX WORKFLOW OPERATIONAL.

Start from the selected worktree:
```powershell
cd C:\Users\rezag\ai-agent-lab-c09-continuation
$env:PYTHONPATH='src'
C:\Users\rezag\ai-agent-lab\.venv\Scripts\python.exe -m uvicorn agent_lab.local_case_host:app --host 127.0.0.1 --port 8766
```

Open http://127.0.0.1:8766/?tab=cases&lang=fa-IR, select tax year and assessment mode, create. The workflow assigns CASE-YYYY-NNNN and persists canonical case/state/owner UI authorization in SQLite. Data root: %LOCALAPPDATA%\AI-Tax-Agent\Cases. Integrity key protected with Windows DPAPI; no cloud-sync SQLite. Documents/Evidence/Tax_Categories/Calculations/Reports/Audit directories are local.

Owner authorization is scoped to the actual interactive Windows access-token SID, not an invented identity. IMPORTANT: this authenticates the local application account ONLY, not the legal identity of the taxpayer. Taxpayer identity and spouse/party evidence must still be enrolled/verified through the tax identity workflow. Do not treat this as proof of AITaxKernel Windows service identity. No protected provider, Gemini upload, ELSTER submission, or Google Drive mutation is enabled.

Creation uses existing CaseCreationWorkflow, CaseRegistry, CaseIdentityAssociationService and SQLiteCasePersistence. It does not activate ProductionRuntime.request_operation or bypass protected operation denial. Duplicate owner+year is rejected. Existing cases reopen from canonical SQLite after restart.

Known limitations: local filesystem case folders are not yet provider-journaled/transactional; failures after folder creation can require manual reconciliation. Audit of creation event is in memory while durable case registration and SQLite audit remain persistent. Case UI sections beyond creation remain read-only. The source app's owner is Windows account SID, not verified taxpayer legal identity. Review and production hardening are pending.
