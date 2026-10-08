# DR-04 rules extraction and contract review — 2026-10-08

Status: SOURCE_RULES_EXTRACTED / LOCAL_EVALUATOR_NOT_IMPLEMENTED / DR04_OPEN

Source: protected ELSTER E10/2024 annual ODS, SHA256 6379af3c83b8d8ea1f5b8e683d2cfc401cb1506a6018cd44d68452f8b67dacd5; sheet HA_35a - Regeln; rows 7–16. Read-only extraction through Python stdlib zipfile + ElementTree; all ten IDs and predicates confirmed.

| Row | ID | Exact official error predicate |
|---|---|---|
| 7 | 101100089 | FeldAngegeben(E0107208) Und KeinFeldAngegeben(Einz*/E0107206, Einz*/E0107207) |
| 8 | 101100090 | FeldAngegeben(E0107208) Und MindestensEinFeldAngegeben(Einz*/E0107207) Und [E0107208] UngleichMitToleranz2 Summe(Einz*/E0107207) |
| 9 | 101100091 | MindestensEinFeldAngegeben(Einz*/E0107207) und FeldNichtAngegeben(E0107208) |
| 10 | 101100088 | FelderNichtGemeinsamAngegeben(E0107206, E0107207) |
| 11 | 10817 | FeldAngegeben(E0111215) und KeinFeldAngegeben(Einz*/E0111217, Einz*/E0111214) |
| 12 | 12204 | FeldAngegeben(E0111215) Und MindestensEinFeldAngegeben(Einz*/E0111214) Und [E0111215] UngleichMitToleranz2 Summe(Einz*/E0111214) |
| 13 | 101100079 | MindestensEinFeldAngegeben(Einz*/E0111214) Und FeldNichtAngegeben(E0111215) |
| 14 | 101170002 | FeldAngegeben(E0170601) und FeldNichtAngegeben(E0111214) |
| 15 | 10821 | FelderNichtGemeinsamAngegeben(E0111217, E0111214) |
| 16 | 101170007 | AlleFelderAngegeben(E0170601, E0111214) und [E0111214] > [E0170601] |

All ten are severity Fehler. Exact rule-to-field mapping is in the source's field-reference column; all paths under /HA_35a/St_Erm. Current CASE-001/2024 XML fields: E0107206 description, E0107207=70, E0107208=70; E0111217 description, E0170601=90, E0111214=90, E0111215=90. Exact source bases 69.13 and 90.00 remain distinct; successor credit 32.00 and refund 134.00.

Stages: (1) rule source extraction PASS; operator semantic verification PARTIAL because UngleichMitToleranz2 precise tolerance not established; (2) field/structure mapping PASS; (3) accepted-values structural comparison PASS, not runtime execution; (4) evaluator audit PASS, ten IDs are only metadata and no evaluator runs; (5) interface design PROPOSED, not yet frozen.

Proposed evaluator contract: bind case/year/run, request identity, XML digest, protected source digest and rule source row, exact predicate, per-rule evidence, deterministic outcome. Treat predicates as error conditions; distinguish NO_VIOLATION, VIOLATION, NOT_APPLICABLE, BLOCKED; unknown tolerance/operator fails closed. No fabricated official ERiC success; preserve NON_TRANSMITTING_PREVIEW, no signing, network or transmission. Do not set local_plausibility_passed true without evaluated evidence.

Next: locate authoritative definition of UngleichMitToleranz2 (do not assume numeric 2), freeze operator semantics, then implement and test evaluator in a separately authorized bounded slice. DR-04 OPEN; DR-05 BLOCKED. No tests run in this documentation-only extraction. Local dirty worktree was not modified by Git operations.

## Authoritative tolerance semantics resolved

Official ERiC 44.3.6.0 package `ERiC-44.3.6.0-Dokumentation.zip`, embedded `Dokumentation/Datenarten/Zusatzinformationen_zur_Plausibilitaetspruefung.pdf`, PDF page 70, section 4.5, Table 4-20 (`Vergleichsoperatoren`) explicitly defines `UngleichMitToleranz2`: the predicate is true iff `abs(v1 - v2) > 2`. Equality at difference exactly 2 is FALSE; difference 3 is TRUE for integer whole-euro values. Applies to rule IDs `101100090` and `12204`. This resolves the prior operator-semantics blocker. Definition sourced from locally protected official archive, not inferred from operator name. No ERiC engine executed and no local evaluator implemented yet. Stage 1 operator semantics VERIFIED; DR-04 overall still OPEN.
