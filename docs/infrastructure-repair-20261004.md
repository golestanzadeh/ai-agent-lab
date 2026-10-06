# Infrastructure repair — 2026-10-04

Status: **INFRASTRUCTURE_REPAIR_COMPLETE**

Starting checkpoint was `12069bcc26ed02a1e6cfb33b4e9ad7f937d8f97c7`. Starting live capacity was 99 percent five-hour and 86 percent weekly; the final post-push observation was 31 percent and 76 percent. Service reset epochs were `1791146339` and `1791715052`.

Repair A introduces an executable deterministic Limit Controller. `RUN`, `CAUTION`, `TOKEN_PAUSED`, `UNKNOWN_PAUSED`, and `CAPACITY_DEFERRED` are distinct. A healthy 50/92 observation is `RUN`; hard pause thresholds remain inclusive at 15/10. Service reset timestamps are mandatory and never inferred. Proactive deferral uses a closed versioned cost catalog, records the exact operation/reason/checkpoint, and does not inherit genuine token-pause resume semantics. Only the existing reset-aligned economical continuation guard is retained.

Repair B introduces a Git-reviewed manifest-pinned official-knowledge index. Accepted entries bind exact authority, release, tax year, source identity/hash, locator, form/topic, datatype, transformation, dependencies, extraction version, verification and acceptance. Normal exact lookup reads only the bounded JSON derivative and does not invoke protected-source resolution. Wrong year/release/hash, manifest or extract drift, missing/ambiguous knowledge, and unresolved DR-03/DR-04 extracts fail closed. Exception-driven source inspection has versioned request and completion records, and comparison supports `UNCHANGED`, `CHANGED`, `NEW`, and `REMOVED`.

Focused verification passes (`50 passed`); the relevant declaration/source regression passes (`74 passed`). Independent Acceptance: Repair A `PASS`, Repair B `PASS`, canonical continuation preservation `PASS`. Full repository regression is explicitly deferred to DR-05 as already required.

CASE-001 did not advance. DR-01/DR-02 remain `PASS`; six Owner facts remain `SUPPLIED_NOT_REGISTERED`; DR-04 retains exactly three acceptance defects; DR-05 remains `NOT_STARTED`; EUR 133.83 remains frozen. Exact next action is to register the supplied Human Declarations, complete DR-03, repair and independently accept DR-04, then start DR-05 only when both pass. No external ERiC/ELSTER/Finanzamt, signing, submission, certificate, production, Gemini/CSV rerun, or Drive mutation occurred.
