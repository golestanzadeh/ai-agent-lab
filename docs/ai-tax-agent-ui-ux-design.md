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


## 27. UI-4 — Visual System

### 27.1 Visual character

The product should communicate:

- trust
- calm
- precision
- explainability
- administrative professionalism without bureaucratic visual overload

The interface should not imitate ELSTER visually. Official form identity is preserved where needed, but AI-Tax-Agent remains a distinct, more understandable product layer.

Avoid “AI theater”: glowing agent avatars, animated neural motifs, chat bubbles as the universal interface, or decorative automation indicators that compete with tax information.

### 27.2 Design-system principles

1. **Information before decoration.**
2. **Status must not depend on color alone.**
3. **Consequential actions must be visually distinct from routine actions.**
4. **Official identity and explanatory UI must be distinguishable.**
5. **Progressive disclosure controls technical density.**
6. **German and Persian receive equal design quality.**
7. **Desktop density may increase without changing mobile semantics.**
8. **Accessibility is structural, not a later skin.**

### 27.3 Typography

The implementation must choose a font stack with strong, legible German/Latin and Persian/Arabic-script support.

Requirements:

- clear distinction among headings, labels, values, helper text, and technical identifiers;
- stable numerals and punctuation in mixed-direction content;
- no font whose Persian glyph quality is visibly inferior to its Latin rendering;
- sufficient weight range without relying on ultra-light text;
- technical identifiers may use a suitable monospace fallback when beneficial.

Typography roles:

- Display / page title
- Section heading
- Card heading
- Body
- Label
- Helper/secondary
- Numeric/result emphasis
- Technical/reference

Exact font family is an implementation/design-selection decision for prototype validation, not hard-coded by this specification.

### 27.4 Type hierarchy

Large typography is reserved for:

- page identity
- expected refund/payment
- major approval/submission state

Ordinary tax values should not all compete for visual dominance.

Result values use tabular/consistent numeric treatment where practical.

Long Persian labels must be allowed to wrap naturally; German compound nouns must not force unusable fixed-width controls.

### 27.5 Spacing and layout

Use a consistent spacing scale rather than page-specific arbitrary gaps.

Desktop content uses a readable maximum width for explanatory/review screens, while document/evidence/audit views may use wider work areas.

Cards group meaningful concepts, not every field.

Avoid excessive nested cards. A tax application can become a filing cabinet made of rounded rectangles remarkably quickly.

Mobile uses one primary reading column, with contextual details progressively expanded.

### 27.6 Surface hierarchy

Recommended semantic surface levels:

1. App background
2. Primary content surface
3. Grouped/secondary surface
4. Elevated transient surface
5. Consequential confirmation surface

Elevation/shadow is restrained. Borders, spacing, and typography carry most hierarchy.

### 27.7 Color semantics

Exact palette values are selected during prototype work, but semantic roles are fixed:

- Primary action / navigation
- Neutral/informational
- Success / complete / verified
- Attention / warning / incomplete
- Critical / blocking / failed
- Approval-required
- Paused/system-neutral
- Excluded/not-applicable

Rules:

- color never carries meaning alone;
- status includes icon/text/label;
- “Approval required” must not look identical to “Error”;
- “Paused” must not look like tax failure;
- excluded/not-applicable use quiet neutral treatment rather than alarming colors;
- successful submission is visually distinct from merely “ready to submit”.

### 27.8 Status component

A shared Status component should support:

- icon
- localized label
- semantic tone
- optional explanation
- optional technical status reveal

The same semantic state must render consistently across Overview, Documents, Analysis, Declaration, and Submission.

### 27.9 Buttons and action hierarchy

Action levels:

- **Primary** — one clear next action within a context
- **Secondary** — safe alternative/navigation action
- **Tertiary/text** — low-emphasis supporting action
- **Consequential** — approval/transmission/destructive domain action

A page should generally avoid multiple competing primary actions.

Consequential actions use explicit verbs.

Bad:
- Confirm
- OK
- Continue

Preferred:
- Approve declaration content
- Authorize electronic transmission
- Mark as sent by me

The exact localized wording is finalized in the terminology/content pass.

### 27.10 Human Gate visual pattern

Human Gate screens use a dedicated review layout.

They contain:

