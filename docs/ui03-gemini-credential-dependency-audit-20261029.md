# UI-03 Gemini credential dependency audit — 2026-10-29

## Scope and findings
- Canonical active branch: `c09-witness-hardening`. Existing unrelated dirty UI/host/worker changes were preserved.
- `git grep` of tracked active-branch sources found **no** literal `GOOGLE_API_KEY` dependency. Tracked runtime references use `GEMINI_API_KEY` in `scripts/run_tax_agents.py` and `src/agent_lab/local_case_host.py`; new untracked case worker also uses `GEMINI_API_KEY`.
- The Windows User environment has both `GOOGLE_API_KEY` and `GEMINI_API_KEY`, with different values. No secret values were read into this report.
- The Google GenAI SDK warns when both variables exist and prefers `GOOGLE_API_KEY` by default. Project code explicitly passes `api_key=...` in the relevant paths, but implicit SDK clients elsewhere must be audited before deleting the old credential.
- Real text-only SDK smoke test using the explicit `GEMINI_API_KEY`, model `gemini-3.8-flash` and `store=False`: `completed`, response `CONNECTION_OK`. No private documents were transmitted.
- Explicit `store=False` added to both `src/agent_lab/gemini_document_extraction.py` and `src/agent_lab/tax_agent_runtime.py`.
- Focused tests: 7 passed (`test_document_extraction.py`, `test_ui03_gemini_authority_boundary.py`). This is **not** Kernel-authorized end-to-end acceptance.

## Operational decisions
1. Do not delete or rotate `GOOGLE_API_KEY` automatically. First inventory other non-repository consumers of this User environment variable.
2. Do not expose, print, commit, or log secret values.
3. Restart the local service only after completing provider and Kernel execution gates; inherited process environments may be stale.
4. Preserve the old key until an end-to-end authorized Gemini Worker test has passed.
5. Do not infer that disabling AI Studio logging and `store=False` eliminates Google abuse-monitoring retention.

## Outstanding scope
- Complete review of other local clones, remote branches, ignored/untracked configurations, and unrelated programs consuming `GOOGLE_API_KEY`.
- Kernel-authorized case worker, persistence, dashboard, and restart verification remain pending.
