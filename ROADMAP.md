# Roadmap

This file contains remaining work only. Completed-stage detail belongs in `DECISIONS.md`, `ERRORS_AND_LESSONS.md`, focused technical documents, and Git history.

Last reconciled: **2026-09-13**

## Completed baseline

The accepted baseline includes case/identity isolation, Drive integration, document/evidence foundations, durable approval, controlled CASE-001 migration, tax dataset/category processing, the six-role tax runtime, Chief supervision, Agent Bridge production architecture, Local Sync, and Windows Relay implementation.

CASE-001 / tax year 2024 analytical preparation is human-confirmed complete and Chief-approved. See `PROJECT_CHECKPOINT.md`.

## Track 1 — Canonical architecture and autonomous project control

Status: **in progress — Phase O2 technically complete; Human acceptance gate open**

Goals:

- preserve all existing GitHub, ChatGPT Work, Codex, Windows, Python/Docker, Google Drive, Gemini, Agent Bridge, Local Sync, Windows Relay, approval, audit, and tax-agent integrations;
- define one current architecture map and capability registry;
- implement a durable Master Project Orchestrator;
- maintain a persistent task/dependency graph and exact task lineage;
- delegate bounded work to specialist Agents;
- independently verify code, tests, security, and documentation;
- continue routine low-risk work without repeated human interaction;
- provide compact milestone, cost, blocked, and final reports;
- preserve Human Gates and a global kill switch.

Exit criteria:

- a project can run across process/session boundaries;
- restart recovers exact task state without chat history;
- routine failures are retried or delegated within policy;
- no Agent self-approves its own consequential output;
- only genuine Human Gates interrupt the user;
- every material transition updates `PROJECT_CHECKPOINT.md`.

## Track 2 — Controlled ELSTER/Finanzamt integration

Status: **planned; no transmission performed**

Goals:

- select and document the supported official integration path;
- implement tax-year-specific schema/form mapping;
- validate completeness and plausibility before transmission;
- produce a complete human-readable preview;
- require explicit case/run/artifact-bound human authorization;
- perform authenticated transmission only after authorization;
- store official response/receipt and audit evidence;
- fail closed on version, credential, network, schema, or response uncertainty;
- support safe retry/recovery without duplicate filing.

Exit criteria:

- a controlled test path succeeds;
- one explicitly authorized real submission succeeds;
- receipt and final package are durably recoverable;
- no submission can occur silently or from stale authorization.

## Track 3 — User interface

Status: **planned**

Goals:

- create/select person, entity, case, and tax year;
- upload and inspect documents;
- show processing state, Agent findings, evidence gaps, and provenance;
- display calculations and ELSTER/form preview;
- present Human Gates clearly;
- authorize submission and display its receipt;
- expose pause, resume, stop, recovery, and support diagnostics;
- work from phone and Windows without requiring GitHub or terminal use.

Exit criteria:

- a user completes the supported workflow through the UI;
- no terminal, Codex session, or ChatGPT conversation is required for ordinary use;
- errors are actionable and do not expose secrets or private data.

## Track 4 — Product-level acceptance and release

Status: **blocked by Tracks 1–3**

Required acceptance flow:

`Create Case -> Upload Documents -> Process -> Specialist Review -> Chief Review -> Calculation -> Form Preview -> Human Approval -> ELSTER Submission -> Receipt`

Required operational checks:

- restart and crash recovery;
- idempotency and duplicate-submission prevention;
- authorization expiry/revocation;
- backup and restore;
- monitoring and bounded notifications;
- dependency/version update process;
- annual tax-law and ELSTER compatibility update;
- security and privacy review;
- cost and rate-limit controls;
- end-to-end audit reconstruction.

Exit criteria:

- ordinary operation is independent of chat and development tools;
- supported workflows are repeatable and documented;
- unresolved limitations are explicit;
- the human issues final production acceptance.

## Dependency order

1. Canonical architecture/capability inventory.
2. Master Orchestrator contract and persistent control plane.
3. Controlled pilot of autonomous development.
4. ELSTER integration.
5. UI implementation.
6. End-to-end product acceptance.
7. Production release and operational handoff.

ELSTER and UI work may overlap only after their shared backend, identity, state, approval, and audit contracts are stable.

## Future-file rule

A planned artifact must be registered here before creation. Registration must state its purpose and dependency. A file is not implemented merely because it is planned.

## Cleanup rule

- Current status belongs only in `PROJECT_CHECKPOINT.md` and `CURRENT_STATE.md`.
- Completed history must not remain in this roadmap as active work.
- Obsolete progress snapshots may be deleted after their durable rules, decisions, verification evidence, and lessons are preserved canonically.
- Code, tests, audit contracts, and recovery evidence are not disposable merely because their original stage completed.


## Constitutional foundation

Project Constitution v2 is ratified and active at `CONSTITUTION.md`.

## Registered organizational artifact

- `docs/agent-organization-v1-proposal.md` — Human-ratified active organizational contract defining the Agent chart, 20 permanent roles, three inactive domain templates, hierarchy, access tiers, authority boundaries, communication routes, Agent lifecycle, deterministic kernel boundary, separation of duties, and O0–P4 execution path.

Phase O2 contract design and technical verification are complete. Human acceptance is required before Phase O3. Agent activation and Master Orchestrator implementation remain gated behind their later phases.

## Registered Phase O2 artifacts

The following Phase O2 artifacts were implemented at `382a140e42496ad9edd92dc2016cfde51d091575`. They depend on the ratified Agent Organization v1 contract and await Human phase acceptance before Phase O3 begins:

- `contracts/orchestrator/v1/contract-set.json` — versioned index and compatibility boundary for the complete O2 contract set.
- `contracts/orchestrator/v1/roles.json` — canonical catalog of the 20 permanent Agent roles and three inactive domain templates.
- `contracts/orchestrator/v1/agent-manifest.schema.json` — strict schema for temporary, task-bound Agent instances.
- `contracts/orchestrator/v1/permission-matrix.json` — access-tier, capability, role-default, and A6-denial policy.
- `contracts/orchestrator/v1/task.schema.json` and `response.schema.json` — registered command, lineage, evidence, status, and handoff contracts.
- `contracts/orchestrator/v1/lifecycle.json` — Agent-instance lifecycle states, transitions, expiry, revocation, and retention rules.
- `contracts/orchestrator/v1/human-gates.json` — Human Gate triggers, conflict-of-interest rules, and two-stage external-transfer policy.
- `contracts/orchestrator/v1/execution-policy.json` — budget, timeout, retry, loop, escalation, and kill-switch policy.
- `docs/o2-machine-readable-contracts.md` — authoritative design, invariants, compatibility rules, and Phase O2 acceptance evidence.
- `scripts/validate_o2_contracts.py` — deterministic offline validator for cross-contract consistency; it grants no runtime authority.
- `tests/unit/test_o2_contracts.py` — positive and fail-closed contract validation coverage.
