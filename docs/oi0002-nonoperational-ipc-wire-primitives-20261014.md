# OI-0002 non-operational IPC wire primitives — 2026-10-14

Status: **DEVELOPMENT PROFILE PASS / NON-OPERATIONAL / NO C03-C12 ACCEPTANCE CREDIT**

Baseline: `b3731096b4c52774b3d3f93aa8bddf2479537f42`

## Scope

Following the Owner-approved separation of ordinary development from operational anti-rollback acceptance, this bounded package implements only portable canonical-message and framing primitives. It uses the Python standard library and performs no transport I/O, Named Pipe operation, peer authentication, permission decision, dispatch, persistence, transaction, mutation, audit finality, backup or restore.

The module cannot activate protected Identity state and is not an in-process operational adapter. It does not satisfy or earn acceptance credit for C03-C09, C11 or C12.

## Implemented behavior

- strict canonical UTF-8 JSON objects using UTF-16 key ordering;
- boolean, string, array and object values only; number and null denial;
- Unicode scalar validation with surrogate and noncharacter denial;
- maximum nesting depth 12;
- four-byte unsigned little-endian payload length;
- exact one-frame decoding with payload range `1..65,532`;
- BOM, duplicate-key, alternate formatting/order, early EOF and trailing-byte denial;
- canonical SHA-256 identity over exact bytes;
- no Unicode normalization, preserving composed/decomposed distinctions.

## Verification

- focused wire tests: `21 passed`, exit 0;
- relevant wire/Kernel/continuity/Identity/custody regression: `106 passed`, exit 0;
- exact ADR golden vectors pass;
- exact 65,532-byte payload round-trips in a 65,536-byte frame; the next byte is rejected;
- `-0`, exponent, `NaN`, `Infinity`, null and ordinary numeric values are rejected;
- independent read-only review: PASS, no required finding.

## Preserved boundary

C09 remains OPEN / NOT ACCEPTED. No replacement freshness authority is approved. The TPM-bound proposal remains an unaccepted operational profile. Protected mutation, rollback-resistant finality, operational restore, OI-0002 closure, OI-0003 and ELSTER remain blocked behind their existing architecture, security and Human Gates.

## Exact next development package

A transport-neutral closed envelope/schema validator may be developed next under fresh Limit Guard admission, provided it remains non-operational, accepts no caller-supplied authority as trust, exposes no dispatch or protected mutation, and is independently reviewed. Actual Windows peer authentication or protected service activation requires the separately accepted operational architecture.
