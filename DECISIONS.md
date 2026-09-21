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

**Reason:** This scope creates a demanding real-world learning environment covering document understanding, retrieval/research, structured reasoning, calculations, specialist delegation, conflict resolution, validation, current-information handling, adversarial testing, auditability, and human-in-the-loop control.

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

## D-014 — Document Identity is separate from source location and evidence snapshots

**Status:** accepted as design baseline

**Decision:** Document Identity will use a case-scoped logical `document_id` separate from filename, provider object ID, inventory evidence ID, and derived artifacts.

The initial identity chain is:

```text
case_id + provider + source_object_id
                ↓
         logical document_id
                ↓
       source observations
                ↓
   derived versions / evidence
```

A repeated observation of the same source object within the same case resolves to the existing logical document. A different object with the same filename remains a separate document. A renamed object with the same provider object ID remains the same logical document. Cross-provider migration requires an explicit audited link and must not be auto-merged. Identical content in different source objects does not collapse their source identities.

The initial implementation is metadata-only. Content fingerprints may be added only after controlled document-content access is separately designed and verified.

Document Identity must remain downstream of the mandatory case-isolation boundary. It does not determine tax relevance, party attribution, tax category, deductibility, legal qualification, or final calculations.

Ambiguous identity must fail closed into an explicit unresolved state rather than being guessed. Source documents remain immutable.

**Reason:** Filename and provider location are operational attributes, while evidence and derived representations require a stable logical identity and historical provenance. Separating these concepts now prevents later OCR, extraction, migration, and evidence layers from coupling themselves to a storage provider or a mutable filename.

## D-015 — CASE-001 migration validation must be anchored to Document Identity and Inventory Evidence

**Status:** accepted

**Decision:** CASE-001 migration compatibility validation must use the existing Document Identity registry as the authoritative source for logical document identity and may use a verified Inventory Evidence snapshot as an exact preflight manifest boundary.

When Document Identity is connected, every migration mapping must resolve to an existing logical document for the same `case_id`, and its provider, source object ID, and source scope must exactly match the identity record. A migration mapping must never invent a logical `document_id`.

When Inventory Evidence is supplied, migration mappings must match the evidence snapshot exactly for source object sequence and logical document sequence. Evidence must belong to the same case and source scope.

The migration layer remains non-mutating. No Drive copy, move, rename, delete, or overwrite operation is introduced by this decision. Physical execution remains a separate consequential workflow requiring authorization, verification, rollback handling, and audit.

**Verification requirement:** The CASE-001 migration test suite must cover the original structural checks plus successful identity/evidence linkage and fail-closed behavior for unknown or mismatched identity/evidence data.

**Reason:** A migration plan is dangerous if it can assert an identity that the system has never observed or silently omit an observed source document. Anchoring migration to the two existing deterministic records creates a stronger preflight boundary without prematurely introducing physical storage mutation.

## D-016 — CASE-001 migration manifests are generated from observed inventory and stable identity

**Status:** accepted

**Decision:** The first CASE-001 migration manifest must be generated deterministically from a case-scoped `DocumentInventory` and the existing `DocumentIdentityRegistry`, rather than being manually authored from filenames or remembered document IDs.

The generator must:

- require `CASE-001` and tax period 2024;
- accept only an explicitly supplied source provider and source scope;
- create one mapping for each non-folder inventory item;
- resolve the logical `document_id` from the existing Document Identity registry using the same case, provider, and source object ID;
- reject inventory documents without a known logical identity;
- reject identities whose source scope differs from the supplied source scope;
- reject inactive logical documents;
- optionally bind the manifest to a matching Inventory Evidence record;
- validate the resulting manifest through the existing CASE-001 migration compatibility boundary;
- perform no Drive mutation and store no private Drive object IDs in repository documentation.

The manifest is an execution/preflight artifact, not permission to mutate storage. Physical migration remains blocked until separate preflight, human approval, execution, rollback, and post-migration verification controls exist.

**Reason:** The live CASE-001 inventory has established the actual source population, while Document Identity establishes stable logical identities. Generating the manifest from those deterministic records eliminates filename-based guessing and makes the migration boundary reproducible and auditable.

## D-017 — Human Approval Gate for Physical Migration

**Status:** accepted

**Decision:** Physical Migration must be preceded by a deterministic, case/run-scoped Human Approval Gate. Approval is an immutable authorization record bound exactly to the `case_id`, `run_id`, manifest identity/version, successful preflight identity/result, intended operation, actor/approver, timestamp, and authorization reference. Physical migration execution must fail closed unless all execution-context fields exactly match the approved artifact and the approval is otherwise valid.

The Approval Gate is independent of Manifest and Preflight. Manifest generation does not grant approval, and a successful Preflight does not grant approval. The Approval Gate itself performs no Drive mutation and creates no Manifest or Preflight artifact.

The approval lifecycle is `PENDING → APPROVED → CONSUMED`, with terminal/revocation paths `REJECTED`, `REVOKED`, and `EXPIRED` as applicable. `CONSUMED` is strictly one-time: an approval may authorize at most one physical migration execution. Consumption must be atomic so concurrent or sequential execution attempts cannot both use the same approval. A successful atomic consumption must be audit-linked.

The approval contract must be deterministic and fail closed. Validation must not depend on an LLM or model judgment. Missing, malformed, mismatched, revoked, expired, or otherwise invalid approval data must prevent physical migration. `intended_operation` is a controlled deterministic operation value, initially `PHYSICAL_MIGRATION`, rather than free-form authorization text.

Approval creation, approval state transitions, atomic consumption, and subsequent execution events must remain separately auditable and linked through the existing case/run-scoped Audit boundary. Approval is authorization evidence, not execution itself.

This decision does not authorize Drive mutation by itself and does not introduce a Physical Migration Executor.

**Reason:** Physical migration is a consequential external action. The architecture therefore requires an explicit human authorization boundary that is independent of planning and readiness checks, deterministically bound to the exact artifacts being authorized, fail-closed, auditable, and protected against approval reuse. Making consumption atomic prevents both concurrent and sequential executions from reusing one authorization.

## D-018 — Deterministic Migration Artifact Identity

**Status:** accepted and implemented

**Decision:** CASE-001 migration Manifest and Live Target Preflight outputs must expose deterministic artifact identities. Each identity consists of a controlled `kind`, an explicit identity/schema `version`, and a `reference` formed as `sha256:<digest>` over the artifact's canonical payload, excluding the identity itself.

Canonicalization uses deterministic JSON representation with sorted object keys, compact separators, UTF-8 encoding, and deterministic handling of the supported Python value types. Equivalent payloads must produce the same reference; any change to a hashed field must produce a different reference.

The initial controlled artifact kinds are `CASE001_MIGRATION_MANIFEST` and `CASE001_MIGRATION_PREFLIGHT`, both at version `1`.

The Manifest identity covers its case, tax period, provider, source scope, target scope, complete mapping sequence, and optional Inventory Evidence reference. The Preflight identity covers the complete deterministic preflight result, including target verification and pass-state fields.

These identities provide the concrete values required by D-017's exact manifest and preflight bindings. This decision does not itself create or consume approval and does not authorize or perform Drive mutation.

The identity reference is an integrity/identity reference, not a cryptographic signature or proof of authorship.

**Reason:** D-017 requires approval to bind to exact Manifest and Preflight artifacts. Without deterministic artifact references, an approval could not reliably distinguish the exact artifacts that were reviewed from later reconstructions or modified values. The artifact identity boundary closes that gap without coupling authorization to an LLM or to physical storage mutation.

## D-019 — Controlled Agent-Assisted Development Workflow

**Status:** accepted

**Decision:** Codex and other AI coding agents are optional, controlled development tools and are not runtime dependencies. Human authority remains required for architecture, contracts, stage acceptance, migration authorization, destructive operations, and governance decisions. Passing tests demonstrates technical test success only and does not constitute architectural or stage acceptance.

When authorized, development may use the controlled workflow: inspect → implement → test → analyze → fix → retest → git review → commit → push → report. The project must remain understandable, maintainable, testable, and continuable without Codex.

**Reason:** A controlled agent-assisted workflow can improve engineering execution while preserving human governance, Git traceability, and operational independence from any specific coding agent.

## D-020 — CASE-001 approval context composition and manifest provenance

**Status:** accepted by the human at `e6f28e89acf45541e4cfaa55c9efd8db35fc7909` and integrated into main. D-020 is closed; no physical migration or approval consumption is authorized by this acceptance.

**Decision:** A dedicated CASE-001 composition layer translates the exact manifest and successful live-target-preflight artifacts into the generic D-017 `ApprovalExecutionContext`. `LiveTargetScopeResult` records the existing Manifest `ArtifactIdentity` at preflight execution. Composition requires exact equality with the supplied manifest identity and rejects missing provenance. The nested D-018 structural preflight identity and hashed payload remain unchanged.

Identical manifest contents intentionally share artifact identity. Attempt/run provenance is a separate concern and is not introduced. Composition does not create, grant, or consume approval, access Drive, or execute migration. D-017 remains generic; Manifest and Preflight do not become approval-aware.

**Reason:** Different mappings can produce identical structural preflight results. Their distinct manifest identities must be retained in the live result to prevent substitution during composition. This provenance binding closes that ambiguity without redefining D-018 identity semantics. Implementation and verification are documented in `docs/case001-approval-context.md`; tests do not constitute human stage acceptance.


## D-029 — Canonical cross-session checkpoint and recovered CASE-001 closure

**Status:** accepted by explicit human instruction on 2026-09-13

**Decision:** `PROJECT_CHECKPOINT.md` is the mandatory first-read and handoff record for every new ChatGPT conversation, Codex session, or Agent process. Chat history is not durable project authority. A material stage transition is incomplete until the checkpoint and relevant state/roadmap/decision documents are updated in the same governed change set.

Agents must not ask the human to repeat facts already recorded in the checkpoint, referenced project documents, or authorized case evidence. When records conflict, the conflict must be exposed and reconciled before work continues. Missing historical detail must be labeled not recovered and must never be fabricated.

The human additionally confirmed as a recovery decision that CASE-001/tax year 2024 completed its tax-analysis preparation, received Chief Agent approval, and was closed in the preceding project conversation. Only the controlled ELSTER/Finanzamt submission path and UI remain as product boundaries; no submission has occurred. This recovered current-state authority supersedes older D-024 through D-028 open-gap language for continuation purposes, while preserving those records as historical checkpoints.

**Reason:** The prior conversation reached the message limit before the final state was durably synchronized to GitHub. A new conversation therefore revived an obsolete checkpoint and asked the human to repeat completed work. A single mandatory checkpoint plus same-change-set updates prevents chat boundaries from becoming project-state loss.

**Safety:** This decision records state and continuity rules only. It does not authorize filing, Finanzamt contact, irreversible mutation, permission expansion, protected-main merge/release, or Human-Gate bypass.


## D-030 — Canonical repository cleanup and retention policy

**Status:** implemented under explicit human authorization on 2026-09-13

**Decision:** The active repository must contain current canonical state, reusable contracts, implementation, regression tests, accepted decisions, verified lessons, and recovery-critical evidence. One-purpose probes, placeholder write tests, expired progress snapshots, and duplicated status narratives are removed once their durable rules and evidence are preserved.

Current status belongs in `PROJECT_CHECKPOINT.md` and `CURRENT_STATE.md`. Future work belongs in `ROADMAP.md`. Historical implementation rationale belongs in this decision log, focused technical documents, `ERRORS_AND_LESSONS.md`, and Git history.

The cleanup removed completed Agent Bridge probe triggers/workflows, placeholder repository-write artifacts, redundant populated-directory keep files, and superseded D-024/D-025 progress snapshots. Durable tax-analysis rules were consolidated in `docs/d025-tax-calculation-contract.md`. D-027, D-028, Agent Bridge, README, documentation index, current state, roadmap, and checkpoint were reconciled.

**Retention boundary:** Source code, regression tests, reusable architecture/contracts, security and approval rules, verified lessons, audit/recovery evidence, and case-isolation guarantees are retained even after their originating stage completes.

**Recovery:** Deleted repository material remains recoverable through Git history. This cleanup did not delete private Drive evidence, runtime approval/audit state, source code, or test coverage.


## D-031 — Ratification of Constitution v2 for governed adaptive orchestration

