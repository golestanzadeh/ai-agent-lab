# CASE-001 / 2024 - EUR 60 donation evidence reconciliation

Date: **2026-09-28**  
Run: `RUN-CASE001-DONATION-20260928-005`  
Scope: **only the EUR 60 Bjorn Steiger Stiftung payment**

## Outcome

Final classification: **`DONATION_EVIDENCE_INCOMPLETE`**.

The payment is a real, completed outgoing debit and is deterministically linked to the existing frozen PDF. The available recipient-produced document does not, however, contain every element required by the simplified-proof route in section 50(4), sentence 1, number 2(b) EStDV. The accepted EUR 133.83 successor refund therefore remains unchanged. No new calculation version was created.

## Capacity and recovery gates

- Starting capacity: five-hour remaining `86%`; weekly remaining `35%`.
- Observed resets: 2026-09-29 03:06:26 Europe/Berlin and 2026-10-04 20:39:49 Europe/Berlin.
- Recovery: branch `d021-agent-case-provisioning`; local and remote HEAD both `c1ad926316122329c430f739c35a4ecaea8529fd`; clean working tree.
- The accepted 946-row ledger and its EUR 133.83 successor calculation were read as durable artifacts. The CSV was not reparsed, Gemini was not rerun, and unrelated reviews were not reopened.

## Exact source and payment lineage

- PDF identity: `DOC-CASE-001-00000007`; source SHA-256 `3ceb772e30a37b5cd51499167bcd5c475f7b27ec132c1ff227ce831ebb2a1213`.
- Existing extraction: Gemini document vision; `Foerderantrag`; request number `A 994978`; annual contribution EUR 60; support start 2024-08-01.
- Stable transaction identity: `TX-c67f3a594d3273589c5a9ce3`; canonical source row 400.
- Payment facts already accepted in the ledger: booked 2024-08-01; `ERSTLASTSCHRIFT`; EUR -60.00; direction `DEBIT`; recipient `Bjorn Steiger Stiftung`; purpose `Foerderernummer: 994978 Vielen Dank`; mandate reference `994978`; creditor identity matches the form.
- Match: exact amount, recipient, supporter/request number, support start date, debit timing, and recurring-support semantics. The row is neither income, refund, purchase, duplicate, nor reversal.

## Document-content verification

The one-page recipient-produced form was reviewed visually, not inferred from its filename. It states, among other things:

- `Foerderantrag fuer "Lebensretter"`, minimum term two years;
- voluntary annual contribution EUR 60;
- recurring support rather than a one-time donation;
- direct-debit authorization and support start 2024-08-01;
- the Bjorn Steiger Stiftung is recognized by Finanzamt Waiblingen, with a displayed tax number, as `gemeinnuetzig und mildtaetig`.

The existing Gemini extraction correctly captured the request identity, amount, recurring nature, payment mandate and dates. Its note that the form alone is not proof of actual outflow is correct; the accepted bank booking supplies that separate fact. The extraction did not record the recipient-status footer, which was recovered through direct visual review.

## Legal test

- Section 10b(1) EStG permits donations and eligible membership contributions for tax-privileged purposes as Sonderausgaben, subject to its recipient and ceiling rules.
- Section 50(4), sentence 1, number 2(b) EStDV permits simplified proof for a payment not exceeding EUR 300 to an eligible tax-exempt recipient only when a recipient-produced document prints (1) the tax-privileged purpose for which the payment is used, (2) information about the recipient's exemption from corporation tax, and (3) whether the payment is a donation or membership contribution.
- Section 50(4), sentence 2 EStDV additionally requires the bank confirmation to identify payer and recipient, amount, booking date, and actual execution. Sentence 3 requires retention of the recipient-produced document.

Requirement comparison:

1. Amount at or below EUR 300: **met** (EUR 60).
2. Actual bank execution and required booking particulars: **met** by the accepted debit ledger.
3. Recipient-produced document: **met** by the frozen form.
4. Recipient tax-privileged status: **partially evidenced**; the form says recognized as charitable and benevolent and gives the competent tax office/tax number.
5. Exact tax-privileged purpose for which this payment will be used: **not stated with the specificity required by section 50(4)**. `Lebensretter` and general recurring support do not identify the tax-privileged statutory purpose of use.
6. Information about exemption from corporation tax: **not stated**. Recognition as `gemeinnuetzig und mildtaetig` is not an express statement of the corporation-tax exemption or its applicable notice/period.
7. Donation versus membership contribution: **not stated deterministically**. `Keine einmalige Spende, da wiederkehrende Foerderung` describes recurrence but does not clearly classify the payment as a donation rather than a membership contribution for section 50(4).

The document's title is not the reason for exclusion. The failure is content-specific: three required recipient-side particulars are absent or indeterminate.

## Calculation and acceptance boundary

Because the evidentiary route is incomplete, EUR 60 does not enter the calculation. The accepted version remains: z.v.E. EUR 27,784; tariff income tax EUR 674.00; section 35a credit EUR 31.83; final tax EUR 642.17; wage tax withheld EUR 776.00; refund EUR 133.83.

The affected Sonderausgaben evidence review is `PASS_WITH_EXCLUSION`: the payment was assessed completely and excluded for exact statutory-document gaps. Chief rerun is `NOT_REQUIRED` because no calculation input or result changed. Independent Acceptance is `PASS`; it independently verified the PDF content, unique ledger match, primary-law requirement matrix, fail-closed exclusion, and scope controls.

Durable private result identity: SHA-256 `ad265dd1c4ea203260865f383d9b22b8d713221f7283735238a2991084ec86cf`. Focused documentation and structured-financial regression: `14 passed`.

Only this evidence/legal issue was reviewed. Medical and lawyer expenses were not analyzed; the 946-row intake, Gemini extraction, unrelated Specialists, Chief review and full case acceptance were not rerun. No historical result was used as a target. No Drive source was changed and no ERiC, ELSTER or Finanzamt action occurred.