- clear gate identity
- scope/context
- what the user is authorizing
- what the user is **not** authorizing
- material warnings
- bound artifact/version information at an understandable level
- explicit action

Human Gate 1 and Human Gate 2 use related visual structure but different semantic emphasis.

Human Gate 2 must visually emphasize the external destination/data-leaving boundary.

No pre-checked authorization control.

### 27.11 Forms

Form design requirements:

- persistent labels, not placeholder-only fields;
- helper text only when it adds meaning;
- validation next to the affected field and summarized when blocking;
- locale-aware date/number input;
- clear optional/required semantics;
- safe handling of official identifiers;
- preserve entered data on recoverable errors.

RTL changes layout direction but not the semantic order required by an official identifier.

### 27.12 Tables and lists

Desktop tables are used when comparison across columns matters.

Mobile converts tables to cards/stacked rows unless horizontal comparison is essential.

Audit and evidence tables may remain horizontally scrollable when preserving exact technical columns is more useful than destructive reflow.

Sticky headers may be used for long structured views.

### 27.13 Cards

Cards are appropriate for:

- Case summaries
- Tax-Year stages
- tax topics
- submission methods
- result summary
- Attention items

Cards are not used merely to put a border around every paragraph.

Clickable cards must have clear focus/hover/pressed states and not hide unrelated actions inside ambiguous hit areas.

### 27.14 Icons

Icons support labels; they do not replace critical text.

Directional icons mirror in RTL only when their meaning is directional.

Icons representing intrinsic objects/actions do not mirror merely because the language changes.

Official/legal meaning must never depend on a culturally ambiguous icon.

### 27.15 Evidence lineage visualization

Desktop may present lineage horizontally when space permits:

```text
Document → Fact → Decision → Declaration
```

Mobile presents the same lineage vertically.

Each node is navigable where permitted.

The visual system distinguishes source evidence from system decisions and official declaration output.

### 27.16 Result presentation

Expected refund/payment is the primary numeric focal point.

The UI must pair the amount with:

- semantic label
- readiness/provisional state
- tax year
- explanation access

Positive visual styling must not imply legal certainty when the result is provisional.

### 27.17 Official declaration presentation

Official form sections use a restrained “official document” treatment distinct from ordinary product cards.

The product may show:

- official German form name
- translated/explanatory Persian label
- section/field identity
- populated value
- provenance link

It must not visually forge a government-issued receipt or imply that an AI-generated review sheet is an official Finanzamt document.

### 27.18 Document viewer

Document Detail should support a split-view pattern on sufficiently large desktop screens:

- source preview
- extracted/used information

On mobile, source and extracted information become switchable/stacked views.

Highlighted extraction must not alter the original artifact.

### 27.19 Empty states

Empty states explain the next useful action.

They do not use celebratory illustrations in contexts where “nothing here” may actually mean missing tax information.

Examples:

- No documents yet → explain upload.
- No Attention items → calm confirmation that no action is currently required.
- No submission yet → explain readiness rather than treating it as failure.

### 27.20 Loading and progress

Use determinate progress only when the backend provides meaningful progress.

Otherwise use honest indeterminate processing state.

Do not fabricate percentage completion for Agent work.

Long-running processing allows the user to leave the screen safely and return later.

### 27.21 Error design

Errors answer:

1. What happened?
2. Did my data/action persist?
3. What can I do now?
4. Is this a tax/content problem or a system problem?

Technical diagnostics are expandable/copyable but not the first thing shown to ordinary users.

### 27.22 Accessibility baseline

Target accessible interaction from the start:

- keyboard-operable desktop controls
- visible focus states
- semantic headings/landmarks
- meaningful control names
- adequate contrast
- non-color status cues
- touch targets suitable for mobile
- screen-reader-friendly status changes
- no critical information available only on hover
- zoom/reflow resilience
- reduced-motion-safe behavior

Formal implementation conformance target should be aligned with current applicable accessibility requirements before production release.

### 27.23 Motion

Motion is functional and restrained:

- navigation transition
- expand/collapse
- state update
- progress indication

No decorative motion around tax results, approvals, or submission.

Consequential state changes favor clarity over animation.

### 27.24 Responsive breakpoints

Breakpoints are implementation tokens rather than business logic.

