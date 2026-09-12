# D-027 — Real Tax Agent Runtime

Status: PAUSED / IMPLEMENTATION CHECKPOINT (2026-09-12)

Purpose: turn the previously conceptual tax-agent roles into executable, case-scoped agents with explicit contracts and controlled handoffs.

Implemented in this checkpoint:
- `src/agent_lab/tax_agents.py`: role definitions and structured contracts.
- `src/agent_lab/tax_agent_runtime.py`: orchestration, validation, LLM backend, handoffs and terminal-state handling.
- `scripts/run_tax_agents.py`: executable pipeline entry point.
- `tests/unit/test_tax_agent_runtime.py`: targeted runtime and safety tests.

Agent chain:
`Evidence -> Tax Law -> Opportunity -> Calculation -> Adversarial Reviewer -> ELSTER/Form`

Runtime invariants:
- `case_id` and `tax_year` are mandatory and validated at the runtime boundary.
- Agents receive only the packet and prior reports handed to them by the orchestrator.
- Structured output is validated before handoff.
- Case/year mismatch fails closed.
- `HUMAN_REQUIRED` is currently terminal.
- No agent may submit to ELSTER/Finanzamt, merge/release, or mutate source evidence.
## Verification at pause

Targeted test command was executed on 2026-09-12:
`python -m pytest tests/unit/test_tax_agent_runtime.py -q`

Result: **5 passed**.

A real Gemini-backed smoke run was also executed against a sanitized CASE-001 / tax-year 2024 packet. The Evidence Agent returned structured findings and evidence gaps. The orchestrator then stopped with `HUMAN_REQUIRED`; downstream agents were not executed.

This is evidence that the LLM backend, structured response parsing, role execution and terminal guard are real. It is **not** evidence that the complete six-agent chain has passed end-to-end.

## Known issue / next action

The first live smoke exposed an orchestration-policy defect: the Evidence Agent can currently escalate ordinary evidence gaps to `HUMAN_REQUIRED`, which prematurely stops the whole chain. Routine missing evidence should normally be carried forward as `EVIDENCE_GAP` / candidate state so Tax Law, Opportunity, Calculation and Reviewer agents can still analyze it without fabricating a claim.

Next session must first narrow the Evidence Agent's stop authority to genuinely consequential ambiguity/conflict, then rerun targeted tests, execute the full six-agent smoke, run the full regression suite, update state/decision documentation, and only then commit/push the checkpoint.

## Legal-version regression learned from Challenge-01

Tax-year/effective-date awareness is mandatory. For VZ 2024, §9a EStG provides the EUR 1,230 Arbeitnehmer-Pauschbetrag when higher Werbungskosten are not proven. The additional treatment of union contributions beside the Pauschbetrag appears in the 2026 version and must not be back-applied to 2024. This must become a dedicated version-awareness regression test.

No filing, ELSTER transmission, Finanzamt contact, main merge or release occurred in this checkpoint.