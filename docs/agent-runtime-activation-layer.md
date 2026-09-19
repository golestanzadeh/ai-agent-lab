# Local Agent Runtime Activation Layer

Status: **IMPLEMENTED LOCALLY / NON-PRODUCTION**

## Purpose

This layer closes the gap between an `ACTIVE` Kernel manifest and execution of a
bounded local worker. It connects the existing Planning, Implementation, Quality
Engineering, and Independent Acceptance roles without changing the Human-ratified
organization or accepted O2 contract digest.

## Execution flow

`Planning -> independent acceptance -> checkpoint/pause -> recovery -> Implementation -> QA -> independent QA acceptance -> independent implementation acceptance -> checkpoint/halt`

Every worker is a temporary, task-bound instance with a distinct actor identity.
Every task and manifest is registered and validated by the existing Kernel. The
runtime checks each declared capability immediately before invoking its fixed
local worker, charges the durable budget, records the exact response/evidence, and
requires a separate active Independent Acceptance instance before completion.

## Safety boundary

- only four exact role IDs are dispatchable;
- inputs must use `synthetic://` references;
- artifacts are immutable JSON below `artifacts/agent-runtime/`;
- workers are fixed in-process adapters, not arbitrary callables;
- no provider, model API, network, subprocess, shell, credential, real case data,
  persistence outside the selected local SQLite/artifact paths, production,
  protected-main action, destructive action, or external transfer exists;
- start requires the exact D-067 Human authority reference; completion halts the
  kill switch;
- recovery verifies the Kernel audit/checkpoint and immutable plan before continuing;
- replay and artifact overwrite fail closed.

This package accepts only the fixed D-067 synthetic proof objective and criteria;
caller-defined/free-form objectives are denied. It is genuine local role dispatch,
but it is not yet an LLM/model-backed Agent provider. Adding any provider or
broader tool adapter is a separate Human Gate.

Recovery is deliberately bounded to the durable `PLANNED/PAUSED` checkpoint.
An interruption after the resumed implementation transaction begins fails closed
and is not automatically replayed. General per-stage crash continuation is a
remaining non-production limitation, not a capability claimed by this package.

## Verification

- targeted runtime suite: `8 passed`;
- relevant runtime/Kernel/pilot suite: `39 passed`;
- full regression: `537 passed, 1 skipped`;
- Python compile check: passed;
- local two-invocation demonstration: 6 tasks/manifests, 4 roles, 2
  dependencies, 3 independent acceptances, 2 checkpoints, 46 audit events,
  audit `PASS`, final kill switch `HALTED`.

The unchanged Starlette TestClient deprecation warning belongs to the existing UI
test dependency boundary and did not affect this runtime result.
