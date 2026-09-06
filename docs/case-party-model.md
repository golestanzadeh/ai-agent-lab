# Case Party and Tax-Family Model

## Status

**Approved architectural requirement — Phase 10**

This document defines how the system identifies the people and relationships that participate in a tax case. It is a foundational requirement for document attribution, fact extraction, calculation, optimization, reconciliation, and final-form generation.

## 1. Core principle

A tax case must never be modeled as if it automatically belongs to one unnamed taxpayer.

Before substantive tax analysis begins, the system must establish a **Case Party Model** containing the relevant natural persons, their relationships, their role in the case, and the tax-year-specific facts that affect the workflow.

The system must distinguish:

- the person for whom a fact is true;
- the person to whom a document belongs;
- the person who incurred or paid an expense;
- the person who received income;
- the person to whom a tax attribute applies;
- the person to whom a deduction, allowance, benefit, or obligation may legally be attributed;
- the person represented by a document or form;
- the person who is the primary taxpayer/case owner;
- the spouse/partner and children participating in the case.

These relationships must never be inferred solely from filenames or document position.

## 2. Case-level questions required before analysis

For a natural-person income-tax case, the intake layer must determine or explicitly mark unknown:

1. Who is the primary taxpayer/case owner?
2. What tax year/assessment period is being analyzed?
3. Is the taxpayer single, married, widowed, divorced, separated, or otherwise in a relevant family-status situation during the tax year?
4. If married/registered partnership applies, who is the spouse/partner?
5. Did the spouses/partners live together during the relevant period, and were there periods of permanent separation?
6. Is the filing intended as **Zusammenveranlagung** or **Einzelveranlagung**, where legally applicable?
7. If joint/individual assessment is relevant, what filing structure follows from that choice?
8. What were the relevant Steuerklasse/ELStAM values for each employed person and during which periods?
9. Are there children relevant to the case? For each child, what relationship, residence/household facts, age, education/training, and other tax-relevant facts apply?
10. Which income, expenses, benefits, insurance contributions, donations, services, and other facts belong to which person?
11. Which expenses were personally borne, jointly borne, reimbursed, or paid from a shared account?
12. Which documents refer to more than one person?
13. Which facts are shared household facts versus person-specific facts?
14. Are any relevant facts changing during the tax year?

If a material answer is unavailable, the case must enter an explicit **missing/uncertain fact** state rather than silently assuming a default.

## 3. Tax class versus tax assessment

The system must store Steuerklasse/ELStAM because it is tax-relevant case evidence and can affect wage-tax withholding, mandatory-filing conditions, and interpretation of payroll documents.

However, the system must **not model Steuerklasse as the final income-tax calculation itself**. German income-tax assessment determines the tax liability from the tax case and credits tax already withheld/paid. Steuerklasse is primarily an employment wage-tax withholding characteristic.

Therefore the case model must keep these concepts separate:

```text
ELStAM / Steuerklasse
        ↓
Wage-tax withholding evidence
        ↓
Lohnsteuer actually withheld
        ↓
Income-tax assessment calculation
        ↓
Final tax / refund / payment difference
```

For married couples, the system must capture the tax class of **each spouse individually**, including relevant changes during the tax year. It must never infer the spouse's class from the primary taxpayer's class.

The legal applicability of the tax class and its consequences must always be evaluated for the relevant tax year and facts.

## 4. Assessment mode

For spouses/registered partners, the case must explicitly represent the assessment mode where legally applicable:

- `JOINT_ASSESSMENT` / Zusammenveranlagung
- `INDIVIDUAL_ASSESSMENT` / Einzelveranlagung
- `NOT_APPLICABLE`
- `UNKNOWN_PENDING_VERIFICATION`

The system must not choose a filing mode merely because one mode appears more favorable. It must first establish legal eligibility and then compare lawful alternatives when optimization requires it.

Under individual assessment, person-specific ownership and economic burden of relevant expenses become particularly important. Shared payments must therefore retain allocation evidence rather than being automatically assigned to the primary taxpayer.

## 5. Party roles

The minimum conceptual party roles are:

- `PRIMARY_TAXPAYER`
- `SPOUSE_OR_PARTNER`
- `CHILD`
- `OTHER_DEPENDENT_OR_RELEVANT_PERSON`
- `DOCUMENT_ISSUER`
- `EMPLOYER`
- `INSURER`
- `DONATION_RECIPIENT`
- `SERVICE_PROVIDER`
- `TAX_AUTHORITY_CONTACT`

