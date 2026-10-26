# Real case creation reset and Drive Desktop provisioning

Owner-directed reset: permanently deleted ONLY the new 2025/CASE-2025-0001 tree created in the previous trial, including its empty 2025 and Cases parents under the established Tax_Years folder. The 2024 tree and other existing Drive project data remain untouched. Removed the isolated local case SQLite/DPAPI/journal/data root. No tax case was created after reset.

Current launch uses the existing CaseCreationWorkflow and DurableStorageProvisioningAdapter, storing an intent before filesystem writes and the committed scope in SQLite. Google Drive Desktop mounted project root is G:\My Drive\AI-Tax-Agent. Creator refuses an unavailable/mismatched root, existing unjournaled year/case tree, or an uncertain journal. It creates Tax_Years/<year>/Cases/CASE-<year>-<id> and six standard folders.

IMPORTANT: google_drive_desktop scope references are filesystem paths, NOT Google Drive API folder IDs. The mount creates objects for Drive Desktop to synchronize asynchronously; local folder creation is not proof of cloud upload. Owner checks Drive in browser, and supervisor must verify exact remote parent IDs after creation. No ELSTER, Gemini document ingestion, automatic agent execution or full tax workflow has been activated. Current product case lifecycle begins READY with its initial case registry and state; further agents are not yet wired.

Acceptance for owner trial: 1) dashboard empty; 2) owner creates a case once; 3) canonical SQLite verified case, owner, year, assessment, lifecycle and committed storage intent; 4) Drive Desktop journal and tree verified; 5) independently confirm cloud folder and children via Google Drive API/connector, matching names and parent hierarchy. On failure, stop and reconcile; never blindly delete an unknown preexisting folder.

This is an intermediate launch checkpoint, NOT full project acceptance.
