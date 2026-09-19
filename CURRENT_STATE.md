# Current State

Last reconciled: **2026-09-19**

## Authoritative status

- CASE-001 / tax year 2024 analytical preparation is complete and Chief-approved by explicit Human recovery confirmation.
- No ELSTER submission or Finanzamt transmission has occurred.
- Unrecovered post-D-028 details remain `NOT_RECOVERED` and must not be fabricated.
- `PROJECT_CHECKPOINT.md` is the mandatory cross-session entry point.

## Completed foundations

- Deterministic case/person/tax-period identity, case isolation, scoped storage, evidence, audit, and durable approval boundaries.
- Controlled CASE-001 migration, document processing, six-role tax runtime, and Chief review.
- Agent Bridge, Local Sync, Windows Relay, and Orchestrator phases O1-O5; O5 was Human-accepted at `d64da2588b18f548c877aed6044f8884e7644cdc`.
- Phase P1 local synthetic ERiC boundary through package 7.
- Local four-role Agent Runtime Activation Layer at `cb41d13`; verification: `537 passed, 1 skipped`.
- Local FastAPI + Jinja/HTMX Persian UI through UI-8 at `c153014`; verification: `564 passed, 1 skipped` plus loopback visual/accessibility inspection.

## Live external status

- The ELSTER developer-access email was received and the Human authenticated privately on 2026-09-16.
- After explicit Human acceptance, the official ERiC Release 44 software-manufacturer license was accepted.
- Official `44.3.6.0` documentation and schema-documentation ZIPs were retrieved locally and hash-verified. They remain outside Git.
- The official page states ERiC 41 and 42 can no longer transmit after the 2026-04-27 minimum-version increase. The Project Owner authorized the local non-production migration, and adapter contract version `2` now binds ERiC `44.3.6.0`, procedure `UFA10`, tax year `2024`, and the E10/2024 material categories. Mapping and executable plausibility validation remain fail-closed.

## Active boundaries

- Development remains on `d021-agent-case-provisioning`; `main` is behind and protected.
- Current work is limited to authorized local, synthetic, non-production, architecture-compatible changes.
- Real data, credentials, protected access before Human login, provider/network activation, external transfer, production, ELSTER/Finanzamt action, merge/release, and destructive action remain Human Gates.
- Article 1 exact-content and exact-recipient/channel approvals are separate and both remain `NOT_APPROVED`.
- Plan-limit continuation must stop at its documented thresholds.
- Execution status is `TOKEN_PAUSED`: weekly remaining reached exactly `10%` on 2026-09-19. The weekly window resets at `2026-09-20 13:48:09 Europe/Berlin`; resume only after a fresh limit check confirms five-hour remaining at least `80%` and weekly remaining above `10%`.

## Remaining product work

1. Independently map the recovered official E10/2024 interface, XSD, annual field documentation, and plausibility material into a separately reviewed fail-closed implementation.
2. Validate that mapping against official examples and negative fixtures without enabling credentials, networking, signing, or transmission.
3. Extend the UI from synthetic display boundaries to governed real workflows only after each required authority.
4. Harden restart/recovery and provider-backed Agent operation before production activation.
5. Complete product acceptance, security review, release controls, and an explicitly authorized end-to-end submission with recoverable receipt.

## Exact next action

Remain `TOKEN_PAUSED` until the reset conditions are verified. Then independently implement and review the detailed E10/2024 mapping and local plausibility-validation package without credentials, Manufacturer-ID, real data, networking, signing, or transmission.

## Non-negotiable constraints

- Never reopen completed CASE-001 questions solely from superseded historical reports.
- Require `case_id` for every tax-case operation; never mix cases or tax years.
- Never store credentials, private Drive IDs, private tax documents, or protected material in GitHub.
- Never treat tests as Human acceptance or a displayed approval state as authority.
- Never submit, sign, transmit, release, merge protected `main`, or expand permissions without the applicable explicit Human Gate.