The design responds by available space, preserving semantic hierarchy.

Typical transformations:

- sidebar → compact mobile navigation
- multi-column dashboard → single column
- split document viewer → stacked/toggle
- horizontal evidence lineage → vertical lineage
- table → card list where comparison is not essential

### 27.25 Localization resilience

Components are designed against realistic long German strings and Persian RTL content from the beginning.

No critical button has a fixed width based on English-length assumptions.

Text truncation is avoided for legal/approval meaning. If truncation is unavoidable in dense lists, full text must be readily accessible.

### 27.26 Visual prototype direction

The first prototype should use a **light, neutral, professional interface** with strong content hierarchy and restrained accent use.

Dark mode is not required for the first prototype and must not delay validation of core tax workflows.

Prototype should first validate:

- comprehension
- workflow
- trust
- bilingual behavior
- approval safety
- mobile equivalence

before aesthetic expansion.

### 27.27 UI-4 status

This Visual System defines semantic design rules. Exact visual tokens such as final font family, color values, radii, spacing constants, and breakpoints will be selected/tested during prototype construction and then frozen into the implementation specification.

No implementation authorization is implied by UI-4.


## 28. UI-5 — Prototype Findings and Canonical Interaction Rules

### 28.1 Prototype scope

The conceptual prototype exercised the end-to-end experience across:

- Workspace / Cases
- Tax-Year Overview
- Documents and Document Detail
- Analysis and topic detail
- Issues / Attention
- Result
- Declaration
- Human Gate 1
- Submission method selection
- Human Gate 2
- Print / Export
- Evidence / Activity / Audit
- Desktop and mobile
- German LTR and Persian RTL

CASE-001 / 2024 remains the reference fixture. Prototype-only visual examples must not be interpreted as new tax facts.

### 28.2 Single-language runtime rule

The production UI displays one selected interface language at a time.

Prototype boards may show German and Persian together to validate terminology/layout, but production controls must not routinely duplicate every label in both languages.

In Persian mode:

- approved Persian UI text is primary;
- official German tax/form identity remains visible where legally or semantically important;
- technical/data identifiers preserve their natural direction.

### 28.3 Prototype-data discipline

Mockups must not accidentally introduce new personal facts, tax values, employers, addresses, dates, deductions, or declaration outcomes into the canonical case.

Three data classes are permitted in design artifacts:

1. accepted frozen CASE-001 fixture values;
2. clearly marked synthetic/demo values;
3. neutral placeholders.

Synthetic values are never evidence and never become project truth merely because they appeared in a mockup.

### 28.4 Extraction confidence is not tax confidence

Any extraction/OCR confidence indicator refers only to extraction quality.

The UI must distinguish:

- source/document quality;
- extraction confidence;
- classification state;
- evidence sufficiency;
- tax decision state;
- independent verification/acceptance state.

A percentage produced by extraction must never be presented as “confidence that the tax treatment is correct.”

### 28.5 Context persistence

Case and Tax Year context remain visually persistent across deep workflow screens.

The user should not need to infer which declaration/year is being reviewed from browser history or a hidden state.

On mobile, compact context may replace full breadcrumbs but must preserve the same identity.

### 28.6 Review-before-authority pattern

Consequential actions follow:

```text
Inspect
→ Understand scope
→ Review consequences
→ Explicit human action
→ Authoritative backend transition
→ Confirm resulting state
```

UI optimism is prohibited: the interface does not switch to “approved” or “submitted” merely because a button was pressed.

### 28.7 Stale approval state

When authoritative context changes after approval, the UI must represent the approval as stale/superseded rather than silently retaining a green approved state.

Presentation pattern:

- previous approval remains visible as history;
- current declaration clearly says review/approval is required again;
- submission actions requiring current approval remain unavailable;
- user can inspect why re-review is required.

Exact invalidation is backend-owned.

### 28.8 Validation failure

Validation problems appear at both:

- the affected declaration field/section where useful;
- Issues/Attention when human action is required.

Blocking validation prevents Human Gate 1 readiness.

The user receives a route back to the exact affected source/topic/field.

### 28.9 Submission failure

Submission has explicit attempt and outcome states.

A failed or uncertain attempt:

