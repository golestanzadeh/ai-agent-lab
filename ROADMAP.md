# Roadmap

This is the authoritative plan for the project. Planned files are registered here before they are created so future work is not reconstructed from memory.

## Phase 0 — Initialization

Status: **complete**

- Establish repository as source of truth.
- Create operating principles and project definition.
- Create anti-hallucination rules.
- Establish roadmap, future-file registry, and decision log.

## Phase 1 — Problem and requirements

Status: **in progress**

Goals:
- define the German tax-assistance domain and supported first workflow;
- define users, inputs, outputs, constraints, risks, and success metrics;
- define party/household context;
- define the minimum viable workflow before adding agent complexity;
- establish the first real Golden Test Case.

Existing files:
- `docs/requirements.md`
- `docs/use-cases.md`
- `docs/case-party-model.md`
- `docs/document-inventory.md`
- `docs/document-processing.md`

## Phase 2 — System architecture and case foundation

Status: **in progress**

Goals:
- define control loop and state model;
- define deterministic versus Agent boundaries;
- define tool interfaces and evidence flow;
- define human approval points;
- establish persistent multi-case and multi-year identity;
- establish Case Registry and Person/Entity Registry contracts;
- establish mandatory case-scoped access and isolation;
- define execution/run identity and idempotency;
- define case creation workflow;
- define migration strategy for the existing CASE-001 structure;
- anchor CASE-001 migration validation to Document Identity and Inventory Evidence;
- implement the deterministic human approval boundary for consequential actions.

### Preserved detailed Phase-2 register

Accepted architecture/storage/migration documents include:
- `docs/architecture.md`
- `docs/case-management.md`
- `docs/case-registry.md`
- `docs/person-entity-registry.md`
- `docs/case-creation-workflow.md`
- `docs/case-scoped-drive-resolver.md`
- `docs/state-and-memory.md`
- `docs/google-drive-storage-adapter.md`
- `docs/case001-migration-compatibility.md`
- `docs/document-identity.md`
- `docs/approval-gate.md`
- `docs/artifact-identity.md`
- `docs/case001-approval-context.md`

Implemented runtime foundations include:
- `src/agent_lab/case_registry.py`
- `src/agent_lab/person_entity_registry.py`
- `src/agent_lab/case_identity_association.py`
- `src/agent_lab/case_creation_workflow.py`
- `src/agent_lab/case_scoped_drive.py`
- `src/agent_lab/case_state.py`
- `src/agent_lab/storage.py`
- `src/agent_lab/google_drive_storage.py`
- `src/agent_lab/google_drive_auth.py`
- `src/agent_lab/document_inventory.py`
- `src/agent_lab/document_identity.py`
- `src/agent_lab/inventory_evidence.py`
- `src/agent_lab/case001_migration.py`
- `src/agent_lab/case001_migration_manifest.py`
- `src/agent_lab/case001_live_target_preflight.py`
- `src/agent_lab/approval.py`
- `src/agent_lab/artifact_identity.py`
- `src/agent_lab/case001_approval_context.py`
- `src/agent_lab/durable_approval.py`
- `src/agent_lab/case001_physical_migration.py`
- `src/agent_lab/google_drive_mutation.py`
- D-021 provisioning/approval-preparation implementation on `d021-agent-case-provisioning`.

Latest branch-wide verification for the controlled migration work package is **279 passed, 1 skipped**.

### Google Drive Storage Adapter

Status: **complete through Stage 6**

The provider-neutral contract, case-scoped resolver integration, metadata-only adapter, deterministic scope enforcement, unit/live isolation verification, and documentation gate are complete. Live storage access remains bounded by accepted case-isolation and authorization rules.

### CASE-001 inventory / identity / migration work package

Status: **controlled physical migration executor, guarded Drive mutation adapter, and controlled local execution harness implemented and synthetically verified end-to-end; real CASE-001 execution is Human-Gated**

- Metadata-only CASE-001 inventory: last recorded 15 PDFs, 0 folders; fresh live reconstruction is required before execution.
- Document Identity and Inventory Evidence: implemented and verified.
- CASE-001 migration compatibility, deterministic Manifest, Live Target Preflight, D-017 Approval Gate, D-018 Artifact Identity, D-020 Approval Context Composition, durable/reloadable approval, controlled executor, and guarded Drive mutation adapter: implemented.
- D-021 standard target provisioning and approval preparation: implementation complete on its branch.
- Physical Drive migration against real CASE-001 data has **not** been executed.

Still required before real physical migration:
- fresh authoritative live inventory, manifest, and target preflight reconstruction;
- a newly created durable executable approval for that exact binding;
- explicit human grant and separate consequential Human Gate for the live attempt;
- post-execution evidence before any legacy alias retirement.

