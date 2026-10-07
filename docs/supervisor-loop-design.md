# Supervisor Loop Design

Status: G1 PASS / G2-G4 LOCAL VALIDATION REQUIRED
Date: 2026-10-07
Branch: `d022-supervisor-loop-design`

## Purpose

Close the currently recorded `NO_AUTHORITATIVE_SCHEDULER` gap without introducing a second orchestrator, autonomous product authority, polling loop, or credential-bearing GitHub workflow.

The Deterministic Orchestrator Kernel remains the execution authority. ChatGPT Work remains supervisor/planner/Human-Gate surface. Codex remains a development worker.

## Target loop

```text
Human Authority
  -> ChatGPT Supervisor
  -> zero-inference usage telemetry
  -> deterministic Limit Guard
  -> one-shot Work wake carrying one exact task
  -> Work
  -> Deterministic Orchestrator Kernel
  -> bounded worker(s)
  -> tests / Independent Acceptance
  -> durable result/checkpoint
  -> completion event
  -> subscribed ChatGPT Work chat
  -> supervisor review
  -> next bounded task OR HUMAN_REQUIRED
```

No component may invent new product authority.

## Component contracts

### 1. Usage telemetry

Preferred source, subject to local validation:

`codex app-server -> account/rateLimits/read`

The reader must be read-only and must not issue an inference request.

Normalized runtime output:

```json
{
  "schema_version": 1,
  "measured_at": "<RFC3339>",
  "source": "codex_app_server",
  "five_hour": {
    "used_percent": 0,
    "remaining_percent": 100,
    "reset_at": "<RFC3339|null>"
  },
  "weekly": {
    "used_percent": 0,
    "remaining_percent": 100,
    "reset_at": "<RFC3339|null>"
  }
}
```

Values above are schema examples, not account observations.

Requirements:
- fail closed on missing/malformed/ambiguous limits;
- never read or persist OAuth/access/refresh tokens;
- never call an LLM to obtain usage;
- runtime output is local and non-authoritative evidence, not Git source;
- Limit Guard consumes normalized values only after local equivalence is proven against the account Usage display.

### 2. Limit Guard

Existing deterministic capacity governance remains authoritative.

Inputs:
- normalized live usage snapshot;
- exact bounded task budget;
- existing project thresholds and Human Gates.

Outputs are closed:
- `ALLOW`
- `WAIT_UNTIL_RESET`
- `HUMAN_REQUIRED`
- existing governed stop states where applicable.

No polling loop is introduced.

### 3. One-shot Work wake

The existing reserved logical identity `plan-limit-continuation-guard` remains the scheduler identity unless repository authority later changes it.

A wake carries one exact bounded task. It may not:
- choose a new product objective;
- create an autonomous continuation chain;
- bypass Kernel dispatch;
- bypass Independent Acceptance;
- merge/release/submit externally;
- amplify authority.

Real Work wake behavior remains unproven until the local smoke test.

### 4. Runtime result

Local runtime paths:

```text
.runtime/usage/CODEX_USAGE.json
.runtime/work-bridge/WORK_RESULT.md
.runtime/work-bridge/BRIDGE_STATE.json
```

These paths must remain ignored by Git.

Minimum bridge state:

```json
{
  "schema_version": 1,
  "task_id": "<id>",
  "status": "PASS|BLOCKED|HUMAN_REQUIRED|TOKEN_PAUSED",
  "completed_at": "<RFC3339|null>",
  "commit": "<sha|null>",
  "checkpoint": "<id|null>",
  "supervisor_review": "REQUIRED"
}
```

### 5. Completion event

Preferred transport, subject to product-availability validation: OpenAI MCP Events subscribed by one persistent AI-Tax-Agent Work chat.

Closed event names:
- `task.completed`
- `task.blocked`
- `task.human_required`
- `task.token_paused`

Event payload must contain only non-sensitive routing/status metadata. Taxpayer evidence, credentials, tax values, documents, and private case content are prohibited.

Example:

```json
{
  "event_id": "<unique id>",
  "name": "task.completed",
  "timestamp": "<RFC3339>",
  "data": {
    "repository": "golestanzadeh/ai-agent-lab",
    "task_id": "<id>",
    "status": "PASS",
    "commit": "<sha|null>",
    "result_path": ".runtime/work-bridge/WORK_RESULT.md"
  }
}
```

The subscribed supervisor must retrieve authoritative detail from the repository/runtime rather than trusting event prose.

### 6. Supervisor behavior

On a completion event the supervisor:
1. resolves exact task identity;
2. reads result/state/checkpoint;
3. inspects referenced Git changes;
4. verifies tests and Independent Acceptance evidence;
5. accepts, rejects, or requests Human authority;
6. reads fresh usage telemetry before any next execution;
7. creates at most one next bounded wake if existing authority permits it.

The supervisor must stop at any unresolved Human Gate.

## Security boundaries

- no secrets in Git;
- no direct handling of Codex auth tokens by project code;
- no taxpayer/private data in MCP events;
- no Telegram dependency in the target architecture;
- no direct external tax submission;
- no new orchestrator;
- no recurring high-frequency polling;
- no claim that MCP Events or Work wake works until smoke-tested in the actual account/environment.

## Validation gates

### G1 - Usage telemetry

PASS only if:
- local `account/rateLimits/read` is callable;
- returned 5-hour and weekly windows are unambiguous;
- reset timestamps are present/understood;
- values match the account Usage display within an explicitly explained refresh tolerance;
- the probe causes no model inference/task execution.

Failure: retain existing Limit Controller source and do not integrate the reader.

### G2 - MCP event delivery

Use a non-sensitive synthetic event only.

PASS only if:
- one designated Work chat subscribes;
- one event reaches that same chat;
- signature/callback handling succeeds;
- no duplicate execution occurs;
- event arrival invokes only the pre-authorized smoke-test instruction.

Failure: do not build a replacement automation subsystem. Keep the current manual supervisor boundary.

### G3 - One-shot wake

Use one inert task: read the latest checkpoint and write a short result/state only.

PASS only if:
- exactly one wake occurs;
- the intended local project context is available;
- no product/code change occurs;
- result/state are written once;
- no continuation is invented.

### G4 - End-to-end loop

Only after G1-G3 PASS:
`usage -> guard -> wake -> Work -> Kernel boundary -> result -> event -> supervisor review`

The first E2E proof must use synthetic/non-sensitive data and must not perform an external tax action.

## Deferred implementation

G1 was locally validated on 2026-10-07 and the strict Codex usage reader is now implemented. Evidence: `docs/supervisor-loop-g1-validation-20261007.md`.

The following remain intentionally NOT implemented before their local validation:
- an MCP callback server requiring account-specific subscription details;
- a Work scheduler binding;
- credentials/secrets;
- Telegram;
- any production continuation behavior.

This is deliberate compliance with AGENTS.md: no speculative production code before the relevant design is agreed and experimentally validated.
