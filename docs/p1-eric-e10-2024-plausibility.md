# Local E10/2024 plausibility subset

The protected ERiC `44.3.6.0` annual documentation contains the official `N - Regeln` table. Plausibility profile version 4 covers seventeen deterministic rules directly implicated by the bounded mapping: `241`, `310010`, `310030`, `310050`, `310060`, `310070`, `310090`, `310110`, `310120`, `100200001`, `100200112`, `121355`, `100200099`, `100200109`, `201010`, `330121`, and `100200108`.

Every result binds those codes to the exact reviewed protected source filename `Jahresdokumentation_E10_2024.ods` and SHA-256 `6379af3c83b8d8ea1f5b8e683d2cfc401cb1506a6018cd44d68452f8b67dacd5`. The protected file itself remains outside Git; changing either provenance value invalidates the result.

The local evaluator implements only those seventeen reviewed conditions. It includes the existing wage and expense checks plus the bounded professional-association integrity rules; no broader semantics are inferred.

Rule `100200112` exposed a concrete gap in the earlier mapping: `E0204803` cannot stand alone. The mapping now requires an explicit supported official expense category and emits `E0205405`/`E0205406` itemization before the matching `E0204803` sum. The currently supported synthetic category is `Schreibmaterial`; no broader semantic inference is made.

A local subset pass is not equivalent to official ERiC plausibility acceptance. All unimplemented official rules remain outside this evaluator, and ERiC FFI, the official engine, credentials/certificates, Manufacturer-ID, signing, networking, and transmission remain denied.

The implemented professional-association subset comprises official rules `100200099` (negative item sum forbidden), `100200109` (sum requires itemization), `201010` (sum must equal the non-negative item total), `330121` (itemization requires sum), and `100200108` (description and amount must occur together). It remains single-item and synthetic.
