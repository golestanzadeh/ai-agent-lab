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


## 24. UI-2 — Workflow Design

### 24.1 Workflow topology

The Tax-Year workflow is **stage-based but non-linear**. It is not a one-way wizard.

Users may move backward to inspect or correct earlier stages. The product preserves state and explicitly surfaces downstream consequences of material changes.

```text
Setup
→ Documents
→ Analysis
↔ Issues / Attention
→ Result
→ Declaration
→ Human Gate 1: Content Approval
→ Ready for Submission
   ├─ Electronic → Human Gate 2 → External Transmission
   ├─ Print → Official Print Package → User Prints/Signs/Sends
   └─ Export Only → No External Transmission
```

Attention/Issues is an overlay across the workflow rather than a terminal stage.

### 24.2 Stage readiness model

Each workflow stage has two separate concepts:

1. **State** — what is happening in that stage.
2. **Readiness** — whether the user may safely proceed to a dependent stage.

A stage being visually “complete” does not automatically imply that the whole Tax Year is ready for submission.

Core readiness states:

- Not started
- In progress
- Needs attention
- Ready
- Approval required
- Approved
- Paused
- Problem detected
- Superseded / review required after material change

Technical/internal states remain inspectable but are not the primary user vocabulary.

### 24.3 Setup

Setup establishes the Tax-Year context without forcing an early submission choice.

It may include applicable participants, year, and tax context required by the real Case contract.

Submission method is **not** selected here.

Setup may be revisited. A material identity/participant change can invalidate downstream analysis or approval and must surface its impact before continuation.

### 24.4 Document intake

Document intake supports repeated uploads throughout the workflow.

Conceptual document lifecycle:

```text
Uploaded
→ Processing
→ Classified
→ Information extracted
→ Linked to tax topic/evidence
→ Reviewed/usable
```

Alternative outcomes include:

- duplicate
- unsupported/unreadable
- ambiguous classification
- missing required information
- conflicting information
- evidence incomplete

Human-actionable outcomes create/update an Issue and become discoverable in Attention.

The user is not required to understand which Agent processed the document.

### 24.5 Analysis loop

Analysis runs by tax topic.

A topic can be:

- not started
- in progress
- complete
- needs attention
- excluded
- not applicable

The user may enter a topic, inspect the decision, see supporting evidence, and resolve an Issue without leaving the Case context.

Resolving an Issue returns the user to the affected topic/stage and triggers only the downstream re-evaluation required by the real system contract.

The UI must never imply that an unresolved material Issue has disappeared merely because the user navigated away.

### 24.6 Result readiness

Result becomes authoritative for review only when the required analysis inputs are sufficiently resolved under the system’s actual validation rules.

The Result page may still be visible earlier, but an incomplete/provisional result must be explicitly labelled and must not be visually confused with a declaration-ready result.

The UI must not invent or silently recalculate values independently from the authoritative backend result.

### 24.7 Declaration workflow

Declaration is generated/mapped from accepted tax decisions and authoritative declaration rules.

The user can review:

- official form/section identity
- populated values
- explanation
- evidence/provenance
- validation status

Technical field identifiers are available through progressive disclosure.

Declaration validation problems route to Issues/Attention and block Content Approval when material.

### 24.8 Human Gate 1 — Content Approval workflow

Human Gate 1 occurs only when the declaration is ready for meaningful review.

Before approval, the UI presents a review checkpoint containing at least:

- Case identity
- Tax Year
- declaration readiness
- material unresolved warnings, if any are legally/technically permitted to remain
- result summary
- declaration/forms included

Approval semantics:

> The user confirms the content for the identified declaration version.

It does **not** authorize transmission.

The approval must be bound to a concrete declaration/version/checkpoint according to the real backend approval contract.

### 24.9 Approval invalidation and re-review

A material change after Content Approval must never silently retain a misleading “Approved” state.

UX rule:

```text
Approved declaration
+ material upstream change
→ Previous approval becomes stale/superseded
→ Review required
→ Human Gate 1 must be completed again before submission
```

Examples of potentially material changes include accepted tax values, participants, declaration fields/forms, or evidence that changes a tax decision.

A purely presentational change must not automatically invalidate approval.

