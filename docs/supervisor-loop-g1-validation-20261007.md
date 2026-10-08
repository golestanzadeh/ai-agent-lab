# Supervisor Loop G1 Validation — 2026-10-07

Status: **PASS**

## Scope

Validate read-only Codex usage telemetry on the actual Windows/ChatGPT account without starting a model thread or project task.

## Environment

- Codex CLI: `0.160.1`
- Authentication mode reported by Codex: ChatGPT
- Transport: local `codex app-server --stdio`
- Request: `account/rateLimits/read`
- Reader output: local ignored `.runtime/usage/CODEX_USAGE.json`

No OAuth/access/refresh token was read, copied, logged, or committed.

## Observed contract

The live response unambiguously exposed:

- primary window: 300 minutes;
- secondary window: 10080 minutes;
- service-provided `usedPercent` and `resetsAt` for both windows;
- `ordinaryUsageAllowed`.

The validation observation reported 0% used in both windows (100% remaining). The reset timestamps were service-provided and successfully normalized as timezone-aware values. These values are validation evidence only and must not be reused as future live capacity.

The probe initialized App Server and read account rate-limit metadata only. It did not create a Codex thread, submit a model prompt, or execute project work.

## Implementation

- `src/agent_lab/codex_usage_reader.py` performs the read and strict normalization.
- `scripts/codex_usage_reader.py` writes the normalized snapshot.
- The reader accepts only the expected `codex` limit identity, 300-minute primary window, and 10080-minute secondary window.
- Missing, malformed, expired, or ambiguous evidence fails closed.
- `.runtime/` is Git-ignored.
- The normalized snapshot adapts directly to the existing `CapacityObservation`; no second Limit Guard was introduced.

## Verification

- Focused unit tests: `33 passed`.
- Real local smoke: PASS; `.runtime/usage/CODEX_USAGE.json` created from the authenticated App Server.
- Git ignore check: PASS; runtime snapshot is ignored.

## Next gate

G2 only: validate one non-sensitive synthetic MCP Event delivered to one designated ChatGPT Work chat. G1 grants no scheduler, product, merge, submission, or external-transfer authority.