## Phase 3 — Evaluation and safety design

Status: planned

Planned files include `docs/evaluation.md`, `docs/safety.md`, `docs/failure-modes.md`, and `tests/fixtures/README.md`.

## Phase 4 — First executable prototype

Status: planned

The smallest useful end-to-end workflow must remain observable and case-scoped, with deterministic components independently testable.

## Phase 5 — Evidence, observability, and auditability

Status: planned

Consequential outputs must remain traceable with case/run provenance and post-run analysis support.

## Phase 6 — Adversarial testing and improvement

Status: planned

Challenge scope boundaries, identity resolution, tool permissions, and regressions deliberately.

## Phase 7 — Packaging and portfolio quality

Status: planned

Reproducible setup, clear documentation, architecture diagrams, demonstration workflow, limitations, and evaluation evidence.

## D-020 approved integration boundary

D-020 is accepted and integrated into main. Its composition layer binds exact Manifest and successful Live Target Preflight artifact identities into D-017 execution context. It does not grant/consume approval or perform migration.

## Agent Bridge Production Migration — approved sequential plan

Status: **production accepted; Step 11 durable approval accepted; controlled migration executor verified; real execution Human-Gated**

1. Baseline + Durable Documentation + Canonical State Cleanup — **complete**.
2. Production Architecture and Governance — **human accepted 2026-09-10**.
3. Protocol Contract — **defined**.
4. Production Security Model — **defined**.
5. Passive / Observe-only Bridge — **complete**.
6. Codex Bounded Execution — **complete**.
7. GitHub → Work Response Wake-up and independent review — **complete**.
8. Controlled Continuation for low-risk bounded tasks only — **complete**.
9. Deliberate Human Gate validation — **complete; HUMAN_REQUIRED terminal behavior proved**.
10. Production acceptance, rollback drill, audit and kill-switch verification — **complete; production human-accepted 2026-09-10**.
11. Resume AI-Tax-Agent development at the durable/reloadable approval lifecycle blocker — **complete; architecture and stage human-accepted 2026-09-10**.

Agent Bridge is a **development control plane only**. It does not replace D-017, authorize approval consumption, or authorize physical migration.

### Agent Bridge production files

- `docs/agent-bridge-production.md`
- `.github/workflows/agent-bridge-passive.yml`
- `.github/workflows/agent-bridge-codex.yml`
- `.github/workflows/agent-bridge-response.yml`
- `scripts/agent_bridge_validate.py`
- `tests/unit/test_agent_bridge_validate.py`

Temporary probe trigger files and disposable test branches are validation artifacts, not long-term production interfaces, and should be removed or left unmerged when no longer needed.

### Durable/reloadable approval lifecycle — Step 11

Architecture and stage accepted by the human on 2026-09-10.

Implemented files:
- `docs/durable-approval-lifecycle.md`
- `src/agent_lab/durable_approval.py`
- `tests/unit/test_durable_approval.py`

Implementation constraints remain authoritative:
- SQLite is the initial durable backend for the local single-host runtime.
- Approval and its authoritative approval-lifecycle audit event commit in one SQLite transaction for durable lifecycle transitions.
- Executable authority is reconstructed only from validated durable records, never from exported review JSON/text or chat/GitHub prose.
- Unknown schema version, integrity mismatch, partial/corrupt state, case/run mismatch, or transaction uncertainty fails closed.
- `CONSUMED` remains terminal and exactly-once across process restart and concurrent consumers.

### Controlled physical migration executor — implemented and verified

Registered before implementation on 2026-09-10 and now present:
- `docs/physical-migration-executor.md`
- `src/agent_lab/case001_physical_migration.py`
- `tests/unit/test_case001_physical_migration.py`
- `src/agent_lab/google_drive_mutation.py`
- `tests/unit/test_google_drive_mutation.py`

Controlled harness registered before creation:
- `scripts/case001_controlled_migration.py` — local runtime entry point for fresh inventory/manifest/preflight reconstruction, dry-run, and separately Human-Gated live execution using a new durable approval.
- `tests/unit/test_case001_controlled_migration.py` — fail-closed mode/authorization and safe-summary tests without live Drive access.

Verification already recorded:
- CI run `34509462092`: executor tests **9 passed**, full suite **272 passed, 1 skipped**.
- CI run `34509683965`: executor **9 passed**, guarded Drive adapter **7 passed**, durable approval **11 passed**, Bridge validator **6 passed**, full suite **279 passed, 1 skipped**.
- CI run `34509914717`: all registered migration/durable/Bridge regression checks **success** after the Human-Gate state update.
- Local Windows verification 2026-09-11: controlled migration work package **34 passed**; full regression **310 passed, 1 skipped**. The added end-to-end harness test proved fresh run binding, durable approval creation/grant, exact 15-object synthetic move, verification, approval consumption, durable reload, and consumed-state persistence without live Drive access.

