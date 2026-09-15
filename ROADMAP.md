# Roadmap

This file contains remaining work only. Completed-stage detail belongs in `DECISIONS.md`, `ERRORS_AND_LESSONS.md`, focused technical documents, and Git history.

Last reconciled: **2026-09-13**

## Completed baseline

The accepted baseline includes case/identity isolation, Drive integration, document/evidence foundations, durable approval, controlled CASE-001 migration, tax dataset/category processing, the six-role tax runtime, Chief supervision, Agent Bridge production architecture, Local Sync, and Windows Relay implementation.

CASE-001 / tax year 2024 analytical preparation is human-confirmed complete and Chief-approved. See `PROJECT_CHECKPOINT.md`.

## Track 1 — Canonical architecture and autonomous project control

Status: **Phase P1 local synthetic scope complete through package 7; protected ERiC access and UI-1 continuation authorized**

Registered cross-phase cost-control artifact:

- `docs/plan-limit-continuation-controller.md` — design for live Codex plan-limit inspection, conservative stop thresholds, durable `TOKEN_PAUSED` checkpoints, and guarded same-thread scheduled continuation after the actual account reset.

Implementation status: **exact continuation authority recorded**. Hourly same-task heartbeat `plan-limit-continuation-guard` may be reactivated for one bounded local UI package per run; it must stop at registration submission, protected-download authentication, architecture, production, real-data, external-connectivity, or other consequential gates.

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

Status: **protected ERiC developer-registration/material-retrieval boundary authorized and started; awaiting Human-entered registration data and CAPTCHA**

Registered Phase P1 package 1 artifacts:

- `src/agent_lab/elster_dry_run.py` — deterministic synthetic-only submission-envelope identity, two-stage approval-binding evaluator, and permanently non-transmitting dry-run plan.
- `tests/unit/test_elster_dry_run.py` — exact-route, synthetic isolation, immutable identity, two-stage ordering/binding, expiry, mutation, and no-transmission tests.
- `docs/p1-controlled-elster-path.md` — official-route evidence, bounded architecture, acceptance criteria, limitations, and next Human Gate.

Package 1 implementation commit: `aaf5bec86e103480ef5d36cedca29cfbfb607862`. Verification: targeted `23 passed`; full regression `405 passed, 1 skipped`; Python compile check passed. The Project Owner explicitly accepted this exact package and commit on 2026-09-14. The later package-2 authority below supersedes only its design gate; every developer-access or external-capability step still requires separate explicit authority.

Registered Phase P1 package 2 artifacts:

- `src/agent_lab/eric_adapter_contract.py` — versioned, non-production ERiC adapter contract and deterministic fail-closed compatibility assessment; no FFI, XML mapping, credential, network, signing, or transmission capability.
- `tests/unit/test_eric_adapter_contract.py` — exact-version, route-binding, official-material completeness, synthetic isolation, and capability-denial tests.
- `docs/p1-eric-adapter-contract.md` — package-2 boundary, unknowns, acceptance criteria, and next Human Gate.

Initial package 2 implementation commit: `a024ff5c608700ff7650c4b9c02c643fa72884fd`. The three Human-authorized hardening amendments are implemented at `3fd1e4d586cc97411acaa563e6d5712e31c5dacd`: non-forgeable plans, hash-bound material/capability policies, and explicit blocked-mapping outcome. Amended verification: relevant package-1/package-2 suite `45 passed`; full regression `427 passed, 1 skipped`; Python compile check passed. The Project Owner explicitly accepted the amended package and exact commit on 2026-09-14. Every further package, developer-access step, and external capability requires separate exact authority.

Registered Phase P1 package 3 artifacts:

- `src/agent_lab/eric_material_process.py` — deterministic synthetic-only registration and independent-review process for the three required ERiC material categories; official status remains blocked.
- `tests/unit/test_eric_material_process.py` — completeness, uniqueness, route/version binding, review independence, mutation, and no-external-capability tests.
- `docs/p1-eric-material-process.md` — package-3 process, acceptance criteria, limitations, and next boundary.

