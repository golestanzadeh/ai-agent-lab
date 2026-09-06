# Person / Entity Registry Model

## Status

Foundational model. Implementation is not yet complete.

## Purpose

The Person/Entity Registry provides persistent identity for natural persons and legal entities across tax periods. It prevents the system from treating each tax-year case as a new person/entity and provides the controlled starting point for cross-year case retrieval.

The registry is an identity and lookup layer. It is not a tax-data warehouse and does not replace source documents, evidence, or case state.

## 1. Core identity model

```text
Person / Entity
      ↓
persistent person_id / entity_id
      ↓
zero or more tax cases
      ↓
case_id + tax_period
```

A persistent identity may therefore be associated with many cases:

```text
PERSON-00042
├── 2020 → CASE-2020-0001
├── 2021 → CASE-2021-0007
├── 2022 → CASE-2022-0011
└── ...
```

The persistent identity must not change merely because the tax year changes.

## 2. Separate Person and Entity concepts

The model distinguishes:

- `PERSON`: natural person;
- `ENTITY`: legal entity or other supported non-natural taxpayer/entity.

A natural person receives a `person_id`.

A legal entity receives an `entity_id`.

The two namespaces must not be silently mixed. If a future domain model needs a common subject abstraction, it must preserve the underlying type and identifier.

## 3. Minimum registry record

### PersonRecord

```text
person_id                 required, immutable, unique
record_type               PERSON
status                    required
preferred_display_name    optional
created_at                required
updated_at                required
schema_version            required
```

### EntityRecord

```text
entity_id                 required, immutable, unique
record_type               ENTITY
status                    required
preferred_display_name    optional
created_at                required
updated_at                required
schema_version            required
```

`preferred_display_name` is for controlled human-facing discovery only. It is not the authoritative identity.

## 4. Identity and lookup attributes

Names and other identifying attributes are stored as lookup information, not as the primary identity.

Future extensible lookup attributes may include:

```text
legal_name / full_name
name_variants
address_history_reference
approved tax-identifier references
other verified identity references
```

Sensitive identifiers must only be stored where legally and technically appropriate. They must not be exposed in logs, GitHub documentation, or unrestricted Agent context.

The model must support changes over time. A changed name or address must not create a new persistent identity when evidence establishes continuity.

## 5. Identity confidence and resolution

Identity resolution must distinguish between:

```text
CONFIRMED
CANDIDATE
UNRESOLVED
```

A registry entry may be created only when the system has sufficient evidence for the identity decision required by the workflow. A weak name match must never silently create or merge identities.

Potential identity matches must be resolved using multiple appropriate signals and explicit evidence. Filename similarity alone is insufficient for a material identity decision.

Contradictory identity evidence must enter an explicit unresolved/escalation path.

## 6. Case mapping

The Person/Entity Registry does not duplicate the complete Case Registry record. It maintains the persistent identity-to-case relationship.

Conceptually:

```text
PERSON-00042
   │
   ├── CASE-2024-0003
   ├── CASE-2025-0012
   └── CASE-2026-0004
```

The Case Registry remains authoritative for the case itself, including tax period, case type, lifecycle state, and exact case-folder scope.

The relationship is therefore:

```text
Person/Entity Registry
        ↓
persistent identity → case IDs
        ↓
Case Registry
        ↓
exact case scope
```

## 7. Cross-year retrieval

A request such as "show all cases for this person from 2020 to 2026" must follow this sequence:

```text
identity lookup
      ↓
validated person_id / entity_id
      ↓
Case Registry lookup for requested periods
      ↓
resolved case_ids
      ↓
individual case-scoped access
```

The system must not search all Drive documents and infer which documents belong to the person.

Cross-year reporting is therefore a controlled multi-case operation, not a bypass of case isolation.

## 8. Relationships to other people/entities

The registry identifies persistent subjects. Relationships such as spouse, child, employer, representative, or related entity belong to the appropriate case/domain model unless they are required as persistent identity relationships.

In particular, the Person/Entity Registry must not become a dumping ground for tax-year-specific household facts. Those facts belong to case-scoped state and the Case Party / Household Context.

## 9. Lifecycle status

The registry needs a small explicit lifecycle vocabulary. Initial values:

```text
ACTIVE
INACTIVE
ARCHIVED
UNRESOLVED
```

`ARCHIVED` means the identity record is retained for historical reference and must not be treated as an active current identity without appropriate validation.

Status changes are auditable.

## 10. Security and isolation

The registry may be used to resolve identity and case relationships, but resolving a person/entity does not grant unrestricted access to all associated case data.

Access remains:

```text
persistent identity
      ↓
resolved case_id
      ↓
case-scoped authorization
      ↓
exact case data
```

An Agent must never receive unrestricted access to all cases merely because they share one `person_id` or `entity_id`.

## 11. Provenance and auditability

Material identity creation, merge, split, correction, status change, and case association decisions must be auditable.

The system should retain references to the evidence supporting identity decisions without unnecessarily duplicating sensitive source content.

Identity changes must preserve history rather than silently overwriting the previous state.

## 12. Deliberately deferred details

The following are intentionally not finalized in this step:

- physical storage format (JSON, database, etc.);
- exact sensitive tax-identifier fields;
- identity matching algorithm;
- merge/split algorithm;
- full relationship graph;
- user authentication/authorization model;
- Person/Entity Registry runtime API;
- migration of existing CASE-001 data.

Those decisions belong to later implementation steps and must not be invented here.

## 13. Acceptance criteria

The model is considered structurally adequate when:

1. a natural person can retain one persistent identity across multiple tax periods;
2. a legal entity can retain one persistent identity across multiple tax periods;
3. identities are distinct from case IDs;
4. cases are resolved through the Case Registry rather than inferred from Drive;
5. identity ambiguity can be represented explicitly;
6. sensitive lookup data is controlled and not treated as folder identity;
7. historical identity changes are auditable;
8. cross-year retrieval resolves cases individually and preserves case isolation;
9. the model can grow without redesigning CASE-001-specific assumptions.
