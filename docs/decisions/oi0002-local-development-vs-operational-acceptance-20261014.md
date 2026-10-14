# OI-0002 local development versus operational acceptance

Date: 2026-10-14

Authority: Project Owner clarification

Status: **OWNER-APPROVED DEVELOPMENT BASELINE / OPERATIONAL IPC NOT ACCEPTED**

## Decision

AI-Tax-Agent development continues on the existing Windows laptop with the existing Python/Docker architecture. The implementation must remain portable to a replacement laptop or VPS. Ordinary local development does not require a TPM, new hardware or an external service.

The TPM and GitHub App investigations are completed historical diagnostics. They establish that:

- this host cannot provide the TPM NV counter required by the proposed operational IPC profile;
- GitHub remains the source of truth for code and documentation;
- GitHub branch state is not an approved independent monotonic anti-rollback witness.

Neither result is a global development stop.

## Development profile

The following may proceed through their existing authorization, dependency, Limit Guard and test gates:

- UI, accessibility, localization and owner-testable product behavior that uses no protected data;
- portable Python contracts, canonical framing, deterministic validation and negative tests;
- Docker/local configuration that does not create a second authority or activate protected persistence;
- synthetic or disposable transport tests that cannot commit protected Identity state;
- documentation and migration-readiness checks.

Development-profile work must fail closed before protected mutation, rollback-resistant finality, backup replacement or operational restore. A test double, local file, Git branch, registry value, ordinary database row or software-only HMAC must not be described as satisfying C09.

## Operational acceptance profile

Operational Kernel↔Identity acceptance still requires an independently reviewed mechanism that preserves:

- Kernel as the sole transaction coordinator;
- exact Windows/service peer authentication and least privilege;
- separation of Kernel and Identity stores;
- durable idempotency, audit and deterministic reconciliation;
- detection of single-store and coordinated rollback;
- governed backup/restore and migration;
- fail-closed startup when continuity cannot be verified.

The existing TPM-bound ADR is retained as a proposed operational profile. Because this host does not satisfy its TPM prerequisite, that profile is not implementable here as written. This decision does not select, approve or imply a replacement freshness authority. Selecting one requires an explicit Owner architecture decision, ADR revision and independent security review.

## Portability and migration

Development artifacts remain source-controlled and reproducible. Mutable runtime state must remain outside source control and explicitly separated from Docker images and rollback-prone application volumes. Migration to another laptop or VPS is a governed operation that verifies deployment identity, generation and audit heads; it must never silently reset or initialize continuity state.

## Preserved gates

`C09_NOT_ACCEPTED != PROJECT_EXECUTION_BLOCKED` remains binding. C09 is OPEN / NOT ACCEPTED. No protected persistence activation, operational IPC acceptance, OI-0002 closure, OI-0003 release, ELSTER transmission, new orchestrator, new scheduler, external service or hardware purchase is authorized by this decision.
