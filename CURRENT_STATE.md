# Current State

## Project status

The project is in the foundational architecture and Phase 2 implementation stage. CASE-001 is the first real validation case, but the architecture is being built for long-term multi-case, multi-year operation for natural persons and legal entities.

## D-018 Deterministic Migration Artifact Identity

D-018 is accepted and implemented at `src/agent_lab/artifact_identity.py`, with artifact identity exposure added to the CASE-001 migration Manifest and Preflight result.

The identity contract is:

- controlled artifact `kind`;
- explicit identity/schema `version`;
- `sha256:<digest>` reference over deterministic canonical payload;
- identity payload excludes the identity itself, avoiding circular hashing;
- equivalent payloads produce the same reference;
- changing a hashed field produces a different reference.

Current artifact kinds are `CASE001_MIGRATION_MANIFEST` and `CASE001_MIGRATION_PREFLIGHT`, both version `1`.

The Manifest identity covers its case, tax period, provider, source/target scopes, mapping sequence, and optional Inventory Evidence reference. The Preflight identity covers the complete deterministic preflight result.

Documentation: `docs/artifact-identity.md`.

Test suite: `tests/unit/test_artifact_identity.py` contains **8 tests** covering canonicalization, deterministic identity, content-change invalidation, Manifest identity, and Preflight identity.

D-018 performs no Drive mutation and does not authorize or execute migration. The next boundary is to construct the D-017 approval context from the exact real Manifest and successful Live Target Preflight artifact identities.

## Existing verified foundations

The repository already contains the established multi-case architecture, case isolation boundary, Case Registry, Person/Entity Registry, Case State/Run ID, Audit Store, Google Drive metadata-only adapter, Document Identity, Inventory Evidence, CASE-001 migration compatibility, migration manifest generator, Live Target Preflight, and D-017 Human Approval Gate.

Existing verified evidence remains recorded in the prior sections of project history and in the corresponding repository documents. In particular, CASE-001 live metadata inventory is 15 documents and 0 folders, live identity bootstrap covers 15/15 documents, and no physical Drive migration has occurred.

The D-017 unit suite was expanded to **13 tests**. The assistant performed a separate deterministic local reconstruction of the D-017 implementation boundary with **13 passed tests in 0.20s**. Repository-hosted GitHub Actions previously reported zero workflow runs, so no GitHub-hosted execution result is claimed.

## Safety boundary

No change in D-018 authorizes physical migration. Manifest generation, preflight, artifact identity, and approval remain separate deterministic boundaries. No Drive mutation, migration executor, or LLM authorization path is introduced by D-018.

## Next implementation priorities

1. Generate the real CASE-001 migration manifest from the live inventory and persisted logical identities.
2. Validate the generated manifest against the authoritative source scope and Inventory Evidence.
3. Run the read-only live target preflight and bind its exact artifact identity to the exact Manifest identity.
4. Construct and validate a D-017 approval record from those exact artifact identities before any physical migration design/execution.
5. Design the controlled physical migration executor, rollback, and post-migration verification. No physical Drive migration yet.
6. Continue toward controlled document-content access and evidence extraction.
