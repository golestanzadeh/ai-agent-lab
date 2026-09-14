# Phase P1 continuous package — Synthetic Human-readable Preview

Status: **IMPLEMENTED UNDER CONTINUOUS NON-PRODUCTION AUTHORITY**

## Boundary

The preview is local, immutable, synthetic, and incapable of credential access, networking, signing, or transmission. It is not an official tax form and does not claim that official ERiC mapping or plausibility validation has occurred.

## Design

`SyntheticElsterPreview` binds the exact package-1 envelope identity, accepted adapter-contract identity, completed synthetic material-process decision, ERiC 41.2 / UFA10 / tax-year 2024 route, synthetic summary values, official-material status, and a non-removable warning into one deterministic artifact identity.

The rendered text uses a fixed field order. Free-text purpose content is JSON-quoted so line breaks cannot inject an unlabelled field. Any payload or binding mutation changes the preview identity.

## Acceptance criteria

- Every synthetic identity, route value, summary value, and upstream artifact reference is visible.
- Rendering is deterministic and purpose text cannot inject preview structure.
- The preview cannot be created from an incomplete or differently bound material-process decision.
- Official-material status remains `NOT_RECOVERED` and official mapping remains blocked.
- Direct construction or replacement cannot weaken the disclaimer or enable credentials, networking, or transmission.
- No real data, protected material, credential, connection, or external transfer is used.
