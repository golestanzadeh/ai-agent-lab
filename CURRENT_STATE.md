# Current State

Last verified: 2026-09-06

## Repository

- Repository: `golestanzadeh/ai-agent-lab`
- Default branch: `main`
- Visibility: public
- GitHub write access through the current Codex-enabled integration: verified.
- GitHub is the durable project source of truth.
- Local clone: `C:\Users\rezag\ai-agent-lab`
- Local `main` branch was verified up to date with `origin/main` after cloning.

## Phase

**Phase 10 — Problem discovery and requirements**

## Completed

- Repository located and verified.
- Direct GitHub write capability verified.
- Core project documentation initialized.
- Durable anti-hallucination rule established.
- Future-file registry established in `ROADMAP.md`.
- Complete initial Phase 0–100 lifecycle and final definition of done recorded in `MASTER_PLAN.md`.
- German tax assistance selected as the primary domain.
- Final-goal direction expanded to German tax work for natural persons and legal entities.
- Current-law verification, authoritative evidence, final document generation, and controlled electronic submission are explicit project requirements.
- `docs/requirements.md` created as the Phase 10 requirements baseline.
- `docs/use-cases.md` created with candidate workflows.
- **Golden objective added: Maximize Legally Achievable Tax Benefit.**
- **Tax Optimization Supervisor established as a primary architectural role candidate** responsible for continuous optimization review and cross-agent challenge/feedback.
- Python 3.14.2 verified on the user's Windows machine.
- Docker Desktop / Docker Engine verified by successfully running `hello-world`.
- Google Drive case-storage folder structure created for `AI-Tax-Agent` and `CASE-001`.
- Google Cloud project `AI-Tax-Agent` created.
- Google Drive API enabled.
- Google OAuth configuration completed and a Desktop OAuth client `AI-Tax-Agent Desktop` created.
- Repository cloned locally to `C:\Users\rezag\ai-agent-lab`.
- Project-local `.venv` created and verified at `C:\Users\rezag\ai-agent-lab\.venv`.
- Project-local Python interpreter verified as `C:\Users\rezag\ai-agent-lab\.venv\Scripts\python.exe`.
- Project-local pip upgraded and verified as `26.2.1`.
- VS Code successfully opened from the project root with `code .`.
- VS Code workspace interpreter verified as the project-local `C:\Users\rezag\ai-agent-lab\.venv\Scripts\python.exe`.
- Development setup history and local-state corrections recorded in `docs/development-setup.md`.
- OAuth credential location verified as `C:\Users\rezag\ai-tax-agent\credentials.json`.
- Mistaken repository copy of `credentials.json` removed; `git status` verified a clean working tree afterward.
- Repository `.gitignore` was verified as already excluding local secrets/environment files and common local development artifacts.
- Google Drive Python dependencies installed successfully in the project-local `.venv`.
- Google Drive library import smoke check completed successfully with output: `Google Drive libraries: OK`.
- `requirements.txt` added with the verified Google Drive/Auth dependency versions.
- **Google Drive OAuth authentication and metadata-only API smoke test completed successfully.**
- **The Python smoke test authenticated the user and successfully located the private `AI-Tax-Agent` Drive folder.**
- The smoke test used the `drive.metadata.readonly` scope and did not read, modify, upload, or process tax-document contents.
- **CASE-001 source documents were placed by the user in `Google Drive/AI-Tax-Agent/Cases/CASE-001/Documents`.** The user reported 15 PDF files totaling approximately 4.25 MB in the local Google Drive mirror. This observation is not yet treated as the authoritative machine inventory.
- **The Document Inventory boundary was formally approved as the first executable processing stage.**
- `docs/document-inventory.md` was created with the inventory contract, metadata model, deterministic-first rule, permissions, privacy/minimization requirements, pagination/completeness requirements, idempotency, failure states, and acceptance criteria.
- `docs/architecture.md` was upgraded to the approved logical architecture, including the source-document boundary, intake pipeline, evidence/provenance boundary, permissions, audit/observability, evaluation, and implementation sequence.
- **Case Party / Household Context was formally added as a foundational architecture layer.**
- `docs/case-party-model.md` was created as the conceptual contract for taxpayer, spouse/partner, child, household, tax-year status, document attribution, economic burden, assessment mode, temporal facts, ambiguity handling, and privacy.
- `docs/requirements.md` was extended with explicit party/context, document-to-person attribution, and reconciliation requirements.
- `docs/use-cases.md` was extended with a dedicated family/spouse/children use case and party-aware escalation requirements.
- **Decision D-009 accepted:** every natural-person case requires an explicit party/household model before substantive calculations are considered reliable.

