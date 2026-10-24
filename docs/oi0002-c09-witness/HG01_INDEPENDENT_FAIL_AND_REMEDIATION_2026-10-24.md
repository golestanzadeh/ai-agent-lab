# HG01 independent Codex review outcome - 2026-10-24

Decision: INDEPENDENT_FAIL. User-supplied Codex review handoff; not independently re-executed by Supervisor. Reviewer detached worktree, source f1af82fd1a7c858074db868d412604dba9589833, preparation d637042601a7c621a6b807cbf8867e51a0a19b2a. Reviewer reported no source changes between these commits.

- F01 HIGH: VERIFY_WITNESS returns VERIFIED by calculating a new MAC without accepting and verifying an existing authenticated GCS record, object key or generation. Supervisor readback of c09_custodian_host.py confirms the same shared AUTHENTICATE/VERIFY branch and newly computed HMAC.
- F02 HIGH: Custodian relies on boolean authorization callback and digest field; no independent pinned Kernel public-key signature verification or complete proof in request schema.
- F03 MEDIUM: config/c09-r3/hg01-build-evidence.json still describes original failed 97adcca build; config/c09-r3/hg01-windows-services.json contains outdated implementation claims. Historical evidence must remain immutable, with a new exact-source evidence record.
- F04 MEDIUM: canonical CURRENT_NEXT_ACTION markers diverge. Reviewer full suite: 1556 passed, 5 skipped, 1 failed, 343.77 seconds, exit 1; failing test test_canonical_state_markers_are_identical.

Reviewer positive evidence: focused/relevant 309 passed; A/B 75/75 identical entries, zero duplicate paths/hash/size mismatches; all three EXEs NotSigned and services intentionally fail-closed. This positive evidence does NOT supersede INDEPENDENT_FAIL.

Reviewer reported end capacity five-hour 87% (reset 2026-10-25T02:36:13Z), weekly 61% (reset 2026-10-30T18:15:20Z), reserve 15 points maintained. These are historical measurements, not live dispatch admission. Supervisor MCP delivery failed -32603; user supplied complete handoff.

Remediation order: separate exact closed schemas AUTHENTICATE_WITNESS and VERIFY_WITNESS; verification of existing authenticated record bytes, object key, generation, MAC and digests; pinned Kernel public-key signature verification, durable replay reservation, adversarial forged/stale/substitution tests; canonical marker repair; new immutable build evidence; focused/full regression; new-source A/B clean rebuild; separate independent reviewer re-review. No HG01 operational acceptance or privileged activation.

Stage 1 remains FAILED / REMEDIATION_REQUIRED. Stages 2-5A cannot be marked completed or independently accepted. All HG-01..HG-07 Owner gates remain closed.