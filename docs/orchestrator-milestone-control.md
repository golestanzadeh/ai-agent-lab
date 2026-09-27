# Orchestrator Milestone Control

## Authority and purpose

Owner approval `ORCH-CONT-20260927-001` authorizes a bounded extension of the existing Master Orchestrator and deterministic Kernel. It does not create another orchestrator, Agent Bridge, scheduler, or remote shell. The extension remains local, synthetic, non-production, and bound to the existing branch and Human Gates.

## Versioned authority contract

`contracts/orchestrator/v1/milestone-authority.schema.json` defines one exact `ACTIVE` authority envelope. It pins the repository/ref, Owner approval reference, ordered package templates, dependency package IDs, maximum generated packages, maximum queue-exhaustion replans, the sole `SYNTHETIC_LOCAL_V1` adapter, and mandatory forbidden actions.

The Kernel validates the same closed boundary before persisting an authority. A generated task must exactly match its authorized template for objective, role and actor, synthetic inputs, local outputs, tools, permissions, forbidden actions, budgets, retry limit, acceptance criteria, stop conditions, and escalation route. Repository/ref changes, case context, parent substitution, extra tools or permissions, weakened prohibitions, expired authority, unknown packages, forward dependencies, and limits fail closed.

## Queue semantics

`select_ready_package()` reads the existing task/dependency registry and returns the lowest authorized sequence whose task is `REGISTERED`, whose dependencies are all independently accepted and `COMPLETED`, and whose Human Gates are resolved. It does not dispatch or grant capability.

`replan_authorized_package()` is available only when no registered authorized package is ready. It can materialize only a still-unused pre-approved package template, preserves dependency ordering, increments a durable bounded counter, and cannot add or alter authority.

## Durable diagnostics and recovery

Every non-token terminal stop can be persisted through `record_stop_diagnostic()` with exact category, summary, impact, automated recovery, required next action, continuation point, and time. Diagnostics, authorities, package lineage, and counters are included in the Kernel checkpoint snapshot and hash-chained audit. Token pauses remain governed by the existing token checkpoint rather than this non-token record.

## Dispatch and proof boundary

The only authorized adapter is `SYNTHETIC_LOCAL_V1`. Its implementation and the two-package proof are the next registered package. The proof must include one classified recoverable failure with a new attempt identity, independent acceptance for both packages, queue-exhaustion replanning, checkpoint close/reopen recovery, and a simulated capacity pause. It must use no network, provider, credential, tax case, real data, official ERiC engine, protected-main write, external transmission, production operation, or scheduler change.