- does not become Submitted;
- preserves the attempt in Activity/Audit;
- shows whether retry is safe/allowed according to backend state;
- does not reuse/assume approval authority unless the authoritative approval/submission contract permits it.

### 28.10 System pause

Execution-resource pause is visually separated from tax-content failure.

The user sees:

- work is paused;
- existing completed work remains intact;
- whether any user action is required;
- last meaningful completed state.

Raw token-budget mechanics need not dominate ordinary UX.

### 28.11 Evidence / Activity / Audit triad

Prototype validation confirms three distinct presentations are useful.

**Evidence** answers:
“Where did this value/decision come from?”

**Activity** answers:
“What happened in this Case?”

**Audit** answers:
“What exact authoritative event/artifact/actor/version proves it?”

These views may cross-link but are not merged.

### 28.12 Evidence interaction pattern

Evidence lineage is navigable in both directions.

Desktop:
```text
Document → Fact → Decision → Declaration Field
```

Mobile:
vertical step chain with expandable detail.

Each node visually indicates its type so a source fact cannot be confused with a tax decision.

### 28.13 Document-detail interaction

Desktop prefers split view:

- original document
- extracted/classified information

Mobile uses stacked or switched panels.

Editing extracted information is an explicit action and must preserve provenance/history rather than visually rewriting the original source.

### 28.14 Result interaction

The expected refund/payment is prominent but always paired with its readiness state.

Prototype hierarchy:

1. expected refund/payment;
2. provisional/final-ready status;
3. main contributing items;
4. “Why?” / detailed calculation;
5. links into Analysis/Evidence.

The UI must not turn a favorable provisional amount into celebratory certainty.

### 28.15 Declaration interaction

Declaration supports two levels:

- understandable summary/form navigation;
- official field-level review.

Official form names remain stable.

Technical mappings are optional detail, not the default reading experience.

### 28.16 Submission-choice interaction

Submission methods are peer choices after valid Content Approval:

- Electronic
- Print and submit personally
- Export only

Each card states:

- availability;
- consequence;
- whether external transmission occurs;
- next gate/action.

Selecting a method does not itself perform the method.

### 28.17 Mobile Human Gates

On mobile, Human Gate 1 and Human Gate 2 are full-screen review steps.

The consequential action is placed after the review content, not floating above unseen warnings.

Critical scope/destination information remains visible near the action.

### 28.18 Prototype accessibility findings

Prototype implementation must avoid:

- tiny status text;
- icon-only critical actions;
- low-contrast pale status chips;
- fixed-width bilingual buttons;
- horizontal-only evidence relationships;
- hover-dependent explanations.

Long German and Persian labels are treated as normal content, not edge cases.

### 28.19 UI-5 acceptance baseline

The conceptual prototype validates that the accepted IA and workflow can be represented coherently across desktop/mobile and DE/FA without exposing infrastructure as the primary UX.

UI-5 is considered design-complete when these interaction rules are treated as canonical and the remaining contract-dependent gaps are explicitly handed to UI-6.

No production UI code is authorized by UI-5.

## 29. UI-6 — Implementation Specification Preparation

### 29.1 Purpose

UI-6 translates the accepted design into an implementation-ready contract for Work/Codex without authorizing implementation.

It must identify:

- routes/screens;
- reusable components;
- presentation state;
- backend-owned state;
- required API/domain bindings;
- localization resources;
- accessibility requirements;
- responsive behavior;
- acceptance tests;
- security invariants.

### 29.2 Proposed route model

Conceptual routes:

```text
/
 /cases
 /cases/:caseId
 /cases/:caseId/:taxYear
 /cases/:caseId/:taxYear/documents
 /cases/:caseId/:taxYear/documents/:documentId
 /cases/:caseId/:taxYear/analysis
 /cases/:caseId/:taxYear/analysis/:topicId
 /cases/:caseId/:taxYear/issues
 /cases/:caseId/:taxYear/result
 /cases/:caseId/:taxYear/declaration
 /cases/:caseId/:taxYear/approval/content
 /cases/:caseId/:taxYear/submission
 /cases/:caseId/:taxYear/submission/authorize
 /cases/:caseId/:taxYear/evidence
 /cases/:caseId/:taxYear/activity
 /cases/:caseId/:taxYear/audit
 /attention
 /administration
```

