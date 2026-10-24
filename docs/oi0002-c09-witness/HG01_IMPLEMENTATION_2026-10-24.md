# C09/R3 HG-01 governed implementation

## BP-01 frozen development build profile

Status: `PASS / PROFILE_FROZEN / NO EXECUTABLE YET`.

Host evidence: CPython `3.14.2`, Windows amd64, and installed pywin32 `312`. PyInstaller was not preinstalled. The selected profile uses PyInstaller `6.22.3` in `onedir` mode with `--clean`, no UPX and three distinct role-specific executables/directories. `onedir` preserves observable role-specific executable paths and avoids one-file temporary extraction. PyInstaller is a packaging tool only and introduces no runtime authority.

`requirements-hg01-build.txt` pins PyInstaller, pywin32 and all build-time transitive dependencies to exact versions and downloaded wheel SHA-256 values. Installation is binary-only with `--require-hashes`. The frozen machine-readable profile is `config/c09-r3/hg01-build-profile.json`.

Two clean builds are mandatory. Whole output trees must be compared by relative path and SHA-256. Bit-for-bit reproducibility may be claimed only if every entry matches; otherwise every difference must be recorded and the package remains not approval-ready. Development artifacts are unsigned. Operational Authenticode signing remains a separate Human Gate and custody decision.

Focused build-profile/security verification: `35 passed`. No package was installed, no executable was built, no service source or host state changed, and no reproducibility claim is made.

Exact continuation: `HG01-I01` three explicit service entry points and non-privileged lifecycle harnesses, followed by focused tests and checkpointing.

## HG01-I01 service entry points

Status: `TECHNICAL_PASS / FAIL_CLOSED_SKELETON / NOT OPERATIONAL`.

Three separate fixed-role entry modules now target `AITaxKernel.exe`, `AITaxIdentity.exe` and `AITaxKeyCustodian.exe`. They expose no role-selection or service-install command line. The shared pywin32 SCM host reads only each role's fixed protected configuration path, queries the actual process token SID and requires the exact manifest-pinned service name/SID/role before constructing a runtime.

Lifecycle transitions are locked and deterministic. Wrong SID/role, malformed/unknown/disabled configuration, unavailable composition and start/stop exceptions enter `HALTED`. The current runtime factory deliberately fails closed because transport, dispatch and Custodian composition belong to later packages; the services cannot perform a protected operation.

Verification: `46 passed` focused and `363 passed` relevant C09/Identity/IPC/Kernel. No service was installed or started, no account right/ACL changed and no credential or protected store was accessed.

Exact continuation: HG01-I02 authenticated Named Pipe transport. It must authenticate actual Windows tokens, enforce fixed DACL/local-only/first-instance behavior, bind retained server image identity, reuse canonical framing and remain independently testable without installing services.

## HG01-I02 authenticated Named Pipe transport core

Status: `TECHNICAL_PASS / HOST-INTEGRATION_PENDING / NOT ACTIVATED`.

The Windows-native transport core freezes the two approved pipe names, creates message-mode local-only single-instance servers with `FILE_FLAG_FIRST_PIPE_INSTANCE`, a protected DACL containing only SYSTEM and the pinned Kernel SID, bounded canonical frames and no generic endpoint. Server-side authorization impersonates the connected client, reads the actual thread token SID and always calls `RevertToSelf` before dispatch. Client-side verification retains the server process handle and binds two PID reads, actual process-token SID, normalized pinned image path and executable SHA-256. PID turnover, wrong SID/path/hash, malformed/trailing/oversized frames and noncanonical envelopes fail closed.

The first run exposed an incorrect envelope helper name and an oversized pytest parameter ID; both were corrected before any PASS claim. Verification passes `227` focused transport/protocol/service tests and `112` relevant C09/Identity/Kernel tests. No pipe endpoint was activated outside tests and no service/ACL/account was changed. Wiring the transport into the service runtimes remains pending with HG01-I03 Custodian/runtime composition.

## HG01-I03 synthetic Custodian boundary

Status: `TECHNICAL_PASS / SYNTHETIC_KEY_ONLY / OPERATIONAL_PROVIDER_BLOCKED`.

