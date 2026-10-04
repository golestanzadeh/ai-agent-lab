# CASE-001 / 2024 — DR-04 acceptance

Status: **INDEPENDENT_ACCEPTANCE_FAIL**

DR-04 adds one versioned, CASE-001/2024-scoped `HA_35a` composer on top of the accepted DR-02 result. It preserves the source invoice, exact eligible bases, exact accepted credit and both document/payment provenance chains independently. Every lineage reference is canonical SHA-256 input to the deterministic artifact identity. Duplicate `HA_35a`, cross-case use, a non-transmitting-boundary change, malformed amounts, labor above invoice, or a credit inconsistent with the exact bases fails closed.

The protected 2024 annual documentation establishes the exact paths and whole-euro field types. Household services use `E0107206`, `E0107207` and `E0107208`; craftsman work uses `E0111217`, `E0170601`, `E0111214` and `E0111215`. Exact accepted bases remain EUR 69.13 and EUR 90.00. Their official `GeldBetragOhneCent` declaration representations are EUR 70 and EUR 90; those representations are recorded separately and never replace the frozen cent-denominated calculation. The accepted section-35a credit remains EUR 31.83 and the frozen refund remains EUR 133.83.

Local deterministic checks cover paired description/amount fields, required sums, sum-to-item consistency and labor not exceeding invoice, corresponding to reviewed official rules `101100088`, `101100089`, `101100090`, `101100091`, `10817`, `12204`, `101100079`, `101170002`, `10821` and `101170007`. The composed declaration passes the exact hash-pinned E10/2024 XSD.

Focused verification: `5 passed`. The artifact remains a `NON_TRANSMITTING_PREVIEW`; official ERiC was not executed and no ELSTER/Finanzamt transmission, signing, certificate use, Drive mutation or production filing occurred.

Independent Acceptance is `FAIL`: the rule identifiers are recorded but no evaluator executes them, exact lineage is not pinned against the accepted artifacts, and whole-euro declaration bases imply a EUR 32.00 credit rather than the frozen EUR 31.83. The implementation is a recoverable checkpoint, not an accepted package.
