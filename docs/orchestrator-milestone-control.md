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

## Dispatch and proof result

The only authorized adapter is `SYNTHETIC_LOCAL_V1`. It writes a deterministic JSON evidence artifact below one fixed local root and cannot invoke a shell, network, provider, credential, tax-case path, ERiC engine, scheduler, or protected branch.

The executed two-package proof returned `PASS` with two completed packages, three uniquely identified dispatch attempts, one classified `retriable_process_error`, two distinct Independent Acceptance records, one bounded queue-exhaustion replan, audit integrity `PASS`, and final kill-switch state `HALTED`. The simulated capacity pause was checkpointed, the database was closed and reopened, and the exact pause checkpoint was verified before resumption.

- pause checkpoint: `sha256:8aa03d0e3fd8f86f2add293982a5772dd1844f0907d1cd234f4c667368176eaf`
- final checkpoint: `sha256:66e5fda339348d375846a1128eb792828cf68576fb8853321b0751e7aacd8442`
- focused continuity/Kernel verification: `31 passed`
- complete unit regression: `863 passed, 1 warning`

The negative suite also proves that authority amplification, premature replanning, duplicate/over-limit replanning, token misuse of non-token STOP diagnostics, and a terminal synthetic proof failure fail closed. A terminal non-token failure persists its impact, automated recovery, required next action, and continuation point.