The exact technical invalidation predicate must come from the durable approval/declaration contracts; UI implementation must not invent it.

### 24.10 Ready for Submission

After valid Content Approval, the Tax Year enters **Ready for Submission**.

This is a stable decision point, not an automatic transmission trigger.

The Submission page presents only methods that are supported/eligible for the declaration context.

No submission method is preselected in a way that could accidentally authorize transmission.

### 24.11 Electronic submission workflow

```text
Ready for Submission
→ Select Electronic
→ Review destination and transmission summary
→ Human Gate 2: External Transmission Approval
→ Submit
→ Receive technical outcome
```

Human Gate 2 must clearly identify:

- destination
- Case
- Tax Year
- declaration/version
- what action will occur
- that data will leave AI-Tax-Agent

Failure/cancellation before successful transmission returns to a safe non-submitted state.

A technical attempt is not presented as successful submission unless the authoritative submission contract reports success.

### 24.12 Print and personal submission workflow

```text
Ready for Submission
→ Select Print / submit personally
→ Eligibility confirmed
→ Generate Official Declaration Print Package
→ Preview
→ Download / Print
→ Sign where required
→ User posts or delivers personally
```

Generating/downloading the package does not trigger Human Gate 2 because AI-Tax-Agent is not transmitting to an external authority.

The product may separately generate a Review/Evidence Package.

User-recorded states may include:

- Print package prepared
- Printed
- Marked as sent by user

“Marked as sent” is explicitly a user assertion and not proof of Finanzamt receipt.

### 24.13 Export-only workflow

```text
Ready for Submission
→ Export only / no submission yet
→ Generate selected output
→ Remain not submitted
```

Export must not be treated as submission and must not consume External Transmission Approval.

The Case/Tax Year remains available for later submission.

### 24.14 Attention behavior

Attention is a global action inbox, not a duplicate workflow.

Each Attention item must point to the exact affected Case, Tax Year, stage/topic, and action.

Opening an item deep-links into the relevant context.

After resolution:

- the item resolves/disappears from the actionable queue when authoritative state confirms resolution;
- Activity/Audit retain the history;
- downstream readiness is recalculated by the authoritative system.

The UI must not allow a user to “dismiss” a material blocking condition merely to make the dashboard look clean.

### 24.15 Pause and system problems

`TOKEN_PAUSED` and similar execution-resource states are not tax problems.

The user-facing workflow distinguishes:

- **Tax/content attention** — user action may be required.
- **System paused** — work is temporarily not progressing.
- **System problem** — technical intervention may be required.

A pause does not erase progress or turn completed tax decisions into failures.

System diagnostics remain progressively disclosed.

### 24.16 Navigation and resumability

Leaving the application, changing device, or switching language must not change workflow meaning.

On return, the user should land on the Tax Year with:

- current overall status
- next meaningful action
- unresolved Attention count
- last meaningful activity
- safe continuation point

“Continue” is contextual. It routes to the highest-priority meaningful next action, not mechanically to the next navigation tab.

### 24.17 Desktop/mobile equivalence

The workflow semantics are identical on desktop and mobile.

Mobile may change presentation and navigation density, but not:

- available core workflow actions
- approval semantics
- evidence access
- declaration review capability
- submission safety

No critical approval or submission step may require desktop merely because the screen is smaller.

### 24.18 German/Persian workflow equivalence

Switching between `de-DE` and `fa-IR` changes language/direction, not state or meaning.

Approval wording must be semantically equivalent in both languages.

Official German declaration identities remain visible in Persian mode where needed for legal/form identity.

### 24.19 Workflow safety invariants

The UI must preserve these invariants:

1. Navigation does not equal approval.
2. Content Approval does not equal transmission authorization.
3. Export does not equal submission.
4. Print-package generation does not equal submission.
5. A submission attempt does not equal successful submission.
6. User-marked postal delivery does not equal authority receipt.
7. Material post-approval change requires re-review/re-approval according to the authoritative approval contract.
8. Blocking Issues cannot be hidden by navigation or cosmetic dismissal.
9. Paused execution does not erase completed work.
10. The UI does not create an independent tax-calculation truth separate from the Kernel/authoritative result.

### 24.20 UI-2 design status