Package 3 implementation commit: `2d6efd25e85ba9874ccbdad695b5b24c0c205887`. Verification: relevant P1 suite `66 passed`; full regression `448 passed, 1 skipped`; Python compile check passed. The Project Owner explicitly accepted the package and activated revocable continuous authority for remaining local synthetic/non-production P1 work. No such authority crosses an external or consequential Human Gate.

Next registered continuous-authority package:

- `src/agent_lab/elster_preview.py` — immutable Human-readable synthetic preview bound to accepted P1 identities with no execution capability.
- `tests/unit/test_elster_preview.py` — preview completeness, deterministic rendering, mutation sensitivity, binding, and capability-denial tests.
- `docs/p1-synthetic-preview.md` — preview contract, limitations, evidence, and continuation boundary.

Package 4 implementation commit: `8237882d29c2d7171f776fe684e2f0d1b609d476`. Verification: relevant P1 suite `77 passed`; full regression `459 passed, 1 skipped`; Python compile check passed. It completed under continuous authority without a package-level Human Gate.

Next registered continuous-authority package:

- `src/agent_lab/elster_submission_lifecycle.py` — synthetic-only state machine for idempotency, bounded retry planning, duplicate prevention, and receipt placeholders with no transmitter.
- `tests/unit/test_elster_submission_lifecycle.py` — transition, identity, retry, duplicate, mutation, and capability-denial tests.
- `docs/p1-synthetic-submission-lifecycle.md` — lifecycle contract, limitations, evidence, and external boundary.

Package 5 is implemented and verified under continuous authority. Verification:
targeted `15 passed`; relevant P1 `92 passed`; full regression `474 passed, 1 skipped`;
Python compile check passed.

Next registered continuous-authority package:

- `src/agent_lab/elster_submission_audit.py` — privacy-minimized synthetic lifecycle audit and deterministic restart/recovery assessment.
- `tests/unit/test_elster_submission_audit.py` — lineage, replay, corruption, restart, and capability-denial tests.
- `docs/p1-synthetic-submission-audit.md` — audit/recovery contract, limitations, evidence, and external boundary.

Package 6 is implemented and verified under continuous authority. Verification:
targeted `12 passed`; relevant P1 `104 passed`; full regression `486 passed, 1 skipped`;
Python compile check passed.

Next registered continuous-authority package:

- `src/agent_lab/elster_readiness_dossier.py` — immutable synthetic P1 evidence manifest and explicit external-readiness blockers with no execution capability.
- `tests/unit/test_elster_readiness_dossier.py` — completeness, lineage, mutation, privacy, blocker, and capability-denial tests.
- `docs/p1-synthetic-readiness-dossier.md` — dossier contract, verification evidence, and next Human Gate boundary.

Package 7 is implemented and verified under continuous authority. Verification:
targeted `19 passed`; relevant P1 `123 passed`; full regression `505 passed, 1 skipped`;
Python compile check passed.

The Project Owner authorized developer registration and protected retrieval of the
official ERiC documentation/package on 2026-09-15. The official registration form
has been opened, but no personal/organizational value has been entered and no form
has been submitted. Human entry of the exact contact values, CAPTCHA completion,
and action-time confirmation before final submission are still required. This
authority does not include manufacturer-ID work, tax-transmission credentials or
certificates, real taxpayer data, acceptance-server connectivity, transmission,
Finanzamt contact, production activation, or action on `main`.

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

Status: **package UI-1 foundation complete; implementation architecture Human Gate reached**

Registered UI package 1 artifact:

- `docs/ui-phase-foundation.md` — non-production interaction and safety foundation for the ordinary cross-device workflow, derived from the stable case, identity, state, approval, audit, and synthetic ELSTER contracts; no framework selection, external connection, real data, or submission capability.

Package UI-1 is implemented at `docs/ui-phase-foundation.md`. Targeted safety-contract
regression: `63 passed`. The next interactive prototype requires an explicit UI
architecture/framework choice. Production architecture, real-data use, external
deployment, and submission capability remain separate Human Gates.