## Current local development state

```text
C:\Users\rezag\ai-agent-lab
        ↓
      .venv
        ↓
 Python 3.14.2
        ↓
    pip 26.2.1
        ↓
 Google Drive libraries installed
        ↓
 Google OAuth + Drive metadata API verified
        ↓
      VS Code
        ↓
    Git / GitHub
```

OAuth credentials and the generated token are stored outside the repository under:

```text
C:\Users\rezag\ai-tax-agent\
```

No credential or token belongs in GitHub.

## Current architecture milestone

The first executable pipeline is now explicitly defined as:

```text
Google Drive
    ↓
Drive Connector
    ↓
Case/Folder Resolver
    ↓
Case Party / Household Context
    ↓
Document Inventory
    ↓
Inventory Validation
    ↓
Document → Party Attribution
    ↓
Document Processing
    ↓
Evidence Extraction
    ↓
Fact Normalization / Reconciliation
```

The immediate implementation target remains deterministic, metadata-only intake. The Party/Household layer is a required case-state contract; it does not automatically become an LLM Agent.

## Party-model architectural rules

- A case is not assumed to belong to one person.
- For married/registered partners, each spouse's relevant Steuerklasse/ELStAM must be captured independently where applicable.
- Steuerklasse/ELStAM is treated as wage-tax/withholding evidence and must not be confused with final income-tax liability.
- Joint versus individual assessment must be explicit and legally verified before optimization comparison.
- Children are first-class case parties when tax-relevant.
- Every material document/fact must be attributable to a person, multiple persons, or shared household context.
- Filename alone is never sufficient for material attribution.
- Shared expenses must not automatically be assumed to be 50/50.
- Material ambiguous or contradictory party attribution must stop or escalate the affected workflow.
- Party and tax attributes are time-dependent and must support tax-year/effective intervals.

## Not yet completed

- Implement the Drive Connector contract for case-scoped access.
- Implement deterministic resolution of `CASE-001/Documents`.
- Implement Document Inventory with pagination and explicit field selection.
- Add mocked/unit tests for the inventory component.
- Run the live metadata-only inventory against CASE-001.
- Record the authoritative API inventory snapshot.
- Define the concrete CASE-001 taxpayer/family profile from evidence.
- Define the exact tax year/assessment period for CASE-001.
- Define detailed party-model schemas and validation tests for the first workflow.
- Detailed requirements and acceptance thresholds for the first tax workflow.
- Authoritative German source inventory and current-law retrieval strategy.
- Evidence extraction and fact/reconciliation implementation.
- Workflow decomposition beyond the approved intake baseline.
- Final architecture decisions for each candidate agent/component.
- Agent/tool contracts.
- Evaluation dataset and harness, including party-attribution and tax-optimization opportunity coverage metrics.
- Safety/privacy threat model.
- First executable end-to-end tax prototype.
- Production deployment and operations design.
- Official electronic submission integration decision.

## Next action

Implement and test the deterministic, metadata-only Document Inventory component against `CASE-001/Documents`. Do not download or interpret tax documents yet. The first live run must prove complete, paginated enumeration and produce a structured inventory without mutating source data.

## Continuity rule

Before every project-level or architectural action, reconstruct the verified state from repository documents, especially `CONSTITUTION.md`, `PROJECT.md`, `MASTER_PLAN.md`, `ROADMAP.md`, `CURRENT_STATE.md`, `DECISIONS.md`, and `docs/development-setup.md`. After any material decision, setup change, correction, or completed milestone, update the appropriate repository documentation before proceeding.
