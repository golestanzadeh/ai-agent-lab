# PostgreSQL Persistence PoC — Final Technical Acceptance

Date: 2026-10-16  
Repository branch: `oi0002-identity-persistence`  
Baseline: `2bb0150c873133326465a1352bf2e882b74a0b81`  
Scope: synthetic local PoC only; no application integration or protected persistence activation

## Executive decision

PostgreSQL 18 is technically suitable as a future AI-Tax-Agent structured-data backend, subject to an application adapter, reviewed SQLite-to-PostgreSQL migration, production custody/hardening and an independent C09 authority. The existing Docker lab is usable for isolated synthetic development, but is not acceptable as a canonical application or protected-production deployment in its current form.

PostgreSQL does not independently provide rollback-resistant freshness. A database administrator was able to rewrite a synthetic audit row successfully. A database/volume snapshot can likewise be restored to an older internally consistent state. C09 therefore remains rejected for this tested configuration and open at project level.

## Recovered contracts and boundaries

The PoC was evaluated against:

- `docs/oi-0002-identity-family-persistence-design-20261008.md`, including the recovered frozen Persistence Contract v1;
- `docs/oi-0002-persistence-operations.md`;
- `docs/case-party-model.md`;
- `docs/document-identity-persistence.md`;
- `docs/decisions/oi0002-local-development-vs-operational-acceptance-20261014.md`;
- `src/agent_lab/identity_persistence.py` and its migration/acceptance tests;
- `docs/postgresql-local-lab-verified-20261016.md`.

The frozen contract still names SQLite as the current authoritative structured application database and PostgreSQL as an upgrade path. This PoC tests that upgrade path; it does not amend the contract, create a second live authority or authorize integration.

## Environment

- Host: Windows `DESKTOP-HVRUQB7`; Docker Desktop/Engine in Linux-container mode.
- Docker Engine: `29.8.2`.
- Existing container: `ai-tax-postgres-test`; no new container/server was created.
- PostgreSQL: `18.6 (Debian 18.6-1.pgdg13+2)`.
- Existing database: `ai_tax_test`; endpoint `127.0.0.1:55432`.
- Existing named volume: `ai-tax-postgres-test`, mounted read/write at `/var/lib/postgresql`.
- Host free space before the PoC: approximately 160.5 GB.
- Existing `public.lab_events` evidence remained exactly `2` rows with maximum epoch `103`.
- PoC schema: `ai_tax_poc_20261016`; synthetic values only.
- Temporary restore database: `ai_tax_poc_restore_20261016`; created, verified and removed on the same server.

The active root checkout was an older clean `d021-agent-case-provisioning` branch. The named OI-0002 worktree contained unrelated local modifications and was 32 commits behind. Work therefore used the clean detached worktree `C:\Users\rezag\ai-agent-lab-c09-continuation` at the exact remote OI-0002 baseline. No unrelated worktree or change was modified.

Authenticated Codex telemetry before execution was 98% five-hour and 97% weekly remaining at `2026-10-16T19:02:57.284539Z`; the bounded mission fit while preserving the mandatory 15-point reserve.

## Schema and method

The versioned schema in `scripts/postgresql_persistence_poc_schema.sql` maps the approved portable requirements to explicit PostgreSQL primary, foreign, unique and check constraints; application-style stable IDs; UTC timestamps; schema versioning; case/tax-year composite scope; evidence and lineage references; idempotency records; and indexed audit records. Row-level-security policies require exact `case_id` and tax year for the restricted reader role.

The executable harness `scripts/postgresql_persistence_poc.py` refuses to overwrite an existing PoC schema or restore database. It applies the schema through the existing container, uses only synthetic data, exercises transactions and concurrency, restarts the container, takes a schema-scoped custom-format backup, restores it into an isolated database, verifies content/integrity fields and deletes only that disposable restore database.

## Exact executed commands

Sensitive values were read only into a process-local variable and never printed.