Registered architecture-neutral UI package 2 artifacts:

- `src/agent_lab/ui_state_contract.py` — immutable synthetic presentation-state contract that resolves `case_id` through the Case Registry, clears stale scope on case changes, represents Human Gates exactly, and permanently disables submission.
- `tests/unit/test_ui_state_contract.py` — case isolation, stale-state clearing, exact gate binding, synthetic privacy, and denied-submission tests.
- `docs/ui-state-contract.md` — state fields, invariants, verification evidence, and framework Human Gate.

Package UI-2 is implemented and verified. Verification: targeted `7 passed`;
relevant safety-contract regression `70 passed`; full regression `512 passed, 1 skipped`;
Python compile check passed. No further architecture-neutral UI
implementation package is registered; the interactive layer requires an explicit
framework/architecture choice.

Registered UI package 3 artifacts after Human architecture approval:

- `src/agent_lab/ui_app.py` — loopback-only FastAPI application using the package-2 state contract and a synthetic in-memory Case Registry.
- `src/agent_lab/ui_templates/base.html`, `index.html`, and `_workspace.html` — Jinja/HTMX Persian right-to-left shell and case-scoped partial rendering.
- `src/agent_lab/ui_static/app.css` and `htmx.min.js` — responsive local styling and a pinned local HTMX 2.0.10 asset, with no runtime CDN dependency.
- `tests/unit/test_ui_app.py` — route, case isolation, HTMX partial, no-real-data, no-network, and disabled-submission tests.
- `docs/ui-interactive-prototype.md` — local run instructions, dependency evidence, verification, and remaining Human Gates.

Authority: FastAPI + Jinja/HTMX, local only, as explicitly selected by the Project
Owner on 2026-09-15. The existing synthetic/non-production and no-external-action
boundaries remain in force.

Package UI-3 is implemented and verified. Verification: UI-2/UI-3 targeted
`13 passed`; full regression `518 passed, 1 skipped` with one upstream
Starlette TestClient deprecation warning. Visual inspection on the loopback server
confirmed the Persian RTL shell and disabled submission control. The next package
may improve synthetic interactions but must not cross into real data,
authentication, persistence, external access, deployment, or transmission.

Registered independent UI package 4 artifacts:

- `src/agent_lab/ui_workflow_contract.py` — immutable synthetic workflow-stage and privacy-safe recovery/diagnostic view bound to one package-2 workspace state.
- `src/agent_lab/ui_templates/_workflow.html` — accessible progress timeline and local operational-status panel embedded in the existing prototype.
- `tests/unit/test_ui_workflow_contract.py` and extensions to `tests/unit/test_ui_app.py` — exact ordering, scope binding, privacy, fail-closed status, and rendering tests.
- `docs/ui-synthetic-workflow.md` — contract, verification, and remaining gates.

Package UI-4 is independent of pending ERiC developer-account review and requires no
real data, persistence, authentication, external connectivity, or transmission.

Package UI-4 is implemented and verified. Verification: UI targeted `19 passed`;
full regression `524 passed, 1 skipped`; Python compile and loopback visual
inspection passed. The previously recorded upstream TestClient deprecation warning
remains unchanged.

Registered independent UI package 5 artifacts:

- `src/agent_lab/ui_document_contract.py` — synthetic, metadata-only document/provenance presentation contract bound to one validated case/run.
- `src/agent_lab/ui_templates/_documents.html` — case-scoped document inventory and provenance-status table in the local prototype.
- `tests/unit/test_ui_document_contract.py` and UI route-test extensions — cross-case denial, private-name rejection, exact provenance binding, and rendering tests.
- `docs/ui-synthetic-document-intake.md` — package boundary, verification, and real-upload gate.

Package UI-5 uses no document contents, file upload, Drive lookup, persistence, real
identifier, authentication, external connection, or transmission.

Package UI-5 is implemented and verified. Verification: UI targeted `24 passed`;
full regression `529 passed, 1 skipped`; Python compile and loopback visual
inspection passed. The known upstream TestClient deprecation warning is unchanged.