Final route names are implementation details, but Case/Tax-Year scoping is mandatory.

### 29.3 Core reusable components

Implementation should prefer a small stable component vocabulary:

- AppShell
- WorkspaceSwitcher
- CaseContext
- TaxYearContext
- WorkflowProgress
- Status
- AttentionBadge
- NextAction
- CaseCard
- TaxYearCard
- DocumentList / DocumentCard
- DocumentViewer
- ExtractedFact
- TaxTopicCard
- IssueCard
- ResultSummary
- CalculationBreakdown
- OfficialFormNavigator
- DeclarationField
- EvidenceLineage
- ApprovalReview
- SubmissionMethodCard
- ExternalDestinationSummary
- ActivityTimeline
- AuditTable
- EmptyState
- ErrorState
- StaleState

Components must not embed independent tax/business logic that competes with backend authority.

### 29.4 State ownership boundary

Frontend owns:

- local navigation;
- display preferences;
- language/direction;
- transient UI expansion/collapse;
- unsaved form interaction where explicitly supported.

Authoritative backend/domain owns:

- Case identity/state;
- Tax-Year state;
- document/evidence identity;
- tax decisions;
- result values;
- declaration readiness/version;
- approval lifecycle/authority;
- submission eligibility;
- transmission outcome/receipt;
- audit truth.

The frontend may derive presentation labels but not authoritative domain facts.

### 29.5 Authority-sensitive action rule

Before enabling/executing approval or submission actions, implementation must consume current authoritative state.

Cached visual state is insufficient authority.

After the action, the UI renders the returned/reloaded authoritative result rather than assuming success.

### 29.6 Localization implementation contract

All user-facing product strings are localization resources.

Do not hard-code German/Persian strings into business logic.

Localization keys represent semantic concepts, not word-by-word fragments.

Official form names/identifiers may come from authoritative declaration metadata and are not casually translated.

Locale selection is per-user.

Direction is applied at application/layout level with isolated bidi handling for identifiers and mixed-direction fields.

### 29.7 Terminology artifact required

Before production implementation is accepted, create a versioned terminology resource containing the canonical German/Persian tax vocabulary described in UI-1.

It should support:

- canonical concept key;
- DE official term;
- FA approved translation;
- short labels;
- explanatory labels;
- official-name preservation rule.

### 29.8 Responsive implementation contract

Responsive behavior is component-defined, not a separate reduced mobile application.

Core feature parity is mandatory.

Automated/UI acceptance should cover at minimum:

- desktop DE;
- desktop FA/RTL;
- mobile DE;
- mobile FA/RTL.

### 29.9 Accessibility implementation contract

Implementation acceptance must include automated and manual accessibility checks for:

- keyboard navigation;
- focus order;
- focus visibility;
- semantic landmarks/headings;
- form labels/errors;
- status announcements;
- contrast;
- zoom/reflow;
- touch targets;
- screen-reader naming;
- RTL navigation/focus coherence.

### 29.10 Security acceptance cases

UI acceptance must prove at minimum:

1. Human Gate 1 cannot be confused with external transmission.
2. Human Gate 2 identifies destination and exact context.
3. stale approval cannot authorize submission.
4. cross-case state is not retained.
5. changing Case/Tax Year clears incompatible presentation state.
6. export/print cannot display Submitted.
7. failed submission cannot display Submitted.
8. backend denial cannot be overridden by client state.
9. technical review/export data cannot become executable approval authority.
10. synthetic/demo data cannot enter real case authority.

### 29.11 Contract gaps to verify before coding

Read-only repository verification is required for:

- current Case/Tax-Year DTO/domain shape;
- document/evidence references;
- issue representation;
- result representation;
- declaration/version/readiness contract;
- durable approval API/domain interface;
- submission/receipt interface if implemented;
- audit/activity event contracts;
- permissions.

If a required production contract does not yet exist, UI-6 must mark it as a backend dependency rather than inventing it inside the frontend.

### 29.12 Implementation authorization boundary

Completion of UI-6 documentation does not itself authorize code changes.

Actual UI implementation requires a separate explicit Owner authorization and should be executed through the project’s controlled Work/Kernel/Codex development path.

