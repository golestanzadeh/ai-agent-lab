# CASE-001/2024 — DR-04 Recovery Execution Plan (Authoritative)

Plan ID: CASE001-DR04-RECOVERY-20261008
Status: OWNER-APPROVED EXECUTION ORDER / NOT AN EXECUTION AUTHORIZATION
Owner directive: 2026-10-08
Repository branch: d022-supervisor-loop-design
Canonical status authority: PROJECT_CHECKPOINT.md and independently accepted evidence.

## Purpose
Use CASE-001/2024 to discover and resolve foundational structural defects before completing DR-04. Preserve all prior accepted financial evidence and calculation versions. This plan is a durable cross-session continuation contract, not a new orchestrator, scheduler, registry, or replacement checkpoint.

## Mandatory order and gates

| Order | Stage | Current baseline | Exit gate |
|---|---|---|---|
| 1 | Identity & Family Persistence | BLOCKED / not implemented durably | Approved compatible schema, persistent person identities, effective-dated family/case roles, subject-bound immutable protected facts, deterministic readback, tests, independent acceptance PASS |
| 2 | Package A — Owner Facts Registration | BLOCKED / HUMAN_REQUIRED at f9a4b99 | Verify existing protected owner declaration integrity, bind confirmed 2024 facts to authoritative subjects, idempotent protected persistence, independent acceptance PASS |
| 3 | DR-01 — Lineage Reacceptance | Historical PASS but successor independent acceptance FAIL | Recover or safely reconstruct exact request/result/XML identities from authoritative evidence, detect substitution, validate official XSD and identity bindings, independent acceptance PASS |
| 4 | DR-02 — Independent Reacceptance | BLOCKED pending DR-01 | Independent lineage and substitution-resistant validation based on accepted DR-01, independent acceptance PASS |
| 5 | Package B — Annual Carryover Contract & Kernel Gate | PLANNED | Versioned annual profile snapshot, effective-dated carryover/change review, deterministic Kernel gate, tests and independent acceptance PASS |
| 6 | Package C — Bilingual Annual Questionnaire & UI | PLANNED | German/Persian RTL/LTR change-review UI, explicit Owner annual snapshot approval, Kernel integration, tests and independent acceptance PASS |
| 7 | DR-04 — Rounding & Declaration Acceptance | Part 1 implemented; full acceptance pending | Reconcile accepted successor rounding and precise artifacts, bind ten official plausibility rules, full tests, independent acceptance PASS |

Execution order is 1→2→3→4→5→6→7. Packages B/C are OWNER-CHOSEN schedule order, not technical prerequisites for DR-04. DR-03 has historical acceptance; verify compatibility without gratuitous replay. DR-05 remains blocked until its own prerequisites are satisfied.

## Known evidence and cautions
- CASE-001/2024 frozen historical analytical refund EUR 133.83; DR-04 Part 1 versioned rounding successor refund EUR 134.00. Preserve both identities; do not silently overwrite or conflate.
- Historical DR-01 accepted at 6b3c90c, but independent lineage reacceptance could not recover original immutable request/result/XML identities. A PASS must not be inferred from historical XSD success.
- Package A attempt CASE001-OWNER-FACTS-PACKAGE-A-20261008 ended HUMAN_REQUIRED/SCHEMA_BLOCKED at f9a4b99. Owner declaration integrity PASS; owner fact registration and identity binding BLOCKED.
- Protected declaration exists outside Git in the CASE-001 protected artifacts store; no private taxpayer facts, identity attributes, credentials or protected content may enter this repository.
- Existing CaseRegistry, PersonEntityRegistry, CaseIdentityAssociationService, HumanDeclaredFact, frozen Persistence Contract, and DurableApprovalStore must be inspected and extended compatibly. Do not create parallel registries, stores, orchestrators, or checkpoint files.
- Existing confirmed Owner facts for 2024 are final. Never demand reconfirmation of unchanged historical facts. A future-year annual review is distinct.
- Technical person/role mapping must be supported by authoritative identity evidence; do not guess from role labels or names.
- Do not rerun Gemini, reparse the 946-row ledger, or reopen accepted tax calculations absent a separately authorized evidenced defect.
- No ERiC/ELSTER/Finanzamt transmission, signing, certificate use, merge, release, or scheduler/Wake is authorized by this plan.

## Durable continuation protocol
Before every project task or status claim:
1. Read PROJECT_CHECKPOINT.md, AGENTS.md, and this plan; inspect current GitHub branch HEAD and relevant authoritative artifacts.
2. Read actual independently accepted stage evidence and current blocker, not merely a historical PASS label.
3. Check authenticated live Codex quota, Limit Guard and reserve before dispatch. Never treat a stale quota snapshot as live.
4. Execute only the next independently authorized bounded package. Stop at HUMAN_REQUIRED, schema blocker, capacity pause, or acceptance FAIL.
5. After each stage, update this plan's status table AND PROJECT_CHECKPOINT.md in the same governed change, with evidence paths, commit IDs, test results, independent acceptance, and exact next permitted action. Do not mark PASS without actual acceptance.
6. Preserve prior states and owner decisions in Git history. Do not erase, skip, or silently reorder unfinished steps.
7. Completion is reached only when all seven stages have independently accepted PASS, including DR-04. Until then this plan remains an active required reference.

## Change control
Only explicit Owner approval can reorder or remove a stage or expand scope. Record the change with rationale in DECISIONS.md and update checkpoint/plan together. This documentation records the approved order; it does not authorize implementation, external action, or automated continuation.

## Parallel GitHub CI email-notification repair — tracked independently

**Priority:** Owner reports excessive GitHub Inbox emails. Required reference: [DOC-INDEX-CI-REPAIR six-step plan](doc-index-ci-repair-plan-20261008.md). Status: OWNER-PRIORITIZED / NOT EXECUTED. This is an independent bounded CI/documentation-maintenance workstream, not a prerequisite for DR-04.

Reported failing test: `test_every_focused_document_is_registered_in_the_index`. The exact root cause and which notifications correspond to this test must be verified against live GitHub Actions evidence. Six steps: identify failing documents/workflows → determine index eligibility → minimally repair index → rerun exact test → run related CI regression → independent acceptance and checkpoint evidence. Do not disable tests or blanket-mute notifications.

**Separate, unrelated topic:** governed operational email notification sender remains PROVIDER_BLOCKED after a failed real activation attempt. Do not conflate the project's outbound notification provider with incoming GitHub CI emails. This tracking does not authorize mailbox access or email sending.
