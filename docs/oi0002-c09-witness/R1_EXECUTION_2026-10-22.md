# C09-R1 execution gate and scope (2026-10-22)

Status: R1 STARTED / IMPLEMENTATION PENDING / NO OPERATIONAL PASS.

Owner direction: proceed sequentially R1-R4 without routine human intervention, and commit test evidence plus `OPEN_ITEMS.md` and `PROJECT_CHECKPOINT.md` reconciliation before starting each next stage. This is not approval for irreversible retention lock, expanded cloud privilege, production taxpayer mutation or self-attested independent acceptance.

Preflight observations: `c09-witness-hardening` clean; `OPEN_ITEMS.md` still listed `OWNER_DECIDE_C09_WITNESS_PROFILE` and obsolete 15-test-only evidence; checkpoint likewise stale. Existing `src/agent_lab/c09_witness_simulation.py` is explicitly non-operational. Prior T01-T08 evidence committed as `9d6401f`, `e48edfa`, `2cfb926`, `5f586ea`. GCS Frankfurt pilot is selected as the bounded synthetic implementation target; seven-day retention remains unlocked.

R1 minimal implementation target: provider adapter with create-if-absent generation precondition, authenticated ordered chain verification, exact generation/bytes readback, durable staged receipt, Kernel-controlled PENDING/Identity/witness/COMMITTED sequencing and fail-closed startup/recovery. Reuse existing Kernel interfaces and test identities. No new orchestrator or DB.

R1 acceptance: actual adapter tests plus synthetic end-to-end protected operation with fault injection, independent readback, and evidence of no acknowledgement before durable commit. Only after PASS, documentation commit, checkpoint/open-items synchronization and push may R2 begin.

Current result: BLOCKED FROM R2 because R1 operational integration is not yet implemented or tested. This record is a truthful execution-start checkpoint, not test evidence or acceptance.
