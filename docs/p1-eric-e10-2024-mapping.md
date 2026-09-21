# Phase P1 — Local E10/2024 mapping profile

Status: **IMPLEMENTED / LOCAL SYNTHETIC NON-PRODUCTION ONLY**

## Authority and evidence

The Project Owner authorized this package on 2026-09-20. The implementation was derived locally from the hash-verified ERiC `44.3.6.0` documentation package recorded in D-071. The reviewed official material included the E10/2024 example, annual field documentation, and E10/2024 XSD set. Protected source files remain outside Git.

## Supported subset

`src/agent_lab/eric_e10_2024_mapping.py` maps one explicitly synthetic employment summary to an E10/2024 `N` fragment:

- tax classes 1–5: `E0200002`, `E0200201`, and `E0200301` under `N/ArbL/LStB_1_5_Sum`;
- tax class 6: `E0200203` and `E0200303` under `N/ArbL/LStB_6_Sum`;
- explicitly supplied solidarity surcharge and church tax: `E0200401`/`E0200501` for tax classes 1–5, or `E0200403`/`E0200503` for tax class 6; omitted values remain absent and are never inferred;
- explicitly classified other employment expenses: one `E0205405`/`E0205406` item under `N/Wk/Weitere_Wk/Sonst` and the matching `E0204803` aggregate under `N/Wk/Weitere_Wk/Sum`.

The mapper preserves the official E10 namespace and version, whole-euro lexical form for gross wages and expense amounts, comma-decimal two-cent form for wage tax, the twelve-digit amount boundary, and separate Person A/Person B identity. Tax class, expense semantics, and an exact supported official expense category are mandatory because the older synthetic summary did not carry enough meaning to choose official fields safely. The current bounded category is `Schreibmaterial`.

## Fail-closed boundary

The output is a deterministic synthetic subset fragment, not a complete tax declaration. It does not contain transfer headers, recipient data, taxpayer identity, tax number, Manufacturer-ID, credentials, certificates, signatures, or transport data. It does not invoke ERiC or claim that the official ERiC plausibility engine accepted the fragment.

The immutable result retains two blockers: the full E10 declaration is not implemented, and the official ERiC plausibility engine has not been executed. ERiC FFI, full-declaration construction, signing, Manufacturer-ID access, credential/certificate access, networking, and transmission remain denied.

## Verification

The package tests cover tax classes 1–5 and 6, exact field identifiers and paths, lexical formatting, zero and upper-bound behavior, explicit semantics, deterministic identities, payload/person/tax-class mutations, XML/binding mismatch, and every denied capability.

- Mapping/relevant targeted suite: `70 passed`.
- Regression excluding the unrelated Windows-sensitive Google Drive provisioning file: `574 passed, 1 skipped`.
- Google Drive provisioning file under Python 3.11: `15 passed`.
- Two Python 3.14 Windows full-suite attempts produced order-varying failures only in the pre-existing Google Drive journal-replace tests; the mapping tests remained green.

## Later refinement

The declaration/XSD package subsequently resolved the mapper's standalone full-declaration blocker. Review of the official `N - Regeln` table then showed that rule `100200112` requires itemization when `E0204803` is present, which produced the source-evidenced `E0205405`/`E0205406` refinement above. Invoking the official ERiC plausibility engine, using a Manufacturer-ID or credential, processing real data, connecting externally, signing, or transmitting remains separately gated.

Mapping profile version 2 adds the optional wage-tax fields above from the reviewed official E10/2024 example and annual documentation. Targeted mapping, declaration, and local-plausibility verification passed (`67 passed`).
