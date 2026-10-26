# A1.1: bounded Kernel Health client and ServiceHost adapter

Status: DEVELOPMENT_IMPLEMENTED / 258_FOCUSED_TESTS_PASS / INDEPENDENT_REVIEW_PENDING / NOT_DEPLOYED.

## Implemented
- `kernel_health_client.py`: Windows Named Pipe health query in a separately spawned Python worker. Caller enforces a wall-clock timeout and terminates/kills the worker if blocked. The worker uses the existing `c09_named_pipe.verify_connected_server` to check actual peer process PID continuity, token SID, executable path and SHA-256 against caller-supplied pinned `PinnedProcess` evidence, before sending the canonical health request. Fail closed for invalid identity, timeout and transport errors. A pin must be supplied; no fallback to trusting arbitrary peer.
- `kernel_health_service_adapter.py`: explicit composition of restricted HEALTH runtime with existing `ServiceHost` lifecycle. It checks fixed Kernel role/name/SID, exposes only start/stop and leaves existing `run_scm_service` unchanged. No service registration or privilege change.
- Tests: successful real Windows peer verification, wrong pinned SID, missing endpoint deadline, missing pin, simulated ServiceHost lifecycle and real rejection of unprivileged current Windows user. All 258 focused tests passed.

## Critical boundaries
- This is **not** an operational Kernel Service. The adapter test supplying a pinned SID string is explicitly synthetic and cannot prove a real service token. Actual local Windows account is not `AITaxKernel`.
- The pinned process values used by the development test are obtained from the local test executable. Production pinning must use a separately approved, immutable manifest and actual deployed binary evidence.
- The client worker has bounded caller wait but may take additional time to terminate/reap; the server still uses synchronous blocking pipe I/O and does not implement independent cancellation of a stalled malicious client. This is not a fully bounded end-to-end server transport.
- Existing development server uses current-user ACL, not production pinned Kernel SID ACL. The SCM host entrypoint remains fail-closed `unavailable_runtime`.
- No Identity/Custodian dispatch, protected mutation, Drive, Gemini, ELSTER, owner approval, or C09 acceptance is enabled.

## Remaining
Independent review exact commit, hostile/hung server and client fault-injection tests, production-safe peer pin provisioning, fully cancellable server lifecycle, SCM composition under real approved principal, config/ACL review, Owner deployment gate, and operational acceptance.
