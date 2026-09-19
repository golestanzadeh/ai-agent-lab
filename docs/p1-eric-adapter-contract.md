# Phase P1 package 2 — Versioned ERiC Adapter Contract

Status: **VERSION 2 MIGRATION IMPLEMENTED / LOCAL NON-PRODUCTION ONLY**

## Authorized boundary

The Project Owner authorized package 2 only to design and implement a non-production, versioned ERiC adapter boundary. Registration, account creation, manufacturer ID, protected package retrieval, credentials, certificates, signing, network access, live connectivity, real taxpayer data, ELSTER/Finanzamt contact, and transmission are not authorized.

## Design

`src/agent_lab/eric_adapter_contract.py` defines adapter contract version `2`, bound exactly to the package-1 synthetic envelope schema, ERiC `44.3.6.0`, procedure `UFA10`, and tax year `2024`.

The contract records the three required official categories: ERiC interface specification, E10/UFA10 2024 XML schema, and E10/UFA10 2024 plausibility rules. Their packages were recovered locally and hash-verified, but mapping and executable plausibility validation remain unimplemented and blocked.

`design_eric_adapter` produces an immutable local plan that binds the contract identity to the synthetic envelope identity. `BOUNDARY_READY_MAPPING_BLOCKED` means only that the inert software boundary is well-formed while official mapping remains blocked. The plan lists unimplemented E10/2024 mapping and plausibility validation as blockers and keeps mapping, validation, signing, credential access, networking, and transmission disabled.

The required-material list and complete denied-capability policy are fields inside the hash-bound contract. Neither policy may change under contract version `2`. The design-plan constructor independently rejects any attempt to enable an execution flag, add a network call, remove a blocker, or weaken the denied-capability policy.

## Acceptance criteria

- Only adapter contract version `2` and environment `NON_PRODUCTION_DESIGN` are accepted.
- The exact ERiC version, procedure, tax year, and envelope schema are fail-closed bindings.
- Official-material status cannot be advanced by caller input or this package.
- Required-material and denied-capability policy cannot drift without a contract-version change.
- The three missing official material categories are explicit and no XML element, ERiC function, endpoint, response, or plausibility rule is guessed.
- Only a package-1 `SyntheticSubmissionEnvelope` may be bound.
- A boundary-ready result never permits mapping, validation, signing, credential access, networking, or transmission.
- Direct construction or replacement of a plan cannot enable a forbidden capability or insert a network call.

## Verification evidence

- Initial implementation commit: `a024ff5c608700ff7650c4b9c02c643fa72884fd`.
- Amended implementation commit: `3fd1e4d586cc97411acaa563e6d5712e31c5dacd`.
- Relevant package-1/package-2 suite after amendment: `45 passed`.
- Full repository regression after amendment: `427 passed, 1 skipped`.
- Python compile check: passed.
- Version-2 migration targeted suite: `123 passed`.
- Full repository regression: `561 passed, 1 skipped, 3 failed`; all three failures are the pre-existing O4 pilot validator's stale requirement for the removed `ROADMAP.md` heading `## Registered Phase O4 pilot artifacts`, not an ERiC migration failure.
- The first targeted invocation omitted the repository `src` import path and stopped during test collection with two import errors. The command was corrected to use the documented `PYTHONPATH=src` environment and passed; no test failure was hidden.

## Next Human Gate

On 2026-09-14, the Project Owner explicitly accepted amended package 2 and exact implementation commit `3fd1e4d586cc97411acaa563e6d5712e31c5dacd`.

Any further Phase P1 package, developer access, official protected-material retrieval, verified material digest registration, ERiC FFI/XML mapping, credential/certificate use, live connection, or transmission requires separate exact authority.