**Status:** accepted and ratified by explicit Project Owner / Human approval on 2026-09-13

**Decision:** Replace the original twelve-principle Constitution with a versioned supreme governance contract for the Adaptive Orchestrator Kernel and Governed Agent Factory. The proposal defines constitutional supremacy, exclusive Human amendment authority, durable truth, scope fidelity, deterministic governance, Orchestrator limits, Agent lifecycle, least privilege, separation of duties, Human Gates, case isolation, tax integrity, verification, audit, recovery, bounded autonomy, cost control, retention, trustworthy completion, and conflict resolution.

The exact ratified text is the active root `CONSTITUTION.md`. Activation commit: `ef935a4ba0493c1f2904d0983614b2b73e656254`. The Project Owner explicitly approved “Project Constitution v2, including Article 1 on two-stage information transfer and all 20 recorded Articles.” Constitution v2 is now the supreme project authority. Every subsequent Agent, role, permission, Agent Factory, and Orchestrator contract must be subordinate to it.


**Article 1 approval record — 2026-09-13:** At the Project Owner’s explicit instruction and ratification, Article 1 now establishes absolute Default Deny for any data transfer outside the approved project processing boundary. It requires two separate and ordered Human approvals: first, approval that the exact versioned artifact is correct and eligible for release; second, approval to transmit that same artifact to one exact named destination through one exact channel and purpose. Neither approval implies the other, and any mismatch or uncertainty fails closed.


## D-032 — Ratification of Agent Organization v1

**Status:** accepted and ratified by explicit Project Owner / Human approval on 2026-09-13

**Decision:** Adopt the redefined ten-section Agent Organization v1 model in `docs/agent-organization-v1-proposal.md` as the governing organizational basis for continued project work.

The accepted organization contains the Human Project Owner; an independent Control Office; the Master Project Orchestrator; Project Management, Engineering, and Tax Operations divisions; 20 permanent Agent roles; three inactive case-selected domain specialist templates; deterministic enforcement components; access tiers A0–A6/AX; task-mediated communication; temporary Agent lifecycle; separation of duties; Human Gates; and the O0–P4 execution path.

The Project Owner / Human retains exclusive organizational change authority. The `MASTER_PROJECT_ORCHESTRATOR` may identify a need, prepare an exact change proposal, and request Human review. It may not approve or activate an organizational change.

**Authorized next phase:** Phase O2 may design the machine-readable role catalog, Agent manifest schema, Permission Matrix, task/response communication schema, lifecycle state machine, Human Gate and conflict-of-interest rules, and budget/retry/timeout/kill-switch policy.

**Non-authorization:** This ratification does not activate an Agent instance, grant or expand permissions, authorize credentials, begin Master Orchestrator implementation, authorize protected-main merge/release, destructive action, tax filing, ELSTER/Finanzamt contact, or external transfer.

**Activation commit:** `15c0f9855f361ade1133d22f20cee21f75a812fc`.


## D-033 — Phase O2 machine-readable Orchestrator contract set

**Status:** accepted by explicit Project Owner / Human approval on 2026-09-13

**Technical result:** The versioned `ORCHESTRATOR_CONTRACT_SET_V1` was implemented under `contracts/orchestrator/v1/` from the Human-ratified Agent Organization v1. It contains the exact role catalog, Agent manifest schema, Permission Matrix, task and response schemas, Agent-instance lifecycle, Human Gate and conflict-of-interest policy, and bounded execution policy.

The contract set uses exact-version compatibility and Default Deny. Unknown or mixed versions, missing contracts, unknown roles, permission ambiguity, invalid transitions, A6 Agent requests, incomplete Human Gates, collapsed external-transfer approvals, invalid budgets, and unsafe kill-switch definitions fail closed.

`scripts/validate_o2_contracts.py` verifies cross-contract consistency offline without granting runtime authority. Positive and negative contract tests completed with `12 passed`; the full repository regression completed with `337 passed, 1 skipped`.

**Implementation commit:** `382a140e42496ad9edd92dc2016cfde51d091575`.

**Human acceptance:** The Project Owner explicitly accepted the exact Phase O2 contract set at commit `382a140e42496ad9edd92dc2016cfde51d091575` and authorized Phase O3 to begin.

**Authorized next phase:** Phase O3 may implement the deterministic Task/Dependency Registry, Agent Factory Kernel and Manifest Validator, Permission Broker, state/checkpoint/recovery controls, audit/event store, budget and loop controls, kill switch, and binding to the existing Agent Bridge. This does not authorize Agent activation or consequential runtime authority.

**Non-authorization:** O2 created policy and schema artifacts only. It did not activate an Agent, grant a permission or credential, access private case data, implement the Master Orchestrator Kernel, merge protected main, release, perform a destructive action, submit tax data, contact ELSTER/Finanzamt, or transmit externally.

**Acceptance record commit:** `bd18777cf00cade02abfa58869417948742a7e28`.


## D-034 — Phase O3 deterministic Orchestrator Kernel

**Status:** accepted by explicit Project Owner / Human approval on 2026-09-13

**Technical result:** The deterministic Orchestrator Kernel implements the accepted O2 contracts as a persistent SQLite control plane. It provides task/dependency registration, an explicit separate Human Gate registry, Agent manifest validation, Default-Deny permission decisions, case/run scope enforcement, lifecycle transitions, response and independent-acceptance recording, budget/retry/loop control, a fail-closed kill switch, hash-chained audit, checkpoint/recovery, read-only inspection, and exact binding to the existing Agent Bridge.

The Kernel is bound to the canonical SHA-256 digest of the exact O2 JSON set accepted at `382a140e42496ad9edd92dc2016cfde51d091575`. Same-version contract modification, unknown database or contract versions, unregistered tasks, unresolved Human Gates, dependency cycles, lineage mismatch, A6 Agent requests, case mismatch, invalid transitions, hidden failed tests, cost-ledger mismatch, budget exhaustion, retry misuse, audit alteration, and Bridge scope expansion fail closed.

An Agent `PASS` response cannot complete its task. The task remains `AWAITING_ACCEPTANCE` until a separate active `INDEPENDENT_ACCEPTANCE_AGENT` child task with a different actor instance records its decision.

**Verification:** O2 validator `PASS`; O3 targeted suite `26 passed`; relevant O2/O3/Agent Bridge suite `44 passed`; full regression `363 passed, 1 skipped`; compile check passed.

**Implementation commit:** `d70a28b9b33710a81881855048baccb63f3fc176`.

**Human acceptance:** The Project Owner explicitly accepted implementation commit `d70a28b9b33710a81881855048baccb63f3fc176` and authorized Phase O4 on 2026-09-13.

**Non-authorization:** No real Agent was activated. No credential, external permission, A6 capability, private case-data access, production deployment, protected-main merge/release, destructive action, tax submission, ELSTER/Finanzamt contact, or external transfer was authorized or performed.


## D-035 — Organized token-budget pause before Phase O4

**Status:** active pause requested by the Project Owner / Human on 2026-09-13

**Decision:** Phase O4 is authorized but its start is intentionally deferred until 2026-09-14 because approximately 25% of the current five-hour token allowance remained. No O4 design, file registration, implementation, pilot execution, or Agent activation began before this pause.

**Resume rule:** On or after 2026-09-14, continuation starts from `PROJECT_CHECKPOINT.md`, verifies the active branch and PR head, and designs one bounded low-risk, reversible, non-tax-private pilot. Any new artifact must first be registered in `ROADMAP.md`.

**Efficiency rule:** Apply the existing progressive-context protocol: load only checkpoint and directly relevant O4 contracts first, keep one implementation owner for the bounded package, run targeted tests before relevant regression, and reserve full regression for integration risk or phase acceptance. Token savings may not weaken correctness, audit, privacy, security, or Human Gates.

**Non-authorization:** This scheduling decision does not authorize production operation, private tax-case processing, credentials, A6, protected-main action, destructive action, tax submission, ELSTER/Finanzamt contact, or external transfer.


## D-036 — Phase O4 controlled autonomous-development pilot

**Status:** implemented and technically verified; awaiting explicit Human phase acceptance

**Decision:** Use a deterministic local consistency check of five explicitly allowlisted public governance documents as the single Phase O4 work package. The pilot records document hashes and required markers, stops at a durable paused checkpoint, recovers in a separate Kernel instance, requires a distinct Independent Acceptance identity, and ends with a verified checkpoint and the global kill switch halted.

**Verification:** O4 targeted suite `5 passed`; relevant O2/O3/O4/Agent Bridge suite `49 passed`; full regression `368 passed, 1 skipped`; Python compile check passed. A local two-invocation demonstration completed with audit integrity `PASS`, 2 tasks, 2 manifests, 1 response, 1 independent acceptance record, 2 checkpoints, 21 audit events, zero model tokens, 12 bounded local tool operations, and zero external cost.

**Implementation commit:** `b81f4060c5973ad0e5b4ec88a385ce3e046f7ee3`.

**Current gate:** Technical success is not phase acceptance. Phase O5 requires explicit Project Owner acceptance of the exact O4 implementation or an exact amendment request.

**Non-authorization:** The pilot used no tax-case data, network, credential, external service, LLM dispatch, protected-main write, merge, release, production operation, destructive action, tax submission, ELSTER/Finanzamt contact, or external transfer.


## D-037 — Phase O4 acceptance and Phase O5 authorization

**Status:** accepted and authorized by explicit Project Owner / Human approval on 2026-09-14

**Decision:** Accept Phase O4 implementation commit `b81f4060c5973ad0e5b4ec88a385ce3e046f7ee3` and authorize Phase O5 production-control-plane readiness work, with explicit emphasis on token-efficient execution.

**Initial O5 finding:** Read-only host inspection found the Local Sync scheduled task present but disabled, the Windows Relay scheduled task absent, and no local automation record proving Work automation scope for `golestanzadeh/ai-agent-lab`. O5 must represent these as blockers rather than claim production readiness.

**Non-authorization:** Phase O5 authorization permits readiness design, implementation, tests, and read-only verification. It does not authorize production Agent activation, service installation, credential or permission changes, protected-main action, merge/release, destructive action, tax submission, ELSTER/Finanzamt contact, or external transfer.


## D-038 — Phase O5 deterministic readiness evaluation

**Status:** evaluator technically verified; readiness blocked

**Decision:** Production-control-plane readiness is decided from one strict, non-secret evidence snapshot. Every repository, Work automation, Codex, GitHub, Local Sync, Windows Relay, monitoring, recovery, and protected-main-gate condition must be proven simultaneously. Missing, malformed, disabled, mismatched, or unknown evidence returns `BLOCKED`.

**Verification:** Targeted suite `11 passed`; relevant suite `72 passed`; full regression `379 passed, 1 skipped`; compile check passed. Implementation commit: `9e00bcfccdddd04cda7195a907fbc3aaa9dd9772`.

**Current result:** Six blockers remain: Work automation repository scope, Work automation enabled state, monitoring configuration, protected-main Human Gate enforcement, disabled Local Sync, and absent Windows Relay.

**Gate:** Enabling/installing scheduled services, changing an automation, establishing monitoring, or changing repository protection requires exact governed authority. O5 cannot become ready until those actions complete and a fresh evaluator run returns `PASS`.


## D-039 — Phase O5 local scheduled-service actions

**Status:** partially completed under explicit Human authorization on 2026-09-14

**Authorized actions:** Enable the existing `AI-Tax-Agent Local Sync` task and install `AI-Tax-Agent Windows Relay` through the registered installer.

**Result:** Windows Relay installation succeeded and the task is enabled, `READY`, limited-run-level, with last result `0`. Local Sync activation was attempted but Windows denied access; the task remains disabled. A manual bounded Local Sync smoke run returned `UP_TO_DATE` with identical local and remote SHA `ef9078b7c853d2d920430632a8aecdc4c0ec3e17`.

The two known user-owned untracked files were added to local `.git/info/exclude` so scheduled components cannot stage or process them. Their contents and locations were not changed, and this local exclusion is not committed.

**Gate at this decision:** O5 remained `BLOCKED`; Local Sync required elevated Windows activation. The later D-040 record resolves that item. No privilege bypass, credential change, production activation, merge, release, or external transfer occurred.


## D-040 — Phase O5 Local Sync elevated activation verification

**Status:** completed and independently verified on 2026-09-14

