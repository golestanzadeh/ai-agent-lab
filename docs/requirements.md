# Requirements — German Tax Agent

## Status

Phase 10 discovery baseline. These requirements define the target direction and must be refined into a concrete first workflow before implementation.

## 1. Product goal

Build an evidence-driven Agentic AI system for German tax work that can process tax cases for natural persons and legal entities using the documents and information supplied by the user, apply the German tax rules relevant to the case, prepare validated tax results and documents, and support controlled submission to the relevant tax authority where an official and lawful technical path exists.

The quality target is senior-tax-expert-level performance for supported workflows. This is an engineering/evaluation target, not an unsupported guarantee of legal perfection.

## 2. Jurisdiction

- Country: Germany.
- Relevant tax authority: determined per case, including Finanzamt and other competent authorities/systems where applicable.
- Tax year and assessment period must be explicit case data.
- Rules must be evaluated according to their applicability and effective dates.

## 3. Core functional requirements

### FR-01 — Document intake

Accept supported user-provided tax documents and structured information.

### FR-02 — Document understanding

Classify documents, extract relevant facts, preserve source references, and identify missing or unreadable information.

### FR-03 — Reconciliation

Detect contradictions across documents and require resolution or explicit uncertainty instead of silently choosing a value.

### FR-04 — Current-law verification

For every material tax/legal conclusion, verify the applicable German rules against authoritative sources available at execution time. The system must track source identity, relevant date/version information, and applicability to the case.

### FR-05 — Research

Research authoritative German tax sources and provide traceable citations for material conclusions.

### FR-06 — Calculation

Perform tax calculations with deterministic code or independently validated calculation logic wherever practical.

### FR-07 — Analysis

Identify applicable tax treatment, deductions, allowances, obligations, deadlines, risks, and supported options.

### FR-08 — Challenge

Perform an independent challenge pass that actively searches for contradictory evidence, alternative interpretations, missing facts, calculation errors, and unsupported conclusions.

### FR-09 — Audit

Perform a final QA/audit pass before documents are approved.

### FR-10 — Output package

Generate complete, clear, traceable, and print-ready tax documents for the supported workflow, including required attachments and supporting evidence where applicable.

### FR-11 — Electronic submission

Where an official and lawful technical submission route exists, support controlled electronic submission. Submission must require explicit authorization/approval and must never occur silently.

### FR-12 — Audit trail

Preserve a traceable record of source documents, extracted facts, evidence, research, calculations, decisions, approvals, generated documents, and submission events.

## 4. Non-functional requirements

- Accuracy must be measurable, not asserted.
- Current-law freshness must be testable.
- Effective-date handling must be testable.
- Outputs must be reproducible for a fixed case, source set, and configuration.
- Every material conclusion must have provenance.
- Sensitive taxpayer data must be minimized, protected, and not used unnecessarily for development.
- Tools and external actions require explicit permissions.
- Failures and uncertainty must be visible.
- The system must fail closed when a material rule cannot be verified.
- Model/version and source configuration must be recorded for important runs.
- The architecture must allow deterministic components to be tested independently.

## 5. Final output quality bar

For a supported workflow, final documents must be:

1. complete;
2. internally consistent;
3. mathematically validated;
4. grounded in applicable German tax rules;
5. traceable to evidence;
6. clear enough for review by a human and the relevant authority;
7. correctly formatted for the intended submission channel;
8. accompanied by explicit uncertainty or unresolved items;
9. approved before consequential submission.

"Completely error-free" is the desired quality objective but cannot be established by assertion. Phase 40+ evaluation must define measurable acceptance thresholds and residual-risk reporting.

## 6. First workflow constraint

The final product may eventually support many German tax workflows. The first implementation must be a deliberately narrow, high-value workflow that can be evaluated rigorously. The concrete first workflow, target taxpayer profile, tax year, documents, official forms, and submission route are Phase 10 decisions still to be made.
