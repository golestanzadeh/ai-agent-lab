# Local Agent Runtime recovery inspector

This package adds a read-only classifier for the existing local, synthetic four-role runtime. It verifies the immutable plan/state artifacts, Kernel audit chain, latest checkpoint, kill switch, and durable response lineage before returning one of three states:

- `PLANNED_RESUMABLE`: the exact planned checkpoint is intact and paused;
- `COMPLETED`: the exact completion checkpoint is intact and halted;
- `INTERRUPTED_FAIL_CLOSED`: execution began after the planned checkpoint and exact completed-stage evidence is available, but automatic replay remains forbidden.

The inspector never resumes, rewrites, deletes, retries, or repairs work. An interrupted state explicitly requires governed repair because replaying a stage after an uncertain crash could duplicate side effects. This closes the diagnostic gap for mid-resume interruptions while preserving the existing runtime's fail-closed execution contract.

Provider activation, arbitrary work, real data, credentials, networking, subprocesses, production, protected-main actions, and external transfer remain outside this package.
