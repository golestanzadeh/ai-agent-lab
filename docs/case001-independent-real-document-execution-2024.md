# CASE-001 / 2024 Independent Real-Document Execution

Status: **COMPLETE / PASS**

- Authority: `OWNER-CORRECTION-CASE001-INDEPENDENT-20260928-002`
- Run: `RUN-CASE001-INDEPENDENT-20260928-002`
- Recovery commit: `3a139932e7f5e4859b43412e42b72a3f6219b100`
- Case/year: `CASE-001` / `2024`

The objective is to produce the current system's independent result solely from the current real Drive PDFs, newly generated Gemini extractions, applicable 2024 rules, and existing deterministic components. Historical z.v.E., tax, refund, Chief status, opportunities, conclusions, and expected-result assertions are excluded from the calculation packet and final report. Historical records may only support technical folder discovery.

Exact-root, read-only recursive discovery traversed 15 folders and found 20 files, including 17 PDFs. Sixteen PDFs under `Tax_Categories` are taxpayer-source documents and exactly match the Owner-confirmed expected count. One additional PDF, `ESt_1A_2024_official_package.pdf`, is located under `D026_Forms`; it is an official blank/project form package rather than taxpayer source evidence and is explicitly excluded. The missing sixteenth taxpayer source overlooked by the earlier non-recursive identity inventory is `Gehaltsabrechnung Asma.pdf` under `Tax_Categories/Einkommensnachweise`.

The 16-source inventory is frozen for this run before raw download or Gemini processing. Every source must reach an explicit terminal processing state and bind stable Drive identity, current category path, MIME type, size, content hash, and extraction identity inside the ignored private case boundary. Drive mutation, historical-target optimization, external submission, another provider/case/year, signing, production, and duplicate stores/orchestrators/schedulers remain prohibited.

## Completed execution

The frozen private inventory is `sha256:d36daeb574e17e8487a830decd0ea31bc823a7d1aa5f5415c9a0c8df7e6a5694`. All 16 PDFs passed PDF-header, size, and SHA-256 validation. Fresh `GeminiDocumentExtractor` processing completed `16/16`, with zero failed or skipped documents; every extraction binds the exact inventory identity, Drive identity, and source content hash. The independent case packet contains all 16 newly generated extractions and no historical target value or analytical conclusion.

The newly discovered payroll PDF resolved spouse marginal-employment evidence: year-to-date marginal-employment social-insurance gross EUR 3,337.29, employer flat-tax treatment, and employee pension contribution EUR 120.15. Visual page review independently confirmed the material year totals. The marginal-employment gross is excluded from the regular assessment under the reviewed section 40a treatment, while the employee pension contribution remains a deductible section 10 contribution.

The first complete six-specialist/Chief pass was rejected because it omitted the spouse pension contribution. Correction round 1 fixed that omission but was rejected for incorrect 2024 tariff arithmetic. A versioned deterministic Decimal trace then reconciled all contributions and statutory rounding. Correction round 2 ran all six specialists and the Chief; every role returned `PASS` and adopted the corrected trace.

The independently calculated result is:

- gross primary employment income: EUR 36,470.23;
- employee lump sum: EUR 1,230.00;
- deductible pension contributions: EUR 3,511.89;
- other Vorsorge deduction under the joint ceiling: EUR 3,800.00;
- z.v.E. before statutory floor: EUR 27,928.34;
- statutory z.v.E.: EUR 27,928;
- joint 2024 Einkommensteuer: EUR 700;
- solidarity surcharge: EUR 0;
- creditable withheld wage tax: EUR 776;
- independently calculated refund: EUR 76.

Kindergeld remains more favorable in the section 31 comparison. Unsupported optional claims were excluded without blocking the base assessment: school-fee payment execution, section 35a cashless payment, donation payment, additional meal-absence evidence, the mixed EVG legal-protection component, incomplete medical payment/reimbursement evidence, and the 2025 software outflow.

The form role produced a completed non-transmitting preview bound as `sha256:9955f9a6a4ab198176b16728816d61016c1b7c10bc4870405127cdb72616f135`. The final private result is `sha256:9d6dc9c69ff9572a64320d7cd5b607c32577156ea0498d2d4e88ec420355f4a5`. Independent Acceptance returned `PASS` after detecting and requiring repair of two Windows materialization hash bindings. Focused verification passed with `20 passed`; full unit regression passed with `915 passed, 1 warning`.

No historical tax result was used or compared. No external ERiC execution, ELSTER/Finanzamt transmission, signing, production action, Drive mutation, or processing of another case/year/provider occurred.