Registered independent UI package 6 artifacts:

- `src/agent_lab/ui_review_contract.py` — immutable case/run-bound synthetic findings, allowlisted evidence gaps, calculation summary, and form-preview presentation contract using canonical references and explicit `NOT_RECOVERED` official mapping.
- `src/agent_lab/ui_templates/_review_preview.html` — accessible Persian findings, evidence, calculation, route, preview, and blocker panel.
- `tests/unit/test_ui_review_contract.py` and UI route-test extensions — scope, ordering, privacy, numeric, preview-binding, case-switch, and denied-capability tests.
- `docs/ui-synthetic-review-preview.md` — package contract, verification, and remaining gates.

Package UI-6 reuses accepted UI/P1 synthetic contracts and changes no architecture.
It excludes real/free-form private content, persistence, authentication, protected
ERiC access, external connectivity, official validation, production, and transmission.

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

## Execution scheduling and delivery target

- Operational target: complete project design and full implementation in less than 20 days from the Project Owner instruction of 2026-09-15; therefore the target boundary is **before 2026-10-05 Europe/Berlin**.
- The numbered dependency order describes real technical prerequisites, not a blanket requirement to finish every phase serially.
- Tracks and packages with no shared prerequisite or coupling should proceed in parallel or be interleaved to avoid idle time.
- A blocked track does not stop independent authorized work in another track.
- Parallel execution may not bypass a Human Gate, invent authority, weaken case isolation or verification, consume unregistered future files, or start work whose prerequisite contract is unstable.

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

Phases O2, O3, O4, and O5 are complete and Human-accepted. The former blanket
gate on activation beyond O4 was superseded on 2026-09-15 only for the exact
local D-067 runtime proof below; provider-backed, real-data, external, and
production activation remain gated.

The Project Owner explicitly authorized a local, non-production, low-risk Agent
Runtime Activation Layer on 2026-09-15. The package connects only the existing
`PLANNING_DEPENDENCY_AGENT`, `IMPLEMENTATION_AGENT`,
`QUALITY_ENGINEERING_AGENT`, and `INDEPENDENT_ACCEPTANCE_AGENT` roles to the
accepted Kernel. It may not use real data, credentials, external connectivity,
production authority, protected `main`, or alter the ratified organization.

Registered Agent Runtime Activation Layer artifacts:

- `src/agent_lab/agent_runtime.py` — fail-closed local dispatcher, bounded in-process worker boundary, four-role sequencing, evidence binding, and Kernel lifecycle integration.
- `scripts/run_agent_runtime.py` — local synthetic demonstration/inspection entry point with explicit state paths and no external provider.
- `tests/unit/test_agent_runtime.py` — role allowlisting, dependency order, separation of duties, scope, budget, stop, recovery, and acceptance tests.
- `docs/agent-runtime-activation-layer.md` — exact runtime boundary, execution flow, verification evidence, and later production/provider gate.

This package depends on the accepted O2 contracts and O3 Kernel. It activates no
model provider, network connector, credential, private-data source, production
service, or autonomous operating-system command capability.

Implementation status: **complete and technically verified**. Targeted runtime
suite: `8 passed`; relevant runtime/Kernel/pilot suite: `39 passed`; full
regression: `537 passed, 1 skipped`; compile check passed. A two-invocation local
demonstration completed with six temporary manifests across four roles, two
dependencies, three independent acceptances, two checkpoints, audit `PASS`, and
final kill switch `HALTED`. General mid-resume crash continuation and any
provider-backed execution remain future gated work.

## Registered Phase O2 artifacts

The following Phase O2 artifacts were implemented at `382a140e42496ad9edd92dc2016cfde51d091575` and explicitly accepted by the Project Owner / Human:

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

## Registered Phase O3 artifacts

The following artifacts are registered for Phase O3. They depend on the Human-accepted `ORCHESTRATOR_CONTRACT_SET_V1` and grant no real Agent or external authority by their creation:

- `src/agent_lab/orchestrator_kernel.py` — deterministic SQLite-backed Task/Dependency Registry, manifest validation, Permission Broker, lifecycle, audit, checkpoint/recovery, budget/retry, kill-switch, and Agent Bridge binding.
- `scripts/inspect_orchestrator_kernel.py` — read-only operational inspection and integrity-check entry point for an explicitly selected Kernel database.
- `tests/unit/test_orchestrator_kernel.py` — persistence, recovery, permission, isolation, lifecycle, budget, retry, kill-switch, audit, and Bridge-binding coverage using synthetic data only.
- `docs/o3-deterministic-orchestrator-kernel.md` — architecture, schema, invariants, failure behavior, verification evidence, and activation boundary.

Phase O3 implementation may create and validate synthetic local Kernel databases only. Real Agent activation, credential issuance, A6 authority, production deployment, protected-main action, private tax-case processing, and external transfer remain outside this phase.

Phase O3 implementation and technical verification completed at `d70a28b9b33710a81881855048baccb63f3fc176` and was explicitly Human-accepted on 2026-09-13. The planned token-budget pause ended when Phase O4 resumed on 2026-09-14.

## Registered Phase O4 pilot artifacts

Phase O4 resumed on 2026-09-14 under the Project Owner's existing authorization and the scheduled 11:30 Europe/Berlin stop. The selected work package is a deterministic local consistency check of explicitly allowlisted public governance documents. It reads no tax-case data, uses no network or credential, and performs no external or protected-main action.

- `src/agent_lab/orchestrator_pilot.py` — resumable pilot controller and allowlisted deterministic work-package executor.
- `scripts/run_o4_pilot.py` — local initialize/resume/inspect command with explicit database and evidence paths.
- `tests/unit/test_orchestrator_pilot.py` — end-to-end continuation, retry, independent acceptance, recovery, budget, scope, and stop-control coverage.
- `docs/o4-controlled-autonomous-development-pilot.md` — pilot contract, scope, state flow, acceptance criteria, evidence, and authority boundary.

Generated pilot databases and evidence remain outside version control. Technical completion cannot authorize Phase O5, production operation, private case access, credential use, protected-main action, or external transfer.

Phase O4 implementation and technical verification completed at `b81f4060c5973ad0e5b4ec88a385ce3e046f7ee3`. The Project Owner explicitly accepted that implementation and authorized Phase O5 on 2026-09-14.

## Registered Phase O5 readiness artifacts

- `src/agent_lab/control_plane_readiness.py` — deterministic fail-closed evaluator for repository, Work automation, Codex, GitHub, Windows Relay, Local Sync, monitoring, recovery, and protected-main-gate evidence.
- `scripts/check_control_plane_readiness.py` — read-only evaluator for an explicit non-secret JSON evidence snapshot.
- `tests/unit/test_control_plane_readiness.py` — PASS, missing evidence, scope mismatch, installation, monitoring, recovery, and Human-Gate coverage.
- `docs/o5-production-control-plane-readiness.md` — readiness contract, current evidence, blockers, acceptance criteria, and activation boundary.

The evaluator grants no runtime authority and may not install services, modify automations, issue credentials, change repository protection, merge, release, or transfer data.

The evaluator was implemented at `9e00bcfccdddd04cda7195a907fbc3aaa9dd9772` and verified with `11` targeted, `72` relevant, and `379 passed, 1 skipped` full-regression results. Windows Relay, Local Sync, monitoring, restart/recovery, and protected-main enforcement are verified. On 2026-09-14, all three active Agent Bridge Work automations were updated in place and independently verified active with Repository condition and prompt scoped to `golestanzadeh/ai-agent-lab`. A fresh evaluator snapshot returned `PASS` with fourteen verified conditions and no blockers. The Project Owner explicitly accepted Phase O5 and readiness-record commit `d64da2588b18f548c877aed6044f8884e7644cdc`. That historical gate was later superseded by the exact bounded Phase P1 package authorizations recorded above; production activation remains unauthorized.
