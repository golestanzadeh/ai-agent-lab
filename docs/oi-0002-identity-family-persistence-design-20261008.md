# OI-0002 — Identity & Family Persistence: bounded implementation contract

Status: **DESIGN BASELINE RECORDED / IMPLEMENTATION NOT AUTHORIZED OR ACCEPTED**
Date: 2026-10-08
Authority: Owner-requested architecture review; CASE001-DR04-RECOVERY-20261008 stage 1.
Scope: compatible extensions of existing registries and protected persistence only. No CASE-001 identity inference, fact registration, Codex dispatch, or external transmission.

## Reviewed actual code and constraints

- `src/agent_lab/person_entity_registry.py`: `PersonRecord`/`EntityRecord` have stable IDs, timestamps, schema_version and lookup attributes, but registry dictionaries and `CaseAssociation` set are **in-memory only**. `associate_case` checks known identity but not Case Registry existence, owner binding or tax-year role; its `validate` checks only identity existence. Attribute lookup deliberately reports ambiguity.
- `src/agent_lab/case_registry.py`: in-memory case records, canonical owner_type/owner_id, tax period, assessment mode, opaque storage root; case resolution and root uniqueness validation exist. It is the authority for case scope, not a family-role graph.
- `src/agent_lab/case_identity_association.py`: in-memory association set and strict owner-only validation (`case.owner_id == identity_id`). It cannot represent a spouse/child as a non-owner party and loses associations on restart. Do **not** relax owner invariants to fit a spouse.
- `src/agent_lab/human_declared_fact.py`: immutable v1 fact, case/year/semantic key, confirmation, provenance and artifact hash, but **no subject_id/party binding**, and no general durable fact repository. `assert_consumable` validates case/year/confirmation/validation, not person membership.
- `src/agent_lab/durable_approval.py`: SQLite WAL/transactions and integrity digests exist for approvals. This is a useful implementation pattern, **not** authority to repurpose approval tables or merge unrelated stores.
- `src/agent_lab/case_state.py`: `parties_ref` and `facts_ref` exist, but state itself is in-memory; a pointer alone does not prove protected facts are durable.
- `docs/person-entity-registry.md`: explicitly keeps household/case-specific relationships outside the global identity registry, requires evidence-backed resolution, audit and case-scoped access.
- CASE-001 protected Owner Declaration integrity previously verified at SHA-256 `560310A335E80C54E37F5030E5213180072E0C2F2787D819F924B9CA8D98A0F3`; existing case owner reference is `CASE-001-OWNER`, **not** verified Person A or Person B. Do not map identities from labels or names.

## Compatible logical schema (versioned extension, not parallel authority)

**Identity**: reuse `PersonRecord`/`EntityRecord` fields and ID namespace. Durable rows `identity_record(identity_type, identity_id, schema_version, status, created_at_utc, updated_at_utc, protected_lookup_ref, revision, integrity_digest)`; unique `identity_id`, immutable type and ID. Keep names/identifiers in protected storage only, not Git/logs.

**Case owner**: `CaseRegistry` retains `case_id, owner_type, owner_id, tax_period, assessment_mode, storage_scope_reference` as canonical. Existing `CaseIdentityAssociationService.associate` remains **owner-only**. No implicit rebind of `CASE-001-OWNER`; resolve its authoritative mapping through protected evidence and an explicit approved migration if needed.

**Case parties and time-bounded roles**: add a case-scoped `case_party_role(role_binding_id, case_id, subject_type, subject_id, role_code, valid_from, valid_to_exclusive, evidence_ref, authorization_ref, revision, status, integrity_digest)` persisted under the existing protected case scope, exposed via a compatible case-party service/extension rather than a new global identity registry. At minimum role vocabulary: `TAXPAYER`, `SPOUSE`, `CHILD`; actual applicability must be evidence-supported. Half-open date interval `[valid_from, valid_to_exclusive)`; open-ended end allowed; `valid_from < valid_to_exclusive` when end exists. Tax-year membership is determined by explicit period overlap plus domain-specific tax-rule checks, **not** assumed from overlap alone. Reject conflicting same-role bindings for the same case/period; retain history and effective-dated changes.

