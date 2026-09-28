# CASE-001 / 2024 final closure and declaration-readiness audit

Date: **2026-09-28**

Primary state: **`CASE_CLOSED_REMEDIATION_REQUIRED`**.

## Frozen case

The accepted tax analysis is frozen at `RUN-CASE001-STRUCTURED-FINANCIAL-20260928-004`: z.v.E. EUR 27,784; tariff income tax EUR 674.00; section 35a credit EUR 31.83; final tax EUR 642.17; withheld wage tax EUR 776.00; refund EUR 133.83. The 16-PDF inventory, canonical structured source, 946-row ledger, evidence relationships, Specialist/Chief decisions, Independent Acceptance and hashes are preserved in the machine-readable companion manifest.

Closure decisions are explicit: lawyer expenses and medical/pharmacy expenses are `OWNER_DECLINED / EXCLUDED`; the EUR 60 Bjorn Steiger Stiftung payment is `DONATION_EVIDENCE_INCOMPLETE / EXCLUDED`. Additional accepted exclusions remain visible and were not reopened.

## Coverage result

The manifest contains 18 items: zero `SUPPORTED`, zero `MISSING_MAPPING`, one `MISSING_RULE`, seven `MISSING_FORM_OR_SECTION`, one `SUPPORTED_BUT_UNVERIFIED`, two `IRRELEVANT_FOR_CASE`, and seven `EXCLUDED_BY_ACCEPTED_CASE_DECISION`.

Mapping profile 14, declaration profile 1 and plausibility profile 11 cover a bounded synthetic Anlage N subset. Existing wage-class, gross-wage and withheld-tax field semantics are official-source/XSD/local-rule backed, but the contract is synthetic-only and has no accepted real CASE-001 binding. In addition, gross wages currently accept only whole euros while the accepted source contains cents; the required authoritative transformation is missing. These fields are therefore not overstated as fully supported.

Seven affirmative requirements are outside current form coverage: Hauptvordruck/joint-assessment context; pension inputs; other Vorsorge inputs; school fees in Anlage Kind; the accepted EUR 3,000 Kindergeld/section 31 context; craftsman labor; and tenant household-service allocation. One additional gross-wage transformation rule is missing. Existing field semantics touch 2 of 9 affirmative requirements (22.22 percent), while end-to-end case-bound verified coverage is zero percent. A complete non-transmitting declaration cannot currently be generated.

The supported-portion artifact is explicitly `NON_TRANSMITTING_PREVIEW` and `DECLARATION_CONTENT_INCOMPLETE`. It shows only the existing Anlage N tax-class semantic and withheld wage-tax field. It deliberately omits gross wages until the cent-to-whole-euro transformation is authoritative and tested, and it invents no missing identity or form data.

## Authoritative boundary

Current E10 field semantics are backed by the protected, hash-pinned ERiC 44.3.6.0 E10/2024 annual material and exact local XSD. The official Bundesfinanzverwaltung 2024 income-tax form package confirms that Hauptvordruck, Anlage Vorsorgeaufwand, Anlage Kind and Anlage Haushaltsnahe Aufwendungen are distinct required form surfaces. Exact ERiC field identifiers for the missing surfaces must be recovered from protected official annual material during remediation; none is guessed in this audit.

## Remediation queue

The dependency-ordered queue is `DR-01 -> (DR-02, DR-03, DR-04) -> DR-05`. DR-01 adds case-bound E10 composition and Hauptvordruck; DR-02 implements Vorsorgeaufwand; DR-03 implements the school-fee plus EUR 3,000 Kindergeld/section 31 vertical slice; DR-04 implements section 35a household/craftsman content; DR-05 performs integrated XSD, local plausibility, recovery, isolation, regression and Independent Acceptance.

Implementation is not authorized by this audit. One bounded Owner approval can authorize DR-01 through DR-05 as a coherent queue; no per-field approval is necessary inside that future envelope. Official ERiC execution, signing, certificate use and external filing remain separate Human Gates. The existing Orchestrator and scheduler must be reused; no parallel controller is permitted.

Independent Acceptance is `PASS` after four review cycles. The review forced correction of the gross-wage transformation overclaim, missing Kindergeld/section 31 and Vorsorge component lineage, aggregate tenant-payment references, freeze hashes, and queue completeness. Final focused manifest/mapping/declaration/XSD/plausibility/readiness/documentation verification passes (`254 passed`).

No accepted calculation was recomputed or target-fitted. No CSV/Gemini/full Specialist/Chief rerun occurred. No ERiC, ELSTER or Finanzamt action, signing, credential use, Drive mutation or production action occurred.
