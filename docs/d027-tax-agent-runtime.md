# D-027 — Tax Agent Runtime

Status: **IMPLEMENTED AND LIVE-VERIFIED**

## Purpose

Execute case-scoped specialist analysis through explicit contracts, validated handoffs, and deterministic stop conditions.

## Runtime

Implemented components:

- `src/agent_lab/tax_agents.py` — role definitions and structured contracts.
- `src/agent_lab/tax_agent_runtime.py` — orchestration, validation, LLM backend, handoffs, and terminal states.
- `scripts/run_tax_agents.py` — executable entry point.
- `tests/unit/test_tax_agent_runtime.py` — runtime and safety coverage.

Specialist chain:

`Evidence -> Tax Law -> Opportunity -> Calculation -> Adversarial Reviewer -> ELSTER/Form`

## Invariants

- `case_id` and `tax_year` are mandatory and validated.
- An Agent receives only its authorized packet and prior handoff reports.
- Structured output is validated before handoff.
- Case/year mismatch and consequential conflict fail closed.
- Ordinary evidence gaps may continue as explicit gaps; they must not be fabricated or prematurely terminate all analysis.
- No Agent may submit to ELSTER/Finanzamt, merge/release, or mutate source evidence.

## Verification

A controlled Gemini-backed CASE-001/2024 run reached all six specialist roles. Runtime status was `PASS`; each role produced structured findings.

Recorded verification:

- targeted runtime suite: **6 passed**;
- full regression: **323 passed, 1 skipped**.

This proves the runtime and handoff path, not final tax entitlement. Chief supervision and current CASE status are defined in `docs/d028-chief-tax-auditor.md` and `PROJECT_CHECKPOINT.md`.