```powershell
docker info --format '{{.OSType}} {{.ServerVersion}}'
docker ps -a --filter name=^/ai-tax-postgres-test$
docker inspect ai-tax-postgres-test
docker exec ai-tax-postgres-test pg_isready -U postgres -d ai_tax_test
python scripts\postgresql_persistence_poc.py --schema scripts\postgresql_persistence_poc_schema.sql --result .runtime\postgresql-poc-final.json
docker exec -e PGPASSWORD=$pw ai-tax-postgres-test psql -X -h $containerIp -U postgres -d ai_tax_test -Atc "SELECT current_database()||'|'||current_user;"
docker exec -e PGPASSWORD=definitely-wrong ai-tax-postgres-test psql -X -h $containerIp -U postgres -d ai_tax_test -Atc "SELECT 1;"
docker exec ai-tax-postgres-test psql -X -v ON_ERROR_STOP=1 -U postgres -d ai_tax_test -Atc "BEGIN; ALTER TABLE ai_tax_poc_20261016.identity_record ADD COLUMN migration_probe text; ROLLBACK; ..."
docker exec ai-tax-postgres-test psql -X -v ON_ERROR_STOP=1 -U postgres -d ai_tax_test -Atc "BEGIN; INSERT ... SELECT ... FROM generate_series(1,10000); EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) ...; ROLLBACK;"
```

The harness internally used `psql`, `pg_dump -Fc`, `CREATE DATABASE`, `pg_restore --exit-on-error`, verification queries and `DROP DATABASE` against the existing server. The disposable backup bytes were streamed in memory and were not committed.

## Results

Automated harness: **29/29 PASS**, exit code `0`, elapsed `17.871s`.

Repository verification after the PoC:

- relevant Identity/Persistence/documentation suite: `77 passed`;
- complete unit regression: `1359 passed, 5 skipped` in `267.02s`;
- Python harness compilation: PASS;
- `git diff --check`: PASS.

The first relevant-suite run exposed that the pre-existing local-lab runbook was absent from `docs/README.md`; the index was corrected and the suite was rerun to the passing result above. No test failure was hidden or waived.

### Contract compatibility

| Requirement | Result | Evidence |
|---|---|---|
| Portable schema and version | PASS | Migration row `POSTGRESQL_POC_SCHEMA_V1`; explicit PostgreSQL-compatible constraints/indexes. |
| Case and tax-year isolation | PASS | Composite foreign keys plus RLS; missing, wrong-year and cross-case context returned zero rows. |
| Evidence references and lineage | PASS (structural) | Required SHA-256 references and non-empty JSON lineage enforced. Protected resolver was intentionally not integrated. |
| Audit records and integrity | FAIL (full contract) | Referential/format constraints passed, but a PostgreSQL administrator successfully rewrote the audit payload digest. No keyed application verification or independent anchor was present. |
| Required identifiers and constraints | PASS | Invalid ID, revision, digest and unresolved foreign key were rejected. |
| Transaction boundaries | PASS | Atomic multi-table commit and explicit rollback passed. |
| Migration feasibility | PASS (PoC) | Initial migration passed; transactional `ALTER TABLE` rollback left no column. SQLite data conversion is not yet implemented. |

Full Persistence Contract compliance is therefore not a complete PASS.

### Functional correctness — 10/10 PASS

- create/read, permitted update and permitted delete;
- transaction rollback and atomic multi-table commit;
- foreign-key and input-check rejection;
- unique/idempotency conflict rejection;
- concurrent row-lock conflict with deterministic timeout;
- indexed representative query after a transient 10,000-row synthetic workload.

The 10,000-row transaction was rolled back. The indexed last-20 event query used `audit_scope_idx` and completed in `0.034 ms` in this local observation. This is a basic feasibility result, not a capacity or production benchmark.

### Persistence and recovery — 7/7 PASS

- container restart;
- post-restart row durability;
- custom-format controlled backup (`26,745` bytes in this run);
- isolated restore database creation;
- restore with stop-on-error;
- restored fact and audit-field verification;
- disposable restore database removal.

This proves ordinary PostgreSQL durability/restore mechanics. It does not prove rollback-resistant restore authorization.

### Security — 8/9 controls satisfactory; 1 decisive limitation

- SCRAM-SHA-256 was configured; the protected lab password authenticated over a TCP path and a deliberately wrong password was rejected with exit code `2`.
- Port publication was loopback-only: `127.0.0.1:55432`.
- `ai_tax_poc_reader` was `NOLOGIN`, non-superuser, read-only; unauthorized update was rejected.
- Exact case/year RLS returned only the authorized case; missing and wrong-year contexts returned zero rows.
- The administrator could modify the audit row: expected adversarial probe succeeded and establishes that PostgreSQL alone is not a tamper-resistant audit authority.
- The existing password file is outside Git, but its inherited ACL grants `ReadAndExecute` to local `CodexSandboxUsers`; ACL inheritance is not disabled. In addition, the original container configuration exposes `POSTGRES_PASSWORD` to Docker administrators through inspect. These are unacceptable production credential-custody properties.
- The PoC used the `postgres` superuser for administration. A dedicated authenticated application login, ownership separation, default-privilege policy and operator/recovery role split were not provisioned because production security changes were outside scope.

