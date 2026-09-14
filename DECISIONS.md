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
