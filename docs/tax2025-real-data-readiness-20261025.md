# Tax year 2025 real-data readiness: verified findings (2026-10-25)

Status: PARTIAL / REAL_CASE_BLOCKED. This document records observations, not acceptance.

## Owner decisions
- Gemini document extraction is pre-approved for this project; do not repeatedly request permission for routine extraction.
- No other AI is permitted as a runtime dependency for 2025 tax processing. Deterministic Kernel owns orchestration, validation, calculations, and case transitions.
- Owner manually reviews UI appearance, tab placement, numbers, extracted documents, and results; successful automated tests are not owner acceptance.
- ELSTER transmission requires explicit, separate owner approval; content accuracy approval is a distinct gate.
- C09 advanced witness hardening is not a prerequisite to non-privileged tax development. HG-01 remains NOT ACCEPTED; do not activate privileged features.

## Database inspection
- The 2025 UI documentation `docs/ui25-2025-canonical-test-backend-20261016.md` confirms an isolated SQLite `FunctionalTestStore`, TEST-* cases and synthetic document metadata only. It explicitly states REAL_CASE_BLOCKED.
- An authoritative live database path and inventory of actual TEST records have NOT been established in this inspection. No rows or databases were deleted. Do not infer that deleting a development database will reset the active application.
- Next: identify the running UI process, resolved SQLite path, schema, TEST row counts, foreign-key relations and backup; delete only confirmed synthetic records transactionally, verify integrity, preserve canonical/protected data.

## Google Drive (verified via connector)
- Root `AI-Tax-Agent`: folder ID `1djEP6c4enpCgXquC8CCodLtpjeujdM0z`.
- Existing `Tax_Years`: folder ID `1ZXgMAUxi3gX1_kKle6eFqyEB87ZWMuLV` (previously contained 2024 only).
- CREATED and read back `Tax_Years/2025`: ID `1F2f4qm9ZTeycbnUcobHxUgO5CaBFG9a0`.
- CREATED and read back `Tax_Years/2025/Incoming`: ID `1abPHisHxSng415EddOY8IGN56rKbm5di`.
- CREATED and read back `Tax_Years/2025/Processed`: ID `1Ujv_RNp34kGg6_q8Z-Bf7Ja4yW0oTQIt`.
- No real financial documents moved or uploaded. Runtime path-to-folder binding is not yet verified.

## Runtime AI dependency scan
- Source references found: `src/agent_lab/gemini_document_extraction.py` (`gemini-3.8-flash`) and `src/agent_lab/tax_agent_runtime.py` (Gemini model default). This is a partial source scan, not proof of exclusive runtime dependency.
- Next: trace actual 2025 execution entrypoint, provider/worker dispatch and environment/configuration; block non-Gemini AI providers in real-data runtime, while retaining deterministic non-AI workers.

## Bank CSV
- Existing ingestion function: `src/agent_lab/structured_financial.py:ingest_sparkasse_csv` (line 97 at inspection).
- This confirms source-level CSV support, not end-to-end integration or owner acceptance. Verify encoding, delimiter, German decimal/date handling, duplicates, overlapping statements, provenance, privacy, and correct tax classification before live import.

## Admission and next gate
- REAL_CASE_BLOCKED until database location/cleanup, real-case persistence, Drive binding, CSV ingestion and Gemini-only runtime isolation are verified.
- Do not upload real documents to the synthetic-only UI. Do not perform ELSTER submission.
- Follow up with focused tests, owner UI review and full regression before marking ready.
