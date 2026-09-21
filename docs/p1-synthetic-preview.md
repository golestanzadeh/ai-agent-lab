# Phase P1 continuous package — Synthetic Human-readable Preview

Status: **COMPLETE / VERIFIED UNDER CONTINUOUS NON-PRODUCTION AUTHORITY**

## Boundary

The preview is local, immutable, synthetic, and incapable of credential access, networking, signing, or transmission. It is not an official tax form. Its embedded material status is a historical upstream package-2 value and is not the canonical current E10 readiness result.

## Design

`SyntheticElsterPreview` binds the exact package-1 envelope identity, accepted adapter-contract identity, completed synthetic material-process decision, ERiC 44.3.6.0 / UFA10 / tax-year 2024 route, synthetic summary values, official-material status, and a non-removable warning into one deterministic artifact identity.

The rendered text uses a fixed field order. Free-text purpose content is JSON-quoted so line breaks cannot inject an unlabelled field. Any payload or binding mutation changes the preview identity.

## Acceptance criteria

- Every synthetic identity, route value, summary value, and upstream artifact reference is visible.
- Rendering is deterministic and purpose text cannot inject preview structure.
- The preview cannot be created from an incomplete or differently bound material-process decision.
- The immutable preview preserves upstream status `RECOVERED_LOCAL_MAPPING_UNVERIFIED`; current local mapping profile v4, exact official-XSD validation, and the seventeen-rule local plausibility subset are recorded separately and do not retroactively alter this artifact.
- Direct construction or replacement cannot weaken the disclaimer or enable credentials, networking, or transmission.
- No real data, protected material, credential, connection, or external transfer is used.

## Verification evidence

- Implementation commit: `8237882d29c2d7171f776fe684e2f0d1b609d476`.
- Relevant P1 suite: `77 passed`.
- Full repository regression: `459 passed, 1 skipped`.
- Python compile check: passed.
- No package-level Human Gate applies under the active revocable continuous authority.

## Current relationship to the E10 readiness artifact

This preview predates the separately versioned local E10 pipeline. Consumers must use the current readiness artifact for mapping/XSD/plausibility claims and must not infer current readiness from the preview's historical status field. Official ERiC-engine execution, credentials, networking, signing, and transmission remain blocked.
