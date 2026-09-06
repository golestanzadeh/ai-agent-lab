# Current State

Last verified: 2026-09-06

## Repository

- Repository: `golestanzadeh/ai-agent-lab`
- Default branch: `main`
- Visibility: public
- GitHub write access through the current Codex-enabled integration: verified.
- GitHub is the durable project source of truth.

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
- Google Drive case-storage folder structure created for `AI-Tax-Agent/` and `CASE-001`.
- Google Cloud project `AI-Tax-Agent` created.
- Google Drive API enabled.
- Google OAuth configuration completed and a Desktop OAuth client `AI-Tax-Agent Desktop` created.
- Development setup history and local-state corrections recorded in `docs/development-setup.md`.

## Important local-state correction

The user has **not yet cloned `ai-agent-lab` to the local PC**. The repository has so far been maintained directly on GitHub through the Codex-enabled integration.

Therefore the previously created `C:\Users\rezag\.venv` is a temporary/home-directory environment and is **not** the final project virtual environment. The next local setup step is to clone the repository deliberately, then create and verify a `.venv` inside the cloned project.

The downloaded Google OAuth credential must not be committed to GitHub.

## Current target

Build a Germany-focused tax-assistance system that can ultimately handle supported tax matters from user-supplied documents through current-law-verified analysis, validated calculations, systematic lawful tax optimization, audited results, final print-ready documents, and controlled electronic submission where an official and lawful technical path exists.

The optimization target is explicit: minimize legally payable tax and maximize legally recoverable/refundable tax for the user, supported by applicable law, evidence, documentation, and measurable financial impact where calculable.

## Not yet completed

- Local repository clone.
- Project-local Python virtual environment.
- Google Drive API Python integration and OAuth smoke test.
- First concrete tax workflow selection.
- Exact target taxpayer profile for the first workflow.
- Exact tax year/assessment period for the first workflow.
- Detailed requirements and acceptance thresholds for the first workflow.
- Authoritative German source inventory and current-law retrieval strategy.
- Workflow decomposition.
- Architecture decision, including final justification for the Tax Optimization Supervisor and other agent roles.
- Agent/tool contracts.
- Evaluation dataset and harness, including tax-optimization opportunity coverage metrics.
- Safety/privacy threat model.
- First executable prototype.
- Production deployment and operations design.
- Official electronic submission integration decision.

## Next action

Clone `golestanzadeh/ai-agent-lab` locally. Then create a project-local `.venv`, verify the interpreter, establish the Git workflow, and only then continue with the Google Drive API smoke test.

## Continuity rule

Before every project-level or architectural action, reconstruct the verified state from repository documents, especially `CONSTITUTION.md`, `PROJECT.md`, `MASTER_PLAN.md`, `ROADMAP.md`, `CURRENT_STATE.md`, `DECISIONS.md`, and `docs/development-setup.md`. After any material decision, setup change, correction, or completed milestone, update the appropriate repository documentation before proceeding.
