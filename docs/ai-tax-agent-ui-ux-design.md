# AI-Tax-Agent UI/UX Design Specification

**Status:** Canonical design-session document  
**Design phase:** UI-1 — Information Architecture  
**Implementation status:** NOT AUTHORIZED  
**Reference repository:** `golestanzadeh/ai-agent-lab`  
**Design branch:** `ui-ux-design-session`  
**Runtime/execution branch at design-session baseline:** `d021-agent-case-provisioning`

> This document records approved UI/UX product decisions. It does not authorize implementation, runtime changes, Work/Codex execution, Kernel changes, Docker changes, declaration execution, or external submission.

## 1. Product design principles

AI-Tax-Agent is a tax product, not a developer dashboard. Ordinary users must not need to understand Agents, GitHub, Docker, Kernel, Codex, task registries, checkpoints, or other implementation details.

The primary experience should be calm, professional, trustworthy, desktop-first, responsive, and fully functional on mobile.

Technical depth remains available through progressive disclosure.

The product must be able to grow from personal single-user use toward multi-user/professional tax workflows without prematurely building unnecessary enterprise complexity.

## 2. Core information architecture

The approved primary hierarchy is:

```text
Workspace
└── Case
    └── Tax Year
        └── Tax Workflow
```

A Case is a persistent tax identity/context. A Tax Year is a separate annual tax workflow within that Case.

### Global navigation

- Overview
- Cases
- Attention
- Administration

Documents, Analysis, Result, Declaration, Evidence, Agent Activity, and Audit are not global top-level destinations when they belong to a specific Case/Tax Year.

### Tax-Year navigation

Primary workflow:

- Overview
- Documents
- Analysis
- Issues
- Result
- Declaration
- Submission

Secondary/transparency layer:

- Evidence
- Activity
- Audit

Technical/infrastructure information such as Agents, Tasks, Kernel state, checkpoints, Independent Acceptance details, and system diagnostics must remain behind progressive disclosure or administration/technical views.

## 3. Primary user journey

The approved conceptual flow is:

```text
Enter
→ Select/Create Case
→ Select Tax Year
→ Upload Documents
→ Processing/Analysis
→ Resolve Issues / Attention
→ Review Result
→ Review Declaration
→ Content Approval
→ Select Submission Method
→ Submission or Export
```

Analysis and declaration correctness are independent from the eventual submission channel.

## 4. Documents and Evidence are distinct concepts

**Document** is a source artifact.

**Evidence** is the evidentiary use of information derived from a source.

The UI must preserve traceability without forcing ordinary users into technical views.

Approved lineage model:

```text
Document
→ Extracted Fact
→ Tax Decision
→ Declaration Field
```

Important values should support navigation in both directions, from source to declaration and from declaration field back to supporting evidence.

## 5. Tax Analysis organization

Analysis is organized by understandable tax topics, not by Agent identity.

Examples include:

- Income
- Werbungskosten
- Sonderausgaben
- Vorsorge / insurance
- Kinder
- Schulgeld
- §35a
- Donations
- Other applicable tax domains

User-facing tax-decision states include:

- Accepted
- Excluded
- Missing evidence
- Needs review
- Not applicable

Internal status detail remains available when needed but does not dominate the ordinary workflow.

## 6. Attention / Issues

There is one coherent human-attention concept.

Global **Attention** aggregates actionable items across Cases.

Tax-Year **Issues** shows only actionable items for that Tax Year.

User-facing categories include:

- Action required
- Review required
- Missing information
- Missing evidence
- Conflict
- Approval required
- Validation problem
- System problem

Anything that genuinely requires human action must ultimately be discoverable through Attention/Issues.

## 7. Result and Declaration are separate

**Result** answers: “What is the tax outcome?”

**Analysis** answers: “Why?”

**Declaration** answers: “Where does the accepted information appear in the official declaration?”

Declaration views must preserve official German form/field identity while allowing user-friendly explanations and evidence traceability.

## 8. Activity and Audit are separate presentations

**Activity** is a human-readable history of meaningful events.

**Audit** is the specialist/professional evidentiary record, including as applicable:

