# UI25 full functional completion — governed stop

Date: 2026-10-11  
Directive: `CODEX EXECUTION ORDER — AI-Tax-Agent UI25 Full Functional Completion`  
Branch: `oi0002-identity-persistence`  
Recovery baseline: `ffa8ae67825f485baf9bf8a429f61eee7bfb2866`  
Status: `BLOCKED_PREREQUISITE / PARTIAL_SAFE_WORK_COMPLETE / NOT ACCEPTED`

## Recovery and inventory

The authorized worktree was clean and synchronized with origin. Authenticated admission capacity was 98 percent five-hour and 100 percent weekly, so quota did not block execution.

The repository has three distinct UI boundaries: `ui_app.py` is explicitly synthetic; the port-8766 `ui_functional_test_app.py` and `ui_functional_test_store.py` are isolated test infrastructure; and `ui_dashboard.py` is the fail-closed product shell but has no approved authoritative persistent case resolver. HTTP 200 responses from workflow tabs are not treated as backend integration proof.

## Safe work completed

- Added selectable `fa-IR` RTL and `de-DE` LTR modes to the product-facing dashboard.
- Preserved language selection across tab navigation and rejected unknown locale values.
- Made Approval/Submission navigation inert and visibly disabled. No outbound action, alternate route, approval control, ERiC/ELSTER call or Finanzamt transmission was added.
- Preserved the fail-closed empty state when no verified case source is connected.
- Added negative tests for unsupported languages and active submission navigation.

Verification: focused UI `32 passed`; relevant UI/documentation `42 passed`; complete unit regression `1114 passed, 5 skipped` in 266.35 seconds. All commands exited 0.

## Unavoidable prerequisite blockers

- `CaseRegistry` and `CaseStateStore` are in-memory; there is no approved durable live case-list/create/reopen resolver.
- OI-0002 is `REVIEW_READY / NOT INDEPENDENTLY ACCEPTED / NOT RELEASED`; E-03, C-02 and C-06 remain blocked.
- OI-0003 / Package A is `HUMAN_REQUIRED / SCHEMA_BLOCKED`; durable Person A/Person B identities and protected subject-bound facts are not accepted.
- Package B/C annual carryover and questionnaire gates are not accepted.
- A new UI-owned registry, SQLite database, scheduler or orchestration path would be a prohibited competing source of truth.
- Protected real-document Gemini processing remains blocked until the exact provider product, retention/data-use terms and configuration are verified.

These blockers directly prevent a real 2025 workflow across UI25-02 through UI25-09 and therefore UI25-12. Synthetic fixtures and the isolated port-8766 app cannot substitute for acceptance evidence.

## Package disposition

| Package | Disposition |
| --- | --- |
| UI25-00 | Technical inventory exists; Owner UI acceptance outstanding. |
| UI25-01 | Fail-closed shell exists; live persistent resolver blocked. |
| UI25-02 | BLOCKED by absent approved durable case resolver/create contract. |
| UI25-03 | BLOCKED by OI-0002/OI-0003 and carryover gates. |
| UI25-04 | Protected live intake BLOCKED; isolated hash tests are not ingestion acceptance. |
| UI25-05 | Real dispatch BLOCKED by missing authorized case/run composition; no parallel scheduler created. |
| UI25-06–09 | Real propagation BLOCKED by upstream identity, evidence and persistence prerequisites. |
| UI25-10 | DISABLED. |
| UI25-11 | German/Persian direction/navigation technical tests PASS; Owner device acceptance outstanding. |
| UI25-12 | BLOCKED by UI25-02..09 and Owner hands-on acceptance. |

## Exact continuation

Complete separate independent acceptance and explicit Owner disposition of OI-0002 SEC remediation, then resolve and accept OI-0003 Package A identities/facts. Next, implement the approved durable case resolver inside the existing persistence architecture and connect `ui_dashboard.py`; proceed dependency-order through UI25-02..09 while keeping UI25-10 disabled. No merge or release is authorized by this record.