**Result:** After the Project Owner executed the approved commands in elevated PowerShell, `AI-Tax-Agent Local Sync` was independently verified enabled and `READY`, with run level `Limited` and latest task result `0`. Local and remote active-branch heads matched at `bc1749317450c449e8446bdf813bf13afa885715`.

At this checkpoint, the evaluator verified both Windows scheduled components and still blocked on Work automation, monitoring, and protected-main verification. D-042 later resolves the monitoring and protected-main items. No credential, permission expansion, merge, release, production Agent activation, or external transfer occurred.


## D-041 — Windowless Windows scheduled execution

**Status:** implemented and live-verified on 2026-09-14

**Problem:** The one-minute scheduled checks opened and closed multiple command windows because Windows Relay used console `python.exe` and child Git/PowerShell processes lacked no-window creation flags.

**Decision:** Use `pythonw.exe` for the Windows Relay scheduled action, mark that task hidden, and pass Windows `CREATE_NO_WINDOW` to Local Sync and Windows Relay subprocess calls.

**Verification:** Implementation commit `345cadb83ce0fd6b30b851c394cebdc891037672`; targeted regression `27 passed`. The reinstalled Relay is enabled, hidden, `READY`, uses `C:\Python314\pythonw.exe`, and returned last result `0`.


## D-042 — Phase O5 monitoring and protected-main verification

**Status:** verified on 2026-09-14

**Protected main:** Active GitHub ruleset `22799423` targets `main`, has an empty bypass list, requires pull requests before merge, and blocks force pushes. This satisfies the current deterministic protected-main Human-Gate evidence requirement without changing repository settings.

**Monitoring:** Agent Bridge Passive Validation run `34821613554` completed successfully for the latest windowless-execution checkpoint. Local Sync and Windows Relay were independently verified enabled and `READY`, with latest result `0`.

**Readiness result:** A fresh evaluator snapshot verified twelve conditions and returned `BLOCKED` only for the unproven ChatGPT Work automation repository scope and enabled state. No GitHub setting, automation, permission, credential, merge, release, or external-transfer state was changed during this verification.


## D-043 — Phase O5 Work automation scope resolution and readiness PASS

**Status:** technically ready; Human acceptance required

**Authority:** On 2026-09-14, the Project Owner explicitly authorized changing all three active ChatGPT Work Agent Bridge automations from `golestanzadeh/agent-bridge-poc` to `golestanzadeh/ai-agent-lab` while preserving their existing behavior and safety restrictions.

**Decision and result:** `Bridge PR Wake-up`, `Agent Bridge Human Gate`, and `Agent Bridge Continuation` were updated in place. Each automation's GitHub Repository condition and prompt now reference `golestanzadeh/ai-agent-lab`; each remains active. Exact event filters, Agent Bridge markers, Human Gate behavior, duplicate-prevention logic, no-merge constraints, and other safeguards were retained. No task was run and no GitHub data or plugin permission was changed during the updates.

**Verification:** Each task was reopened and inspected after update. A fresh non-secret readiness snapshot collected at `2026-09-14T10:49:00+02:00` also verified synchronized branch head `bac8a4cf279952fab92fc4ab0cb54fe7fdfea2c8`, draft PR #1, active ruleset `22799423`, successful Passive Validation run `34821985936`, and both Windows scheduled tasks `READY` with latest result `0`. The deterministic evaluator returned `PASS`, `ready: true`, fourteen verified conditions, and zero blockers.

**Boundary:** This technical PASS does not authorize Phase P1, production Agent activation, permission or credential expansion, protected-main action, merge, release, destructive action, tax submission, or external transfer. Exact Human acceptance remains required.


## D-044 — Phase O5 Human acceptance and controlled pause

**Status:** accepted and complete by explicit Project Owner / Human approval on 2026-09-14

**Decision:** Accept the Phase O5 technical-readiness result and exact readiness-record commit `d64da2588b18f548c877aed6044f8884e7644cdc`. The acceptance basis is deterministic `PASS`, `ready: true`, fourteen verified conditions, zero blockers, and successful GitHub validation run `34824845788` at that commit.

**Token constraint:** At acceptance, the Project Owner reported that approximately 9% of the current five-hour token allowance remained. The governed continuation point is therefore a controlled pause after completing the acceptance record.

**Next gate:** Phase P1 or any other next work requires separate explicit Project Owner instruction. This acceptance grants no production activation, credential or permission expansion, protected-main action or merge, release, destructive action, tax submission, ELSTER/Finanzamt contact, or external transfer authority.


## D-045 — Live plan-limit stop and guarded continuation control

**Status:** designed and activated by explicit Project Owner request on 2026-09-14

**Decision:** Treat the Codex account usage-limit service as the authoritative runtime source. Enter caution at five-hour remaining 25% or weekly remaining 20%; enter a durable `TOKEN_PAUSED` state at five-hour remaining 15% or weekly remaining 10%; fail closed when usage is unknown. Resume only when five-hour remaining is at least 80%, weekly remaining is above 10%, repository recovery is safe, and the checkpoint contains one exact next action that was already authorized.

**Automation:** Active same-task heartbeat `Plan Limit Continuation Guard`, id `plan-limit-continuation-guard`. After the first guarded recovery it runs hourly and may perform at most one exact, clearly authorized local synthetic package per run. It stays quiet while state is unchanged or non-actionable and reports only meaningful pause, resume, completion, failure, conflict, or required Human action.

**Initial evidence:** The live service reported five-hour `usedPercent: 1` (99% remaining; UI rounded to 100%), weekly `usedPercent: 38` (62% remaining), primary reset `2026-09-14 23:47:38 +02:00`, and weekly reset `2026-09-20 13:48:09 +02:00`.

**Authority boundary:** The controller preserves and resumes existing authority; it cannot grant Phase P1, production, permission, protected-main, merge, release, destructive, tax-submission, ELSTER/Finanzamt, or external-transfer authority.


## D-046 — Phase P1 authorization and first non-production ERiC boundary

**Status:** package 1 technically verified; Human acceptance required

**Authority:** The Project Owner explicitly authorized Phase P1 only for design and non-production implementation with synthetic data and without real transmission to ELSTER or Finanzamt.

**Official route decision:** Use ERiC as the target third-party integration boundary. Official ELSTER material describes ERiC as a C library that plausibility-checks tax data and transmits it encrypted to tax-administration acceptance servers. The official availability schedule records ERiC `41.2` for unlimited income tax (`UFA 10`) for tax year 2024.

**Package 1:** Implement only an immutable synthetic envelope, exact route metadata, two separately bound and ordered Human approvals, and a deterministic dry-run plan that always denies transmission. Do not implement an ERiC FFI, XML field mapping, signing, authentication, certificate handling, endpoints, network calls, or receipt ingestion.

**Unknown/blocked facts:** Exact 2024 XML schemas, annual plausibility rules, and ERiC API details require the official developer package and are not durably available. They must not be reconstructed from memory or unofficial examples.

**Verification:** Implementation commit `aaf5bec86e103480ef5d36cedca29cfbfb607862`; targeted package-1 suite `23 passed`; full regression `405 passed, 1 skipped`; Python compile check passed. The first full-suite invocation completed all test cases but failed during Windows pytest temporary-link cleanup; rerunning with an isolated temporary base completed successfully.

**Gate:** Package 1 requires exact Project Owner acceptance before package 2. Technical success is not approval to obtain developer access or use an external capability.

**Non-authorization:** Developer registration, account creation, manufacturer ID, ERiC download, credentials, certificates, real taxpayer data, live connectivity, submission, Finanzamt contact, and external transfer remain unauthorized.


## D-047 — Phase P1 package 1 Human acceptance

**Status:** accepted; package complete

**Decision:** On 2026-09-14, the Project Owner explicitly accepted Phase P1 package 1 and exact implementation commit `aaf5bec86e103480ef5d36cedca29cfbfb607862`.

**Accepted evidence:** Targeted package-1 suite `23 passed`; full regression `405 passed, 1 skipped`; Python compile check passed. The acceptance preserves the recorded Windows pytest temporary-link cleanup incident and the successful isolated-base rerun.

**Effect:** Package 1 moves from `P1_PACKAGE_1_TECHNICALLY_COMPLETE -> HUMAN_REQUIRED` to `P1_PACKAGE_1_ACCEPTED / PACKAGE COMPLETE`.

**Next gate at acceptance:** This decision did not authorize package 2 or any external capability. The later D-048 authority supersedes only the package-2 design gate; developer registration/account creation, manufacturer ID, ERiC package retrieval, credentials, certificates, real taxpayer data, live connectivity, submission, Finanzamt contact, and external transfer still require separate exact Project Owner authority.


## D-048 — Phase P1 package 2 versioned ERiC adapter boundary

**Status:** technically verified; Human acceptance required

**Authority:** On 2026-09-14, the Project Owner explicitly authorized package 2 only for non-production design and implementation of a versioned ERiC adapter, without registration, credentials, live connectivity, or real transmission.

**Decision:** Implement adapter contract version `1`, bound exactly to package-1 envelope schema `1`, ERiC `41.2`, procedure `UFA10`, and tax year `2024`. Treat the ERiC interface specification, UFA10 2024 XML schema, and UFA10 2024 plausibility rules as `NOT_RECOVERED`; do not guess their contents or let caller input advance their status.

**Capability boundary:** `BOUNDARY_READY` means only that the inert local contract is well formed. It does not permit official mapping, plausibility validation, FFI use, signing, credential/certificate access, networking, or transmission.

**Initial verification:** Implementation commit `a024ff5c608700ff7650c4b9c02c643fa72884fd`; relevant package-1/package-2 suite `36 passed`; full regression `418 passed, 1 skipped`; Python compile check passed. The first targeted invocation omitted `PYTHONPATH=src` and stopped at collection; the corrected documented environment passed.

**Authorized amendments:** The Project Owner approved three precise hardening changes: reject forged plans that enable a forbidden capability or network call; include required-material and denied-capability policies in the hash-bound contract and reject policy drift without a version change; replace `BOUNDARY_READY` with `BOUNDARY_READY_MAPPING_BLOCKED`.

**Amended verification:** Commit `3fd1e4d586cc97411acaa563e6d5712e31c5dacd`; relevant package-1/package-2 suite `45 passed`; full regression `427 passed, 1 skipped`; Python compile check passed.

**Next gate:** The Project Owner must accept amended package 2 commit `3fd1e4d586cc97411acaa563e6d5712e31c5dacd` or request further exact amendments. Developer registration/account creation, manufacturer ID, official material retrieval or verification, ERiC FFI/XML implementation, credentials, certificates, live connectivity, ELSTER/Finanzamt contact, and transmission remain unauthorized.


## D-049 — Amended Phase P1 package 2 Human acceptance

**Status:** accepted; package complete

**Decision:** On 2026-09-14, the Project Owner explicitly accepted amended Phase P1 package 2 and exact implementation commit `3fd1e4d586cc97411acaa563e6d5712e31c5dacd`.

**Accepted evidence:** Non-forgeable plan enforcement, hash-bound required-material and denied-capability policies, explicit `BOUNDARY_READY_MAPPING_BLOCKED` outcome, relevant package-1/package-2 suite `45 passed`, full regression `427 passed, 1 skipped`, and successful Python compile check.

**Effect:** Package 2 moves from `P1_PACKAGE_2_AMENDED_TECHNICALLY_COMPLETE -> HUMAN_REQUIRED` to `P1_PACKAGE_2_ACCEPTED / PACKAGE COMPLETE`.

**Next gate:** This acceptance does not authorize a further package or any external capability. Developer registration/account creation, manufacturer ID, official material retrieval or verification, ERiC FFI/XML implementation, credentials, certificates, live connectivity, ELSTER/Finanzamt contact, and transmission require separate exact Project Owner authority.


## D-050 — Phase P1 package 3 synthetic ERiC material process

**Status:** technically verified; Human acceptance required

**Authority:** The Project Owner authorized only a synthetic, non-production design and implementation of the ERiC material registration and verification process. Registration, protected download, credentials, live connectivity, and real transmission were explicitly excluded.

**Decision:** Require exactly one immutable synthetic record and one later independent synthetic review for each of the three material categories in the accepted adapter contract. Bind every record and review to exact identities, timestamps, route metadata, and canonical SHA-256 references. Fail closed on missing, duplicate, rejected, self-reviewed, reordered, mismatched, or mutated evidence.

