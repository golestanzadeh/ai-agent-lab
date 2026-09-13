# Roadmap

This file contains remaining work only. Completed-stage detail belongs in `DECISIONS.md`, `ERRORS_AND_LESSONS.md`, focused technical documents, and Git history.

Last reconciled: **2026-09-13**

## Completed baseline

The accepted baseline includes case/identity isolation, Drive integration, document/evidence foundations, durable approval, controlled CASE-001 migration, tax dataset/category processing, the six-role tax runtime, Chief supervision, Agent Bridge production architecture, Local Sync, and Windows Relay implementation.

CASE-001 / tax year 2024 analytical preparation is human-confirmed complete and Chief-approved. See `PROJECT_CHECKPOINT.md`.

## Track 1 — Canonical architecture and autonomous project control

Status: **next**

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


## Registered constitutional artifact

- `docs/constitution-v2-proposal.md` — proposed supreme constitution for the governed adaptive Orchestrator and Agent Factory. It must remain non-operative until the human explicitly ratifies its exact content. After ratification, it will replace the current `CONSTITUTION.md` through a dedicated governed commit and decision record.
