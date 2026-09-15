# User-interface phase foundation

## Status and purpose

This document starts UI package 1 as a local, synthetic, non-production design
contract. It translates the project's stable case, identity, state, approval,
audit, and synthetic ELSTER boundaries into an ordinary user workflow without
selecting a UI framework or creating an external capability.

## Supported user journey

The first UI boundary must represent this ordered journey:

`Create/select person or entity -> Create/select case and tax year -> Add and inspect documents -> Process -> Review Agent findings and evidence gaps -> Review calculations and form preview -> Resolve Human Gates -> View submission state and receipt placeholder`

Before real transmission is separately authorized and implemented, the final step
must remain visibly unavailable and must never imply that a synthetic receipt is an
official receipt.

## Required screens and states

1. **Workspace selection** shows person/entity, case, and tax year and refuses to continue when the `case_id` cannot be resolved through the Case Registry.
2. **Document intake** shows only documents scoped to the resolved case, their processing state, provenance, and actionable failures.
3. **Agent review** shows processing progress, findings, evidence gaps, and the responsible review stage without exposing hidden prompts or secrets.
4. **Calculation and form preview** distinguishes recovered official mappings from synthetic or not-recovered content and carries the bound case/run/artifact identities.
5. **Human Gates** show the requested action, exact scope, expiry/revocation state, and consequences. No approval control may silently broaden its scope.
6. **Submission and receipt** remains disabled until the governed production path exists. Synthetic lifecycle outcomes and placeholders must be labelled as such.
7. **Operations and support** expose pause, resume, stop, recovery status, and privacy-safe diagnostics suitable for phone and Windows use.

## Cross-screen invariants

- Every tax-case read or write requires an explicit, registry-resolved `case_id`.
- Changing person/entity, case, or tax year clears stale document, calculation, preview, approval, and receipt views before loading the new scope.
- A component never searches, infers, or displays another case's data.
- Approval controls bind to the exact case, run, artifact, action, and destination; stale, expired, revoked, mismatched, or incomplete authority fails closed.
- Unknown official ERiC material, mapping, validation, credential, network, or receipt status is displayed as blocked or not recovered, never guessed.
- Errors are actionable but exclude secrets, credentials, private document contents, raw prompts, and cross-case identifiers.
- Phone and Windows layouts present the same gates and safety information; a narrow layout must not hide or weaken an approval boundary.

## Synthetic package-1 acceptance scenarios

1. A synthetic user can choose one registry-known case/year and see only its synthetic documents and state.
2. An unknown or mismatched `case_id` fails closed before any case data is shown.
3. Switching cases clears every prior case-derived view before the new scope loads.
4. Synthetic findings, evidence gaps, provenance, calculations, and preview status are distinguishable and traceable to one case/run.
5. A Human Gate displays exact binding, expiry, and revocation information and rejects stale or mismatched authority.
6. Submission is unavailable and a synthetic receipt placeholder cannot be mistaken for an official ELSTER receipt.
7. Pause, resume, stop, recovery, and privacy-safe diagnostic states are legible on representative phone and Windows widths.

## Explicit non-goals and next gate

This package does not select a framework, define production hosting, implement a
backend API, use real taxpayer data, access protected ERiC materials, authenticate,
connect externally, submit to ELSTER/Finanzamt, or act on `main`.

The next UI package may turn these scenarios into a synthetic interactive prototype
only after the Project Owner authorizes the required UI architecture/framework
choice, or after an already accepted project decision is durably identified that
removes that architecture gate.