**Boundary:** `SYNTHETIC_PROCESS_READY_OFFICIAL_STATUS_BLOCKED` validates only the designed workflow. It cannot advance official status beyond `NOT_RECOVERED`, retrieve protected material, access a credential, make a network call, or transmit data.

**Verification:** Implementation commit `2d6efd25e85ba9874ccbdad695b5b24c0c205887`; relevant P1 suite `66 passed`; full regression `448 passed, 1 skipped`; Python compile check passed. The first targeted run produced `13 failed, 53 passed` because `datetime` was not JSON serializable; deterministic ISO timestamp canonicalization fixed the defect before the successful rerun.

**Workflow improvement:** Package-3 acceptance may be combined with one bounded authorization for continuous synthetic/non-production Phase P1 design and implementation. Routine inspection, implementation, repair, testing, documentation, commit, and checkpoint work may then continue without package-by-package approval until an external, credential, protected-material, production, transmission, constitutional, or other consequential Human Gate is reached.


## D-051 — Package 3 acceptance and revocable continuous Phase P1 authority

**Status:** accepted and active

**Acceptance:** On 2026-09-14, the Project Owner explicitly accepted package 3 and exact implementation commit `2d6efd25e85ba9874ccbdad695b5b24c0c205887`.

**Continuous authority:** Remaining local, synthetic, non-production Phase P1 inspection, design, implementation, repair, testing, documentation, commit, push, bounded Agent delegation, review, and result-control work may continue without package-by-package approval.

**Revocation and amendment:** This authority is explicitly revocable and editable. The latest Project Owner instruction controls future work and cannot retroactively authorize an already forbidden action.

**Mandatory stop boundaries:** Registration/account creation, protected download, manufacturer ID, credentials/certificates, real data, external connectivity, ELSTER/Finanzamt contact or transmission, production, architecture or governing-rule change, action on protected `main`, merge, or any other consequential Human Gate require separate exact authority.

**Continuation:** Begin with the registered immutable synthetic Human-readable preview package, then continue through other registered work inside the same boundary until a mandatory stop or token-controller pause.


## D-052 — Synthetic Human-readable ELSTER preview

**Status:** implemented and verified under continuous authority

**Decision:** Create a deterministic preview artifact bound to the exact synthetic envelope, accepted adapter contract, completed synthetic material process, ERiC route metadata, and immutable non-production warning. JSON-quote free text so it cannot inject preview structure.

**Boundary:** The preview is not an official tax form and proves no official XML mapping or plausibility result. Its constructor cannot enable credential access, network calls, or transmission, and its disclaimer cannot be weakened.

**Verification:** Implementation commit `8237882d29c2d7171f776fe684e2f0d1b609d476`; relevant P1 suite `77 passed`; full regression `459 passed, 1 skipped`; Python compile check passed.

**Continuation:** No package-level Human Gate applies. Continue with the registered synthetic submission-lifecycle/idempotency package while D-051 authority remains active.


## D-053 — Early token-caution pause after package 4

**Status:** `TOKEN_PAUSED`; guarded automatic continuation authorized

**Evidence:** After package 4 completed and was durably recorded, the live account service reported 24% five-hour and 51% weekly remaining. The controller entered an early safe pause inside the accepted caution zone rather than consume capacity toward the mandatory 15% boundary.

**Resume:** When five-hour remaining is at least 80%, weekly remaining is above 10%, and repository recovery checks pass, resume automatically with the registered synthetic submission-lifecycle/idempotency package under D-051. No Human approval is required unless a D-051 stop boundary is reached.


## D-054 — Guarded resume and synthetic submission lifecycle/idempotency

**Status:** implemented and verified under continuous authority

**Resume evidence:** A fresh service reading reported 99% five-hour and 49% weekly remaining. The active branch was clean and synchronized locally/remotely at `3c2ff2844bac94387969527b72a8c49c0f997415`, satisfying D-045 recovery conditions.

**Decision:** Bind each synthetic lifecycle to the exact preview, envelope, case/run, and destination approval through a stable SHA-256 idempotency key. Produce no duplicate plan for unresolved work; block uncertain outcomes without retry; permit at most one retry after a definite synthetic failure only when the exact destination approval permits it; and represent success only through a labelled synthetic receipt placeholder.

**Capability boundary:** No attempt artifact is a transmission authorization or transmitter. Network, credential, signing, official receipt, real-data, and external capabilities remain absent and non-forgeably denied.

**Verification:** Targeted `15 passed`; relevant Phase P1 `92 passed`; full regression `474 passed, 1 skipped`; Python compile check passed.

**Continuation:** Continue under D-051 with the registered local synthetic lifecycle-audit and restart-recovery package. Existing Human Gates remain unchanged.


## D-055 — Hourly bounded continuation after token recovery

**Status:** active by explicit Project Owner continuation instruction

**Decision:** After the five-hour allowance recovered and package 5 completed, change the same-task guard from a reset-aligned five-hour cadence to an hourly cadence. Each run may perform at most one exact next package only when canonical state proves that it is local, synthetic, non-production, already authorized, and certainly free of a Human Gate.

**Safety:** Live limit checks, caution/pause thresholds, repository recovery checks, one-package bounds, quiet non-actionable runs, and all D-051/constitutional Human Gates remain unchanged. This decision creates no production, external, credential, real-data, protected-main, merge, release, submission, or transmission authority.


## D-056 — Privacy-minimized synthetic lifecycle audit and restart recovery

**Status:** implemented and verified under continuous authority

**Decision:** Convert validated synthetic lifecycle artifacts into an append-ordered hash chain containing only case/run identities, the stable idempotency key, attempt metadata, artifact references, timestamps, and synthetic outcomes. Restore state only from an exact versioned snapshot after chain, schema, transition, and caller-supplied scope validation.

**Privacy and authority boundary:** Tax values, purpose text, protected material, credentials, external receipt content, and network details are excluded. Recovery is descriptive and cannot plan a retry, grant authority, or enable transmission.

**Verification:** Targeted `12 passed`; relevant Phase P1 `104 passed`; full regression `486 passed, 1 skipped`; Python compile check passed.

**Continuation:** Continue under D-051 with the registered local synthetic submission-readiness dossier. Existing Human Gates remain unchanged.


## D-057 — Synthetic readiness dossier and local P1 boundary

**Status:** implemented and verified; Human Gate reached

**Decision:** Aggregate the exact ordered synthetic P1 evidence lineage into one immutable readiness dossier. Preserve the complete external-blocker and denied-capability policies and reject cross-bound, missing, reordered, duplicated, privacy-expanding, or execution-enabling construction.

**Result:** The dossier is technically complete but explicitly not externally ready. It contains no tax values or purpose text and grants no mapping, validation, credential, network, signing, transmission, or real-receipt capability.

**Verification:** Targeted `19 passed`; relevant Phase P1 `123 passed`; full regression `505 passed, 1 skipped`; Python compile check passed.

**Gate:** D-051 local synthetic authority has been fully exercised through the registered package sequence. Further P1 work requires exact authority for developer registration/manufacturer-ID/protected material retrieval. The separate user-interface phase also requires exact phase authorization. No such step is inferred.

**Automation state:** Pause `plan-limit-continuation-guard` at this Human Gate so hourly non-actionable checks do not consume plan capacity. Preserve its configuration and task attachment for reactivation after the Project Owner supplies an exact authorized continuation point.


## D-058 — Protected ERiC access and user-interface phase authority

**Status:** authorized and started on 2026-09-15

**Authority:** The Project Owner explicitly authorized, in priority order, the developer-registration/protected-official-material retrieval stage and the start of the user-interface phase.

**Registration boundary:** Registration is limited to ELSTER developer access needed to retrieve and inspect protected ERiC documentation/package. The official form is ready for Human-owned contact data and CAPTCHA entry. No field has been populated and no submission has occurred. Final submission requires action-time Human confirmation. Manufacturer-ID work, tax-transmission credentials or certificates, real taxpayer data, acceptance-server connectivity, transmission, Finanzamt contact, production activation, and protected-main action are not authorized.

**UI boundary:** Begin with a local, synthetic, non-production interaction-and-safety foundation derived from the already stable case, identity, state, approval, audit, and synthetic ELSTER contracts. Package UI-1 chooses no framework and creates no external connection, real-data path, deployment, or submission capability. Any architecture choice remains a separate Human Gate.

**Parallel continuation:** The registration step retains first priority. Because it currently waits only for Human-owned form values and CAPTCHA, the separately authorized local UI foundation may proceed without treating that wait as a project-wide stop.

**UI-1 result:** `docs/ui-phase-foundation.md` now defines the ordered workflow, seven required screen/state groups, cross-screen case-isolation and Human-Gate invariants, and seven synthetic acceptance scenarios. Targeted safety-contract regression completed with `63 passed`. The next interactive prototype stops at the pre-existing architecture/framework Human Gate.


## D-059 — Architecture-neutral synthetic UI state

**Status:** implemented and verified under authorized UI phase

**Decision:** Before selecting a renderer or server framework, provide one immutable presentation-state boundary that resolves exact synthetic case/year scope through the Case Registry, clears all derived state on case selection, binds case content and visible Human Gates exactly, and rejects real data or external capability.

**Safety:** Submission remains permanently disabled, official receipts cannot be represented, private document/finding contents are replaced by immutable references, and network calls are absent. This package grants no framework, hosting, authentication, protected-material, production, or transmission authority.

**Verification:** Targeted `7 passed`; relevant case/UI/P1 safety suite `70 passed`; full regression `512 passed, 1 skipped`; Python compile check passed.

**Next gate:** No further architecture-neutral UI implementation package is registered. An interactive prototype requires the Project Owner's explicit framework/architecture choice. The separately authorized ERiC registration remains temporarily paused until 09:00 Europe/Berlin on 2026-09-15.


## D-060 — Local interactive UI architecture

**Status:** explicitly selected by the Project Owner on 2026-09-15

**Decision:** Use FastAPI with server-rendered Jinja templates and HTMX for the local interactive prototype. Serve the pinned HTMX asset locally so opening the prototype makes no CDN request. Bind all rendered case state to the architecture-neutral package-2 contract and its Case Registry checks.

**Boundary:** Listen on loopback only; use only synthetic in-memory examples; provide no authentication, persistence, protected-material access, external connection, deployment, production mode, official receipt, or submission action. A disabled submission control is informational and cannot trigger a route.

**Dependencies:** Pin verified package versions in `requirements.txt`; use the official FastAPI template/TestClient pattern and HTMX `2.0.10` local distribution.

**Implementation result:** The local app is implemented with exact case/year partial rendering, Persian responsive templates, local static assets, and no submission endpoint. The HTMX asset matches the official SHA-384 integrity value. UI-2/UI-3 targeted verification returned `13 passed`; full regression returned `518 passed, 1 skipped`, with one recorded upstream TestClient deprecation warning. Loopback visual inspection passed.


## D-061 — Less-than-20-day parallel delivery policy

**Status:** active by explicit Project Owner instruction on 2026-09-15

**Target:** Complete project design and full implementation in less than 20 days from this instruction, meaning before 2026-10-05 Europe/Berlin.

**Decision:** Treat project tracks as parallelizable whenever they are unrelated and neither is a prerequisite of the other. Prefer concurrent or interleaved completion of independently authorized work so an external wait or Human Gate in one track does not create idle time in another.

**Dependency rule:** Preserve strict ordering only where a later activity demonstrably requires the foundation, stable contract, identity/state model, or organized structure of an earlier activity. Record the dependency rather than assuming phase-wide exclusivity.

**Safety:** Schedule pressure creates no new authority and does not weaken Human Gates, architecture approvals, production/external restrictions, case isolation, required tests, audit evidence, token-limit controls, protected-main rules, or the future-file registration rule.


## D-062 — ERiC registration resumes after temporal pause

**Status:** resumed by explicit Project Owner instruction at 09:15 Europe/Berlin on 2026-09-15

**Decision:** Close the temporary registration pause that ended at 09:00 and reopen the official ELSTER developer-registration form. Preserve the approved personal-project representation and do not fabricate a registered company or independent website.

