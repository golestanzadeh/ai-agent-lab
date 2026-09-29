# CASE-001 / 2024 Structured Financial Evidence Intake

Status: **COMPLETE / PASS**

- Run: `RUN-CASE001-STRUCTURED-FINANCIAL-20260928-004`
- Source: `SFS-CASE-001-2024-0001`, one immutable CSV in canonical `Tax_Years/2024/Cases/CASE-001/Documents`
- Source SHA-256: `f122db653b3e3ef738127e279b82e756fa9ea9744e9b106400e676d08fea90c9`
- Frozen predecessor: refund EUR 76, unchanged

Deterministic cp1252/semicolon ingestion parsed all 946 rows, covering 2024-01-02 through 2024-12-30 in EUR. No row failed parsing. One exact duplicate group (one extra cash-withdrawal row), zero probable-duplicate groups, two explicit debit/credit reversal pairs, and zero identifiable own-account transfers were retained rather than deleted.

The first Independent Acceptance rejected aggregate-only candidate lineage. Remediation assigned every row one stable `TX-` identity and terminal disposition: 832 non-tax rows, 108 terminal candidate rows, four explicit reversal rows, and two retained duplicate rows. All nine candidate categories enumerate exact row IDs; 110 unique rows participate because the two reversal rows are also medical candidates. No candidate relationship remains aggregate-only. Final Independent Acceptance is `PASS`.

The new source establishes two executed school-fee debits totaling EUR 480 and therefore a EUR 144 section 10(1) no. 9 deduction. It also closes the payment condition for the EUR 90 craftsman invoice and, through twelve cashless rent/advance payments matched to the tenant allocation statement, EUR 69.13 of tenant services. The total section 35a basis is EUR 159.13 and the direct credit is EUR 31.83.

The EUR 60 recurring supporter payment is now payment-matched but remains excluded because the recipient-produced simplified-donation proof required by section 50 EStDV is absent. Insurance entries remain allocation-incomplete and have zero incremental effect because the existing other-Vorsorge ceiling is exhausted. Medical payments are materially corroborated but retain a two-cent mismatch, incomplete necessity/reimbursement evidence, and remain below the reasonable-burden threshold. Three newly discovered attorney transfers totaling EUR 1,213.76 remain excluded because their legal matter and income nexus are unknown. EVG payments reproduce at EUR 246.07 but remain below the employee lump sum and include an unallocated family legal-protection component.

The successor calculation preserves the prior result and changes only supported inputs: EUR 144 additional school-fee deduction lowers statutory z.v.E. to EUR 27,784 and tariff tax from EUR 700 to EUR 674; the EUR 31.83 section 35a credit lowers final tax to EUR 642.17. Against EUR 776 withheld wage tax, the successor refund is EUR 133.83. Exact bridge: `76.00 + 26.00 + 31.83 = 133.83`.

All six Specialist roles and the Chief Tax Auditor returned `PASS`. Focused verification passed (`22 passed`); complete unit regression passed (`920 passed, 1 warning`). Capacity Gate observed 99 percent five-hour and 37 percent weekly remaining before lineage continuation. No historical target was used. No source or Drive mutation, external ERiC execution, ELSTER/Finanzamt submission, signing, production deployment, or processing of another case/year/provider occurred.
