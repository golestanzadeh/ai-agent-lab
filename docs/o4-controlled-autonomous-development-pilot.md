# Phase O4 — Controlled Autonomous Development Pilot

Status: **IMPLEMENTED AND TECHNICALLY VERIFIED; HUMAN PHASE ACCEPTANCE REQUIRED**

## Work package

The pilot performs one deterministic local consistency check over five explicitly allowlisted public governance documents: `CONSTITUTION.md`, `PROJECT_CHECKPOINT.md`, `AGENTS.md`, `CURRENT_STATE.md`, and `ROADMAP.md`. It verifies required headings, records SHA-256 evidence, pauses at a durable checkpoint, then reopens the SQLite Kernel and requires a separate Independent Acceptance identity to verify the evidence and complete the task.

## Boundaries

- Local Python, SQLite, and temporary JSON evidence only.
- No tax-case data, broad repository scan, network, credential, connector, LLM dispatch, protected-main write, merge, release, production action, or external transfer.
- Generated databases and evidence are not repository artifacts.
- The accepted O4 authority reference is recorded, but it cannot grant A6 or any later-phase authority.

## State flow

`NEW -> RUNNING -> AWAITING_ACCEPTANCE -> PAUSED/CHECKPOINTED -> RECOVERED -> INDEPENDENT_PASS -> HALTED/CHECKPOINTED`

The `start` operation creates new paths only and stops with the kill switch at `PAUSED`. The `resume` operation verifies the audit chain and checkpoint, revalidates current document hashes against the saved evidence, activates a distinct `INDEPENDENT_ACCEPTANCE_AGENT` manifest, records acceptance, and stops with the kill switch at `HALTED`. Replaying `start`, changing evidence, changing an allowlisted document between stages, or losing checkpoint integrity fails closed.

## Cost and retry controls

The pilot records zero model tokens, twelve bounded local tool operations across implementation and review, and zero external cost. O3 retry enforcement is exercised separately with one authorized retry identity, rejection after the configured limit, and audit-chain verification. The successful pilot does not manufacture a failure merely to consume a retry.

## Commands

```powershell
$env:PYTHONPATH = "src"
python scripts/run_o4_pilot.py start C:\temporary\o4.sqlite3 --evidence C:\temporary\o4-evidence.json
python scripts/run_o4_pilot.py resume C:\temporary\o4.sqlite3 --evidence C:\temporary\o4-evidence.json
python scripts/run_o4_pilot.py inspect C:\temporary\o4.sqlite3
```

## Acceptance criteria

1. Only the fixed public-document allowlist is read.
2. Start and resume occur in separate Kernel instances.
3. The first stage persists an integrity-checked recovery checkpoint and pauses dispatch.
4. Evidence mutation and document drift fail closed before independent acceptance.
5. A distinct independent reviewer closes the implementation task.
6. Final state is checkpointed, audit-valid, and globally halted.
7. Durable budget reporting matches the response record.
8. Retry count and identity are bounded and audited.
9. Targeted and relevant regression tests pass.

## Verification evidence

- Targeted O4 suite: `5 passed`.
- Relevant O2/O3/O4/Agent Bridge suite: `49 passed`.
- Full repository regression: `368 passed, 1 skipped`.
- Python compile check passed for the pilot controller and CLI.
- A real local two-invocation demonstration completed with one independent acceptance record, two checkpoints, 21 audit events, audit integrity `PASS`, final kill switch `HALTED`, zero model tokens, 12 bounded local tool operations, and zero external cost.
- Demonstration evidence SHA-256: `sha256:62a593e1940fc0c09a5ec849ff3e29c75baa406d8cb9e4947e6d46efdba4c680`.
- Final demonstration checkpoint SHA-256: `sha256:24cb8d7fb5fd6f4343863de668a9604f75e44bc9b75d4ff66d5e2dc643111f38`.
- Implementation commit: `b81f4060c5973ad0e5b4ec88a385ce3e046f7ee3`.

All generated state and evidence remained in a local temporary directory outside version control. No private or external system was accessed.

## Phase boundary

Technical pilot completion requires explicit Human acceptance before Phase O5. It does not authorize production operation, real autonomous Agent deployment, private tax-case access, credentials, permission expansion, protected-main merge/release, destructive action, tax submission, ELSTER/Finanzamt contact, or external transfer.