**Current Human Gate:** The form is empty. The Project Owner must enter the exact personal contact fields and CAPTCHA. Final `Absenden` remains a separate action-time confirmation because it creates the developer-account application and communicates externally.


## D-063 — ERiC developer-registration application submitted

**Status:** submitted with separate action-time Human confirmation on 2026-09-15

**Evidence:** The official ELSTER `Versandbestätigung` page confirmed transmission at 09:20:28 Europe/Berlin and displayed a transmission identifier. The identifier and personal contact fields are deliberately excluded from repository history.

**Effect:** Developer-account review is now pending. This is not account approval, manufacturer-ID authority, protected-material verification, credential authority for the agent, production readiness, or transmission authority.

**Continuation:** Await ELSTER's access email. Authentication remains a Human-only action; credentials must never be supplied through chat or stored in the repository. Once the Human is logged in, the already authorized protected ERiC documentation/package download may proceed, followed by independent hash/version/content verification.


## D-064 — Parallel synthetic UI workflow and diagnostics

**Status:** implemented and verified while ERiC developer access is pending

**Decision:** Model the user journey as ten exact ordered stages bound to one already validated synthetic case/run. Permit exactly one current active/blocked boundary, completed predecessors, and locked successors. Render the workflow and a privacy-safe diagnostic panel inside the existing local prototype.

**Safety:** Diagnostic values come only from a closed allowlist. Private content, credentials, arbitrary error text, real data, operational controls, external calls, and submission remain rejected by construction.

**Verification:** UI targeted `19 passed`; full regression `524 passed, 1 skipped`; Python compile and loopback visual inspection passed. The unchanged upstream Starlette TestClient deprecation warning remains recorded.


## D-065 — Synthetic metadata-only document intake UI

**Status:** implemented and verified while ERiC developer access is pending

**Decision:** Present documents in the local UI only through case/run-bound synthetic metadata: immutable document and provenance references, generic labels, allowlisted category/type, and processing status. Render no document content or real filename.

**Safety:** Reject cross-case scope, private labels, malformed/duplicate references, raw source access, real-data classification, upload, persistence, and networking. This package creates no Drive or external capability.

**Verification:** UI targeted `24 passed`; full regression `529 passed, 1 skipped`; Python compile and loopback visual inspection passed. The existing upstream TestClient warning is unchanged.


## D-066 — Agent-led continuous execution and exception-only reporting

**Status:** active by explicit Project Owner instruction on 2026-09-15

**Decision:** Continue the project autonomously across all prerequisite-ready, already authorized work. Use bounded Agent delegation where useful, independently review and test results, and do not impose package-by-package Human acceptance or routine reporting when no governing Human Gate applies.

**Reporting:** Keep routine progress durable in Git and the canonical checkpoint. Interrupt the Project Owner only for a genuine Human Gate, required personal information, consequential decision, material failure/conflict, limit pause, or risk the Project Owner genuinely needs to know. Routine successful packages do not require a full conversational report.

**Authority boundary:** This operating rule changes scheduling and reporting only. It does not authorize real data, credentials, authentication on behalf of the Human, protected downloads before Human login, external connectivity, production, tax transmission, Finanzamt contact, protected-main action, merge, release, destructive action, or bypass of any existing gate.


## D-067 — Local Agent Runtime Activation Layer

**Status:** implemented and verified on 2026-09-15 at `cb41d13`

**Decision:** Implement a local, non-production, low-risk runtime layer that connects the existing Planning, Implementation, Quality Engineering, and Independent Acceptance roles to the accepted deterministic Orchestrator Kernel. Preserve exact task/manifest lineage, dependency order, bounded budgets, separate actor identities, evidence binding, independent acceptance, checkpoint/recovery, and the global kill switch.

**Boundary:** Use only local synthetic inputs and in-process allowlisted workers. Do not activate a model provider, network connector, credential, private-data source, production service, protected-main action, external transfer, or arbitrary operating-system command. Do not change the ratified role catalog or organizational rules.

**Later gate:** Connecting this runtime to an external model/provider, granting additional tools or permissions, processing real case data, or activating production requires a separate exact Human authorization.

**Implementation result:** The fixed D-067 synthetic proof now dispatches the four accepted roles through temporary Kernel-bound instances, performs separate QA and evidence-based independent acceptance, survives the exact planned pause/recovery boundary, and halts safely. Verification returned `8` targeted, `39` relevant, and `537 passed, 1 skipped` full-regression results. Mid-resume crash continuation is deliberately not claimed; it fails closed and remains future work.


## D-068 — Synthetic review and form-preview UI

**Status:** implemented and verified on 2026-09-15

**Decision:** Render only closed, case/run-bound synthetic findings and evidence gaps, a nonnegative explicitly synthetic calculation summary, and the existing immutable preview reference. Preserve the official ERiC mapping state as `NOT_RECOVERED`.

**Safety:** No private/free-form content, authentication, persistence, networking, official receipt, production action, or transmission capability is introduced.

**Verification:** Targeted UI-6/app tests returned `19 passed`; full regression returned `548 passed, 1 skipped`; compile and loopback visual/accessibility inspection passed.


## D-069 — Synthetic display-only Human Decision Queue

**Status:** implemented and verified on 2026-09-15 at `388e8db`

**Decision:** Add a local presentation contract and Persian UI panel for one exact synthetic Human Gate bound to the selected case/run and immutable preview artifact. The queue communicates the boundary but cannot make or persist a decision.

**Safety:** Approval, rejection, authentication, credentials, persistence, networking, protected access, production, receipts, and transmission remain absent and disabled. Implementing a real Human decision lifecycle requires separate exact authorization.

**Implementation result:** The exact case/run/gate-bound display queue is integrated and verified with `16` targeted tests and `555 passed, 1 skipped` full regression; loopback visual/accessibility inspection passed.


## D-070 — Synthetic display-only submission readiness

**Status:** implemented and verified on 2026-09-15 at `c153014`

**Decision:** Present a case/run-bound synthetic readiness summary with Article 1 content-release and destination-transmission approvals as two distinct `NOT_APPROVED` stages and an exact closed blocker list.

**Safety:** The view has no approval control, authentication, credential, transmitter, retry, receipt, networking, production, or submission capability. Displaying the stages grants no authority.

**Implementation result:** The exact synthetic boundary is integrated and verified with `19` targeted tests and `564 passed, 1 skipped` full regression; loopback visual/accessibility inspection passed.


## D-071 — Protected ERiC material retrieval and version incompatibility

**Status:** retrieval complete; architecture/version migration Human Gate reached on 2026-09-16

**Decision:** After private Human authentication and explicit Human acceptance of the ERiC Release 44 software-manufacturer license, retrieve the official `44.3.6.0` documentation and schema-documentation packages locally. Record only non-secret provenance, version, size, and SHA-256 evidence in durable project state; keep protected package contents and credentials outside Git.

**Evidence:** Official release date `2026-09-14`; documentation ZIP size `123,217,775` bytes with SHA-256 `BAD21C27ECCE56D04FC04BCCFD2DFA17B9FF2455AA878758100FC73A28492AD5`; schema-documentation ZIP size `35,503,440` bytes with SHA-256 `A77CCA9E5A0DDB4EAE9E2548F57FC3A064432C1B71C1FF1E53CA9085A8BE779E`. ZIP inventories expose the ERiC API reference, developer handbook/release material, E10/2024 examples, annual documentation, XSDs, and schema documentation.

**Compatibility finding:** The official developer page states that ERiC 41 and 42 have been unable to transmit since the 2026-04-27 minimum-version increase. Existing synthetic 41.2 contracts remain historical test artifacts and must not be promoted operationally.

**Gate:** Updating adapter identity, supported version, schema bindings, or architecture to ERiC 44.3.6.0 requires separate exact Project Owner approval. No software package, forms archive, credential, manufacturer ID, real data, connection, or transmission capability was added.


## D-072 — Local ERiC 44.3.6.0 contract migration

**Status:** authorized, implemented, and verified on 2026-09-16

**Decision:** Supersede the active synthetic ERiC `41.2` baseline with adapter contract version `2`, bound to official ERiC `44.3.6.0`, procedure `UFA10`, tax year `2024`, envelope schema `1`, and the recovered E10/2024 interface/schema/plausibility material categories. Preserve `41.2` only as historical evidence.

**Fail-closed boundary:** Local recovery and hash verification of protected documentation changes material state to `RECOVERED_LOCAL_MAPPING_UNVERIFIED`; it does not establish a correct field mapping or executable plausibility implementation. Those two missing capabilities remain explicit blockers. Credentials, Manufacturer-ID, signing, networking, real data, transmission, and production remain denied.

**Evidence:** Official Release 44 package metadata and hashes are recorded in D-071. Archive inspection identified the E10/2024 example, annual field documentation, `E10-2024-Nutzdaten.xsd`, `E10-2024.xsd`, `elster11_E10_2024_extern.xsd`, schema documentation, and plausibility-related material. The version-migration targeted suite returned `123 passed`.


## D-073 — Post-reset continuation and stable O4 governance marker

**Status:** implemented and verified on 2026-09-20

**Decision:** Resume agent-led continuous execution after a fresh limit check reported full five-hour and weekly capacity and the repository was clean and synchronized. Update the historical O4 governance-document validator to require the canonical compact ROADMAP heading `## Current position` instead of the removed package-registration heading.

**Rationale and boundary:** The former marker became stale when completed artifacts were correctly removed from the remaining-work roadmap. The replacement preserves deterministic validation of the current canonical document without restoring obsolete planning content or changing O4 authority, architecture, permissions, or runtime capability.

**Verification:** O4 targeted tests returned `5 passed`; the first invocation also encountered the known Windows pytest temporary-symlink cleanup error after all five cases passed, and the isolated-base rerun exited successfully. The first full-suite run had one order-sensitive Google Drive provisioning failure that passed immediately in isolation; a fresh full-suite rerun returned `564 passed, 1 skipped` with only the existing upstream TestClient deprecation warning.


## D-074 — Bounded E10/2024 Anlage N mapping profile

**Status:** implemented and technically verified on 2026-09-20

**Decision:** Implement a deterministic local mapping profile for the three-field synthetic employment summary. Require explicit Person A/B, tax class, and `N_OTHER_EMPLOYMENT_EXPENSES` semantics before selecting official fields. Map tax classes 1–5 to `E0200002`, `E0200201`, and `E0200301`; tax class 6 to `E0200203` and `E0200303`; and the explicitly classified expense amount to `E0204803`.

**Official evidence:** Local inspection of the protected, hash-verified ERiC `44.3.6.0` annual documentation, example, and `E10-2024.xsd` confirmed the exact paths, field identifiers, data types, lexical forms, and separate tax-class groups. Protected source content remains outside Git.

**Boundary:** The result is an E10/2024 Anlage N subset fragment, not a complete declaration and not proof of official ERiC plausibility acceptance. Full declaration construction and the official ERiC plausibility engine remain explicit blockers. ERiC FFI, Manufacturer-ID, credentials/certificates, signing, networking, real data, and transmission remain denied.

**Verification:** Mapping/relevant targeted suite `70 passed`; all non-Drive full-regression tests `574 passed, 1 skipped`; Google Drive provisioning tests `15 passed` under Python 3.11. Two Python 3.14 Windows full-suite attempts exposed unrelated, order-varying journal-replace failures in that existing Drive test file; they are preserved as environment-specific evidence rather than attributed to the mapping package.


## D-075 — Complete synthetic E10/2024 declaration and official-XSD validation

**Status:** implemented and technically verified on 2026-09-20

**Decision:** Treat the E10 root containing the verified Anlage N subset as the complete synthetic declaration payload defined by the official schema. Validate it locally through `xmlschema` against an explicitly supplied `E10-2024.xsd`, after exact filename and SHA-256 verification. Do not invent optional identity, address, tax-number, transfer-header, or Manufacturer-ID data.

**Official evidence:** The protected, hash-verified ERiC `44.3.6.0` schema confirms the E10 root namespace, fixed `version="2024"`, optional form components, and Anlage N position. The exact official schema digest is `86c735c6a3070aad1ccd90e5bdc8a0999099f44ed76b5752e74d8dfa5cd7d272`; protected schema content remains outside Git.

**Boundary:** Successful XSD validation establishes structural conformance only. It does not execute the official ERiC plausibility engine, sign, authenticate, access credentials or Manufacturer-ID, connect externally, or authorize transmission. Those capabilities remain denied and official ERiC plausibility execution remains the blocker.

