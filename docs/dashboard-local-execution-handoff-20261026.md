# Dashboard local handoff (2026-10-26)

Status: documentation only. No operational acceptance.

The live port 8766 server starts from worktree ai-agent-lab-c09-continuation, using agent_lab.ui_product_app:app. GET /health reports read-only-dashboard and source unavailable. GET /api/cases and /api/drive/status return 404; these are not confirmed application routes.

Existing ui_product_app.py supports injected ProductionRuntime; default app has no source. Existing ui_dashboard.py has POST /cases/create, requiring authorized callback. Existing production_runtime.py blocks case_creation and drive_mutation pending operational acceptance. Reuse existing case_creation_workflow, case_persistence, google_drive_auth and google_drive_provisioning. Never introduce a second registry, database, dispatcher or Google Drive Desktop dependency.

F06 read-only runtime composition and F07 readiness preparation are independently accepted within bounded scopes. The missing operational service client/dispatcher and SCM composition remain the next F07 prerequisite. OI-0002, C09 finality, OI-0003 protected registration and provider gates remain open. No active OPEN_ITEMS row closes.

The protected root was provisioned, but production recovery identity verification remains unaccepted. Do not change account passwords or ACLs to continue unrelated UI work.

Next: integrate the existing-role service client and SCM host through governed review, then configure the accepted production runtime and authorized real-case callback. Bind direct Google Drive API only with exact scope and accepted provider/Human Gates. Test real case creation, restart durability and Drive status separately. No protected or Drive writes were performed in this discovery.