- timestamps
- actors
- decisions
- evidence
- versions
- hashes
- approvals
- checkpoints
- source provenance
- Independent Acceptance

They may derive from the same backend facts but serve different users and must not be collapsed into one cluttered view.

## 9. Agent Activity

Agent Activity is required but is not a primary product domain.

Ordinary users are not expected to manage Agents or understand task IDs.

Agent/task/checkpoint/Independent Acceptance details belong in technical activity or administration/system views.

## 10. User-facing status model

Internal statuses must be mapped to a smaller understandable UX vocabulary while preserving technical detail behind progressive disclosure.

| User-facing status | Example internal meaning |
|---|---|
| Complete | PASS |
| In progress | running / pending |
| Needs attention | BLOCKED / EVIDENCE_INCOMPLETE |
| Approval required | HUMAN_REQUIRED |
| Paused | TOKEN_PAUSED |
| Problem detected | STOP_DIAGNOSTIC / validation failure |
| Excluded | EXCLUDED |
| Not applicable | N/A |
| Verified | successful Independent Acceptance |

The internal status is not destroyed or rewritten; it remains inspectable as technical/audit detail.

## 11. Bilingual product requirement

The product is bilingual from the beginning:

- Deutsch: `de-DE`
- فارسی: `fa-IR`

Language preference is per-user, not per-case.

Persian support means true RTL layout support, not merely translated strings. German uses LTR.

Direction-aware behavior applies to navigation, breadcrumbs, controls, forms, dialogs, tables, icons/arrows, and alignment.

Data such as IBAN, Steuer-ID, Steuernummer, amounts, dates, filenames, official form identifiers, and ERiC field identifiers must use appropriate data-direction rules rather than blindly inheriting RTL.

## 12. Tax terminology policy

Tax/legal translation must be semantic and controlled.

A canonical terminology dictionary should eventually define, for each concept:

- official German term
- approved Persian translation
- short German UI label
- short Persian UI label
- German explanation
- Persian explanation

Official German legal/form identities must not disappear in Persian mode.

Examples of the intended pattern:

- هزینه‌های مرتبط با کار (Werbungskosten)
- هزینه خدمات خانگی (§35a EStG)
- پیوست N (Anlage N)
- فرم اصلی اظهارنامه (Hauptvordruck)

The UI translates/explains official concepts; it does not replace their official identity.

## 13. Desktop and mobile requirement

The approved requirement is:

**Desktop-first, fully functional mobile.**

Mobile is not a read-only or reduced product.

A mobile user must be able to:

- open/select a Case
- upload documents
- review issues
- read analysis
- inspect evidence
- review the declaration
- perform permitted approvals

Specialist Audit/System diagnostic views may provide richer desktop experiences.

The exact mobile navigation pattern remains to be specified in a later design phase.

## 14. Human Gate model

The project’s two-step outbound security rule must be visually and semantically explicit.

### Human Gate 1 — Content Approval

The user confirms that the declaration information is correct.

This approval does **not** authorize external transmission.

### Human Gate 2 — External Transmission Approval

This is a separate approval authorizing a specific external transmission to a clearly identified destination.

The UI must show the destination and make clear that data is about to leave AI-Tax-Agent.

The two approvals are separate concepts:

```text
Content Approval != Transmission Approval
```

Internal analysis actions must never be visually confusable with external transmission.

## 15. Submission is an independent product stage

The approved workflow is:

```text
Documents
→ Analysis
→ Issues
→ Result
→ Declaration
→ Approval
→ Submission
```

Submission is not synonymous with ELSTER.

After content approval, users may choose among supported/eligible channels.

### Submission channels

1. **Electronic submission**
   - ELSTER/ERiC or another legally supported electronic route.
   - Requires independent Human Gate 2 before external transmission.

2. **Print and submit personally**
   - Prepare the appropriate official forms for the relevant tax year where paper submission is legally available.
   - User reviews, prints, signs where required, and personally posts/delivers the declaration.
   - AI-Tax-Agent does not claim external receipt merely because a PDF was generated.

3. **Export only / no submission yet**
   - Prepare/export the declaration or review material without external transmission.

Future professional delivery channels may be added without changing the analysis workflow.