**Subject-bound fact v2 envelope**: preserve all existing `HumanDeclaredFact` v1 artifacts and their exact digests. Create a *versioned successor binding/envelope* `subject_fact_binding(binding_id, case_id, tax_year, subject_type, subject_id, semantic_key, fact_artifact_ref, declaration_artifact_ref, confirmation_ref, authorization_ref, valid_from, valid_to_exclusive, revision, integrity_digest)`; link to an existing confirmed immutable v1 fact or a separately versioned v2 fact only when necessary. Never add a default subject to v1, recompute historical artifact hashes, or silently migrate fact values. For case-level facts use an explicit case-scope kind, not a guessed person. Fact readback must verify case, year, subject membership, provenance, content integrity and confirmation.

**Storage contract**: use the existing frozen Persistence Contract and protected CASE-001 artifact boundary; implement a compatible durable adapter with atomic transactions, schema migrations, integrity verification, idempotency keys and read-after-restart. SQLite WAL is a proven local pattern already used by `DurableApprovalStore`; it is a *candidate adapter*, not an approved change to the frozen deployment/storage decision. Keep metadata indexes distinct from protected document bodies; no raw facts or PII in Git. Before implementation locate and verify the authoritative frozen Persistence Contract (not found in the inspected code/docs subset); if its provider/schema requirements conflict, **stop for contract reconciliation** rather than inventing a second database.

## Deterministic operations and security invariants

1. `resolve_subject(subject_type, subject_id)`: exact unique identity, otherwise `NOT_FOUND/AMBIGUOUS/HUMAN_REQUIRED`; never match by name alone.
2. `bind_case_party(case_id, subject_id, role, effective_interval, evidence, authorization, request_id)`: resolve Case Registry first, enforce authorized exact case scope and type, reject invalid intervals/overlapping conflicts, persist atomically, idempotent replay only for byte-equivalent request.
3. `register_subject_fact(case_id, year, subject_id_or_case_scope, immutable_fact_ref, authorization, request_id)`: require confirmed owner declaration and validated case party; reject wrong subject, wrong year, changed payload under reused request ID, missing lineage, or unconfirmed evidence. Preserve prior revisions.
4. `read_subject_facts(case_id, year, subject_id)`: verify authorization, case root, subject association and integrity; fail closed on mismatches and corrupted records. No global Drive discovery or cross-case data joins.
5. Use UTC canonical audit timestamps, explicit effective dates, versioned migrations, monotonic revisions, and immutable evidence references. Identity creation/correction and role/fact changes require auditable actor, decision and provenance.
6. Restrict protected store paths/credentials to authorized runtime; do not expose taxpayer data in logs, GitHub, CI fixtures, telemetry or agent prompts. Do not transmit to ELSTER/Finanzamt.

## Acceptance scenarios (synthetic data only)

- T01: create two distinct synthetic person identities, persist, close/reopen store, resolve same IDs and digests.
- T02: existing Case Registry owner association remains strict; spouse as case party succeeds only via explicit party-role path, not owner bypass.
- T03: roles valid in 2024 but changed in 2025 return correct effective-date history; boundary dates and open-ended intervals tested.
- T04: same case/role overlapping conflicting bindings fail closed; non-overlap and evidence-backed correction preserve audit history.
- T05: unknown, ambiguous, archived/unresolved identity cannot silently become confirmed party; owner identity mismatch fails.
- T06: confirmed v1 fact binds through versioned envelope to exact synthetic subject; original artifact digest unchanged.
- T07: wrong case, wrong tax year, unrelated subject, unconfirmed fact, altered fact digest and reused request ID with changed payload all fail closed.
- T08: identical registration replay is idempotent across restart; crash/partial write cannot produce orphaned party/fact rows.
- T09: two cases with shared subject cannot read one another's facts without distinct exact case authorization; different storage roots enforced.
- T10: corrupted storage row, unsupported schema version, missing lineage or bad digest prevents readback and is audited.
- T11: legacy v1 identity/case/fact tests remain green; historical CASE-001 calculation/DR-03 and DR-04 rounding identities untouched.
- T12: actual CASE-001 Person A/B bootstrap remains `HUMAN_REQUIRED` until authoritative protected identity evidence is mapped; never synthesize live identities in tests.

