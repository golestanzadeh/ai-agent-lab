# PostgreSQL 18 local Docker lab: verified runbook (2026-10-16)

Status: VERIFIED LOCAL EXPERIMENT ONLY. Not integrated with AI-Tax-Agent; not C09 acceptance.

## Scope and boundary
- Host: Windows DESKTOP-HVRUQB7, Docker Desktop 4.95.0, Docker Engine 29.8.2, Linux containers.
- Image: official `postgres:18`, observed PostgreSQL server `18.6` (Debian 18.6-1.pgdg13+2), image digest observed at pull: `sha256:74935e72241653ca55e0414067e6d8763aceb8a810eb51b452253ec3dcfc4336`.
- Container: `ai-tax-postgres-test`, restart policy `unless-stopped`.
- Database: `ai_tax_test`, user `postgres`, host endpoint `127.0.0.1:55432` -> container port `5432`.
- Named Docker volume: `ai-tax-postgres-test` mounted at `/var/lib/postgresql` (correct for official Postgres 18 image).
- Lab password file: `%LOCALAPPDATA%\AI-Tax-Agent-Postgres-Lab\postgres-password.txt` (LOCAL ONLY; NEVER commit, paste or upload). Generated using cryptographic RNG. WARNING: password was also passed via Docker `-e POSTGRES_PASSWORD=...`, and can be visible to local Docker administrators through inspect. Rotate and use Docker secrets for any production deployment.
- No real taxpayer data; no Kernel/Identity IPC wiring; no GitHub secrets; no external services.

## Reproduce only if absent
1. Verify `docker info --format '{{.OSType}} {{.ServerVersion}}'` returns `linux` and running engine.
2. Verify container/volume absence before creation: `docker ps -a --filter name=ai-tax-postgres-test`; `docker volume ls --filter name=ai-tax-postgres-test`.
3. Generate a new random password locally, store outside Git, and restrict filesystem ACL before reuse. Never paste password in issue, chat, commit or terminal output.
4. Create volume: `docker volume create ai-tax-postgres-test`.
5. Create container (PowerShell variable `$pw` populated locally from protected secret): `docker run -d --name ai-tax-postgres-test --restart unless-stopped -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=$pw -e POSTGRES_DB=ai_tax_test -p 127.0.0.1:55432:5432 -v ai-tax-postgres-test:/var/lib/postgresql postgres:18`.
6. Verify: `docker exec ai-tax-postgres-test pg_isready -U postgres -d ai_tax_test` and `docker exec ai-tax-postgres-test psql -X -U postgres -d ai_tax_test -c 'SELECT current_database(), current_user, version();'`.
7. Existing environment: DO NOT rerun `docker run` or `TRUNCATE` against any non-disposable data. Inspect current state first.

## Verified SQL checks (synthetic data)
```sql
CREATE TABLE IF NOT EXISTS lab_events (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  epoch BIGINT NOT NULL UNIQUE,
  state_digest TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- Initial lab only: TRUNCATE lab_events RESTART IDENTITY;
INSERT INTO lab_events(epoch,state_digest) VALUES (101,'synthetic-digest-101');
BEGIN;
INSERT INTO lab_events(epoch,state_digest) VALUES (102,'synthetic-digest-102');
ROLLBACK;
SELECT count(*), max(epoch) FROM lab_events; -- expected: 1, 101
-- Duplicate epoch 101 was rejected via unique_violation caught in a DO block.
INSERT INTO lab_events(epoch,state_digest) VALUES (103,'synthetic-digest-103');
SELECT count(*), max(epoch) FROM lab_events; -- expected: 2, 103
```

## Actual test results
- Docker server available and Linux mode: PASS.
- Image pulled, container started and `pg_isready` accepted connections: PASS.
- SQL `SELECT current_database(), current_user, version()`: PASS.
- Transaction rollback left one row, max epoch 101: PASS.
- Duplicate epoch unique constraint rejected the attempted duplicate: PASS.
- Commit added epoch 103; two rows, max epoch 103: PASS.
- `docker restart ai-tax-postgres-test` succeeded: PASS.
- After restart, two rows and max epoch 103 persisted: PASS.
- Host TCP port 127.0.0.1:55432 reachable: PASS.
- Authenticated TCP SQL query with password: PASS.
- Docker inspect verified running status, loopback-only host bind and named volume mount: PASS.
- Backup/restore, disaster recovery, isolation under adversarial rollback, migration and production hardening: NOT TESTED.

## Architectural interpretation
PostgreSQL proves ordinary relational persistence, ACID transaction rollback, uniqueness and restart durability. `ROLLBACK` here means SQL transaction cancellation, NOT C09 rollback-resistant freshness. A local or managed PostgreSQL administrator can potentially restore an older snapshot. C09 remains OPEN / NOT ACCEPTED; no independent anti-rollback witness, protected persistence approval, production IPC, finality or ELSTER submission is authorized by this lab. Do not confuse a synthetic `epoch` UNIQUE index with an independent freshness authority.

## Safe continuation
- Read `PROJECT_CHECKPOINT.md`, `AGENTS.md`, and C09 decision before proposing integration.
- Reuse this container for disposable development tests, but avoid treating it as canonical project persistence.
- Before production: define credential handling (Docker secrets), least-privilege database role, schema/migrations, backup+restore drill, health checks, upgrade pinning, logging and retention, and an independent C09 witness design.
- No paid cloud resources or external sharing authorized by this experiment.