The bounded Custodian runtime exposes only `AUTHENTICATE_WITNESS` and `VERIFY_WITNESS`, requires exact request fields, a Kernel authorization callback, exact staged-receipt resolver, canonical preimage/request digests, a 32-byte nonce and a maximum five-second valid window. It records transaction/nonce replays: exact retry is deterministic and changed retry is denied. Only authentication and signed-record digests leave the boundary; key bytes are never returned or logged. Missing custody, stopped runtime, role/operation/schema substitution, receipt mismatch, expired/overlong time and preimage changes fail closed.

Verification passes `34` focused service/transport/Custodian tests. The implementation deliberately accepts only injected synthetic key bytes. The service executable remains fail-closed because HG-04 has not supplied an operational non-exportable provider reference; no operational key was created/imported/used.

## HG01-I04 local build and reproducibility result

Status: `BUILD_PASS / REPRODUCIBILITY_FAIL / UNSIGNED_DEVELOPMENT_ONLY`.

The hash-locked wheelhouse installed into an isolated ignored virtual environment. Two clean builds from source commit `97adcca94b845dd931aac13cb4f669571daa62f4` produced three actual onedir executables per build. Each tree contained 204 recorded files. Exact comparison returned 12 differing rows across six logical paths: every role's EXE and `base_library.zip`. Bit-for-bit reproducibility is therefore **not** claimed.

Build A executable SHA-256 values are recorded in `config/c09-r3/hg01-build-evidence.json`. All three Authenticode states are `NotSigned`. Artifacts remain only under the ignored `.runtime` build root and were not installed, started or committed. Because they predate the final candidate and fail exact reproduction/signing, they are evidence of build feasibility—not deployment candidates.

## HG01-I05 signing profile

Status: `PROFILE_PASS / OPERATIONAL_SIGNING_HUMAN_GATE`.

The prepared profile requires Authenticode SHA-256, an RFC3161 SHA-256 timestamp, Code Signing EKU, pinned publisher/thumbprint, valid chain and revocation checks. Missing/invalid/revoked/wrong-signer/wrong-hash evidence denies installation and startup. Development builds may remain `NotSigned` but are never deployment-eligible. The private key must be non-exportable in an Owner-selected provider; selection, provisioning, grant, signing and revocation are separately prohibited Human Gates.

The verifier is read-only and fixed to the ignored HG-01 build root. No certificate/key was created, imported, selected or used. No artifact was modified.

## HG01-I04 deterministic rebuild follow-up - 2026-10-24

Status: TECHNICAL_PASS / REPRODUCIBILITY_PASS / UNSIGNED_DEVELOPMENT_ONLY / INDEPENDENT_REVIEW_PENDING.

The original source 97adcca build remains REPRODUCIBILITY_FAIL, as recorded above; its historical evidence is not rewritten. The first repair stabilized Python hash iteration and native process exit handling (b0628a6, 7c4d201). PowerShell 5.1 UTF8 encoding incompatibility was repaired in f9b807d; two clean builds at f9b807d differed in three role-specific EXEs (75 manifest entries each). The PE timestamp was then pinned to source commit epoch in f1af82f.

At exact source f1af82fd1a7c858074db868d412604dba9589833, independent A and B clean onedir builds each recorded 75 relative-path artifact entries; all 75 path/size/SHA-256 entries matched, zero differing paths. Local evidence: ignored .runtime/hg01-build/f1af82fd1a7c858074db868d412604dba9589833/{A,B}/artifact-tree.json and .runtime/hg01-epoch-{A,B}.log. Full regression log .runtime/hg01-full-regression-f1af82f.log: 1558 passed, 6 skipped in 288.64 seconds. Git branch c09-witness-hardening and origin matched f1af82f before this documentation update.

This proves deterministic unsigned development packaging and regression at the cited source commit, NOT Authenticode signing, real service installation/startup, privileged runtime composition, operational key custody, independent security acceptance, or permission to deploy. Owner HG-01 through HG-07 remain closed to operations. Next authorized step: independent read-only HG01 security/architecture evidence review, with a separate approval gate before any operational changes.