**Verification:** Declaration/mapping targeted suite `40 passed`; local acceptance validation against the exact recovered official schema returned `OFFICIAL_XSD_VALIDATED_EXTERNAL_EXECUTION_BLOCKED`; full regression returned `604 passed, 1 skipped`.


## D-076 — Source-evidenced local Anlage N plausibility subset

**Status:** implemented and technically verified on 2026-09-20

**Decision:** Implement only the five official presence rules directly implicated by the bounded mapping: `241`, `310010`, `310070`, `100200001`, and `100200112`. Preserve exact rule codes in immutable local findings and fail closed outside the declared subset.

**Mapping correction:** Official rule `100200112` proves that an `E0204803` other-expense aggregate requires itemization. Require an explicit supported official category and emit `E0205405`/`E0205406` before the matching aggregate. The current bounded synthetic category is `Schreibmaterial`; no generic expense description is inferred.

**Boundary:** A local subset pass is not official ERiC plausibility acceptance. Unimplemented official rules, ERiC FFI, the official engine, credentials/certificates, Manufacturer-ID, signing, networking, real data, and transmission remain outside this result and denied.

**Verification:** Mapping/declaration/plausibility targeted suite `56 passed`; the corrected declaration passed the exact recovered official XSD and the initially bounded five-rule local subset with no findings; the directly implicated paired-field rule `121355` was added in D-077.


## D-077 — Continuous exception-only execution reaffirmed

**Status:** active on 2026-09-20

**Decision:** The Project Owner instructed the project to continue without repeated “continue” prompts wherever no genuine Human Gate applies, with continuous plan-limit monitoring and no routine progress reports. The existing hourly same-task guard was updated to reflect completed developer access, Human login, license acceptance, and protected-material retrieval.

**Operational boundary:** Each heartbeat may perform at most one authorized, prerequisite-ready, local, synthetic, non-production package on the active development branch. At five-hour remaining `25%` or weekly remaining `20%`, no large package starts. At five-hour remaining `15%` or weekly remaining `10%`, no new work starts and a durable `TOKEN_PAUSED` checkpoint is required. Resume requires five-hour remaining at least `80%`, weekly remaining above `10%`, and safe repository recovery.

**Human Gates unchanged:** Real data, Manufacturer-ID, credentials/certificates, authentication actions, official ERiC-engine execution, external connectivity, signing, transmission, production, ELSTER/Finanzamt contact, protected-main action, merge, release, destructive action, and governance/architecture changes remain excluded unless separately and exactly authorized.

**Rule-set completion correction:** The same evidence review identified official rule `121355`, requiring `E0205405` and `E0205406` together. The bounded local subset now covers all six directly implicated presence rules. Targeted and full verification are recorded in the current checkpoint.

**Verification:** Updated targeted suite `57 passed`; full regression `621 passed, 1 skipped`.


## D-078 — Plausibility-rule source provenance binding

**Status:** implemented and technically verified on 2026-09-20

**Decision:** Bind every bounded local E10/2024 plausibility result to the exact reviewed protected annual-documentation artifact: `Jahresdokumentation_E10_2024.ods`, SHA-256 `6379af3c83b8d8ea1f5b8e683d2cfc401cb1506a6018cd44d68452f8b67dacd5`. Filename or digest mutation fails closed and changes the result identity.

**Boundary:** The protected ODS remains outside Git. Provenance binding does not expand the six implemented rules and does not represent official ERiC-engine execution or authorize any protected/external capability.

**Verification:** Plausibility targeted `18 passed`; E10 mapping/declaration/plausibility relevant suite `59 passed`; full regression `623 passed, 1 skipped`.


## D-079 — Current local E10 readiness integration

**Status:** implemented and technically verified on 2026-09-20

**Decision:** Add a new current-state artifact that binds the exact mapping identity, official-XSD declaration identity, and source-provenance-bound passing local plausibility identity. Preserve earlier package contracts as historical evidence instead of mutating their original outcomes.

**Residual boundary:** Local lineage completion does not imply external readiness. Official ERiC plausibility execution, real payload authority, both Article 1 approvals, and a transmitter remain blockers. ERiC FFI, real data, credentials/certificates, Manufacturer-ID, signing, networking, and transmission remain denied.

**Verification:** E10 integrated targeted/relevant suite `75 passed`; full regression `639 passed, 1 skipped`.


## D-080 — Read-only Agent Runtime recovery classification

**Status:** implemented and technically verified on 2026-09-21

**Decision:** Add a deterministic read-only recovery inspector that validates the immutable package artifacts, Kernel audit chain, latest checkpoint, kill switch, and durable response lineage before classifying `PLANNED_RESUMABLE`, `COMPLETED`, or `INTERRUPTED_FAIL_CLOSED`.

**Safety:** The inspector performs no resume, retry, rewrite, deletion, repair, or replay. An interrupted mid-resume state exposes exact completed task IDs and requires governed repair, because automatic replay after an uncertain crash could duplicate effects. Provider activation and every external/production capability remain excluded.

**Verification:** Recovery/runtime targeted suite `15 passed`; relevant runtime/Kernel/pilot suite `46 passed`; full regression `646 passed, 1 skipped`.


## D-081 — UI-9 current local E10 readiness reconciliation

**Status:** implemented and technically verified on 2026-09-21

**Decision:** Replace obsolete UI claims that official mapping/material were unrecovered with the current bounded truth: local E10/2024 mapping and official-XSD validation are complete, and the six-rule local plausibility subset passes. Display the official ERiC engine as `NOT_EXECUTED` and preserve separate Article 1 approval and transmitter blockers.

**Safety:** The change is display-only and synthetic. It adds no approval control, authentication, persistence, real data, credential/Manufacturer-ID access, ERiC invocation, networking, receipt, or transmission capability.

**Verification:** Targeted UI state/review/readiness/app/workflow suite `44 passed`; full regression `649 passed, 1 skipped`.


## D-082 — UI workflow diagnostic consistency

**Status:** implemented and technically verified on 2026-09-21

**Decision:** Advance the synthetic workflow contract to version `2` and replace its obsolete `OFFICIAL_ERIC_MAPPING_NOT_RECOVERED` diagnostic with the verified bounded local E10/2024 XSD-and-six-rule result plus an explicit `OFFICIAL_ERIC_ENGINE_NOT_EXECUTED` boundary. Keep the production submission path unauthorized.

**Safety:** Diagnostics remain a closed privacy-safe allowlist. The change adds no control, approval, authentication, persistence, real data, ERiC invocation, networking, or transmission capability.

**Verification:** Targeted UI state/review/readiness/app/workflow suite `44 passed`; full regression `649 passed, 1 skipped`.


## D-083 — Active plan-limit guard documentation reconciliation

**Status:** implemented and technically verified on 2026-09-21

**Decision:** Reconcile the plan-limit controller document with the later Project Owner authorization that reactivated hourly agent-led continuous execution and exception-only reporting. Preserve the earlier package-7 pause as historical context, not current state, and require every heartbeat to obtain fresh account-service values.

**Boundary:** No thresholds, resume criteria, runtime permission, Human Gate, automation cadence, or project authority changed. The controller remains a cost and continuation guard and cannot create authority.

**Verification:** Canonical checkpoint/current-state/controller consistency inspection and documentation diff check passed; no runtime code changed.


## D-084 — UI-10 synthetic support and recovery diagnostics

**Status:** implemented and technically verified on 2026-09-21

**Decision:** Add a versioned immutable support contract and display-only panel bound to exactly one synthetic case/run. Expose only closed allowlisted status codes for read-only recovery diagnostics, unimplemented pause/resume/stop controls, and receipt absence before transmission. Correct the remaining stale Persian mapping label to the current local E10/XSD state.

**Safety:** The contract rejects arbitrary codes, real classification, enabled controls, receipt presence, and network calls. It performs no stop, resume, repair, replay, authentication, ERiC execution, persistence, or transmission.

**Verification:** Targeted UI/support suite `27 passed`; full regression `653 passed, 1 skipped`.


## D-085 — UI-11 one-click loopback Windows launcher

**Status:** implemented and technically verified on 2026-09-21

**Decision:** Provide a repository-relative Windows double-click launcher for the existing synthetic FastAPI UI. It sets only a process-local source path, opens only `http://127.0.0.1:8000`, binds Uvicorn exactly to loopback, and uses the visible launcher window as the understandable stop boundary.

**Safety:** Deterministic tests deny public/LAN binding, external URLs, credential inputs, and submission paths. The launcher installs and persists nothing and adds no authentication, real data, deployment, ERiC invocation, or transmission.

**Verification:** Targeted launcher/UI suite `15 passed`; full regression `656 passed, 1 skipped`.


## D-086 — UI-12 deterministic phone and keyboard safeguards

**Status:** implemented and technically verified on 2026-09-21

**Decision:** Enforce a deterministic presentation contract for Persian RTL phone widths and keyboard use: preserve viewport/skip-link semantics, stack scope/cards/gates/timeline without hiding safety information, wrap long identifiers, provide 44-pixel targets, and show keyboard focus.

**Safety:** Presentation changes enable no control and add no real data, authentication, persistence, networking, ERiC invocation, or transmission. Hands-on phone validation remains separate.

**Verification:** Targeted responsive/UI suite `15 passed`; regression excluding the unrelated Windows-sensitive Google Drive provisioning file `644 passed, 1 skipped`. Two full Windows runs each had one order-varying pre-existing provisioning journal-replace failure after `658` passes; the first isolated failed case passed.


## D-087 — Focused documentation-index completeness guard

**Status:** implemented and technically verified on 2026-09-21

**Decision:** Reconcile `docs/README.md` with every current focused Markdown document and enforce exact filename-set equality in a deterministic test. Preserve `PROJECT_CHECKPOINT.md` as the only canonical current-status entry point.

**Boundary:** This is documentation and quality enforcement only. It changes no runtime, architecture, authority, external access, or production capability.

**Verification:** Index guard `3 passed`; relevant index/orchestrator-document suite `8 passed`. Full regression not required because no runtime code changed.


## D-088 — Canonical-state drift guard

**Status:** implemented and technically verified on 2026-09-21

**Decision:** Extend deterministic documentation checks so `PROJECT_CHECKPOINT.md`, `CURRENT_STATE.md`, and `ROADMAP.md` cannot silently disagree on the latest completed UI package. Also require the authoritative checkpoint snapshot and current state to retain the same active branch and continuous-execution marker.

**Boundary:** This guard validates durable project memory only. It changes no runtime, architecture, authority, external access, or production capability.

**Verification:** Canonical documentation guard `5 passed`. Full regression not required because no runtime code changed.


## D-089 — UI-13 fail-closed loopback browser policy

**Status:** implemented and technically verified on 2026-09-21

**Decision:** Apply uniform browser hardening to every synthetic FastAPI response: no-store, no-referrer, MIME-sniffing denial, frame denial, restricted device permissions, and a self-only content-security policy that also denies form actions.

**Safety:** The headers reduce accidental browser exposure but do not authorize or implement deployment, public/LAN binding, authentication, real data, persistence, external connectivity, ERiC execution, or transmission.

**Verification:** Targeted UI/security/documentation suite `24 passed`; regression excluding the known Windows-sensitive Google Drive provisioning file `650 passed, 1 skipped`. The full run reached `663 passed, 1 skipped`; after the package-local index correction, the only remaining failure was the pre-existing order-varying provisioning journal-replace issue.


## D-090 — UI-14 closed Persian safety-label catalog

**Status:** implemented and technically verified on 2026-09-21

**Decision:** Present critical workflow, review, readiness, and support states with concise Persian labels from a closed catalog while retaining the exact technical codes for support and audit. Unknown or arbitrary status text fails closed.

**Safety:** The label layer creates no free-form diagnostic channel and adds no private content, control, approval, authentication, persistence, external connectivity, ERiC execution, or transmission capability.

**Verification:** Targeted label/UI/documentation suite `20 passed`; regression excluding the known Windows-sensitive Google Drive provisioning file `652 passed, 1 skipped`.


## D-091 — UI-15 Persian workflow-stage and state labels

**Status:** implemented and technically verified on 2026-09-21

**Decision:** Extend the closed status-label catalog to all workflow stages, stage states, and recovery states. Show concise Persian text first and retain exact technical codes for audit and support.

