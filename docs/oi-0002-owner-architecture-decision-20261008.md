# OI-0002 Owner architecture decision record

Record ID: `ODR-OI0002-OWNER-DISPOSITION-20261008`  
Date: 2026-10-08  
Authority: Project Owner / Human Gate  
Implementation SHA: `ad263284ff211d6d7d75234c03c3005d43b7d2df`  
Architecture report commit: `2cb049eb57934657cdddf8a1747546270efe925b`

The Owner approved `ODR-OI0002-02-PERMISSIONS`: the six dedicated capabilities `identity_create`, `identity_read`, `identity_update`, `identity_status_transition`, `case_party_bind` and `subject_fact_bind`, plus the dedicated `IDENTITY_ADMINISTRATION_AGENT`, may be added in a versioned successor contract. Generic derived-artifact permissions and ordinary tax roles, including `TAX_LAW_AGENT`, must not authorize identity administration.

The Owner conditionally approved `ODR-OI0002-03-EVIDENCE`, subject to E-01 through E-06: reuse existing authorities; metadata only in the existing SQLite deployment; explicit authoritative provider/type mappings; actual resolution and scope verification; fail-closed behavior; and reviewable evidence.

The Owner conditionally approved `ODR-OI0002-06-CONTINUITY`, subject to C-01 through C-06: Kernel-owned independent trust; separate state/key custody; monotonic reservation/finalization and crash recovery; separately authorized restore; rollback rejection/threat model; and operational custody/ACL/key/recovery evidence.

Permitted now: record this decision, update governance, verify the conditions, prepare provider/trust-boundary specifications and plan remediation-02. Prohibited: remediation implementation (including F02 while the package is blocked), treating conditional approval as release, OI closure, OI-0003, real identity bootstrap, merge/release/production/ELSTER/external transmission, or any parallel authority.

Required next gate: `OI-0002-CONDITIONS-VERIFICATION-GATE`. Only the Owner can release unresolved conditional approvals.