## 16. Submission eligibility

Submission methods must not be offered blindly.

Availability of paper/electronic routes must be determined from authoritative rules applicable to the relevant declaration and tax year, not guessed by an Agent.

A channel may therefore be shown as available, unavailable, or requiring an explained exception.

## 17. Print package model

The paper workflow must distinguish official declaration output from the product’s own explanatory material.

### Official Declaration Print Package

The target is to populate/use the official forms applicable to the relevant tax year, rather than creating a merely similar AI-Tax-Agent-designed substitute.

The package may include the required official Hauptvordruck and applicable Anlagen.

It is intended for the user to review, print, sign where required, and personally submit when legally permitted.

### Review / Evidence Package

A separate bilingual AI-Tax-Agent-generated package may contain:

- understandable result summary
- accepted/excluded tax decisions
- explanations
- evidence references
- provenance/lineage
- review aids

This package is primarily for user review/archive and is not automatically treated as the official declaration sent to the Finanzamt.

Supporting evidence must not be automatically added to a submission package merely because it exists; submission/evidence inclusion must follow the applicable official requirements.

## 18. Lifecycle distinction

`Completed` and `Submitted` are not synonyms.

Conceptually:

```text
Analysis complete
→ Declaration ready
→ Information approved
→ Ready for submission
→ Submission method selected
→ [Electronic submitted | Print package prepared | Export only]
```

For user-managed postal/personal delivery, the system may allow the user to record “marked as sent”, but that is not proof that the Finanzamt received it.

## 19. Reference case for design

CASE-001 / tax year 2024 is the approved reference case for mockups.

Use the already accepted frozen prototype values without recalculation:

- Expected refund: **EUR 133.83**
- Schulgeld deduction: **EUR 144**
- §35a eligible basis: **EUR 90**
- §35a eligible basis: **EUR 69.13**
- §35a tax credit: **EUR 31.83**
- Lawyer expenses: excluded by Owner decision
- Medical/pharmacy: excluded by Owner decision
- EUR 60 donation: evidence incomplete / excluded

These values are design fixtures only in this UI/UX session and must not trigger tax recomputation.

## 20. Administration growth path

The IA reserves future administration areas such as:

- Profile / Workspace
- Users & permissions
- Official sources
- Declaration / ERiC versions
- Integrations
- System health
- Security

Personal mode should expose only what is useful. Professional/multi-user capability may expand these areas later without restructuring the primary tax workflow.

## 21. Safety boundary for this design session

This document is documentation only.

Until explicit Owner authorization for implementation:

- do not implement UI code
- do not alter Kernel behavior
- do not alter runtime queues/databases
- do not start Work/Codex execution
- do not alter Docker/runtime configuration
- do not change declaration execution
- do not transmit data externally
- do not merge design changes into an execution branch merely to keep documentation current

The active execution workflow must remain undisturbed.

## 22. Open design work

Approved phase order remains:

1. UI-1 — Information Architecture
2. UI-2 — Workflow Design
3. UI-3 — Screen Specification
4. UI-4 — Visual System
5. UI-5 — Prototype
6. UI-6 — Implementation Specification

Implementation begins only after explicit Owner authorization.

If a future UI decision depends on real API, Kernel, Case, Agent, declaration, or state contracts, the repository must be inspected read-only rather than inventing a backend contract.

## 23. Decision log

### 2026-09-29 — UI-1 baseline

Approved:

- Workspace → Case → Tax Year hierarchy
- user-centric tax workflow rather than developer-centric navigation
- Evidence/Activity/Audit as transparency layers
- Agent internals hidden from ordinary workflow
- bilingual German/Persian product from inception
- true LTR/RTL behavior
- controlled tax terminology
- desktop-first and fully functional mobile
- independent Content Approval and External Transmission Approval
- Submission as an independent stage
- electronic, print/personal submission, and export-only paths
- submission-channel eligibility based on authoritative rules
- official-form-based print target separated from bilingual Review/Evidence Package
- Completed and Submitted as distinct lifecycle states
- CASE-001/2024 frozen values as prototype fixtures

No implementation authorization was granted by these decisions.