**Safety:** Unknown values fail closed. The display refinement changes no workflow transition, control, approval, persistence, networking, ERiC execution, or transmission capability.

**Verification:** Targeted label/workflow/UI suite `21 passed`. Broader regression was not required because contract behavior did not change.


## D-092 — UI-16 Persian case, document, and decision labels

**Status:** implemented and technically verified on 2026-09-21

**Decision:** Extend the closed Persian label catalog to case lifecycle, document category/status, Human Gate status, and the allowlisted decision action/destination. Retain exact technical codes beside user-facing labels.

**Safety:** Unknown values fail closed. The presentation refinement changes no case transition, decision authority, document access, control, persistence, networking, ERiC execution, or transmission capability.

**Verification:** Targeted label/UI/document/decision suite `27 passed`. Broader regression was not required because contract behavior did not change.


## D-093 — End-of-package limit checks and immediate continuation

**Status:** active on 2026-09-21

**Decision:** After every completed, verified, committed, and pushed package, read live five-hour and weekly usage. Treat that observation as the authorization check for the next package and begin the next highest-value bounded authorized package immediately when limits, repository safety, prerequisites, and Human Gates permit. A heartbeat may therefore complete multiple sequential packages.

**Safety:** Keep one fresh check at the start of every heartbeat so no work begins from a stale prior-run observation. Existing caution, pause, resume, repository-recovery, authority, and Human-Gate rules are unchanged.

**Operational update:** Automation `plan-limit-continuation-guard` was updated in place and remains active on its hourly cadence with exception-only reporting.


## D-094 — UI-17 semantic and mixed-direction accessibility

**Status:** implemented and technically verified on 2026-09-21

**Decision:** Add semantic table caption/header scopes, explicit decision-expiry labelling, decorative timeline-index suppression for screen readers, and left-to-right direction for technical identifiers inside the Persian RTL interface.

**Safety:** Presentation semantics change no workflow behavior, document access, decision authority, control, persistence, networking, ERiC execution, or transmission capability.

**Verification:** Targeted responsive/UI suite `17 passed`. Broader regression was not required because runtime behavior did not change.


## D-095 — Concise assistive announcement for dynamic case changes

**Status:** implemented and technically verified on 2026-09-21

**Decision:** Announce a successful synthetic case/year workspace change through a dedicated atomic polite status node. Do not mark the complete dynamically replaced workspace as a live region, because that would cause assistive technology to reread every panel after each selection.

**Safety:** Presentation-only and local. No operational control, case mutation, external access, or transmission capability is introduced.

**Verification:** Targeted responsive/UI/documentation suite `23 passed`. Broader regression was not required because runtime behavior did not change.


## D-096 — Remove stale single-package heartbeat wording

**Status:** reconciled and technically verified on 2026-09-21

**Decision:** Reconcile the current-state record and operational controller with D-093. A heartbeat may chain sequential bounded packages only after each completed package is verified, committed, pushed, and followed by fresh limit and repository-safety checks.

**Historical record:** Older decisions that accurately record the former one-package-per-run policy remain unchanged as chronology; D-093 and this reconciliation supersede that operational limit.


## D-097 — Fail closed when the local UI has no scoped case

**Status:** implemented and technically verified on 2026-09-21

**Decision:** Refuse to construct the synthetic local UI when its injected Case Registry is empty. This replaces a later unstructured index failure with an explicit fail-closed state before any page can be served.

**Safety:** No case creation, persistence, external access, or operational capability is introduced.

**Verification:** Targeted UI and canonical-documentation suite `20 passed`.


## D-098 — Optional wage-tax expansion of E10 mapping profile v2

**Status:** implemented and technically verified on 2026-09-21

**Decision:** Extend the bounded synthetic E10/2024 Anlage N mapping with explicitly supplied solidarity surcharge and church-tax amounts. Use `E0200401`/`E0200501` for tax classes 1–5 and `E0200403`/`E0200503` for tax class 6. Omitted values remain absent; no tax amount is inferred.

**Evidence and safety:** Field identities, grouping, order, and decimal lexical form come from the already retrieved, hash-verified official E10/2024 example and annual documentation. Protected source content remains outside Git. ERiC execution, credentials, Manufacturer-ID, networking, real data, and transmission remain denied.

**Verification:** Targeted mapping, declaration, and local-plausibility suite `67 passed`.

**Contract hardening:** Mapping-request identity is proven to change when either optional wage-tax amount changes, and obsolete profile-version `1` requests fail closed after the version-2 expansion.


## D-099 — E10 local plausibility profile v2

**Status:** implemented and technically verified on 2026-09-21

**Decision:** Add official rules `310030`, `310050`, `310060`, `310090`, `310110`, and `310120` to the source-bound local subset. These require gross wages when wage-tax fields exist and require wage tax when solidarity surcharge or church tax exists, separately for tax classes 1–5 and tax class 6.

**Boundary:** This remains a local subset, not official ERiC plausibility execution. The exact protected annual-documentation source remains outside Git and all external capabilities remain denied.

**Presentation reconciliation:** UI review contract version 3 replaces the stale six-rule status with `LOCAL_TWELVE_RULE_SUBSET_PASS`; readiness and UI documentation now describe the same twelve-rule boundary.

**Regression hardening:** Both gross-wage dependency rules (`310030`, `310090`) and all four optional-tax-to-wage-tax dependency rules have explicit negative tests for their respective wage groups.

**Documentation guard:** Active E10/readiness/UI records now have a deterministic check preventing reintroduction of the superseded six-rule status; historical checkpoint text remains preserved.

**Official-XSD verification:** Both tax-class 1–5 and tax-class 6 synthetic declarations containing the new optional solidarity surcharge and church-tax fields passed local validation against the exact hash-pinned official `E10-2024.xsd`. Protected schema files remained outside Git.


## D-100 — Mandatory continuation and fallback-only initial limit check

**Status:** active on 2026-09-21 by explicit Project Owner instruction

**Decision:** Routine heartbeat-start limit checks are disabled. Use a pre-first-package live check only when the current execution window has no valid reliable observation. Every completed/pushed package must be followed by a live limit check, and safe capacity plus an available authorized package requires immediate same-execution continuation.

**Terminal conditions:** Return control only for `TOKEN_PAUSED`, a genuine Human Gate, exhaustion of authorized prerequisite-ready independent packages, unsafe repository ownership/synchronization, unavailable required live limits, a material failure/conflict, or another explicit governance stop. Record the exact terminal condition. Routine success, clean synchronization, and healthy limits are non-terminal. D-100 supersedes D-093 only where D-093 required an unconditional initial check; all thresholds and safety gates remain unchanged.


## D-101 — Preserve explicit-zero versus omitted optional wage taxes

**Status:** technically verified on 2026-09-21

**Decision:** Keep an explicitly supplied zero solidarity surcharge or church-tax amount as `0,00` in the official field, while an omitted value produces no field. The two requests and results retain different artifact identities; absence is never silently converted into a tax assertion.


## D-102 — Optional wage taxes preserve complete local lineage

**Status:** technically verified on 2026-09-21

**Decision:** Verify both supported wage groups with explicit optional solidarity surcharge and church tax through mapping identity, declaration identity, twelve-rule local plausibility, and readiness binding. Both remain externally blocked and produce no operational capability.


## D-103 — Post-expansion unit regression

**Status:** verified on 2026-09-21

**Result:** The complete unit suite excluding only the previously documented Windows-sensitive Google Drive provisioning file passed with `677 passed`. This verifies the E10 mapping/plausibility/UI expansions against the remaining local regression surface; it does not change any authority or external capability.


## D-104 — Historical P1 status records defer to current E10 readiness

**Status:** implemented on 2026-09-21

**Decision:** Preserve the immutable package-2 adapter and synthetic-preview status names for artifact compatibility, but label them explicitly as historical upstream state. Current mapping, official-XSD, and local-plausibility claims must come from the separately versioned E10 readiness pipeline. This documentation reconciliation changes no runtime contract, capability, Human Gate, or external-execution restriction.


## D-105 — Five-minute cross-execution recovery cadence

**Status:** active on 2026-09-21 by explicit Project Owner instruction

**Decision:** The existing `plan-limit-continuation-guard` remains the only continuation automation and runs every five minutes. Each new execution must recover from the clean synchronized pushed checkpoint without overlapping ownership or duplicate package execution. A hard execution-window boundary is not itself a Human Gate. `TOKEN_PAUSED`, limit thresholds, exception-only reporting, and all existing safety and Human Gates remain unchanged.


## D-106 — Complete post-expansion unit regression

**Status:** verified on 2026-09-21

**Result:** The full local unit suite passed with `693 passed, 1 warning`, including the Google Drive provisioning tests previously excluded because of an intermittent Windows file-replacement failure. The earlier behavior was not reproduced in this run, so this result records current verification without claiming that an environment-dependent issue was permanently repaired.


## D-107 — Material-process status is historical upstream evidence

**Status:** implemented on 2026-09-21

**Decision:** Treat the immutable package-3 `RECOVERED_LOCAL_MAPPING_UNVERIFIED` value as historical upstream evidence, not as the canonical current readiness state. Current mapping/XSD/plausibility claims come from the separately versioned E10 readiness pipeline; official ERiC-engine execution and every external capability remain blocked.


## D-108 — Autonomous queue exhausted at governed boundaries

**Status:** active on 2026-09-21

**Decision:** After reconciling current E10 lineage, the five-minute recovery contract, and a complete `693 passed` unit regression, no further authorized, prerequisite-ready, independent bounded package is identified. Track 1 requires an exact repair/replay policy; Track 2 requires explicit synthetic semantics before adding fields or rules; Track 3 real workflows require accepted authority and persistence design. The execution therefore stops under terminal condition 3 (and the associated Human Gates), not because of `TOKEN_PAUSED`, routine success, repository state, or healthy limits.


## D-109 — Local synthetic repair/replay policy

**Status:** designed on 2026-09-21 under explicit Project Owner authority

**Decision:** Permit only continuation from the first demonstrably unstarted stage after a verified planned checkpoint and exact completed-stage prefix. Never replay a completed or ambiguous stage. Bind a write-once repair decision and at most one attempt to the package, package digest, planned checkpoint ID/hash, completed prefix, and policy version. Completed state is an idempotent no-op; partial or contradictory evidence requires Human review. Implement the non-mutating evaluator before any mutating continuation executor. All external, real-data, production, provider, credential, network, subprocess, protected-main, and governance boundaries remain unchanged.


## D-110 — Read-only runtime repair evaluator

**Status:** implemented and technically verified on 2026-09-21

**Decision:** Implement policy version `1` as a read-only evaluator over the verified recovery assessment, Kernel records, immutable artifacts, and optional write-once decision record. The evaluator emits a hash-bound decision, never mutates runtime state, permits only an exact next stage, treats completed state as an idempotent no-op, detects consumed/foreign repair records, and fails closed on missing or contradictory evidence. Targeted repair/recovery/runtime tests pass with `26 passed`.


## D-111 — Reset-aware five-hour TOKEN_PAUSED checkpoint

**Status:** active on 2026-09-21

**Decision:** Live usage reported five-hour `10%` remaining with reset `2026-09-21T17:19:45Z` and weekly `54%` remaining with reset `2026-09-27T16:07:25Z`. The five-hour window is the sole limiting window. Enter `TOKEN_PAUSED`, set `resume_not_before` to `2026-09-21T17:21:45Z` using the governed two-minute buffer, pin continuation to commit `8e42ac6cf3cbe8aed515a23c109ffb79ea6499e0`, and perform no new project work until the existing resume conditions are verified.


## D-112 — Reset-aware execution resumed

**Status:** active on 2026-09-21

**Decision:** The first reset-aligned wake reported five-hour `99%` and weekly `53%` remaining. End `TOKEN_PAUSED`, restore the normal five-minute cadence, execute the repository recovery gate, and continue the already authorized local synthetic runtime repair package from its exact recorded continuation point. All thresholds and Human Gates remain unchanged.


## D-113 — Bounded remaining-stage repair executor

**Status:** implemented and technically verified on 2026-09-21

