# Local E10/2024 plausibility subset

The protected ERiC `44.3.6.0` annual documentation contains the official `N - Regeln` table. Plausibility profile version 10 covers thirty-six deterministic rules directly implicated by the bounded mapping: `241`, `310010`, `310030`, `310050`, `310060`, `310070`, `310090`, `310110`, `310120`, `100200001`, `100200112`, `121355`, `100200099`, `100200109`, `201010`, `330121`, `100200108`, `330122`, `100200100`, `100200110`, `122050`, `121410`, `100200101`, `100200111`, `122056`, `330123`, `121432`, `100200003`, `100200009`, `100200102`, `100200007`, `121352`, `100200127`, `100200103`, `100200002`, and `121361`.

Every result binds those codes to the exact reviewed protected source filename `Jahresdokumentation_E10_2024.ods` and SHA-256 `6379af3c83b8d8ea1f5b8e683d2cfc401cb1506a6018cd44d68452f8b67dacd5`. The protected file itself remains outside Git; changing either provenance value invalidates the result.

The local evaluator implements only those thirty-six reviewed conditions. It includes the existing wage and expense checks plus the bounded professional-association, work-equipment, home-office workroom, training, home-office-day, and other-expense integrity rules; no broader semantics are inferred.

Rule `100200112` exposed a concrete gap in the earlier mapping: `E0204803` cannot stand alone. The mapping now requires an explicit supported official expense category and emits `E0205405`/`E0205406` itemization before the matching `E0204803` sum. The currently supported synthetic category is `Schreibmaterial`; no broader semantic inference is made.

A local subset pass is not equivalent to official ERiC plausibility acceptance. All unimplemented official rules remain outside this evaluator, and ERiC FFI, the official engine, credentials/certificates, Manufacturer-ID, signing, networking, and transmission remain denied.

The implemented professional-association subset comprises official rules `100200099` (negative item sum forbidden), `100200109` (sum requires itemization), `201010` (sum must equal the non-negative item total), `330121` (itemization requires sum), and `100200108` (description and amount must occur together). It remains single-item and synthetic.

The implemented work-equipment subset comprises `330122` (item requires sum), `100200100` (negative item total forbidden), `100200110` (sum requires item), `122050` (sum comparison using `UngleichMitToleranz5`), and `121410` (type and amount together). The official ERiC 44.3.6.0 `Zusatzinformationen zur Plausibilitätsprüfung`, section 4.5, defines `UngleichMitToleranz5` as true exactly when `abs(v1 - v2) > 5`; differences of exactly `5` in either direction remain accepted. Boundary tests cover `-6`, `-5`, `5`, and `6`.

The implemented home-office workroom subset comprises `100200101` (negative item total forbidden), `100200111` (sum requires item), `122056` (the same authoritative absolute tolerance-of-five comparison), `330123` (item requires sum), and `121432` (type and amount together). It remains single-item, explicit, synthetic, and local.

The implemented training subset comprises `100200003` (any item data requires the sum), `100200009` (sum requires an item amount), `100200102` (negative item total forbidden), `100200007` (the same authoritative absolute tolerance-of-five comparison), and `121352` (type and amount together). It remains single-item, explicit, synthetic, and local.

Rule `100200127` rejects the two explicit home-office day categories only when both are present and their sum exceeds `366`. Boundary tests cover totals `366` and `367`; each individual field is independently restricted to the official positive `1..366` range.

The implemented other-expense completeness rules comprise `100200103` (the combined `E0205406`/`E0204802` item total cannot be negative) and `100200002` (the declared `E0204803` sum uses the same authoritative absolute tolerance-of-five comparison). Boundary tests cover differences `-6`, `-5`, `5`, and `6`; the existing mapping remains deliberately limited to the explicit synthetic `Schreibmaterial` category.

Rule `121361` requires ferry-or-flight description `E0204801` and amount `E0204802` together. Mapping profile v9 emits one paired synthetic item and includes its amount in the derived `E0204803` total; either missing field fails the local evaluator.
