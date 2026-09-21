# Phase P1 package 3 — ERiC Material Registration and Verification Process

Status: **HUMAN-ACCEPTED / PACKAGE COMPLETE**

## Authorized boundary

Package 3 designs and implements only a synthetic, local process for registering and independently reviewing the three material categories required by the accepted adapter contract. It performs no registration, account creation, manufacturer-ID request, protected download, credential/certificate access, network connection, ELSTER/Finanzamt contact, or transmission.

## Process

1. Create one immutable synthetic record for each required material category: ERiC interface specification, UFA10 2024 XML schema, and UFA10 2024 plausibility rules.
2. Bind each record to the exact ERiC 44.3.6.0 / UFA10 / tax-year 2024 route, a canonical SHA-256 reference, a `synthetic://` locator, and a synthetic registrant.
3. Require one later, independently identified synthetic reviewer to approve each exact record identity.
4. Fail closed on missing, duplicate, rejected, reordered, self-reviewed, mismatched, or mutated evidence.
5. Return `SYNTHETIC_PROCESS_READY_OFFICIAL_STATUS_BLOCKED` only when the synthetic workflow is complete. Following governed retrieval, the immutable package-3 status is `RECOVERED_LOCAL_MAPPING_UNVERIFIED`; this process artifact itself grants no mapping or execution capability. Later mapping profile v8, official-XSD validation, and the thirty-five-rule local plausibility subset are separate downstream artifacts and do not rewrite this historical identity.

## Acceptance criteria

- Exactly one record and one independent review exist for every contract-required material category.
- All identities, timestamps, route metadata, and review bindings validate deterministically.
- Non-synthetic identifiers, locators, or classifications are rejected.
- Record mutation invalidates the bound review.
- A result cannot be forged to enable protected retrieval, official-status advancement, credential access, or a network call.
- No real material content, private tax data, secret, credential, endpoint call, or external transfer is used.

## Next boundary

On 2026-09-14, the Project Owner explicitly accepted package 3 and implementation commit `2d6efd25e85ba9874ccbdad695b5b24c0c205887`, and activated revocable continuous authority for remaining local synthetic/non-production Phase P1 work. This authority cannot include registration, protected retrieval, credentials, real data, external connectivity, architecture/governance change, production, `main`, or transmission.

The canonical current mapping/XSD/plausibility state is recorded by the separately versioned E10 readiness pipeline. Official ERiC-engine execution, credentials, networking, signing, and transmission remain blocked.

## Verification evidence

- Implementation commit: `2d6efd25e85ba9874ccbdad695b5b24c0c205887`.
- Relevant package-1/package-2/package-3 suite: `66 passed`.
- Full repository regression: `448 passed, 1 skipped`.
- Python compile check: passed.
- The first targeted run exposed a package-local timestamp canonicalization defect (`13 failed, 53 passed`). Converting identity timestamps deterministically to ISO format fixed it; the successful rerun is the accepted technical evidence.
