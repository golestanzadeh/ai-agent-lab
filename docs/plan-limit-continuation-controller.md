# Plan-Limit Continuation Controller

Status: **ACTIVE / AGENT-LED CONTINUOUS EXECUTION / EXCEPTION-ONLY REPORTING**

## Purpose

Prevent a long-running project turn from exhausting the Codex five-hour or weekly allowance, preserve an exact durable continuation point before stopping, and resume previously authorized work in the same task after capacity returns.

This controller is an operational cost guard. It grants no new project, production, permission, merge, release, tax-submission, or external-transfer authority.

## Authoritative limit source

Use the Codex account usage-limit service exposed by the desktop app. For each available window:

`remaining_percent = max(0, 100 - used_percent)`

UI percentages may be rounded. Decisions use the service value and its actual `resetsAt` timestamp, not an assumed five-hour delay or a screenshot. If the service is unavailable or a required value is unknown, fail closed and start no new work package.

## Control states

| State | Five-hour remaining | Weekly remaining | Allowed behavior |
|---|---:|---:|---|
| `RUN` | above 25% | above 20% | Start or continue one bounded authorized package. |
| `CAUTION` | 16–25% | 11–20% | Start no large package; finish only the current atomic step, verify it, and prepare a checkpoint. |
| `TOKEN_PAUSED` | 15% or less | 10% or less | Start no project work; record the stop reason, exact continuation point, branch/HEAD, dirty-state ownership, next authorized action, and relevant Human Gates. |
| `UNKNOWN_PAUSED` | unknown | unknown | Fail closed until usage can be read reliably. |

The lower weekly threshold avoids permanently stranding the acceptance/checkpoint write near the weekly boundary. A task may choose to pause earlier when the next atomic operation cannot safely complete inside the remaining allowance.

## Required observations

Read limits:

1. at the start of every project turn;
2. immediately after completing, verifying, committing, and pushing each bounded work package;
3. treat that end-of-package observation as the authorization check before starting the next package;
4. before a broad test suite or other expensive operation when the last observation may no longer provide a safe buffer;
5. before commit/push when the package consumed enough capacity that the safety buffer may have changed;
6. whenever the app warns that a limit is nearly exhausted.

An individual tool call cannot be interrupted midway. Therefore work packages must remain small enough that the next observation occurs before the safety buffer is consumed.

## Durable stop contract

Before ending for a limit, update the governed project state with:

- status `TOKEN_PAUSED` or `UNKNOWN_PAUSED`;
- the limiting window and observed remaining percentage;
- the service-provided reset timestamp;
- exact branch, HEAD, and local/remote synchronization state;
- any user-owned or incomplete working-tree changes;
- the last completed verification;
- one exact next action that is already authorized;
- every Human Gate that still blocks later work.

Commit and push this checkpoint only when those Git actions remain safe and authorized. If capacity is too low to do so, do not begin another operation; report that the durable update is incomplete.

## Scheduled continuation guard

Use one hourly heartbeat attached to the current task. On each run it must:

1. read live five-hour and weekly limits;
2. remain quiet if another turn is active, the repository is not safely recoverable, or no exact next action is already authorized;
3. remain quiet and make no project changes while either resume threshold is unmet;
4. resume from a durable `TOKEN_PAUSED` checkpoint only when five-hour remaining is at least 80% and weekly remaining is above 10%;
5. while continuous authority is active, reread `PROJECT_CHECKPOINT.md` and required references, verify branch/HEAD/working tree, then perform a recorded local synthetic non-production package that certainly requires no Human Gate;
6. after each completed and pushed package, reread live limits and use that observation as the precondition for the next package; continue package by package in the same heartbeat while limits, repository safety, prerequisites, and Human Gates allow;
7. stop before the next package when a threshold, unsafe repository state, unclear ownership, missing prerequisite, or Human Gate is reached;
8. notify the Project Owner only on a meaningful pause, resume, completion, failure, conflict, or required Human action.

If the pause was caused by the weekly window, five-hour resets alone cannot authorize resumption; the weekly threshold must also recover.

The same-task heartbeat is named `Plan Limit Continuation Guard`, has automation id `plan-limit-continuation-guard`, and uses an hourly cadence while active. It was paused on 2026-09-15 when package 7 reached a genuine Human Gate. The Project Owner later granted continuous local synthetic non-production authority and explicitly reactivated autonomous progression with exception-only reporting. The guard is therefore active and performs at most one bounded package per heartbeat while the repository, limits, prerequisites, and Human Gates remain safe.

## Host and scheduler limitation

Scheduled local-project work requires the computer to remain on, the Codex desktop app to be running, and the saved project directory to remain available. A missed run is not proof of project failure; the next run must recover from the repository checkpoint rather than chat memory.

## Initial live observation

On 2026-09-14, the account service reported five-hour `usedPercent: 1` (99% remaining; the UI may display 100%), weekly `usedPercent: 38` (62% remaining), five-hour reset at `2026-09-14 23:47:38 +02:00`, and weekly reset at `2026-09-20 13:48:09 +02:00`.

That observation established the initial `RUN` state. Live percentages are intentionally not copied forward as current facts: every heartbeat must reread the account service. Project authority remains in `PROJECT_CHECKPOINT.md` and `DECISIONS.md`; this controller never creates authority.

## Official product basis

OpenAI's scheduled-task documentation states that a task can return to the same chat with its existing context, can run on minute/daily/weekly schedules, and should use a reusable prompt that defines when to report, stop, or request input. Local-project scheduled work requires the desktop app and computer to remain running. See: <https://learn.chatgpt.com/docs/automations>.