**Decision:** Connect only an eligible version-1 repair decision to the existing fixed local workers. Write the decision once before mutation, consume one attempt, recheck the exact checkpoint and kill switch, execute only the first unstarted stage and remaining suffix, never overwrite a completed artifact, preserve QA and independent acceptance, then halt and verify the completed checkpoint and audit chain. Completed packages are idempotent no-ops. Targeted repair/recovery/runtime tests pass with `29 passed`; all external capabilities remain denied.


## D-114 — Complete repair-boundary matrix

**Status:** technically verified on 2026-09-21

**Decision:** Verify continuation from implementation, QA, QA acceptance, implementation acceptance, and complete-checkpoint boundaries. At each boundary, preserve earlier artifacts byte-for-byte and execute only the unstarted suffix. Task-only partial stages and later-stage traces without their required prefix remain ambiguous and fail closed. The targeted repair/recovery/runtime suite passes with `34 passed`.


## D-115 — Runtime repair integration regression complete

**Status:** verified on 2026-09-21

**Result:** The complete local unit suite passes with `712 passed, 1 warning` after integration of the repair policy, evaluator, bounded executor, and full continuation-boundary matrix. No authorized prerequisite-ready independent package remains; the next product boundaries require existing Human Gates for provider workers, real UI workflows, additional E10 semantics, or external capabilities.


## D-116 — Explicit spouse/life-partner church-tax semantics

**Status:** implemented and technically verified on 2026-09-21 under explicit Project Owner authority

**Decision:** Mapping profile version `3` accepts an explicit synthetic `partner_church_tax_eur` and maps it to official E10/2024 field `E0200601` for tax classes 1–5 or `E0200603` for tax class 6. Omission remains omission; no relationship, denomination, or amount is inferred. Plausibility profile version `3` includes these fields only in the source-evidenced gross-wage dependencies `310030` and `310090`; it does not invent a wage-tax dependency absent from the reviewed rule subset. Both wage groups validate against the exact official XSD; the focused package suite passes with `109 passed`, and the complete local regression passes with `718 passed, 1 skipped, 1 warning`. Protected material remains outside Git and all external capabilities remain denied.


## D-117 — Profile-v3 downstream record reconciliation

**Status:** implemented and verified on 2026-09-21

**Decision:** Update active downstream adapter, material-process, preview, and current-state descriptions to identify mapping profile v3 while preserving their immutable historical artifact states. This is documentation-only reconciliation; it changes no runtime behavior, authority, rule count, or external capability.


## D-118 — No inferred employee-church-tax dependency

**Status:** technically verified on 2026-09-21

**Decision:** Explicit spouse/life-partner church-tax fields `E0200601` and `E0200603` participate in the reviewed gross-wage rules `310030` and `310090`, but must not be treated as employee church-tax fields for rules `310060` and `310120`. Negative tests protect this fail-closed distinction in both wage groups.


## D-119 — Next E10 professional-association subset

**Status:** source-reviewed but blocked on exact tolerance semantics on 2026-09-21

**Decision:** Bound the next package to one explicit synthetic professional-association contribution using `E0204001` (description), `E0204003` (item amount), and `E0204002` (matching sum). Implement only official rules `100200099`, `100200109`, `201010`, `330121`, and `100200108` from the reviewed protected source. Require paired semantics, derive the sum, enforce the official string/five-digit boundaries, and fail closed without inferring multi-item or real-case content.


## D-120 — Professional-association E10 subset implemented

**Status:** implemented and technically verified on 2026-09-21

**Decision:** Mapping and plausibility profile version `4` implements the bounded D-119 subset. Paired explicit input produces one item and an identical derived sum, invalid semantics fail closed, the five reviewed official rules are evaluated locally, the targeted E10 suite passes with `114 passed`, and the exact official XSD accepts the generated declaration. All external capabilities remain denied.


## D-121 — Profile-v4 integration regression

**Status:** verified on 2026-09-21

**Result:** The complete local unit suite passes with `733 passed, 1 skipped, 1 warning` after the professional-association mapping and five-rule plausibility expansion. This changes no external authority or capability.


## D-122 — Next E10 work-equipment subset

**Status:** source-reviewed and implementation-ready on 2026-09-21

**Decision:** Bound the next package to one explicit synthetic work-equipment expense using `E0204401`, `E0204402`, and derived sum `E0204403`. Implement only reviewed rules `330122`, `100200100`, `100200110`, `122050`, and `121410`. Preserve the exact official tolerance comparison, require paired type/amount semantics, and infer neither multiple items nor real-case content.

**Blocking evidence:** The reviewed rule expresses `122050` with `UngleichMitToleranz5`, but the exact operator definition was not found in the recovered field/rule material. Fail-closed governance prohibits guessing whether the tolerance is absolute, directional, inclusive, or otherwise defined. Keep this subset unimplemented until authoritative semantics are recovered; continue an independent subset instead.


## D-123 — Official `UngleichMitToleranz5` semantics recovered

**Status:** authoritative source recovered on 2026-09-21

**Decision:** The official ERiC 44.3.6.0 document `Zusatzinformationen_zur_Plausibilitaetspruefung.pdf`, section 4.5, page 70, defines `UngleichMitToleranz5` as true exactly when `abs(v1 - v2) > 5`. Differences of `5` or less are accepted. This resolves the D-122 blocker without approximation; protected source content remains outside Git.


## D-124 — Reset-aware five-hour TOKEN_PAUSED checkpoint

**Status:** active on 2026-09-21

**Decision:** Live usage reported five-hour `12%` remaining with reset `2026-09-21T22:23:51Z` and weekly `40%` remaining with reset `2026-09-27T16:07:25Z`. The five-hour window is the sole limiting window. Enter `TOKEN_PAUSED`, set `resume_not_before` to `2026-09-21T22:25:51Z` using the governed two-minute buffer, pin continuation to commit `00703e784c6395495e7cf615f1907379221bcfd5`, and perform no new project work until the existing resume conditions are verified. The exact next action after safe recovery is the already authorized local synthetic D-122 work-equipment subset.


## D-125 — Reset-aware execution resumed for work-equipment subset

**Status:** active on 2026-09-22

**Decision:** The reset-aligned wake reported five-hour `100%` and weekly `39%` remaining. End `TOKEN_PAUSED`, restore the normal five-minute cadence, execute the repository recovery gate from pushed commit `43b53bab41d94922706a8398396f46874669d219`, and continue the already authorized local synthetic D-122 work-equipment subset. All thresholds, external blockers, and Human Gates remain unchanged.


## D-126 — Work-equipment E10 subset implemented

**Status:** implemented and technically verified on 2026-09-22

**Decision:** Mapping and plausibility profile version `5` implements one explicit synthetic `Computer` work-equipment item in `E0204401`, its whole-euro amount in `E0204402`, and derived sum `E0204403`. It evaluates official rules `330122`, `100200100`, `100200110`, `122050`, and `121410`. Rule `122050` uses the authoritative predicate `abs(sum - item_total) > 5`; exact boundary tests prove that differences `-5` and `5` pass while `-6` and `6` fail. The generated declaration passes the exact hash-pinned official E10/2024 XSD. Focused verification passes with `166 passed, 1 warning`; the complete local regression passes with `748 passed, 1 skipped, 1 warning`. All external capabilities remain denied.


## D-127 — Home-office workroom E10 subset implemented

**Status:** implemented and technically verified on 2026-09-22

**Decision:** Mapping and plausibility profile version `6` implements one explicit synthetic home-office workroom expense using `E0204503`, `E0204505`, and derived sum `E0204504`. It evaluates official rules `100200101`, `100200111`, `122056`, `330123`, and `121432`; rule `122056` uses the already recovered exact `abs(sum - item_total) > 5` predicate. The supported type is closed to the official value `Ausstattung (ohne Büromöbel und Computer)`. The combined declaration passes the exact hash-pinned official E10/2024 XSD. Focused verification passes with `181 passed, 1 warning`; the complete local regression passes with `763 passed, 1 skipped, 1 warning`. All external capabilities remain denied.


## D-128 — Training-expense E10 subset implemented

**Status:** implemented and technically verified on 2026-09-22

**Decision:** Mapping and plausibility profile version `7` implements one explicit synthetic training expense using `E0204804`, `E0204808`, and derived sum `E0204812`. It evaluates official rules `100200003`, `100200009`, `100200102`, `100200007`, and `121352`; rule `100200007` uses the exact `abs(sum - item_total) > 5` predicate. The supported type is closed to the official value `Kursgebühren`. The combined declaration passes the exact hash-pinned official E10/2024 XSD. Focused verification passes with `196 passed, 1 warning`; the complete local regression passes with `778 passed, 1 skipped, 1 warning`. All external capabilities remain denied.


## D-129 — Home-office day categories implemented

**Status:** implemented and technically verified on 2026-09-22

**Decision:** Mapping and plausibility profile version `8` adds the two explicit official home-office day categories `E0204507` and `E0206206`. Each optional field accepts only `1..366`; reviewed rule `100200127` rejects a combined total above `366` when both are present. Boundary tests cover `366` and `367`, and the combined declaration passes the exact hash-pinned official E10/2024 XSD. Focused verification passes with `208 passed, 1 warning`; the complete local regression passes with `790 passed, 1 skipped, 1 warning`. All external capabilities remain denied.


## D-130 — Other-expense plausibility completeness

**Status:** implemented and technically verified on 2026-09-22

**Decision:** Plausibility profile version `9` completes the reviewed rules already implicated by the bounded other-expense mapping. Rule `100200103` rejects a negative combined `E0205406`/`E0204802` item total, and rule `100200002` compares `E0204803` with that total using the authoritative `abs(sum - item_total) > 5` predicate. Exact boundary tests cover `-6`, `-5`, `5`, and `6`. Mapping profile version `8` and its explicit synthetic `Schreibmaterial` semantics remain unchanged; no broader category or real-case content is inferred. The focused E10/UI/documentation suite passes with `209 passed, 1 warning`, and the complete local unit regression passes with `795 passed, 1 warning`. All external capabilities remain denied.


## D-131 — Ferry-or-flight E10 subset

**Status:** implemented and technically verified on 2026-09-22

**Decision:** Mapping profile version `9` adds one explicit synthetic ferry-or-flight expense using `E0204801` and `E0204802`, derives `E0204803` from that amount plus the existing `Sonst` item, and fails closed on unpaired, blank, overlong, negative, or out-of-range input. Plausibility profile version `10` adds reviewed rule `121361`, requiring description and amount together. The generated declaration passes the exact hash-pinned official E10/2024 XSD. The focused E10/UI/documentation suite passes with `218 passed, 1 warning`, and the complete local unit regression passes with `804 passed, 1 warning`. No real-case meaning is inferred and all external capabilities remain denied.


## D-132 — Combined other-expense boundary hardening

**Status:** implemented and technically verified on 2026-09-22

**Decision:** Add explicit regression coverage proving that the derived `E0204803` aggregate fails closed when individually valid `Sonst` and ferry-or-flight amounts exceed the official twelve-digit boundary together. Also prove that official rule `100200002` evaluates the combined `E0205406` plus `E0204802` total, accepting an absolute difference of five and rejecting a difference above five. Focused verification passes with `155 passed`, and the complete local unit regression passes with `807 passed, 1 warning`. This changes no mapping or plausibility profile, authority, or external capability.


## D-133 — Ferry-or-flight omission and identity hardening

**Status:** implemented and technically verified on 2026-09-22

**Decision:** Add explicit regression coverage proving that omission of the optional ferry-or-flight context remains distinct from an explicit zero amount, that zero preserves the derived other-expense aggregate, and that adding the paired context changes the cryptographic request and result identities. Focused mapping verification passes with `86 passed`, and the documentation guard passes with `8 passed`. This changes no mapping or plausibility profile, authority, or external capability.


## D-134 — Reset-aware five-hour TOKEN_PAUSED checkpoint after E10 hardening

**Status:** active on 2026-09-22

**Decision:** Live usage reported five-hour `15%` remaining with reset `2026-09-22T03:26:26Z` and weekly `26%` remaining with reset `2026-09-27T16:07:25Z`. The five-hour window is the sole limiting window. Enter `TOKEN_PAUSED`, set `resume_not_before` to `2026-09-22T03:28:26Z` using the governed two-minute buffer, pin continuation to commit `25c6ad1285fda3b043d896c7daa8c44d0e86e9ba`, and perform no new project work until the existing resume conditions are verified.