Executor/harness constraints:
- dry-run is the default and performs zero mutations and zero approval lifecycle changes;
- live execution requires an exact newly created durable `APPROVED` authorization and separately explicit live enablement;
- creation/grant of the real durable approval and the live attempt occur only after the final consequential Human Gate;
- the executor operates only on explicit manifest object IDs and explicit source/target parent IDs, never names or Drive-wide search;
- each mutation preserves provider object ID and logical document identity;
- partial failure attempts reverse-order rollback of already-applied moves;
- incomplete rollback or unverifiable post-state fails closed and is never success;
- post-migration verification proves exact target placement before approval consumption;
- approval consumption occurs only after successful post-migration verification; consumption failure triggers storage rollback;
- real CASE-001 execution, new durable grant, and approval consumption remain behind the separate consequential Human Gate.

### Local Sync Agent — approved architecture and future-file registry

Architecture human-accepted on 2026-09-10. GitHub remains the durable source of truth while the Windows checkout at `C:\Users\rezag\ai-agent-lab` is kept near-real-time synchronized without routine user intervention.

Registered before implementation:
- `docs/local-sync-agent.md` — sync authority, conflict/failure behavior, installation and operational boundaries.
- `src/agent_lab/local_sync.py` — deterministic one-shot Git synchronization engine.
- `scripts/local_sync_agent.py` — thin unattended CLI wrapper for the synchronization engine.
- `scripts/install_local_sync_task.ps1` — one-time Windows Task Scheduler bootstrap for one-minute unattended runs.
- `tests/unit/test_local_sync.py` — deterministic sync decision tests without network access.

Local Sync Agent constraints:
- remote GitHub state is authoritative when local is clean and strictly behind; update only by fast-forward;
- an already committed local branch may be pushed only when it is strictly ahead of its matching remote branch, never by force;
- uncommitted/staged local changes, branch mismatch, detached HEAD, missing remote ref, or divergent history fail closed with no merge/rebase/reset/stash/commit;
- `main` is never auto-pushed by the Local Sync Agent;
- the agent never auto-commits local working-tree changes and never touches ignored/local secret or runtime data;
- no credentials are stored in the repository or emitted in logs;
- overlapping runs are prevented by the scheduler and a local lock;
- installation/configuration is local-machine bootstrap only and does not weaken protected-main, PR, Agent Bridge, Durable Approval, or Human Gate governance.

### Windows Relay — approved architecture and registered implementation

Architecture human-accepted on 2026-09-10 to close the bounded GitHub-to-local-Windows execution gap without attaching a general-purpose or self-hosted GitHub Actions runner to the public repository.

Registered implementation artifacts:
- `docs/windows-relay.md` — trust, transport, allowlist, bootstrap, and failure boundaries.
- `src/agent_lab/windows_relay.py` — strict request parser, one-shot relay processor, idempotency state, and bounded response publisher.
- `scripts/windows_relay.py` — unattended one-shot CLI with overlap lock.
- `scripts/install_windows_relay_task.ps1` — one-time Task Scheduler bootstrap for the local relay.
- `tests/unit/test_windows_relay.py` — deterministic fail-closed and no-arbitrary-command tests.

Windows Relay constraints:
- request transport is the exact GitHub branch file `.github/windows-relay/request.json` and response transport is `.github/windows-relay/response.json`;
- protocol v1 accepts only `LOCAL_SYNC_BOOTSTRAP`; no request field can contain a shell command, script, path override, credential, Drive ID, or arbitrary argument;
- execution requires Windows, the exact authoritative repository root, the exact approved non-main branch, and a clean working tree;
- task replay is blocked using local state under `.git`;
- response publication may stage/commit only the bounded response file and uses a normal non-force push to the approved non-main branch;
- the relay cannot merge/release, modify `main`, access Drive/tax data, grant/consume migration approval, or perform CASE-001 physical migration;
- first local relay bootstrap remains a one-time host action; after installation, ordinary allowlisted relay requests no longer require the user to open a terminal.

Technical verification:
- CI run `34515017873`: Windows Relay targeted tests **14 passed**, Local Sync tests **10 passed**, full regression **309 passed, 1 skipped**; job **success**.

## Future-file registry rule

A file listed as planned is **not** considered created or implemented until it exists in GitHub. A future file may be added, renamed, split, or cancelled only through an explicit update to this roadmap and, for significant changes, a decision record.

## Ordering rule

Do not jump directly to executable Agent implementation because coding feels productive. Case/identity/scope, evidence/evaluation, governance, protocol, and security boundaries must exist before automation is trusted.