# CASE-001 / 2024 Comparative Audit

Status: **COMPLETE / PASS_WITH_UNRESOLVED_DIFFERENCE**

- Authority: `OWNER-DIRECTIVE-CASE001-COMPARATIVE-AUDIT-20260928-003`
- Audit: `AUDIT-CASE001-COMPARATIVE-20260928-003`
- Frozen run: `RUN-CASE001-INDEPENDENT-20260928-002`
- Scope: diagnostic comparison only; no tax behavior, extraction, prompt, workflow, source PDF, or frozen artifact was changed.

## Result bridge

The reported endpoints reconcile exactly:

`EUR 76.00 - EUR 37.00 reported historical tariff increase + EUR 31.83 historical section 35a credit = EUR 70.83`.

This explains the nominal `EUR 5.17` refund difference at the settlement level. It does not fully reconstruct the historical taxable-income path. The historical z.v.E. is only approximate (`EUR 28,128.41`) and is `EUR 200.07` above the independent pre-floor value (`EUR 27,928.34`), but the durable historical record does not contain the pension/other-insurance intermediate amounts needed to allocate that difference without invention.

There is also a one-euro historical tariff inconsistency: applying the frozen current 2024 splitting formula to statutory z.v.E. `EUR 28,128` yields `EUR 736`, whereas the historical endpoint says approximately `EUR 737`. Therefore the endpoint bridge is exact, while the underlying rule-by-rule historical bridge retains an unresolved `EUR 1` rounding/intermediate-value discrepancy.

## Material findings

- **School fees:** documents `DOC-CASE-001-00000014` and `DOC-CASE-001-00000015` announce two 2024 direct debits of `EUR 240` each. Gemini correctly extracted the `EUR 480` candidate and `EUR 144` 30-percent deduction. The frozen set contains no executed account debit. The independent fail-closed exclusion is therefore evidence-based; historical inclusion depends on an unpreserved payment assumption or evidence outside the frozen set. No extraction or current implementation defect is proven.
- **Section 35a:** `DOC-CASE-001-00000006` supports `EUR 69.13` of tenant-statement candidates and `DOC-CASE-001-00000011` supports `EUR 90.00` of gross labor, totaling `EUR 159.13`. The invoice/service evidence exists, but proof of payment to the provider's account does not. The current exclusion follows the explicit payment condition in section 35a(5). The historical `EUR 31.83` credit is arithmetically reproducible but not evidentially defensible from these 16 PDFs alone.
- **EVG:** seven transactions sum to `EUR 246.07`; the payment text includes family legal protection whose private share is not separated. In any event, EVG plus the historical `EUR 138` commuting amount totals only `EUR 384.07`, below the `EUR 1,230` employee lump sum, so neither treatment changes taxable income.
- **Commuting:** the frozen packet contains no day/distance/work-location proof for `EUR 138`. The historical amount is a source-evidence difference, but it has zero tax effect because it is absorbed by the employee lump sum.
- **Spouse minijob/RV:** Gemini extracted the `EUR 3,337.29` YTD marginal-employment gross from the newly found `DOC-CASE-001-00000016`, but omitted the `EUR 120.15` employee RV and `EUR 66.69` employer flat-tax fields. Those two values were recovered only by the later visual/source-validation step. This is recorded as a `GEMINI_EXTRACTION_DIFFERENCE`, while the final normalized treatment remains source-supported: gross excluded from ordinary assessed income and RV deductible. The historical intermediate calculation is absent, so its claimed inclusion cannot independently prove the full historical z.v.E. bridge.
- **Vorsorge:** the independent path is fully reconstructed: pension `EUR 3,391.74 + EUR 120.15 = EUR 3,511.89`; health after the statutory four-percent reduction `EUR 2,835.93`; care `EUR 620`; unemployment `EUR 474.11`; other-insurance pre-cap `EUR 3,930.04`, joint deduction `EUR 3,800`. No current arithmetic or rule defect was found. Corresponding historical intermediates are not durably available.
- **Meal expenses:** the wage certificate proves `EUR 1,002.21` of tax-free employer allowances, but none of the 16 PDFs supplies a day-level absence log or entitlement/reimbursement reconciliation. The potential `EUR 1,797.79` remains excluded in both paths and contributes zero to the difference.

## Repair Gate

No current implementation defect is proven. No code repair is proposed or authorized. The evidence-safe continuation state is `AUDIT_UNRESOLVED`, limited to the missing historical intermediates and the one-euro historical tariff inconsistency. The current system must not be changed to fit the historical endpoint.

The first independent audit review rejected a lineage error that had attributed the visually recovered spouse RV/flat-tax values to Gemini. The ledger was corrected, and final Independent Acceptance returned `PASS_WITH_UNRESOLVED_DIFFERENCE`. The privacy-safe reconciliation ledger is retained under the ignored case boundary as `sha256:5e5f6d9d749592005940dc8e6c4e11ea80273f2eb8c91256973a2f4ae928a87e`. Frozen inventory, calculation, preview, and final-result hashes were checked before and after the audit. No source PDF was modified and no external ERiC, ELSTER, Finanzamt, signing, production, or Drive mutation occurred.
