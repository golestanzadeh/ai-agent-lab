# A1.1 restricted Kernel health contract: development evidence

Status: PARTIAL_IMPLEMENTATION / NOT_INDEPENDENTLY_ACCEPTED / NOT_DEPLOYED.

## Scope
New `src/agent_lab/kernel_health_contract.py` defines `ai-tax-agent.kernel-health/1.0`, an isolated canonical JSON health message with exact closed fields, bounded 4096-byte messages, deployment/request correlation and SHA-256 response binding. Only `HEALTH` is supported; response status `ALIVE_RESTRICTED` is not an authorization, Identity readiness, C09 acceptance or proof of actual service health.

The protocol is **not connected** to SCM, Windows Named Pipe, or an authenticated Windows service principal. Its `handle_request` is an in-process pure function. Do not treat its success as real peer authentication or service liveness.

## Verification
Local focused pytest run: 237 passed (10 new health contract tests plus 227 existing service host, named pipe and IPC tests).

## Remaining for A1.1
1. Specify and independently review the Kernel health transport endpoint and its Windows ACL/peer authentication rules. Existing `c09_named_pipe.py` freezes Identity and Custodian names only; do not reuse those pipes for Kernel health.
2. Implement the bounded real transport client/server, timeout, cancellation, correlation and deterministic disconnect handling.
3. Implement Kernel runtime factory and actual service lifecycle integration; preserve Identity/Custodian fail-closed factories.
4. Add integration tests for real transport, unauthorized principal, restart and shutdown.
5. Obtain independent exact-SHA review before acceptance.

## Remaining for A1.2
Explicit Owner approval for privileged service principal, executable identity, configuration, SCM install and runtime activation; then verify actual service SID and end-to-end health communication.

## First real case
Still requires operational Identity/C09 acceptance, evidence-bound OI-0003 subject registration, approved Drive binding and restricted UI-to-Kernel case creation workflow. Gemini and CSV are not prerequisites for first case creation.
