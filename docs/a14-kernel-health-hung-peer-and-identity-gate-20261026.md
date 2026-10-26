# A1.1: hung-peer isolation, disconnect tests and real identity gate

Status: DEVELOPMENT_IMPLEMENTED / 261_FOCUSED_TESTS_PASS / INDEPENDENT_REVIEW_PENDING / NOT_DEPLOYED.

## Fault injection
- A Windows client connects to the development Named Pipe and sends no bytes. The server's blocking ReadFile is isolated in a disposable child process; the supervisor stop() terminates and reaps it in a bounded interval.
- A second Windows client disconnects immediately after connection; shutdown succeeds without protected operations.
- The existing C09 ServiceHost refuses the actual interactive Windows user's SID as the fixed AITaxKernel principal.
- Directly constructed ServiceConfiguration is revalidated for exact schema, role, name, SID, enabled flag, and bounded nonempty deployment identity. This fixes the independent review P2 against commit 918fe07.

## Architecture
`kernel_health_supervisor.py` provides bounded process-level stop for a development-only health endpoint. The existing `RestrictedHealthRuntime` uses this supervisor, without changing `run_scm_service`, registering a Windows service, creating an account, or modifying ACLs.

## Real AITaxKernel identity proof: deliberately NOT performed
A real service-principal proof requires explicit Owner authorization for the separate SCM deployment gate. At that future gate, inspect the actual running process token SID using `current_process_sid()` and compare against the pinned `ROLE_BINDINGS[ServiceRole.KERNEL]`, verify SCM service-to-process PID binding and executable hash, and require independently reviewed deployment configuration. A simulated SID string or test-run process is NOT evidence of actual AITaxKernel execution. Current SCM entrypoint remains fail closed and unchanged.

## Known limitations
The development server remains single-connection synchronous: a silent client can prevent *new* health requests until it disconnects or the child process is terminated. Process termination is not a graceful in-flight request cancellation. Full end-to-end service availability, hardened production pipe ACL, approved immutable peer pin manifest, Windows SCM lifecycle, actual service SID proof, crash recovery and independent acceptance remain open. No protected operations or external transmission authorized.
