# Decision Log

Use this file for decisions that materially affect project scope, architecture, safety, or workflow.

## D-001 — Repository as source of truth

**Status:** accepted

**Decision:** GitHub is the durable source of truth. Chat is a working interface, not the canonical project memory.

**Reason:** The project is long-running and must survive large chat histories, context loss, and model mistakes.

## D-002 — Domain remains open during Phase 0

**Status:** superseded by D-006

**Decision:** During Phase 0, the domain was intentionally left open while the project structure was established.

**Reason:** The initial architecture should not be forced by an untested domain assumption.

## D-003 — Anti-hallucination project memory

**Status:** accepted

**Decision:** Verified state, decisions, and planned future files must be recorded in the repository. Unknown information must not be reconstructed as fact.

**Reason:** The user explicitly requires protection against later answers based on model memory or speculation.

## D-004 — Agent count is not an objective

**Status:** accepted

**Decision:** Use the minimum number of agents necessary to solve demonstrated coordination problems.

**Reason:** Multi-agent systems add complexity, latency, cost, and failure modes. More agents do not automatically mean a better system.

## D-005 — AGENTS.md is a map, not the encyclopedia

**Status:** accepted

**Decision:** Keep `AGENTS.md` concise and place detailed project knowledge in structured repository documents.

**Reason:** OpenAI's Codex guidance emphasizes concise agent instructions and structured repository knowledge rather than a giant instruction file.

## D-006 — German tax assistance is the primary project domain

**Status:** accepted

**Decision:** The AI Agent Lab will build a Germany-focused tax-assistance system for natural persons and legal entities and carry this domain through the project unless later evidence justifies a formally recorded change.

**Final-goal scope:** The system should ultimately support defined German tax workflows from user-supplied documents/information through extraction, reconciliation, current-law research, calculations, analysis, challenge, audit, final document preparation, and controlled electronic submission where an official and lawful technical route exists.

**Quality target:** For supported workflows, the engineering target is performance comparable to a senior tax expert. This must be demonstrated through measurable evaluation rather than asserted. The project must not claim legal/tax perfection merely because an LLM produced a plausible result.

**Current-law requirement:** Applicable German tax rules are a live dependency. Material tax/legal conclusions must be checked against authoritative sources available at execution time, with tax-year/effective-date awareness, source provenance, and a fail-closed behavior when current applicability cannot be verified.

**Submission requirement:** Final documents should be print-ready and, where technically and legally supported, electronically submittable through an official channel. Consequential submission requires explicit authorization/approval and must be fully auditable.

**Reason:** This scope creates a demanding real-world learning environment covering document understanding, retrieval/research, evidence grounding, structured reasoning, calculations, specialist delegation, conflict resolution, validation, current-information handling, adversarial testing, auditability, and human-in-the-loop control.

## D-007 — Final-goal breadth, first-workflow narrowness

**Status:** accepted

**Decision:** The final system may grow into a broad German tax platform, but the first executable workflow must be narrow, concrete, and objectively testable. Phase 10 will select the first workflow, taxpayer profile, tax year, document set, output forms, and submission route.

**Reason:** Attempting all personal and corporate German tax matters in the first implementation would make evaluation, correctness, and failure analysis meaningless. Scope must expand only after evidence supports it.

## D-008 — Tax optimization is a golden objective

**Status:** accepted

**Decision:** The system's cross-cutting optimization objective is **Maximize Legally Achievable Tax Benefit**: minimize the legally payable tax amount and maximize the legally recoverable/refundable amount from the tax authority.

This objective must be considered throughout the entire case lifecycle, not only during final reporting. New documents, facts, research results, legal changes, calculations, assumptions, and decisions must be continuously evaluated for their potential effect on the user's lawful tax outcome.

**Primary architectural implication:** A dedicated **Tax Optimization Supervisor** is a primary agent role candidate. Its responsibility is to monitor the case and the work of other agents/components for missed or newly available lawful tax benefits. When it identifies a material opportunity or concern, it may challenge affected work, request additional evidence/research, trigger recalculation or alternative-scenario analysis, and feed the result back into the relevant workflow stage.

