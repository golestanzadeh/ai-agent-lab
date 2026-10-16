\set ON_ERROR_STOP on

CREATE SCHEMA ai_tax_poc_20261016;

CREATE TABLE ai_tax_poc_20261016.schema_migration (
    version integer PRIMARY KEY CHECK (version > 0),
    applied_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    migration_id text NOT NULL UNIQUE CHECK (length(migration_id) BETWEEN 1 AND 128)
);

CREATE TABLE ai_tax_poc_20261016.tax_case (
    case_id text PRIMARY KEY CHECK (case_id ~ '^[A-Z0-9][A-Z0-9_-]{2,63}$'),
    tax_year integer NOT NULL CHECK (tax_year BETWEEN 1900 AND 2200),
    storage_root_ref text NOT NULL UNIQUE CHECK (length(storage_root_ref) BETWEEN 1 AND 256),
    schema_version integer NOT NULL CHECK (schema_version = 1),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    UNIQUE (case_id, tax_year)
);

CREATE TABLE ai_tax_poc_20261016.identity_record (
    identity_id text PRIMARY KEY CHECK (identity_id ~ '^SYN-[A-Z0-9_-]{3,60}$'),
    record_type text NOT NULL CHECK (record_type IN ('PERSON', 'ENTITY')),
    status text NOT NULL CHECK (status IN ('ACTIVE', 'INACTIVE', 'UNRESOLVED')),
    payload jsonb NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
    digest text NOT NULL CHECK (digest ~ '^[0-9a-f]{64}$'),
    revision integer NOT NULL CHECK (revision >= 1),
    schema_version integer NOT NULL CHECK (schema_version = 2),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE ai_tax_poc_20261016.case_party_role (
    binding_id text PRIMARY KEY,
    case_id text NOT NULL,
    tax_year integer NOT NULL,
    subject_id text NOT NULL REFERENCES ai_tax_poc_20261016.identity_record(identity_id),
    role_code text NOT NULL CHECK (role_code IN ('PRIMARY_TAXPAYER', 'SPOUSE_OR_PARTNER', 'CHILD', 'OTHER_DEPENDENT_OR_RELEVANT_PERSON')),
    valid_from date NOT NULL,
    valid_to_exclusive date,
    evidence_ref text NOT NULL CHECK (evidence_ref ~ '^sha256:[0-9a-f]{64}$'),
    authorization_ref text NOT NULL CHECK (length(authorization_ref) BETWEEN 1 AND 128),
    revision integer NOT NULL CHECK (revision >= 1),
    schema_version integer NOT NULL CHECK (schema_version = 2),
    FOREIGN KEY (case_id, tax_year) REFERENCES ai_tax_poc_20261016.tax_case(case_id, tax_year),
    CHECK (valid_to_exclusive IS NULL OR valid_from < valid_to_exclusive),
    UNIQUE (case_id, tax_year, subject_id, role_code, valid_from, revision)
);

CREATE TABLE ai_tax_poc_20261016.subject_fact_binding (
    request_id text PRIMARY KEY,
    case_id text NOT NULL,
    tax_year integer NOT NULL,
    subject_id text NOT NULL REFERENCES ai_tax_poc_20261016.identity_record(identity_id),
    semantic_key text NOT NULL CHECK (length(semantic_key) BETWEEN 1 AND 128),
    fact_artifact_ref text NOT NULL CHECK (fact_artifact_ref ~ '^sha256:[0-9a-f]{64}$'),
    declaration_artifact_ref text NOT NULL CHECK (declaration_artifact_ref ~ '^sha256:[0-9a-f]{64}$'),
    confirmation_ref text NOT NULL CHECK (length(confirmation_ref) BETWEEN 1 AND 128),
    authorization_ref text NOT NULL CHECK (length(authorization_ref) BETWEEN 1 AND 128),
    lineage jsonb NOT NULL CHECK (jsonb_typeof(lineage) = 'array' AND jsonb_array_length(lineage) > 0),
    payload_digest text NOT NULL CHECK (payload_digest ~ '^[0-9a-f]{64}$'),
    revision integer NOT NULL CHECK (revision >= 1),
    schema_version integer NOT NULL CHECK (schema_version = 2),
    FOREIGN KEY (case_id, tax_year) REFERENCES ai_tax_poc_20261016.tax_case(case_id, tax_year),
    UNIQUE (case_id, tax_year, subject_id, semantic_key, revision)
);

CREATE TABLE ai_tax_poc_20261016.idempotency_request (
    request_id text PRIMARY KEY,
    request_digest text NOT NULL CHECK (request_digest ~ '^[0-9a-f]{64}$'),
    outcome_digest text NOT NULL CHECK (outcome_digest ~ '^[0-9a-f]{64}$'),
    committed_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE ai_tax_poc_20261016.audit_event (
    event_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    case_id text NOT NULL,
    tax_year integer NOT NULL,
    action text NOT NULL CHECK (length(action) BETWEEN 1 AND 64),
    payload_digest text NOT NULL CHECK (payload_digest ~ '^[0-9a-f]{64}$'),
    previous_digest text NOT NULL CHECK (previous_digest ~ '^[0-9a-f]{64}$'),
    event_digest text NOT NULL UNIQUE CHECK (event_digest ~ '^[0-9a-f]{64}$'),
    recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    FOREIGN KEY (case_id, tax_year) REFERENCES ai_tax_poc_20261016.tax_case(case_id, tax_year)
);

CREATE INDEX case_party_scope_idx ON ai_tax_poc_20261016.case_party_role(case_id, tax_year, role_code);
CREATE INDEX subject_fact_scope_idx ON ai_tax_poc_20261016.subject_fact_binding(case_id, tax_year, subject_id);
CREATE INDEX audit_scope_idx ON ai_tax_poc_20261016.audit_event(case_id, tax_year, event_id);

INSERT INTO ai_tax_poc_20261016.schema_migration(version, migration_id)
VALUES (1, 'POSTGRESQL_POC_SCHEMA_V1');

DO $$ BEGIN
    CREATE ROLE ai_tax_poc_reader NOLOGIN;
EXCEPTION WHEN duplicate_object THEN
    RAISE EXCEPTION 'PoC role already exists; refusing ambiguous environment';
END $$;

GRANT USAGE ON SCHEMA ai_tax_poc_20261016 TO ai_tax_poc_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA ai_tax_poc_20261016 TO ai_tax_poc_reader;

ALTER TABLE ai_tax_poc_20261016.tax_case ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_tax_poc_20261016.tax_case FORCE ROW LEVEL SECURITY;
ALTER TABLE ai_tax_poc_20261016.case_party_role ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_tax_poc_20261016.case_party_role FORCE ROW LEVEL SECURITY;
ALTER TABLE ai_tax_poc_20261016.subject_fact_binding ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_tax_poc_20261016.subject_fact_binding FORCE ROW LEVEL SECURITY;
ALTER TABLE ai_tax_poc_20261016.audit_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_tax_poc_20261016.audit_event FORCE ROW LEVEL SECURITY;

CREATE POLICY exact_case_tax_year ON ai_tax_poc_20261016.tax_case
    USING (case_id = current_setting('ai_tax.case_id', true)
       AND tax_year = nullif(current_setting('ai_tax.tax_year', true), '')::integer);
CREATE POLICY exact_case_tax_year ON ai_tax_poc_20261016.case_party_role
    USING (case_id = current_setting('ai_tax.case_id', true)
       AND tax_year = nullif(current_setting('ai_tax.tax_year', true), '')::integer);
CREATE POLICY exact_case_tax_year ON ai_tax_poc_20261016.subject_fact_binding
    USING (case_id = current_setting('ai_tax.case_id', true)
       AND tax_year = nullif(current_setting('ai_tax.tax_year', true), '')::integer);
CREATE POLICY exact_case_tax_year ON ai_tax_poc_20261016.audit_event
    USING (case_id = current_setting('ai_tax.case_id', true)
       AND tax_year = nullif(current_setting('ai_tax.tax_year', true), '')::integer);
