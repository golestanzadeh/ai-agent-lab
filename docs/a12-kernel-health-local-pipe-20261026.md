# A1.1 local Kernel HEALTH Named Pipe integration (development only)

Status: IMPLEMENTED_LOCAL_DEVELOPMENT_TRANSPORT / NOT_OPERATIONALLY_ACCEPTED / NOT_DEPLOYED.

A dedicated Windows local Named Pipe `\\\\.\\pipe\\AI-Tax-Agent-Kernel-Health-Dev-v1` now exchanges real canonical `ai-tax-agent.kernel-health/1.0` request/response messages. It uses a first-instance-only, local-client-only pipe with Windows ACL for the executing development user and SYSTEM. The server checks the actual connected client token via Named Pipe impersonation, reverts before handling, and rejects invalid deployment, operation, correlation and digest. It handles only HEALTH, with `ALIVE_RESTRICTED` status, no case data or protected commands. Local tests exercise real connection, response, wrong deployment, first-instance collision and shutdown.

This is a *development process endpoint*, not the fixed SCM Kernel role. It deliberately does not alter `run_scm_service`, install services, modify principals, use production Identity/Custodian pipes, open credentials, or enable case creation. The development-user ACL does **not** satisfy the pinned operational service identity. The client does not yet verify a pinned Kernel server executable/token/hash. The `timeout_ms` parameter bounds WaitNamedPipe availability only; it does **not** enforce an end-to-end read/write deadline. A peer that connects and never replies can block the client. Server shutdown also requires no hung client. These are operational blockers, not accepted features.

Next mandatory steps before service acceptance: independently review transport; add pinned server process evidence and robust bounded I/O cancellation/reconnect/restart; define and review separate operational endpoint ACL and deployment configuration; compose Kernel service lifecycle using the existing SCM role with actual principal validation; test hostile client, peer substitution, hanging I/O, crash/restart. Privileged install and protected activation remain separate Owner gates.

Independent review of commit cb0c9ec reported P2: pywin32 was missing from the standard dependency set. Remediation: pin `pywin32==312; sys_platform == "win32"` in root `requirements.txt`; rerun focused integration tests and re-review the exact remediation commit. This does not address the separate authentication and end-to-end timeout blockers.

No claim of operational service, C09/OI-0002 closure, real case creation, Drive access, or production readiness.
