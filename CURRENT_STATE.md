# Current State

## Project status

The project is in the foundational architecture and Phase 1 preparation stage. CASE-001 is the first real validation case, but the architecture is being built for long-term multi-case, multi-year operation for natural persons and legal entities.

## Established architecture

- GitHub is the source of truth for code, architecture, decisions, and tests.
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

No Agent, pipeline component, or data-access tool may access case data without a validated `case_id`. Access must resolve through the Case Registry to the exact case folder reference. Unscoped broad Drive searches for case data are prohibited.

Case isolation is a deterministic security/correctness boundary, not merely an Agent prompt instruction. Failure to resolve a case or an out-of-scope object must fail closed.

Cross-year summaries resolve cases through persistent `person_id`/`entity_id` and the Case Registry, then access each case separately. They must not scan unrelated Drive content and guess ownership.

## Registries

Case Registry will map case identity to taxpayer/entity identity, tax period, case type, lifecycle state, exact Drive case-folder reference, processing/run metadata, and required version metadata.

Person/Entity Registry will provide persistent identity mappings across tax periods. Registry data is an index and identity layer, not a replacement for source documents or evidence.

## Document inventory

The deterministic metadata-only Document Inventory remains the next processing capability, but its implementation must follow the foundational case-management architecture rather than hard-code CASE-001 as a special case.

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

## Next implementation priorities

1. Implement Case Registry model and Case Creation workflow.
2. Implement case-scoped Drive Resolver and access boundary.
3. Implement case-scoped state and execution/run IDs.
4. Add isolation and cross-case contamination tests.
5. Define migration/compatibility handling for existing CASE-001.
6. Implement deterministic metadata-only Document Inventory using the case-scoped connector.
7. Run the live inventory against CASE-001/Documents only after the scope boundary is verified.