**Evidence and legality constraint:** Every optimization recommendation must be grounded in applicable law and authoritative evidence, account for the relevant tax year/effective date, identify required supporting documentation, and quantify financial impact where calculable. The objective does not permit fabrication, concealment, unsupported claims, unlawful tax avoidance, or omission of material facts.

**Evaluation implication:** The project must measure not only tax-result correctness but also optimization completeness, missed-opportunity rate, false-positive rate, and the financial effect of valid optimization opportunities for supported workflows.

**Reason:** Tax optimization is a core value delivered to the user and therefore must shape requirements, workflow decomposition, architecture, agent contracts, evaluation, safety, and definition of done rather than being treated as an optional feature.

## D-009 — Tax cases require an explicit party and household model

**Status:** accepted

**Decision:** Every natural-person tax case must establish a tax-year-specific **Case Party / Household Context** before substantive calculations are treated as reliable. The model must identify the primary taxpayer, spouse/partner where relevant, children and other material persons, their relationships, relevant family-status changes, and person-specific versus shared household facts.

For married/registered partners, the system must capture each spouse's relevant Steuerklasse/ELStAM independently and explicitly represent the legally relevant assessment mode (Zusammenveranlagung, Einzelveranlagung, or pending verification). Tax class must be stored as wage-tax/ELStAM evidence and must not be confused with the final income-tax assessment calculation.

Every material document and extracted fact must be attributable to the correct person, multiple persons, or shared household context using evidence. Filename-based attribution alone is prohibited. The model must support many-to-many relationships and temporal validity because documents and facts may span multiple people and may change during the tax year.

If party identity, ownership, family status, assessment mode, or economic burden is materially ambiguous or contradictory, the affected workflow must stop or escalate rather than silently assigning the fact.

**Reason:** German income-tax workflows for families depend on the distinction between individual and joint assessment, spouse-specific facts, children, and person-specific economic burden. Official ELSTER guidance also distinguishes the relevant assessment modes and child information. Treating the case as a single anonymous taxpayer would create systematic attribution and calculation errors.

## D-010 — Case-first, multi-year architecture and mandatory case isolation

**Status:** accepted

**Decision:** The system must be designed from the beginning as a long-lived multi-case and multi-year platform. CASE-001 is the first instance of a general Case Model, not a special architecture.

Each concrete tax case has a mandatory `case_id` and an explicit `tax_period`. Each taxpayer or legal entity has a persistent `person_id` or `entity_id` that can map to multiple cases across years.

Cases are organized by tax period for human discoverability, while the Case Registry is authoritative for identity and resolution. The target conceptual Drive structure is:

```text
AI-Tax-Agent/
├── Tax_Years/
│   ├── 2020/Cases/
│   ├── 2021/Cases/
│   ├── ...
│   ├── 2025/Cases/
│   └── 2026/Cases/
├── Case_Registry/
├── Person_Registry/
├── Entity_Registry/
├── Templates/
└── System/
```

A case remains internally structured as `Documents`, `Evidence`, `Tax_Categories`, `Calculations`, `Reports`, and `Audit`.

**Mandatory isolation rule:** No Agent, pipeline component, model, or data-access tool may access tax-case data without a validated `case_id`. The resolver must map the requested identity/period to an exact case scope, and the connector must enforce that scope deterministically. Generic unscoped Drive searches for case data are prohibited.

An operation involving `CASE-A` must never inspect or use documents from `CASE-B`, even if both cases belong to the same year or person. Cross-case contamination is a security and correctness failure.

Cross-year summaries are controlled multi-case operations: resolve cases through the persistent person/entity ID and registry, then access each case separately. They must not scan all Drive documents and infer ownership.

Every processing execution receives a `run_id` associated with one `case_id` at the processing boundary. Isolation, cross-case contamination, multi-year retrieval, and idempotency must be tested automatically.

**Reason:** The system is intended to mature from an educational first case into long-term use for the user and potentially other people/entities across many years. Retrofitting case/year/identity isolation after CASE-001 would create avoidable migration, security, and correctness risks.

