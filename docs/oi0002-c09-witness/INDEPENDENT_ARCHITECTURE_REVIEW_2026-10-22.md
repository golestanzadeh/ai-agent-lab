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

## Re-review of remediation commit `a43bf34c0550ba147d25748e36fc2d6bbf2c9e8b`

Decision: **`INDEPENDENT_ARCHITECTURE_FAIL`**. The independent reviewer confirmed that atomic head CAS, unsigned-preimage binding, same-SID pipe defenses, restore ordering and much of the protocol freeze were materially corrected. Four HIGH gaps remain: (R2-F01) Kernel cannot verify HMAC readback without receiving the custodied key or a closed verification operation; (R2-F02) per-operation payload/proof and request-state-outcome schemas remain open; (R2-F03) the capability statement conflicts with the existing accepted Permission Matrix names; and (R2-F04) Owner restore authorization lacks an independently authenticated canonical signature/custody/revocation profile. Focused verification again passed `251 passed`; that component evidence does not cure these contract gaps. No implementation is authorized before remediation and another independent review.

## Third review of commit `42c8be63bd6154deb14570c09dac0591d7a43a10`

Decision: **`INDEPENDENT_ARCHITECTURE_FAIL`**. R2-F01–F04 were substantially corrected, but four enforceability defects remain: no frozen message can carry verified witness evidence to transition Identity to `COMMITTED_FINAL`; restore is both specified and unreachable because its capabilities are reserved-denied; active-key-only HMAC verification makes pre-rotation history unverifiable; and the separate restore-revocation prefix lacks append/version/deletion/rollback rules. Existing component/documentation verification remained `251 passed`. Operational implementation remains blocked.

## Final re-review of commit `2c664800d8a3ace7cf0995c838a46d46c6a57191`

Decision: **`INDEPENDENT_ARCHITECTURE_PASS`**. Reviewer `/root/c09_architecture_independent_review`, in a separate read-only context, confirmed R3-F01–F04 resolved: `FINALIZE_MUTATION` is reachable and evidence-bound; closed A4 backup/restore capabilities have no default grant and retain exact Human Gates; one deployment keeps one HMAC key for its full evidence lifetime and Kernel verifies through Custodian without key disclosure; and Owner authorization/revocation uses a signed, conditionally-created, version/deletion/fork-checked chain bound into RESTORE records. Frozen C01–C13 were reviewed with no remaining architecture contradiction. Verification passed `251 passed`; worktree stayed clean. This PASS accepts only the architecture at the exact SHA. It does not accept C09/OI-0002, grant capabilities, approve IAM/key/retention changes or replace final implementation acceptance.
