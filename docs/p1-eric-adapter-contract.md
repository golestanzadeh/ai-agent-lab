# Phase P1 package 2 — Versioned ERiC Adapter Contract

Status: **VERSION 2 MIGRATION IMPLEMENTED / LOCAL NON-PRODUCTION ONLY**

## Authorized boundary

The Project Owner authorized package 2 only to design and implement a non-production, versioned ERiC adapter boundary. Registration, account creation, manufacturer ID, protected package retrieval, credentials, certificates, signing, network access, live connectivity, real taxpayer data, ELSTER/Finanzamt contact, and transmission are not authorized.

## Design

`src/agent_lab/eric_adapter_contract.py` defines adapter contract version `2`, bound exactly to the package-1 synthetic envelope schema, ERiC `44.3.6.0`, procedure `UFA10`, and tax year `2024`.

The contract records the three required official categories: ERiC interface specification, E10/UFA10 2024 XML schema, and E10/UFA10 2024 plausibility rules. Their packages were recovered locally and hash-verified. This package-2 contract deliberately preserves its historical `RECOVERED_LOCAL_MAPPING_UNVERIFIED` state and exposes no mapping or validation capability; later bounded components now provide mapping profile v10, exact official-XSD validation, and a thirty-nine-rule local plausibility subset without changing this inert adapter boundary.

`design_eric_adapter` produces an immutable local plan that binds the contract identity to the synthetic envelope identity. `BOUNDARY_READY_MAPPING_BLOCKED` means only that this package-2 adapter object is well-formed and cannot itself map or validate. Its historical blocker names remain part of the version-2 artifact identity. Current local mapping/XSD/plausibility evidence is represented by the separately versioned E10 pipeline and readiness artifact; official ERiC-engine execution remains blocked. The adapter plan keeps mapping, validation, signing, credential access, networking, and transmission disabled.

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
- Initial full repository regression: `561 passed, 1 skipped, 3 failed`; all three failures were the pre-existing O4 pilot validator's stale requirement for the removed `ROADMAP.md` heading `## Registered Phase O4 pilot artifacts`, not an ERiC migration failure. D-073 reconciled that marker; the subsequent full regression returned `564 passed, 1 skipped`.
- The first targeted invocation omitted the repository `src` import path and stopped during test collection with two import errors. The command was corrected to use the documented `PYTHONPATH=src` environment and passed; no test failure was hidden.

## Current relationship to later E10 work

The package-2 artifact is historical, immutable input to later local work; its status text is not the canonical current readiness claim. See `p1-eric-e10-2024-mapping.md`, `p1-eric-e10-2024-plausibility.md`, and `p1-eric-e10-2024-readiness.md` for the current bounded evidence. No official ERiC engine, credential, network, or transmission capability is enabled.

## Historical Human Gate

On 2026-09-14, the Project Owner explicitly accepted amended package 2 and exact implementation commit `3fd1e4d586cc97411acaa563e6d5712e31c5dacd`.

At this checkpoint, further Phase P1 work required separate exact authority. Later decisions supplied bounded local synthetic authority and protected-material review authority; credential/certificate use, live connection, official ERiC-engine execution, and transmission remain separate Human Gates.