A person may have more than one role in a case. Organizations are represented separately from natural-person parties.

## 6. Document-to-party attribution

Every extracted document and every material extracted fact must support party attribution.

The attribution process must consider, where available:

- document title and filename;
- names and addresses appearing in the document;
- tax identification references where appropriate;
- employer information;
- insured-person information;
- invoice recipient/customer information;
- bank/payment information when relevant and permitted;
- dates and tax period;
- form-specific person fields;
- explicit relationships stated in the document;
- cross-document consistency.

A document may legitimately relate to:

- one person;
- multiple people;
- the household/family as a shared context;
- a third party but support a taxpayer's claim.

Therefore the data model must support **one-to-many and many-to-many document/fact/party relationships**.

## 7. Attribution confidence and ambiguity

Party attribution is an evidence problem, not a filename classification problem.

Each material attribution must carry:

- attributed party/parties;
- relationship/role;
- evidence references;
- attribution method;
- confidence/status;
- unresolved alternatives, if any.

Example statuses:

- `CONFIRMED`
- `SUPPORTED`
- `AMBIGUOUS`
- `CONTRADICTED`
- `UNRESOLVED`

An ambiguous or contradicted attribution that could affect tax treatment must block the affected calculation until resolved or explicitly approved under the project's uncertainty policy.

## 8. Shared household facts versus individual facts

The system must distinguish at least:

### Person-specific

- salary and employment
- Lohnsteuerbescheinigung
- personally borne insurance contributions
- personally incurred professional expenses
- individual income
- individual tax withholding
- individual memberships/contributions

### Shared / household-level

- common residence
- household services
- some utility/ancillary-cost documents
- shared contracts
- jointly paid expenses
- family relationships
- children living in the household

A shared fact must not automatically become a 50/50 fact. Allocation depends on the applicable tax rule and actual economic burden/evidence.

## 9. Children

Children must be represented as first-class case parties when relevant.

The model must support at least:

- identity/reference;
- relationship to each parent;
- date of birth/age where relevant;
- residence/household information;
- tax-year-specific status;
- education/training where relevant;
- Kindergeld/child-benefit context;
- Kinderfreibetrag-related facts;
- childcare costs;
- school fees where applicable;
- other child-related expenses or benefits;
- evidence supporting each material child-related claim.

The system must not assume that every person named in a family document is a taxpayer or that every child-related expense belongs to the primary taxpayer.

## 10. Temporal model

Party relationships and tax attributes are tax-year/time dependent.

The case state must therefore support effective intervals for facts such as:

- marital status;
- permanent separation;
- tax class;
- employment;
- residence;
- child household membership;
- education/training;
- insurance coverage;
- other material status changes.

A document from one date must not automatically establish that the same fact held for the entire tax year.

## 11. Required downstream behavior

No substantive calculation, optimization, or final-form generation may proceed until the relevant party attribution is sufficiently established for the affected data.

The workflow must be able to return to party resolution when later evidence reveals:

- an unknown spouse/child;
- an incorrect document owner;
- a shared expense incorrectly assigned to one person;
- a changed tax class;
- a changed family status;
- conflicting identity information;
- a document belonging to another person or tax year.

This makes party resolution a **foundational case-state capability**, not a one-time intake questionnaire.

## 12. Authoritative grounding

German official sources distinguish ELStAM/Steuerklasse from the broader income-tax assessment and provide specific rules for spouses, children, and individual versus joint assessment. The implementation must use current authoritative sources for the relevant tax year rather than hard-code legal assumptions.

Relevant official references include ELSTER guidance on individual/joint assessment and child information, and the Federal Ministry of Finance's official § 38b material on wage-tax classes and child allowances.

## 13. Architectural consequence

The system requires a dedicated **Case Party / Household Context layer** before or alongside document inventory and fact extraction:

```text
Case Creation
     ↓
Party / Household Context
     ↓
Document Inventory
     ↓
Document → Party Attribution
     ↓
Evidence / Fact Extraction
     ↓
Reconciliation
     ↓
Tax Analysis / Optimization
```

This layer may initially be implemented as deterministic data structures plus controlled extraction/validation logic. It is not automatically an Agent.

## 14. Security and privacy

Party identity information is highly sensitive. The repository must contain only the abstract model, schemas, tests, and synthetic examples. Real names, tax IDs, addresses, bank details, or family documents remain in private case storage and must never be committed to the public GitHub repository.