The workflow design above is the canonical design direction derived from the approved UI-1 baseline and project security constraints.

Before implementation, contract-sensitive details must be verified read-only against the repository, especially:

- durable approval lifecycle/version binding
- exact invalidation semantics
- declaration readiness/validation contract
- submission success/failure states
- Case/Tax-Year state transitions

No implementation authorization is implied by UI-2.


## 25. Decision log — UI-2 approval

### 2026-09-29 — UI-2 Workflow Design approved by Owner

The Owner explicitly approved the UI-2 workflow design recorded in Section 24.

UI-2 is therefore an accepted design baseline for subsequent Screen Specification work.

This approval is a **design decision only**. It is not executable authority, does not grant a runtime approval, does not authorize implementation, and does not authorize external transmission.

## 26. UI-3 — Screen Specification

### 26.1 Screen architecture

The product uses three screen scopes:

1. **Workspace scope** — cross-case overview and attention.
2. **Case / Tax-Year scope** — the primary tax workflow.
3. **System / Administration scope** — settings, official-source/version information, integrations, security, and technical health.

The default experience prioritizes tax work. Infrastructure detail remains progressively disclosed.

### 26.2 Global application shell

#### Desktop

Persistent application shell:

- product/workspace identity
- primary navigation: Overview, Cases, Attention, Administration
- current user/language control
- contextual Tax-Year navigation when inside a Tax Year
- visible but non-intrusive system/attention indicators

The shell must not display raw Agent queues or Kernel internals as ordinary navigation.

#### Mobile

Core global destinations remain reachable with a compact navigation model.

Target information architecture:

- Home
- Cases
- Attention
- More

Tax-Year workflow navigation is presented contextually rather than attempting to fit every workflow stage into the global mobile navigation.

Exact visual navigation component is deferred to UI-4/UI-5, but semantic destinations are fixed.

### 26.3 Screen: Workspace Overview

**Purpose:** answer “What needs my attention and where do my tax matters stand?”

Primary content:

- active/recent Cases
- Tax-Year status
- actionable Attention summary
- next meaningful action
- recent meaningful Activity
- submission/readiness status where relevant

Primary actions:

- open Case
- create Case, when authorized by the real Case contract
- continue next meaningful action
- open Attention

Must not become a technical monitoring dashboard.

Empty state explains how to begin without exposing implementation concepts.

### 26.4 Screen: Cases

**Purpose:** browse and select tax identities/contexts.

Each Case item shows only useful summary data:

- display identity/name
- relevant participant summary
- available Tax Years
- latest Tax-Year status
- Attention indicator

Case creation/edit actions must use the real Case contract and permissions.

The UI must not silently merge Case and Tax-Year identity.

### 26.5 Screen: Case Overview

**Purpose:** show persistent Case context across years.

Content:

- Case identity
- participants
- available Tax Years
- per-year workflow/result/submission status
- relevant Case-level Attention
- permitted Case actions

Selecting a Tax Year enters the Tax-Year workflow.

### 26.6 Screen: Tax-Year Overview

**Purpose:** provide the operational home for one tax year.

Header/context:

- Case identity
- Tax Year
- overall workflow status
- Attention count
- language-independent official identifiers where relevant

Core cards/sections:

- next meaningful action
- Documents status
- Analysis status
- Issues status
- Result readiness
- Declaration readiness
- Approval status
- Submission status
- recent Activity

The “Continue” action routes according to authoritative state/readiness, not tab order.

### 26.7 Screen: Documents

**Purpose:** collect and understand source documents.

Views/filters:

- All
- Needs attention
- Missing
- Duplicates

Document row/card:

- human-readable document name/type
- source/upload date where appropriate
- processing status
- tax-topic linkage
- attention indicator

Primary actions:

- upload/add document
- open document
- resolve a document issue when applicable

Technical processing identity is hidden by default.

#### Document Detail

Sections:

- Original
- Classification
- Extracted information
- Used in
- Issues
- Provenance

The page distinguishes source content from tax conclusions.

A user can navigate from extracted information to its Evidence/Analysis use.

### 26.8 Screen: Analysis

**Purpose:** explain tax treatment by tax topic.

Topic list/cards use understandable tax domains rather than Agent names.

Each topic shows:

