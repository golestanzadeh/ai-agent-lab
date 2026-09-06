# Use Cases — German Tax Agent

## Status

Phase 10 baseline. These are candidate use-case families for the final system. The first executable use case must be selected and narrowed before implementation.

## UC-01 — Natural person annual tax return

User supplies the available annual tax documents and relevant personal/tax information. The system extracts facts, verifies applicable German rules for the relevant tax year, calculates the case, identifies relevant deductions/allowances, prepares the supported tax return and attachments, audits the package, and presents it for approval before submission.

## UC-02 — Employee with complex deductible expenses

Process an employee case involving multiple income-related expenses and supporting receipts/documents. The system must distinguish eligible evidence from irrelevant or insufficient evidence and explain each material conclusion.

## UC-03 — Self-employed / freelancer tax case

Process business income and expense documentation for a natural person with self-employment. The workflow must reconcile invoices, expenses, payments, and tax-relevant classifications and identify missing evidence.

## UC-04 — Legal entity tax case

Process a defined tax workflow for a legal entity using accounting/tax documents, contracts, invoices, and relevant company information. The exact entity type and tax workflow must be specified separately before implementation.

## UC-05 — Tax correction / amended filing

Analyze an existing tax filing and newly supplied evidence, determine what may need correction under the applicable rules, prepare the required documentation, and highlight risks and approval points.

## UC-06 — Tax authority correspondence

Ingest a notice or request from the relevant German tax authority, identify what is being requested, research the applicable rules, reconcile the request against the user's case file, and prepare a documented response for human approval.

## UC-07 — Current-law verification

Given an existing tax analysis, re-run the legal/tax evidence check against authoritative sources and determine whether any material rule has changed, expired, been superseded, or has a different effective date.

## UC-08 — Final filing package audit

Given a completed tax case and proposed filing package, independently audit facts, calculations, required documents, citations, consistency, deadlines, and submission readiness. The auditor must be able to reject the package and return a precise defect list.

## UC-09 — Controlled electronic submission

After explicit human approval, transmit a supported filing/package through an official and lawful electronic channel where technically available. Record the authorization, payload/version, submission result, and any receipt or confirmation.

## UC-10 — Human escalation

When evidence is missing or contradictory, current law cannot be verified, the case falls outside the supported scope, or confidence/validation thresholds are not met, stop the autonomous workflow and produce a clear escalation package rather than guessing.

## Selection principle

The first implementation should select one use case that maximizes learning value and measurable quality while keeping the data, legal scope, document set, calculations, and submission route sufficiently bounded for rigorous testing.
