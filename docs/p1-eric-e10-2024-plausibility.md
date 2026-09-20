# Local E10/2024 plausibility subset

The protected ERiC `44.3.6.0` annual documentation contains the official `N - Regeln` table. Review of the rules directly implicated by the bounded mapping identified five deterministic presence rules: `241`, `310010`, `310070`, `100200001`, and `100200112`.

The local evaluator implements only those five reviewed conditions. They require a tax class for tax-class 1–5 wages, explicit wage-tax values when wages are present for either wage group, an aggregate for itemized other employment expenses, and itemization when that aggregate is present.

Rule `100200112` exposed a concrete gap in the earlier mapping: `E0204803` cannot stand alone. The mapping now requires an explicit supported official expense category and emits `E0205405`/`E0205406` itemization before the matching `E0204803` sum. The currently supported synthetic category is `Schreibmaterial`; no broader semantic inference is made.

A local subset pass is not equivalent to official ERiC plausibility acceptance. All unimplemented official rules remain outside this evaluator, and ERiC FFI, the official engine, credentials/certificates, Manufacturer-ID, signing, networking, and transmission remain denied.