## D-011 — Durable audit and observability boundary

**Status:** accepted

**Decision:** Auditability is a first-class deterministic boundary separate from Case State, source documents, evidence, and LLM context. Every audit event must be bound to exactly one `case_id`; execution events are additionally bound to exactly one `run_id`.

The foundational audit event records event identity, actor, operation, event type, outcome, time, references to inputs/evidence/decisions/outputs, errors, approvals, and bounded diagnostic metadata. Audit records are append-only and reference-oriented so raw tax documents, secrets, and unnecessary personal data are not copied into the audit stream.

The first implementation is an in-memory append-only `AuditStore`. Durable database selection, distributed ordering, cryptographic tamper evidence, retention policy, and telemetry integration remain separate later layers. A durable backend must preserve the event contract and case/run isolation invariants.

Unknown cases, cross-case runs, malformed actor/operation data, and other scope violations fail closed. Audit reconstruction must not depend on LLM conversation history.

**Reason:** The project constitution requires traceability and auditability, while the Case State model explicitly deferred the durable audit store. Establishing the contract before selecting infrastructure prevents observability from becoming an accidental, unscoped logging system.

## D-012 — Isolation tests are a release gate before live storage access

**Status:** accepted

**Decision:** Cross-case isolation and contamination tests are a mandatory acceptance gate before implementing or using a live Google Drive storage adapter for tax-case data.

The acceptance suite must exercise the deterministic chain across Case Registry, Case State/Run ID, Case-Scoped Storage Resolver, and Audit Boundary. It must prove that one case cannot resolve, access, or retrieve another case's storage, run, state, or audit events, including when cases share the same persistent owner.

The suite must also verify fail-closed behavior for unknown cases and invalid shared storage roots. A passing suite does not by itself establish Google Drive isolation, authentication/authorization correctness, durable-store isolation, or production security. Those require separate tests at their respective layers.

**Verification:** `tests/unit/test_case_isolation.py` completed with **10 passed tests in 0.14s**.

**Reason:** Case isolation is a foundational security and correctness property. Connecting real storage before proving the deterministic boundary would make later failures harder to distinguish and could expose unrelated case data.

## D-013 — Six-stage Google Drive storage rollout

**Status:** accepted; Stage 6 complete

**Decision:** Google Drive access will be introduced through six explicit stages: (1) provider-neutral Storage Adapter Contract, (2) integration with the verified Case-Scoped Resolver, (3) metadata-only Google Drive adapter, (4) deterministic descendant/scope enforcement, (5) adapter and scope tests including live integration verification, and (6) documentation, verification evidence, and the release gate for CASE-001 inventory.

The stages form one controlled work package. Independent implementation work may proceed in parallel where dependencies permit, but live CASE-001 document access remains blocked until the scope boundary and adapter tests are verified and the live integration evidence is recorded.

The initial Google Drive implementation is metadata-only because the currently verified OAuth capability is metadata-read access. No PDF/content extraction, OCR, tax research, calculations, migration, or electronic filing is part of this rollout.

The adapter must not expose a generic Drive-wide list/search operation. Explicit object access must verify that the object is a descendant of the exact root resolved for the requested `case_id`. Ambiguous ancestry, unrelated objects, trashed objects, unknown cases, and invalid provider scopes fail closed.

**Verification evidence:** The adapter unit suite completed with **8 passed tests in 0.25s**. The required live Google Drive scope-isolation harness was then executed against two isolated test-only Drive roots and completed with the exact result **1 passed in 4.55s**.

**Gate result:** The defined Stage 5 unit and live scope tests passed. Stage 6 documentation and verification evidence have been recorded. The release gate for a metadata-only CASE-001 `Documents` inventory is therefore open. This does not verify CASE-001 document processing, PDF extraction, tax calculations, production authorization, durable storage security, or electronic filing.

**Reason:** Storage is the first physical boundary where a software defect could expose another taxpayer's documents. Making the six stages explicit prevents convenience APIs or premature live access from bypassing the deterministic isolation architecture.
