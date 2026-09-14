# Phase P1 — Controlled ELSTER/Finanzamt Path

Status: **PACKAGE 1 HUMAN-ACCEPTED / COMPLETE**

## Authorized boundary

The Project Owner authorized Phase P1 only for non-production design and implementation with synthetic data. No real taxpayer data, developer registration, account, manufacturer ID, ERiC package download, credential, certificate, signing, network connection, ELSTER/Finanzamt contact, or external transfer is authorized.

## Official route evidence

ELSTER's official developer page identifies ERiC as the integration route for third-party tax software. ERiC is a C library with an interface specification; it plausibility-checks tax data, sends it encrypted to tax-administration acceptance servers, and can produce a PDF after a successful server response:

- <https://www.elster.de/eportal/infoseite/entwickler?locale=en_US>

The official ELSTER availability schedule dated 2026-07-10 records unlimited income tax (`UFA 10`) for tax year 2024 as available in ERiC version `41.2`:

- <https://e4k-portal.een.elster.de/eportal/attachments/bereitstellungstermine/Historie_Bereitstellungstermine.pdf>

Official help states that XML schemas, schema documentation, and annual plausibility documentation are distributed in the ERiC documentation package. Those exact materials are not present in this repository:

- <https://www.elster.de/eportal/helpGlobal?themaGlobal=ustva_upload>

Therefore package 1 records the route identity but deliberately implements no guessed XML element, form-field placement, plausibility rule, FFI call, or endpoint.

## Package 1 architecture

`src/agent_lab/elster_dry_run.py` contains only deterministic local values and pure evaluation:

1. `SyntheticSubmissionEnvelope` accepts only `SYNTH-` case/run identities, the `SYNTHETIC` classification, tax year 2024, procedure `UFA10`, and ERiC `41.2`.
2. The envelope receives a canonical SHA-256 artifact identity. Any payload or binding change produces a different identity.
3. `ContentReleaseApproval` models Constitution Article 1 Stage One and binds exact artifact, version, case/run, classification, purpose, issuance, expiry, status, and synthetic Human identity.
4. `DestinationTransmissionApproval` is a separate later event. It additionally binds Stage One, exact synthetic destination/channel, retry policy, issuance, and expiry.
5. `evaluate_synthetic_dry_run` returns `HUMAN_REQUIRED` when a stage is absent and `BLOCKED` for mismatch, order, status, or expiry failures.
6. Even when both synthetic approvals validate, the result is only `DRY_RUN_READY`; blockers are empty but explicit non-production limitations remain, `transmission_permitted` is false, `network_calls` is empty, credential access is false, and no transmitter exists.

## Acceptance criteria

- Exact supported route is enforced and all alternatives fail closed.
- Non-synthetic case/run/classification input is rejected.
- Artifact identity is deterministic and mutation-sensitive.
- Content and destination approvals cannot be collapsed or reordered.
- Both approvals bind the same artifact, case/run, purpose, and validity window.
- Missing, expired, revoked, future, or mismatched approvals do not pass.
- Successful dry-run evaluation cannot perform or authorize a network call, credential access, signing, or transmission.
- Tests use synthetic local values only.

## Deliberate limitations

Package 1 is not an ELSTER client, tax calculator, official form mapper, XML generator, signer, or submission simulator. Its numeric synthetic payload is only an identity/binding fixture and makes no tax claim.

The exact official schema, plausibility rules, ERiC API, supported platform package, certificate modes, test environment, response codes, PDF behavior, receipt identity, retry semantics, and licensing/developer obligations remain unknown until the official developer materials are separately obtained and durably reviewed.

## Verification evidence

- Implementation commit: `aaf5bec86e103480ef5d36cedca29cfbfb607862`.
- Targeted package-1 suite: `23 passed`.
- Full repository regression: `405 passed, 1 skipped`.
- Python compile check: passed.
- The first full-suite invocation executed all cases but failed during cleanup of pytest's shared Windows temporary link. A rerun with a unique isolated temporary base completed successfully. This was an environment cleanup failure, not a test-case failure, and it is preserved here rather than silently omitted.

## Human acceptance and next gate

On 2026-09-14, the Project Owner explicitly accepted package 1 and exact implementation commit `aaf5bec86e103480ef5d36cedca29cfbfb607862`. Package 1 is therefore `P1_PACKAGE_1_ACCEPTED / PACKAGE COMPLETE`.

This acceptance does not begin or authorize package 2. Any package-2 work must remain non-production and may only proceed after separate exact authority. Registration, account creation, manufacturer ID, package download, credential/certificate handling, live connectivity, or any real transmission likewise requires separate exact authority.
