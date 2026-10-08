# CASE-001 / 2024 — DR-04 acceptance

Status: **PART1 COMPLETE / DR-04 OPEN**

DR-04 contract version 2 adds the Owner-approved CASE-001/2024 successor on top of the accepted DR-02 result. It preserves the source invoice, exact eligible bases, the historical result, the approved successor result and both document/payment provenance chains independently. Every supplied lineage reference remains canonical SHA-256 input to the deterministic artifact identity. Duplicate `HA_35a`, cross-case use, a non-transmitting-boundary change, malformed amounts, labor above invoice, a superseded contract version, or a credit inconsistent with the whole-euro declaration bases fails closed.

The protected 2024 annual documentation establishes the exact paths and whole-euro field types. Household services use `E0107206`, `E0107207` and `E0107208`; craftsman work uses `E0111217`, `E0170601`, `E0111214` and `E0111215`. Exact accepted source bases remain EUR 69.13 and EUR 90.00. Their official `GeldBetragOhneCent` declaration representations remain separately recorded as EUR 70 and EUR 90. Version 2 calculates the approved section-35a credit of EUR 32.00 from those declaration values and records the approved successor refund of EUR 134.00. The historical EUR 31.83 credit and EUR 133.83 refund remain explicit, immutable predecessor values rather than being silently overwritten.

Local deterministic checks cover paired description/amount fields, required sums, sum-to-item consistency and labor not exceeding invoice, corresponding to reviewed official rules `101100088`, `101100089`, `101100090`, `101100091`, `10817`, `12204`, `101100079`, `101170002`, `10821` and `101170007`. The composed declaration passes the exact hash-pinned E10/2024 XSD.

Focused and bounded regression verification: `26 passed, 5 skipped`; the skips are the expected protected-source tests in modules not supplied with their separate fixtures. The DR-04 exact official-XSD path executed and passed. The artifact remains a `NON_TRANSMITTING_PREVIEW`; official ERiC was not executed and no ELSTER/Finanzamt transmission, signing, certificate use, Drive mutation or production filing occurred.

Part 1 resolves only the Owner-approved result-version defect. Overall DR-04 remains open: the ten rule identifiers are recorded but no evaluator executes them, exact lineage is not yet pinned against the accepted artifacts, and full regression plus Independent Acceptance are deferred. DR-05 remains blocked.
