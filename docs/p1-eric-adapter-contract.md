# Phase P1 package 2 — Versioned ERiC Adapter Contract

Status: **TECHNICALLY VERIFIED / HUMAN ACCEPTANCE REQUIRED**

## Authorized boundary

The Project Owner authorized package 2 only to design and implement a non-production, versioned ERiC adapter boundary. Registration, account creation, manufacturer ID, protected package retrieval, credentials, certificates, signing, network access, live connectivity, real taxpayer data, ELSTER/Finanzamt contact, and transmission are not authorized.

## Design

`src/agent_lab/eric_adapter_contract.py` defines adapter contract version `1`, bound exactly to the package-1 synthetic envelope schema, ERiC `41.2`, procedure `UFA10`, and tax year `2024`.

The contract records three official inputs that are still not recovered: the ERiC interface specification, the UFA10 2024 XML schema, and the UFA10 2024 plausibility rules. Package 2 cannot advance their status or infer their contents.

`design_eric_adapter` produces an immutable local plan that binds the contract identity to the synthetic envelope identity. `BOUNDARY_READY` means only that the inert software boundary is well-formed. The plan still lists the three missing official materials as blockers and keeps mapping, validation, signing, credential access, networking, and transmission disabled.

## Acceptance criteria

- Only adapter contract version `1` and environment `NON_PRODUCTION_DESIGN` are accepted.
- The exact ERiC version, procedure, tax year, and envelope schema are fail-closed bindings.
- Official-material status cannot be advanced by caller input or this package.
- The three missing official material categories are explicit and no XML element, ERiC function, endpoint, response, or plausibility rule is guessed.
- Only a package-1 `SyntheticSubmissionEnvelope` may be bound.
- A boundary-ready result never permits mapping, validation, signing, credential access, networking, or transmission.

## Verification evidence

- Implementation commit: `a024ff5c608700ff7650c4b9c02c643fa72884fd`.
- Relevant package-1/package-2 suite: `36 passed`.
- Full repository regression: `418 passed, 1 skipped`.
- Python compile check: passed.
- The first targeted invocation omitted the repository `src` import path and stopped during test collection with two import errors. The command was corrected to use the documented `PYTHONPATH=src` environment and passed; no test failure was hidden.

## Next Human Gate

After technical verification, the Project Owner must accept package 2 or request exact amendments. Obtaining developer access or official protected materials, recording verified material digests, implementing an ERiC FFI/XML mapping, using credentials/certificates, making a live connection, or transmitting anything requires separate exact authority.
