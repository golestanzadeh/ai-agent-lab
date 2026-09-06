# Current State

## Project status

The project is in the foundational architecture and Phase 1 preparation stage. CASE-001 is the first real validation case, but the architecture is being built for long-term multi-case, multi-year operation for natural persons and legal entities.

## Established architecture

- GitHub is the source of truth for code, docs, tests, decisions, and verified state.
- Google Drive is private source-document storage and working-case storage; it is not the system brain.
- Local Python/Docker runtime is the execution environment.
- Source documents under a case's `Documents/` boundary are immutable.
- Tax categories are a dynamic retrieval/organizational layer, not the source of truth.
- Evidence, provenance, calculations, reports, and audit data are case-scoped.
- Party/household context is explicit and ambiguity must not be silently guessed.
- Document processing is deterministic-first.

## Foundational multi-case architecture

The system is designed around three identities:

- `case_id`: identity of one tax case for one tax period and mandatory processing scope.
- `person_id` / `entity_id`: persistent taxpayer/entity identity across years.
- `tax_period`: explicit tax period, initially supporting calendar years and designed to support future fiscal-period variants.

Target Drive organization:

```text
AI-Tax-Agent/
├── Tax_Years/
│   ├── 2020/Cases/
│   ├── 2021/Cases/
│   ├── ...
│   ├── 2024/Cases/
│   ├── 2025/Cases/
│   └── 2026/Cases/
├── Case_Registry/
├── Person_Registry/
├── Entity_Registry/
├── Templates/
└── System/
```

Each case is internally isolated with:

```text
CASE-YYYY-NNNN/
├── Documents/
├── Evidence/
├── Tax_Categories/
├── Calculations/
├── Reports/
└── Audit/
```

The exact migration of the currently existing CASE-001 layout is not yet implemented.

## Mandatory isolation rule

No Agent, pipeline component, model, or data-access tool may access case data without a validated `case_id`. Access must resolve through the Case Registry to the exact case folder reference. Unscoped broad Drive searches for case data are prohibited.

Case isolation is a deterministic security/correctness boundary, not merely an Agent prompt instruction. Failure to resolve a case or an out-of-scope object must fail closed.

Cross-year summaries resolve cases through persistent `person_id`/`entity_id` and the Case Registry, then access each case separately. They must not scan unrelated Drive content and guess ownership.

## Case Registry implementation

`docs/case-registry.md` remains the authoritative contract. The deterministic runtime model is implemented at `src/agent_lab/case_registry.py`, with acceptance-oriented unit tests at `tests/unit/test_case_registry.py`.

Local verification passed: `tests/unit/test_case_registry.py` completed with 10 passed tests.

## Person/Entity Registry foundation and runtime

`docs/person-entity-registry.md` defines the persistent identity model for natural persons and legal entities. The deterministic runtime implementation is at `src/agent_lab/person_entity_registry.py`, with tests at `tests/unit/test_person_entity_registry.py`.

Local verification passed: `tests/unit/test_person_entity_registry.py` completed with 11 passed tests.

## Case ↔ Identity Association runtime

The deterministic association boundary is implemented at `src/agent_lab/case_identity_association.py`, with tests at `tests/unit/test_case_identity_association.py`.

It enforces identity-type compatibility, exact owner-ID matching, existence of both identity and case, idempotent association, and registry consistency. It introduces no document or Drive access.

Local verification passed: `tests/unit/test_case_identity_association.py` completed with 9 passed tests.

## Case Creation Workflow

`docs/case-creation-workflow.md` defines the foundational creation contract. The deterministic runtime is implemented at `src/agent_lab/case_creation_workflow.py`, with tests at `tests/unit/test_case_creation_workflow.py`.

Local verification passed: `tests/unit/test_case_creation_workflow.py` completed with 9 passed tests.

The runtime remains storage-provider-neutral and does not migrate CASE-001 or perform document processing.

## Case-Scoped Drive Resolver and Access Boundary

`docs/case-scoped-drive-resolver.md` defines the mandatory boundary between validated case identity and storage access.

The deterministic runtime is implemented at `src/agent_lab/case_scoped_drive.py`, with tests at `tests/unit/test_case_scoped_drive.py`.

The resolver:

- requires a non-empty validated `case_id`;
- resolves storage only through the authoritative Case Registry;
- returns the exact registered `StorageScopeReference`;
- fails closed for unknown cases;
- rejects objects whose storage scope does not exactly match the resolved case scope;
- does not scan Drive, inspect documents, or infer ownership;
- preserves `case_id` when the physical storage reference changes.

The current runtime uses provider-neutral opaque storage references. A Google Drive adapter remains a separate implementation step.

Local verification passed: `tests/unit/test_case_scoped_drive.py` completed with 8 passed tests.

## Case State + Run ID Model and Runtime

`docs/state-and-memory.md` defines the foundational case-state and execution identity contract.

The deterministic runtime is implemented at `src/agent_lab/case_state.py`, with acceptance-oriented tests at `tests/unit/test_case_state.py`.

The runtime establishes:

- structured case-scoped operational state;
- unique deterministic `run_id` generation;
- exactly one `case_id` per run;
- request-ID idempotency for repeated execution requests;
- rejection of request-ID reuse across cases;
- case-scoped run lookup and listing;
- explicit run lifecycle transitions;
- immutable terminal run status;
- state references for parties, documents, evidence, facts, assumptions, rules, calculations, optimization, challenges, approvals, and outputs;
- validation against the authoritative Case Registry;
- fail-closed behavior for unknown cases and cross-case run/state access.

The current runtime is intentionally in-memory. Durable persistence, workflow queues, checkpoint/resume, durable audit storage, and full tax-domain state schemas remain separate future layers.

Local verification is pending: the user must run `tests/unit/test_case_state.py` locally before this component is marked verified.

## Completed environment work

- Google Drive API enabled.
- Desktop OAuth client configured.
- Metadata-only Drive smoke test passed against the AI-Tax-Agent root.
- Python environment and Google Drive libraries verified.
- Docker Desktop verified.
- CASE-001 `Tax_Categories` default directories created in private Drive.
- Document Processing Contract created.
- Case Party / Household Model created.
- Foundational Case Management and Isolation architecture created.
- Case Registry contract, runtime, and tests created and verified.
- Person/Entity Registry model, runtime, and tests created and verified.
- Case ↔ Identity Association runtime and tests created and verified.
- Case Creation Workflow contract, runtime, and tests created and verified.
- Case-Scoped Drive Resolver contract, runtime, and tests created and verified.
- Case State + Run ID contract and runtime created; local verification pending.

## Next implementation priorities

1. Verify the Case State + Run ID runtime locally.
2. Define durable audit/observability boundary.
3. Add isolation and cross-case contamination tests.
4. Implement a Google Drive storage adapter behind the verified scope boundary.
5. Define migration/compatibility handling for existing CASE-001.
6. Implement deterministic metadata-only Document Inventory using the case-scoped connector.
7. Run the live inventory against CASE-001/Documents only after the scope boundary and adapter are verified.
8. Continue toward evidence extraction, research, analysis, optimization, challenge, audit, and final-output workflows.