## Stage 1 exit gate and handoff

**Implementation is NOT PASS.** Before development: (a) locate frozen Persistence Contract and existing protected storage adapter; (b) confirm authoritative CASE-001 owner/party identity references or retain Human Gate; (c) review migration and security design; (d) obtain separate bounded implementation authorization; (e) use current supervisor-provided quota, conservative Limit Guard and reserve. Development must stay within stage 1, not run Package A or DR-01.

Acceptance requires reviewed schema/migration, successful T01–T12 (or documented equivalent), durable protected readback, no legacy regressions, evidence-linked audit, independent/Owner-authorized acceptance decision, and updates to `PROJECT_CHECKPOINT.md`, recovery plan and `OPEN_ITEMS.md` together. Until then `OI-0002` stays OPEN.

## Authoritative persistence and party-model reconciliation — 2026-10-08

**Recovered Owner-approved design decision from 2026-09-29 project Storage conversation:** `Persistence Contract v1 — FROZEN`. This decision was made in the prior project design conversation; the reviewed Git branch did **not** contain a separately titled frozen contract artifact. The present section durably records the recovered decision, without claiming that a matching pre-existing Git commit was found.

- SQLite is the authoritative **current structured application database**; Google Drive is the authoritative **private file/document store**; GitHub holds engineering assets and non-sensitive governance evidence only. Keep **one authoritative database per deployment**, with deterministic `case_id` isolation, not one improvised database per case.
- Introduce/extend the existing application persistence abstraction; schema must be PostgreSQL-portable from the outset: application-generated stable IDs, explicit primary/foreign/unique/check constraints and indexes, UTC timestamps, schema versions, transactional updates, audit lineage and fail-closed cross-case access. SQLite→PostgreSQL is an upgrade path, **not** a current migration or a second live database.
- Do not place a live SQLite database file in a Google Drive-synced folder. Do not store document binaries inside SQLite. The existing `DurableApprovalStore` SQLite implementation is a compatible precedent; preserve its approval authority and tables. No new competing Kernel/Case Registry/approval authority.
- `docs/case-party-model.md` already specifies canonical roles `PRIMARY_TAXPAYER`, `SPOUSE_OR_PARTNER`, `CHILD`, `OTHER_DEPENDENT_OR_RELEVANT_PERSON`, etc., and **many-to-many** fact/document attribution including shared household scope. These authoritative role codes supersede the illustrative `TAXPAYER`/`SPOUSE` vocabulary earlier in this document. Preserve spouse-specific facts and independent dates; shared household facts do not imply equal allocation.
- The previously frozen document-intake `WritableCaseScopedStorageAdapter` boundary, where applicable, is separate from the current metadata-only Google Drive adapter. Do not interpret metadata-read access as permission for Drive writes; no document intake/upload capability is authorized by OI-0002.
- Evidence: existing repo `DECISIONS.md` D-012/D-013, `docs/architecture.md`, `docs/case-party-model.md`, `docs/agent-case-storage-provisioning.md`, `docs/document-identity-persistence.md`, `src/agent_lab/storage.py`, `src/agent_lab/durable_approval.py`; Owner's 2026-09-29 frozen Storage decision recovered from project conversation. This is a **design documentation recovery**, not evidence that SQLite person/family persistence already exists.

**Stage 1 implementation guidance updated:** implement the compatible person/case-party/subject-fact persistence tables through the approved SQLite structured-data boundary, with PostgreSQL-compatible schema and migrations; preserve existing authority, identity and artifact hashes. Stage remains OPEN until real implementation, tests and acceptance. CASE-001 real person identities still require protected authoritative evidence; never invent them.