- user-facing status
- accepted/relevant amount where meaningful
- number of unresolved Issues
- concise explanation

#### Analysis Topic Detail

Contains:

- topic summary
- accepted items
- excluded items
- missing/incomplete items
- evidence links
- decision explanation
- relevant legal/official-source reference when available
- link to affected Result/Declaration values

Excluded items remain visible enough to explain why they were not used.

### 26.9 Screen: Issues

**Purpose:** resolve human-actionable conditions for the current Tax Year.

Filters:

- Action required
- Review required
- Missing information
- Missing evidence
- Conflict
- Approval required
- Validation problem
- System problem

Each Issue includes:

- what is wrong/needed
- why it matters
- affected stage/topic
- exact requested user action
- severity/blocking meaning
- evidence/document context
- status/history

Resolving an Issue must use an explicit domain action. Cosmetic dismissal cannot bypass a blocking condition.

### 26.10 Screen: Global Attention

**Purpose:** cross-case actionable inbox.

Each item identifies:

- Case
- Tax Year
- issue/action type
- concise requested action
- urgency/dependency where authoritative
- affected workflow location

Opening an item deep-links into the exact Tax-Year context.

Global Attention does not duplicate resolved history; resolved items remain discoverable through Activity/Audit as appropriate.

### 26.11 Screen: Result

**Purpose:** present the tax outcome without forcing the user to read declaration forms.

Primary summary:

- expected refund or payment
- result status: provisional/final-ready as authoritative
- calculation summary

Breakdown may include:

- taxable income
- calculated tax
- credits/reductions
- tax already paid
- expected refund/payment

Each material value can expose “Why?” leading to Analysis/Evidence.

For CASE-001/2024 prototype fixtures, expected refund is EUR 133.83.

Provisional values must be unmistakably different from declaration-ready values.

### 26.12 Screen: Declaration

**Purpose:** let the user review the official declaration representation.

Content hierarchy:

1. declaration readiness/validation summary
2. included official forms
3. user-friendly section summary
4. official fields/values
5. evidence/provenance links
6. technical mapping on demand

Official German form identity remains visible in both languages.

The user can navigate:

```text
Declaration field
→ Tax decision
→ Evidence
→ Source document
```

and the reverse direction.

Primary actions depend on authoritative readiness.

A declaration with blocking validation errors cannot present Content Approval as safely available.

### 26.13 Screen: Content Approval — Human Gate 1

**Purpose:** obtain explicit human confirmation of a concrete declaration version.

This is a dedicated checkpoint, not a generic modal attached to a vague “Approve” button.

Review content:

- Case
- Tax Year
- declaration/version identity
- included forms
- result summary
- unresolved warnings permitted by the authoritative contract
- statement of what is being approved
- clear statement that no external transmission is authorized

Actions:

- return to review
- approve content, only when authoritative approval request is valid
- reject/request correction where supported by the real contract

After approval, the UI displays the bound approval state/reference in user-friendly form, with technical details available progressively.

### 26.14 Screen: Submission

**Purpose:** choose what happens to an already reviewed/approved declaration.

Top section:

- declaration approval state
- submission readiness
- current submission status

Method cards:

- Electronic submission
- Print and submit personally
- Export only / submit later

Each method displays:

- availability
- reason if unavailable
- what the method does
- whether data leaves AI-Tax-Agent
- next required step

No method may imply submission merely by being selected.

### 26.15 Screen: External Transmission Approval — Human Gate 2

**Purpose:** obtain explicit authorization for one external transmission action.

Dedicated confirmation screen shows:

- destination
- Case
- Tax Year
- declaration/version
- transmission method
- data/action summary
- approval expiry where authoritative
- explicit external-data warning

Primary destructive/consequential action wording must name the action, e.g. “Authorize electronic transmission”, rather than generic “Confirm”.

Cancellation leaves the declaration not submitted.

This screen must never be reused for ordinary internal review.

### 26.16 Screen: Electronic Submission Outcome

**Purpose:** report authoritative transmission outcome.

Possible presentation states include:

- preparing
- authorization required
- submitting
- submitted successfully
- failed
- outcome uncertain / requires verification, if the backend contract can produce such a state

Success is shown only from authoritative submission evidence/receipt.

