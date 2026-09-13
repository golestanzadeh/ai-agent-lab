# D-028 — Chief Tax Auditor & Investigation Control

Status: IMPLEMENTED / LIVE-TESTED
Date: 2026-09-13

## Decision
Add `CHIEF_TAX_AUDITOR_AGENT` above the six specialist tax agents.
The Chief owns investigation closure, challenge, re-check directives, and final acceptance.
The deterministic `TaxAgentOrchestrator` remains the execution/guardrail engine.

## Authority
The Chief may read all specialist reports, assign investigation tasks, challenge conclusions,
request re-checks, and accept or reject analytical closure.
It may not submit/sign a return, contact ELSTER/Finanzamt, merge/release code, or mutate evidence.

## Operating doctrine
Default assumption: SOMETHING MAY STILL BE WRONG OR MISSING.
A conclusion is not filing-ready unless the chain is supported:
Fact -> Evidence -> tax-year Law -> Eligibility -> Amount -> Tax Effect -> Form/Line -> Reviewer Challenge.
Ordinary missing evidence remains an Evidence Gap; it is never fabricated.

## Live validation
A real Gemini-backed CASE-001/2024 run executed all six specialists and then the Chief.
The Chief returned `HUMAN_REQUIRED`, deliberately rejecting premature closure.
It preserved the EUR 244.83 working baseline and identified residual investigation targets:
2024 duty roster, Jan-May EVG dues, commute distance, childcare, spouse Minijob tax treatment,
Section 35a payment/labour proof, and school-fee payment/eligibility evidence.

## Test evidence
D-028 targeted runtime tests: 8 passed.
Full regression after implementation: 325 passed, 1 skipped.
One preceding full-suite run had one transient Google Drive provisioning test failure;
the exact failing parametrized test passed 3/3 on immediate isolated rerun, and the complete
suite then passed 325/1. No product-code change was made to hide the transient failure.

## Next phase
Chief-directed Opportunity Discovery begins from the residual suspicion list.
No tax submission or external authority contact is authorized by this decision.
