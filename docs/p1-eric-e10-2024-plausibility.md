# Local E10/2024 plausibility subset

The protected ERiC `44.3.6.0` annual documentation contains the official `N - Regeln` table. Review of the rules directly implicated by the bounded mapping identified six deterministic presence rules: `241`, `310010`, `310070`, `100200001`, `100200112`, and `121355`.

Every result binds those codes to the exact reviewed protected source filename `Jahresdokumentation_E10_2024.ods` and SHA-256 `6379af3c83b8d8ea1f5b8e683d2cfc401cb1506a6018cd44d68452f8b67dacd5`. The protected file itself remains outside Git; changing either provenance value invalidates the result.

The local evaluator implements only those six reviewed conditions. They require a tax class for tax-class 1–5 wages, explicit wage-tax values when wages are present for either wage group, an aggregate for itemized other employment expenses, itemization when that aggregate is present, and paired description/amount values for each supported other-expense item.

Rule `100200112` exposed a concrete gap in the earlier mapping: `E0204803` cannot stand alone. The mapping now requires an explicit supported official expense category and emits `E0205405`/`E0205406` itemization before the matching `E0204803` sum. The currently supported synthetic category is `Schreibmaterial`; no broader semantic inference is made.

A local subset pass is not equivalent to official ERiC plausibility acceptance. All unimplemented official rules remain outside this evaluator, and ERiC FFI, the official engine, credentials/certificates, Manufacturer-ID, signing, networking, and transmission remain denied.
