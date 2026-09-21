# Phase P1 — Local E10/2024 mapping profile

Status: **IMPLEMENTED / LOCAL SYNTHETIC NON-PRODUCTION ONLY**

## Authority and evidence

The Project Owner authorized this package on 2026-09-20. The implementation was derived locally from the hash-verified ERiC `44.3.6.0` documentation package recorded in D-071. The reviewed official material included the E10/2024 example, annual field documentation, and E10/2024 XSD set. Protected source files remain outside Git.

## Supported subset

`src/agent_lab/eric_e10_2024_mapping.py` maps one explicitly synthetic employment summary to an E10/2024 `N` fragment:

- tax classes 1–5: `E0200002`, `E0200201`, and `E0200301` under `N/ArbL/LStB_1_5_Sum`;
- tax class 6: `E0200203` and `E0200303` under `N/ArbL/LStB_6_Sum`;
- explicitly supplied solidarity surcharge, employee church tax, and spouse/life-partner church tax: `E0200401`/`E0200501`/`E0200601` for tax classes 1–5, or `E0200403`/`E0200503`/`E0200603` for tax class 6; omitted values remain absent and are never inferred;
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
Both supported wage groups with explicit optional solidarity surcharge and church tax also passed local validation against the exact hash-pinned official `E10-2024.xsd`; protected schema files remained outside Git.

Mapping profile version 3 adds only the source-evidenced optional spouse/life-partner church-tax fields `E0200601` and `E0200603`. Both wage groups, including all three optional wage-tax amounts, pass the exact official XSD locally. No relationship status, denomination, or amount is inferred; the field is emitted only from an explicit synthetic input.

## Professional-association subset

Mapping profile version 4 implements one explicitly synthetic professional-association contribution under `N/Wk/Berufsverb`: description `E0204001`, whole-euro item amount `E0204003`, and matching whole-euro sum `E0204002`. It requires description and amount together, derives the single-item sum exactly, rejects negative or out-of-range synthetic input, and omits the entire context when no contribution is supplied.

## Work-equipment subset

Mapping profile version 5 implements one explicitly synthetic work-equipment expense under `N/Wk/Arbeitsmittel`: closed supported type `Computer` in `E0204401`, whole-euro item amount `E0204402`, and matching derived sum `E0204403`. Type and amount are required together; the amount is non-negative and limited to the official twelve-digit boundary; omission removes the complete context. No free-form or real-case meaning is inferred. The generated declaration passes the exact hash-pinned official E10/2024 XSD locally.

## Home-office workroom subset

Mapping profile version 6 implements one explicitly synthetic home-office workroom expense under `N/Wk/Arb_Zim`. The closed supported official type `Ausstattung (ohne Büromöbel und Computer)` maps to `E0204503`, its whole-euro amount maps to `E0204505`, and the exact derived sum maps to `E0204504`. Type and amount are paired, non-negative, limited to the official twelve-digit boundary, and omitted as a complete context when absent. The combined profile-v6 declaration passes the exact hash-pinned official E10/2024 XSD locally.

## Training-expense subset

Mapping profile version 7 implements one explicitly synthetic training expense under `N/Wk/Fortb`. The closed supported official type `Kursgebühren` maps to `E0204804`, its whole-euro amount maps to `E0204808`, and the exact derived sum maps to `E0204812`. Type and amount are paired, non-negative, limited to the official twelve-digit boundary, and omitted as a complete context when absent. The combined profile-v7 declaration passes the exact hash-pinned official E10/2024 XSD locally.

## Home-office day categories

Mapping profile version 8 adds explicit positive day counts for both official home-office categories: `E0204507` when another workplace is available and `E0206206` when no other workplace is permanently available. Each optional count is limited to `1..366`; omission remains omission. The combined profile-v8 declaration passes the exact hash-pinned official E10/2024 XSD locally.
