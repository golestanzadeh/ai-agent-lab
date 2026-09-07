# Deterministic Migration Artifact Identity

## Status

Implemented for D-018.

## Purpose

Manifest and Live Target Preflight outputs are execution-boundary artifacts. They must be identifiable independently of the Python object instance, filename, chat context, or a later reconstruction of their contents.

D-018 gives each supported artifact a deterministic identity consisting of:

- `kind`: controlled artifact type;
- `version`: identity/schema version;
- `reference`: `sha256:` followed by the SHA-256 digest of the canonical artifact payload.

The identity is calculated from the artifact payload without including the identity itself, avoiding circular hashing.

## Canonical representation

Canonical JSON uses:

- sorted object keys;
- compact separators;
- UTF-8 encoding;
- deterministic conversion of dataclasses, enums, mappings, sequences, and sets.

Equivalent payloads therefore produce the same reference. Any change to a hashed field produces a different reference.

## Current artifact types

| Artifact | Kind | Version |
|---|---|---:|
| CASE-001 migration manifest | `CASE001_MIGRATION_MANIFEST` | `1` |
| CASE-001 migration preflight result | `CASE001_MIGRATION_PREFLIGHT` | `1` |

## Manifest identity payload

The manifest reference covers its case, tax period, provider, source scope, target scope, complete mapping sequence, and optional inventory-evidence reference.

The mapping content therefore becomes part of the approval binding indirectly through the manifest reference.

## Preflight identity payload

The preflight reference covers the complete deterministic result, including case, tax period, document count, source/target scopes, target verification flags, uniqueness checks, mapping-count check, and final pass state.

A different preflight result cannot retain the same reference.

## Approval integration boundary

D-017 already requires exact `manifest_identity`, `manifest_version`, `manifest_reference`, `preflight_identity`, and `preflight_reference` bindings. D-018 now gives the Manifest and Preflight concrete deterministic values that can populate those fields.

This step does **not** automatically create or consume an approval. The next integration step must take the actual generated Manifest and actual successful Live Target Preflight result and construct the D-017 execution context from those exact artifact identities.

## Safety boundary

D-018:

- performs no Drive mutation;
- does not create a migration executor;
- does not authorize migration;
- does not use an LLM for identity generation or validation;
- does not store private Drive object IDs in repository documentation.

The SHA-256 reference is an integrity/identity reference, not a cryptographic signature or proof of authorship.