Security verdict for synthetic local experimentation is conditional; protected production is rejected.

### Operational suitability

- Windows/Docker workflow, restart, volume persistence and loopback access: PASS.
- Reproducible guarded schema/harness: PASS.
- Transactional schema change: PASS at PoC level.
- Basic indexed workload: PASS; no long-duration capacity, vacuum/bloat, WAL-retention or failover benchmark was performed.
- Storage growth can be measured through `pg_total_relation_size`; production retention/maintenance policy remains undefined.
- PostgreSQL improves future laptop/VPS portability, but a governed export/import, secret rotation and continuity/freshness verification procedure is still required.

## C09 boundary assessment

| C09 concern | Tested conclusion |
|---|---|
| Snapshot rollback | PostgreSQL can restore snapshots; it cannot independently prove the restored snapshot is the newest authorized state. |
| Database administrator tampering | Verified possible: superuser rewrote the synthetic audit payload digest. |
| Audit-log modification | Internal constraints/hash columns do not prevent a privileged coordinated rewrite. Application HMAC validation helps detect ordinary alteration but remains insufficient if DB plus replaceable anchor roll back together. |
| Epoch rollback | A unique/monotonic database column prevents duplicates only within the currently loaded database state; an older snapshot can contain an older internally valid maximum. |
| Freshness verification | Requires state outside the rollback domain. Not supplied by this PoC. |
| Independent witness | Still required and not selected/approved. GitHub branch history and ordinary database rows are explicitly insufficient. |

PostgreSQL may store continuity metadata, but cannot be its own independent freshness witness. C09 for this configuration is **REJECTED**; project-level C09 remains `OPEN / NOT ACCEPTED` pending an approved external or independently protected authority.

## Six mandatory acceptance decisions

1. **PostgreSQL as a database technology for AI-Tax-Agent — `CONDITIONALLY_ACCEPTED`.** Relational constraints, transactions, concurrency, restart, backup/restore and portability passed. Conditions: implement the approved persistence interface, reviewed migration and integrity verification; define operations/maintenance; deploy least privilege and protected secrets; retain an external C09 solution.
2. **Existing Docker-based PostgreSQL environment for local development — `CONDITIONALLY_ACCEPTED`.** It is suitable now only for isolated synthetic PoC development. Conditions: restrict/rotate the password, stop relying on the inspect-visible bootstrap secret, create a least-privilege login for application experiments and retain loopback-only exposure.
3. **Tested PoC compliance with the approved Persistence Contract — `CONDITIONALLY_ACCEPTED`.** The portable relational and isolation subset passed; complete application semantics, keyed audit verification, protected evidence resolution and reviewed SQLite data migration are absent.
4. **Readiness for integration into the application — `NOT_VERIFIED`.** No PostgreSQL adapter implements the existing persistence interface, no application regression runs against PostgreSQL and the frozen contract still designates SQLite as current authority.
5. **Readiness for protected production use — `REJECTED`.** Credential custody, dedicated roles, independently protected audit/freshness, production backup authorization, monitoring, upgrades and operational acceptance are missing.
6. **Satisfaction of C09 anti-rollback requirements — `REJECTED`.** Privileged tampering and snapshot/epoch rollback remain possible without an independent freshness witness.

## Remaining mandatory actions

1. Owner architecture decision before changing the frozen current-authority choice from SQLite to PostgreSQL.
2. Define and independently review a PostgreSQL adapter for the existing persistence interface and a one-authority cutover/migration plan; never run SQLite and PostgreSQL as competing canonical stores.
3. Add exact application-contract parity tests, keyed audit verification and SQLite-to-PostgreSQL populated-data migration/rollback tests.
4. Correct local credential ACLs, rotate the lab password, replace inspect-visible bootstrap-secret handling and test a dedicated least-privilege login.
5. Define backup encryption/retention, recovery authorization, monitoring, patch/upgrade, vacuum and capacity policies.
6. Select and approve an independent rollback-resistant freshness authority, revise the operational ADR and obtain independent security acceptance before protected use.

## Final recommendation

Adopt PostgreSQL as the **preferred candidate future database technology** and permit the existing lab for **synthetic local adapter/migration development after credential hardening**. Do not make it the canonical application database, integrate it into protected flows or use it in production until the conditions above are satisfied through governed implementation and independent acceptance.
