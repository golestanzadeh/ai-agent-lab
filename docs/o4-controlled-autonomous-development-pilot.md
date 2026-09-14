# Phase O4 — Controlled Autonomous Development Pilot

Status: **IMPLEMENTED; VERIFICATION PENDING**

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

## Phase boundary

Technical pilot completion requires explicit Human acceptance before Phase O5. It does not authorize production operation, real autonomous Agent deployment, private tax-case access, credentials, permission expansion, protected-main merge/release, destructive action, tax submission, ELSTER/Finanzamt contact, or external transfer.
