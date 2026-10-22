# Independent C09 architecture and security review

Reviewed commit: `27f2cb8e29745f3cc2a8ddbc1e8b1b724bdb87d6`  
Reviewer: `/root/c09_architecture_independent_review`  
Decision: **`INDEPENDENT_ARCHITECTURE_FAIL`**

The reviewer used a separate read-only context, authored no part of the proposal and made no file, commit or implementation change. Exact branch/SHA and remote alignment were verified. Focused existing protocol/regression verification passed `251 passed` with `PYTHONPATH=src`; an earlier invocation without the source path failed collection and grants no product evidence.

## Findings requiring remediation

| ID | Severity | Finding | Minimum correction and negative evidence |
| --- | --- | --- | --- |
| F01 | HIGH | Concurrent preparations from the same Identity head are not serialized at COMMIT. | Atomic live-head compare-and-swap, proof consumption, mutation, audit and `IDENTITY_COMMITTED`; concurrent same-predecessor commits permit exactly one winner. |
| F02 | HIGH | Staging “exact witness bytes” before Custodian authentication conflicts with the final record containing its MAC/signature. | Freeze an unsigned canonical preimage and bind staged receipt to its digest; verify exact preimage reproduction and both preimage/final-record digests. |
| F03 | HIGH | Kernel↔Key-Custodian authentication, receipt validation, replay protection and audit are unspecified. | Define a closed, token-authenticated, one-time custodian protocol and wrong-SID/forgery/replay/substitution negatives. |
| F04 | HIGH | Kernel server verification by Identity SID alone permits same-SID wrong-binary squatting and leaves PID TOCTOU ambiguity. | Pin and race-resistently verify process handle, SID and protected executable path/hash; deny PID turnover or inspection failure. |
| F05 | HIGH | Restore lacks exact cross-store stage/witness/activation ordering and crash convergence. | Define durable states, generation IDs, authorization reservation/consumption and every crash boundary; mixed generations never become accepted. |
| F06 | HIGH | Operational contract lacks exact fields, closed matrices, algorithms/key rules, transitions and golden vectors. | Freeze a complete operational appendix and exhaustive permitted/forbidden/version/downgrade/scope-confusion tests. |

No operational implementation is authorized by this review. Exact next action is architecture-only remediation F01–F06 followed by a new independent review on the corrected exact commit. C09 and OI-0002 remain open.
