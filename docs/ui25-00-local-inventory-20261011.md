# UI25-00 — Local UI Inventory (2026-10-11)

Status: TECHNICAL INVENTORY PASS / OWNER UI ACCEPTANCE NOT YET RECORDED
Evidence environment: Owner Windows DESKTOP-HVRUQB7, local checkout C:\Users\rezag\ai-agent-lab, branch d021-agent-case-provisioning, HEAD 41554eb (clean). This is **not** the GitHub active documentation branch oi0002-identity-persistence. No local checkout branch switch, product source change, or production transmission was performed.

## Verified
- Local UI entrypoint: src/agent_lab/ui_app.py; FastAPI + Jinja2/HTMX; launcher scripts/start_local_ui.cmd.
- UI endpoints from FastAPI TestClient: GET /, GET /workspace, GET /health. Root HTTP 200; health HTTP 200 and explicit mode synthetic-local-only.
- UI uses build_synthetic_registry and build_synthetic_* contracts for workspace, documents, workflow, review, decisions, readiness and support. No real persisted case list or production agent dispatch in this entrypoint.
- Focused local tests: PYTHONPATH=src .venv\Scripts\python.exe -m pytest tests\unit\test_ui_app.py tests\unit\test_local_ui_launcher.py -q --disable-warnings --maxfail=1 => 17 passed, 1 warning (2026-10-11). Initial invocation without PYTHONPATH failed at test collection with ModuleNotFoundError; corrected invocation succeeded. No test evidence for real-case flows is claimed.
- HTTP verification used in-process TestClient; no physical browser or phone Owner test and no external network transmission.
- UI modules: ui_app.py, ui_state_contract.py, ui_workflow_contract.py, ui_document_contract.py, ui_review_contract.py, ui_decision_contract.py, ui_submission_readiness_contract.py, ui_support_contract.py, and ui_templates / ui_static.

## Package feasibility after inventory
- UI25-00: technical inventory verified; final Owner UI acceptance remains outstanding.
- UI25-01..02: development can begin but real persisted Dashboard and case creation cannot be marked PASS using the current synthetic app; need a bounded, gated connection to existing Kernel case registry and persistence, with case isolation and restart tests.
- UI25-03: blocked for protected real-data path by existing OI-0002/0003/0006/0007 acceptance dependencies; synthetic contract work only until released.
- UI25-04..09: synthetic tests and non-sensitive code work are possible; actual protected document ingestion/analysis and provider egress require applicable security and Gemini retention verification. No complete-package PASS inferred.
- UI25-10: synthetic readiness tests possible; no ELSTER transmission without two independent Owner approvals.
- UI25-11: existing UI synthetic bilingual/mobile regression can be worked on; real mobile Owner acceptance not yet demonstrated.
- UI25-12: full real 2025 E2E cannot be accepted before real service integrations and applicable gates.

## Next bounded work
Start UI25-01 with a **read-only, case-scoped real-data adapter** to the existing authorized Kernel registry (no synthetic fallback falsely presented as real), only after inspecting the current canonical branch and existing persistence APIs. Preserve local working branch and no protected data in public GitHub. UI25-02 follows real dashboard contract. No separate Kernel or scheduler.

This file is an evidence note, not a Human Gate bypass or formal Owner UI acceptance.