Where a receipt/reference exists, it is preserved and linked to Activity/Audit.

A failed attempt must not visually become “Submitted”.

### 26.17 Screen: Official Print Package

**Purpose:** prepare a legally appropriate paper declaration when eligible.

Content:

- eligibility/status
- official forms included
- Tax Year
- preview
- signature instructions where applicable
- print/download action
- personal submission instructions

Separate action/link:

- generate/open Review & Evidence Package

The UI must visually distinguish:

**Official Declaration Print Package** from **AI-Tax-Agent Review/Evidence Package**.

User status actions such as “Mark as sent by me” must state that this is a personal record, not confirmation of Finanzamt receipt.

### 26.18 Screen: Export

**Purpose:** obtain outputs without external submission.

Possible output categories:

- official declaration output where available
- Review/Evidence Package
- other future authorized export artifacts

Export completion leaves submission state unchanged.

### 26.19 Screen: Evidence

**Purpose:** inspect traceability.

Primary model:

```text
Source Document
→ Extracted Fact
→ Tax Decision
→ Declaration Field
```

Evidence detail includes:

- source reference
- extracted fact/value
- tax use/decision
- affected result/declaration location
- provenance
- verification/acceptance state where authoritative

Technical hashes/references are progressively disclosed.

### 26.20 Screen: Activity

**Purpose:** understandable chronological history.

Examples:

- document added
- analysis completed
- issue created/resolved
- result changed
- declaration prepared
- content approved
- print package prepared
- transmission authorized/submitted

Activity uses human-readable language and links back to affected objects.

### 26.21 Screen: Audit

**Purpose:** specialist/professional verification.

May expose:

- timestamp
- actor
- event type
- artifact/version references
- evidence references
- approval lifecycle
- acceptance/checkpoint references
- integrity/hash data

Audit is not optimized as the ordinary user's primary workflow.

### 26.22 Screen: Administration

Personal mode exposes only relevant areas.

Potential sections:

- Profile / Workspace
- Language
- Security
- Official sources / declaration versions
- Integrations
- System health
- Users & permissions when multi-user mode exists

Dangerous/system actions are separated from routine tax workflow actions.

### 26.23 Cross-screen loading, empty, error, and stale states

Every primary screen specification includes:

- loading
- empty
- ready
- needs attention
- error
- stale/superseded where applicable

A stale view must not retain an actionable approval/submission control whose authoritative context has changed.

On authority-sensitive screens, state should be revalidated before consequential action.

### 26.24 Mobile screen behavior

On mobile:

- cards replace wide summary tables where appropriate;
- critical context (Case + Tax Year) remains visible;
- long official identifiers can be copied/expanded without corrupting RTL layout;
- primary action remains reachable without hiding warnings;
- evidence lineage may use a vertical step presentation;
- declaration sections collapse progressively;
- Human Gate screens remain dedicated full screens rather than compressed dialogs.

No consequential action is made easier to trigger merely to save screen space.

### 26.25 RTL/LTR screen behavior

Persian mode mirrors structural navigation where appropriate, while data with inherent direction remains isolated.

Examples that retain controlled LTR/data formatting:

- IBAN
- Steuer-ID
- Steuernummer where required for readability
- filenames
- URLs/references
- hashes
- ERiC/official field identifiers
- numeric/monetary formatting according to locale rules

Mixed German/Persian official labels must be visually stable and selectable/copyable.

### 26.26 Screen priority for prototype

The first prototype should demonstrate the complete product logic with a focused subset rather than drawing every administration screen.

Priority prototype screens:

1. Workspace Overview
2. Tax-Year Overview
3. Documents
4. Document Detail
5. Analysis
6. Analysis Topic Detail
7. Issues / Attention
8. Result
9. Declaration
10. Human Gate 1
11. Submission
12. Human Gate 2
13. Official Print Package
14. Evidence

CASE-001/2024 is the reference data fixture.

### 26.27 UI-3 contract boundary

Screen actions that depend on executable authority, declaration readiness, submission eligibility, receipts, or approval lifecycle must be wired to the real backend contracts during implementation.

The Screen Specification defines presentation/interaction semantics; it does not create authority.

No implementation authorization is implied by UI-3.
