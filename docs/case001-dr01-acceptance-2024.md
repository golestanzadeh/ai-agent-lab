# CASE-001 declaration remediation DR-01

Status: **`PASS`**  
Tax year: **2024**

DR-01 adds one bounded case-scoped composition contract. It cryptographically binds `case_id`, tax year, run, Case Registry, frozen calculation, exact evidence references and the existing Anlage N mapping. No private taxpayer value is stored in Git; private values enter only inside the approved case-data boundary.

The verified annual documentation identifies `E0100001` as the income-tax-return filing basis and `E0101201` as `Zusammenveranlagung`. The exact official Hauptvordruck identity/address/date fields used by the contract are recorded in the machine-readable acceptance artifact. The official 2024 form instructions require Euro entries and taxpayer-favorable rounding unless cents are expressly required; the annual documentation defines gross-wage field `E0200201` as `GeldBetragOhneCent`. Accordingly, the positive source wage `EUR 36,470.23` maps deterministically to `EUR 36,470`, without changing the frozen tax calculation.

Composition with the existing Anlage N output validates against the exact protected `E10-2024.xsd`. Missing/invalid identity, ambiguous lineage, unsupported year, malformed amount, mapping mismatch, protected-source absence/corruption and path escape fail closed. Case/run/evidence changes alter the cryptographic identity. The output remains a `NON_TRANSMITTING_PREVIEW`; official ERiC execution and every external action remain false.

Focused and relevant regression verification passes (`191 passed`). Independent package acceptance is `PASS`. DR-02, DR-03 and DR-04 are dependency-ready; DR-05 remains blocked on their accepted completion. The post-package capacity gate reported 80 percent five-hour and 21 percent weekly remaining. Execution is `TOKEN_PAUSED` before DR-02 to preserve enough weekly capacity for a complete package, acceptance, checkpoint and report.
