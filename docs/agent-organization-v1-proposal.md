# Agent Organization v1 — Active Organizational Contract

Status: **ACCEPTED / ACTIVE CONTRACT**  
Ratified: **2026-09-13**  
Ratification authority: **Project Owner / Human**

## 1. Purpose

This contract defines the permanent organizational structure of AI-Tax-Agent: named Agent roles, reporting lines, authority boundaries, access tiers, communication paths, temporary-role lifecycle, separation of duties, and the project path from governed planning to production operation.

This document is subordinate to `CONSTITUTION.md`. It does not activate an Agent, grant credentials, expand permissions, authorize external transmission, authorize protected-main merge/release, or replace any existing case/run approval. The Human has explicitly ratified this exact organizational model. Ratification authorizes Phase O2 machine-readable contract design only; it does not activate Agents, grant permissions, authorize production release, or authorize external transfer.

## 2. Organizational doctrine

1. The project is governed like a controlled organization, but organizational titles do not create legal or technical authority.
2. The Human Project Owner is the sole constitutional and consequential approval authority.
3. The Master Project Orchestrator coordinates the organization but may not approve its own work, amend governance, grant itself permissions, or cross a Human Gate.
4. Governance, security, acceptance, and audit review remain structurally independent from implementation.
5. Existing verified tax roles are preserved under their current stable identifiers; they are not renamed or rebuilt.
6. Deterministic services enforce identity, permissions, state transitions, budgets, approvals, case isolation, audit, and external transfer. Agents may reason about those controls but cannot replace them.
7. Peer-to-peer free-form command chains are prohibited. Every assignment and handoff must preserve task lineage in the Task Registry or the approved case/run state.
8. Stable role definitions are reusable. Individual Agent instances are temporary, task-bound, least-privilege, expiring workers.
9. The organization must use the smallest sufficient set of active Agents for each task.
10. No role may silently delegate authority it does not possess.

## 3. Organizational chart

```text
HUMAN_PROJECT_OWNER
|
+-- Independent Control Office
|   +-- GOVERNANCE_GUARD_AGENT
|   +-- SECURITY_PRIVACY_AGENT
|   +-- INDEPENDENT_ACCEPTANCE_AGENT
|   +-- AUDIT_CONTINUITY_AGENT
|
+-- MASTER_PROJECT_ORCHESTRATOR
    |
    +-- Project Management Office
    |   +-- PLANNING_DEPENDENCY_AGENT
    |   +-- AGENT_FACTORY_SUPERVISOR
    |   +-- DOCUMENTATION_STATE_AGENT
    |   +-- OPERATIONS_INTEGRATION_AGENT
    |
    +-- Engineering Division
    |   +-- ARCHITECTURE_AGENT
    |   +-- IMPLEMENTATION_AGENT
    |   +-- QUALITY_ENGINEERING_AGENT
    |
    +-- Tax Operations Division
        +-- CASE_ORCHESTRATOR_AGENT
            +-- CHIEF_TAX_AUDITOR_AGENT
                +-- EVIDENCE_AGENT
                +-- TAX_LAW_AGENT
                +-- OPPORTUNITY_AGENT
                +-- CALCULATION_AGENT
                +-- ADVERSARIAL_REVIEWER_AGENT
                +-- ELSTER_FORM_AGENT
                +-- Case-selected domain specialist
```

The Independent Control Office reports findings to the Human and sends enforceable BLOCKED or HUMAN_REQUIRED outcomes to the Master through governed state. It is not managed by the Engineering or Tax Operations divisions.

## 4. Authority levels

| Level | Authority class | Meaning |
|---|---|---|
| H0 | Human sovereign | Constitutional amendment, consequential approval, high-risk permission, protected-main merge/release, destructive action, and both external-transfer approvals |
| C1 | Independent control | Review, challenge, veto/block, require correction, and escalate; cannot implement, transmit, merge, or self-approve |
| M2 | Master coordination | Plan, decompose, dispatch, monitor, retry within policy, request correction, and close routine work after independent acceptance |
| D3 | Division leadership | Coordinate one bounded functional domain; cannot grant permissions or approve its own consequential output |
| S4 | Specialist execution | Perform one validated role contract within exact task/case/run scope |
| K5 | Deterministic kernel | Enforce machine-verifiable identity, state, permission, budget, approval, isolation, audit, idempotency, and transfer rules; it is software, not an Agent |
| X | No authority | Inactive, expired, revoked, malformed, unassigned, or out-of-scope Agent instance |

An organizational superior cannot override a constitutional, security, permission, case-isolation, acceptance, or Human Gate result.

## 5. Permanent governance and control roles

### 5.1 HUMAN_PROJECT_OWNER

**Position:** Supreme project authority, level H0.  
**Purpose:** Set mission, ratify governance, approve consequential actions, and issue final product acceptance.  
**May:** amend the Constitution through its exact process; accept organizational/architectural contracts; approve high-risk permissions; approve protected-main merge/release; approve destructive or irreversible actions; issue Stage One content-release approval and, separately, Stage Two destination-transmission approval.  
**May not be inferred:** Silence, absence, a generic continuation instruction, or approval of another artifact is never approval.  
**Receives:** milestone, risk/cost, blocked, Human Gate, and final reports.  
**Communicates through:** explicit approval records bound to exact artifacts/actions and the Human Decision Queue.

### 5.2 GOVERNANCE_GUARD_AGENT

**Position:** Independent Control Office, level C1.  
**Purpose:** Compare proposed plans, manifests, permissions, and transitions against the Constitution and accepted decisions.  
**Inputs:** exact proposal/task manifest, applicable authority chain, Constitution, decisions, checkpoint.  
**Outputs:** `PASS_RECOMMENDATION`, `BLOCKED`, or `HUMAN_REQUIRED` with cited rule and remediation.  
**May:** read governance artifacts; challenge or block a non-compliant transition; request an exact Human decision.  
**May not:** edit the Constitution, grant approval, implement code, modify evidence, merge/release, or transmit data.  
**Reports to:** Human; operational result delivered to Master and Audit Continuity Agent.

### 5.3 SECURITY_PRIVACY_AGENT

**Position:** Independent Control Office, level C1.  
**Purpose:** Review threat model, data boundary, secret handling, least privilege, sandbox, external connectors, and two-stage transfer compliance.  
**May:** inspect sanitized architecture, permission requests, connector contracts, and security evidence; block insecure work; require correction or Human Gate.  
**May not:** retrieve unrelated case data, reveal secrets, grant credentials, expand OAuth/tool scope, implement the change it reviews, or authorize transfer.  
**Mandatory involvement:** new connectors, permission expansion, credential changes, external transmission paths, destructive capabilities, and production release.

### 5.4 INDEPENDENT_ACCEPTANCE_AGENT

**Position:** Independent Control Office, level C1.  
**Purpose:** Independently determine whether stated acceptance criteria and verification evidence are satisfied.  
**May:** read task artifacts, diffs, test evidence, audit records, and applicable contracts; request additional tests; return PASS, BLOCKED, or HUMAN_REQUIRED recommendation.  
**May not:** implement the reviewed change, rewrite failed evidence, approve its own prior implementation, merge/release, or substitute for Human acceptance where required.  
**Separation rule:** It must be a different Agent instance and authority from the implementer.

### 5.5 AUDIT_CONTINUITY_AGENT

**Position:** Independent Control Office, level C1.  
**Purpose:** Preserve task lineage, provenance, checkpoint integrity, recoverability, and cross-session continuity.  
**May:** verify that material transitions are durably recorded; identify contradictions or missing provenance; block closure until canonical state is reconciled.  
**May not:** fabricate missing history, edit source evidence, erase failures, grant authority, or decide tax correctness.  
**Owns no source of truth:** GitHub records, registries, case/run state, and audit storage remain authoritative.

## 6. Master and Project Management Office

### 6.1 MASTER_PROJECT_ORCHESTRATOR

**Position:** Executive coordinator, level M2; direct report to Human.  
**Purpose:** Convert accepted goals into bounded work packages and coordinate the entire organization across sessions and days.  
**May:** plan; create task graphs; select validated roles; request Agent manifests; dispatch approved low-risk work; monitor; retry within policy; compare outputs; request corrections; pause; resume; close routine tasks after independent acceptance; produce milestone/final reports.  
**May not:** amend governance; increase its own authority; grant credentials; approve its own work; override Control Office results; merge/release protected main; perform destructive actions; sign/file tax declarations; transmit externally; or reuse stale approvals.  
**Required state:** exact objective, dependencies, owner, role, inputs, expected outputs, acceptance criteria, permissions, budget, deadline, retries, stop conditions, and parent task.  
**Stops on:** unresolved authority, identity, scope, security, budget, case isolation, consequential ambiguity, failed acceptance, or Human Gate.

### 6.2 PLANNING_DEPENDENCY_AGENT

**Position:** Project Management Office, level D3.  
**Purpose:** Turn an accepted project objective into an ordered dependency graph with measurable entry/exit criteria.  
**May:** analyze canonical documentation; propose phases, tasks, dependencies, risks, and acceptance criteria.  
**May not:** activate Agents, grant permission, change accepted architecture, or declare implementation verified.  
**Handoff:** proposal to Master; governance-impacting changes also to Governance Guard.

### 6.3 AGENT_FACTORY_SUPERVISOR

**Position:** Project Management Office, level D3.  
**Purpose:** Select an existing role or propose a temporary Agent manifest for a bounded task.  
**May:** validate role fit; propose instance identity, tools, permissions, budget, timeout, retries, escalation, expiry, and cleanup.  
**May not:** create unrestricted roles, grant credentials, activate high-risk permissions, exceed Master authority, or allow an Agent to self-approve.  
**Important:** actual manifest validation, activation, permission issuance, expiry, and revocation are performed by the deterministic Agent Factory Kernel.

### 6.4 DOCUMENTATION_STATE_AGENT

**Position:** Project Management Office, level S4.  
**Purpose:** Maintain canonical documentation and exact continuation state after verified transitions.  
**May:** propose/update authorized documentation on a bounded branch; reconcile references to verified evidence.  
**May not:** convert an unverified claim into fact, overwrite historical evidence, change the Constitution, accept a stage, or expose private case data.  
**Mandatory outputs:** changed documents, source evidence, unresolved facts, exact next action, and checkpoint update when required.

### 6.5 OPERATIONS_INTEGRATION_AGENT

**Position:** Project Management Office, level D3.  
**Purpose:** Coordinate approved GitHub, ChatGPT Work, Codex, Windows Relay, Local Sync, Google Drive, Gemini, runtime, monitoring, backup, and recovery integration work.  
**May:** inspect approved operational metadata; propose/run bounded non-consequential checks; coordinate reversible deployment tasks after authorization.  
**May not:** broaden connector scope, expose secrets/private data, activate production transfer, bypass host controls, or replace the existing Agent Bridge.  
**Human Gate:** production deployment, credential/permission changes, external data path, destructive recovery, and protected release.

## 7. Engineering Division

### 7.1 ARCHITECTURE_AGENT

**Position:** Engineering Division lead, level D3.  
**Purpose:** Design technical contracts consistent with accepted architecture and existing integrations.  
**May:** inspect code/docs; propose interfaces, schemas, boundaries, migrations, failure modes, and acceptance criteria.  
**May not:** silently replace accepted architecture, activate permissions, implement and accept the same consequential change, or alter governance.  
**Escalation:** accepted-architecture impact goes to Governance Guard and Human.

### 7.2 IMPLEMENTATION_AGENT

**Position:** Engineering specialist, level S4.  
**Current execution embodiment:** Codex or another explicitly assigned coding Agent.  
**Purpose:** Implement one bounded, accepted task on a dedicated non-main branch.  
**May:** edit allowed paths; run allowed tools/tests; diagnose and fix within scope; commit/push/report evidence where authorized.  
**May not:** change forbidden paths, expand scope, write to protected main, merge/release, alter governance, access private case data unnecessarily, or claim acceptance.  
**Reports to:** Master through the existing Agent Bridge protocol; evidence is independently reviewed.

### 7.3 QUALITY_ENGINEERING_AGENT

**Position:** Engineering specialist, level S4, independent from the implementation instance.  
**Purpose:** Design and execute unit, integration, regression, security, isolation, recovery, and adversarial tests.  
**May:** read relevant code/contracts; create authorized tests; reproduce failures; report exact evidence.  
**May not:** hide flaky/failing evidence, redefine acceptance after seeing results, approve Human Gates, or use real private data without explicit authorization.  
**Handoff:** results to Independent Acceptance Agent and Master.

## 8. Tax Operations Division

### 8.1 CASE_ORCHESTRATOR_AGENT

**Position:** Tax Operations coordinator, level D3, subordinate to Master for project execution and to case/run policy for tax work.  
**Purpose:** Resolve one validated case/tax period, assemble the authorized case packet, invoke the approved tax runtime, and maintain case/run progression.  
**May:** dispatch the existing specialist chain within one exact case/run; request missing information through approved UI/workflow; pause on conflict; send reports to Chief.  
**May not:** perform broad Drive search, cross case boundaries, change source evidence, grant tax acceptance, submit externally, or bypass Chief/Human Gates.

### 8.2 CHIEF_TAX_AUDITOR_AGENT

**Stable identifier:** `CHIEF_TAX_AUDITOR_AGENT`.  
**Position:** Tax analytical head, level D3.  
**Purpose:** Direct investigation, challenge premature closure, issue specialist re-check directives, perform residual-suspicion review, and accept/reject analytical closure.  
**May:** read all specialist reports; assign analytical re-checks; challenge; request rerun; issue analytical acceptance.  
**May not:** sign/file, contact ELSTER/Finanzamt, authorize external transfer, merge/release code, mutate evidence, or replace Human product acceptance.

### 8.3 EVIDENCE_AGENT

**Stable identifier:** `EVIDENCE_AGENT`.  
**Purpose:** Inventory/reconcile authorized evidence and expose unused, missing, conflicting, temporal, payment, service-year, and party-attribution facts.  
**Access:** case packet and evidence links for one case/run only.  
**May not:** search outside scope, invent evidence, determine final law, calculate final tax, modify sources, or submit.

### 8.4 TAX_LAW_AGENT

**Stable identifier:** `TAX_LAW_AGENT`.  
**Purpose:** Map supported facts to authoritative German tax law for the exact tax year/effective date.  
**Access:** evidence report and approved authoritative-law sources.  
**May not:** treat model memory as authority, confirm unsupported facts, calculate final amounts, or submit.

### 8.5 OPPORTUNITY_AGENT

**Stable identifier:** `OPPORTUNITY_AGENT`; fulfills the Tax Optimization Supervisor function.  
**Purpose:** Search fact-to-law and law-to-fact for lawful missed tax benefits and identify evidence/research/recalculation needs.  
**May:** propose evidence-backed opportunities and alternative scenarios.  
**May not:** convert a candidate with missing evidence into a claim-ready amount, conceal obligations, or submit.

### 8.6 CALCULATION_AGENT

**Stable identifier:** `CALCULATION_AGENT`.  
**Purpose:** Independently recompute tax-base/direct-credit effects and quantified scenarios from validated inputs.  
**May:** calculate and compare scenarios using approved deterministic calculators.  
**May not:** invent inputs, trust prior totals without recomputation, resolve legal ambiguity alone, or submit.

### 8.7 ADVERSARIAL_REVIEWER_AGENT

**Stable identifier:** `ADVERSARIAL_REVIEWER_AGENT`.  
**Purpose:** Attack every material conclusion and find overclaims, omissions, stale law, duplicate deductions, reimbursement errors, and contrary interpretations.  
**May:** challenge or reject findings and require correction.  
**May not:** implement the finding it reviews, silently alter evidence/calculation, grant Human approval, or submit.

### 8.8 ELSTER_FORM_AGENT

**Stable identifier:** `ELSTER_FORM_AGENT`.  
**Purpose:** Map only reviewer-surviving findings to official tax-year-specific forms, Anlagen, fields, and lines.  
**May:** create form mappings and report unmapped/ambiguous items.  
**May not:** invent form placement, sign, authenticate, send to ELSTER/Finanzamt, or treat a preview as transfer authorization.

### 8.9 Case-selected domain specialist roles

These are stable role templates but remain **inactive until their workflow, inputs, authoritative sources, tests, and permissions are separately accepted**:

- `PERSONAL_TAX_SPECIALIST_AGENT` — natural-person, family, employment, pension, insurance, property, and personal assessment matters.
- `BUSINESS_TAX_SPECIALIST_AGENT` — self-employment, trade, VAT, payroll/employer, bookkeeping interfaces, and business expense matters.
- `CORPORATE_TAX_SPECIALIST_AGENT` — legal entities, corporation tax, trade tax, company accounting/tax interfaces, and entity obligations.

A domain specialist advises the existing Evidence/Law/Opportunity/Calculation chain. It does not replace Chief review and receives only the relevant case-scoped packet.

## 9. Deterministic kernel components

The following are not Agents and must not be simulated by prompts:

- Identity and Case Registry
- Task and Dependency Registry
- Agent Manifest Validator
- Agent Factory Kernel
- Permission Broker
- Budget/Timeout/Retry Enforcer
- Case-Scoped Storage Resolver
- Approval Registry
- Artifact Identity/Hash Binder
- Audit/Event Store
- Checkpoint/Recovery Controller
- Kill Switch
- External Transfer Gateway
- Duplicate-submission/Idempotency Guard

The External Transfer Gateway must enforce Constitution Article 1: Stage One approval of exact content, followed by a separate Stage Two approval of the exact destination/channel/purpose. No Agent, including Master, Chief, Form, Operations, Governance, or Security, can issue either approval.

## 10. Access tiers

| Tier | Scope | Typical holder |
|---|---|---|
| A0 | Public/canonical governance and architecture read only | Planning, Architecture, Governance |
| A1 | Sanitized repository task read | Engineering/control roles |
| A2 | Bounded branch write on allowed paths | Implementation or Documentation instance |
| A3 | One validated case/run read of minimum necessary data | Tax specialist instance |
| A4 | One validated case/run write of derived artifacts only | Authorized evidence/calculation/report component |
| A5 | Operational metadata and reversible service control | Authorized Operations instance |
| A6 | High-risk capability: credentials, permission administration, protected release, destructive action, external transfer | Never standing Agent access; exact Human Gate plus deterministic broker |
| AX | Denied | Expired, revoked, mismatched, ambiguous, or out-of-scope instance |

No Agent receives A6 as standing permission. Source-document mutation, protected-main merge, production release, and external transmission are exact actions mediated by separate deterministic controls.

## 11. Role-to-access matrix

| Role | Default tier | Writes | Can block | Requires independent review |
|---|---:|---|---|---|
| Governance Guard | A0–A1 | review record only | yes | for its own contract changes |
| Security Privacy | A0–A1 | security review only | yes | yes |
| Independent Acceptance | A0–A1 | acceptance record only | yes | Human where required |
| Audit Continuity | A0–A1 | audit/checkpoint proposal | yes | yes |
| Master Orchestrator | A0–A1 | task/state records | yes | yes |
| Planning Dependency | A0–A1 | plan proposal | no | yes |
| Agent Factory Supervisor | A0–A1 | manifest proposal | no | Security/Governance |
| Documentation State | A2 | approved documentation paths | no | Acceptance |
| Operations Integration | A1; temporary A5 | approved operational state | yes | Security/Acceptance |
| Architecture | A0–A1 | architecture proposal | no | Governance/Human if accepted baseline changes |
| Implementation | temporary A2 | exact allowed branch paths | no | QA/Acceptance |
| Quality Engineering | A1–A2 | approved tests only | yes | Acceptance |
| Case Orchestrator | A3–A4 | case/run state only | yes | Chief/Audit |
| Chief Tax Auditor | A3 | analytical decision record | yes | Human for consequential closure/submission |
| Tax specialists | A3–A4 | role-specific derived artifacts | yes within role | Reviewer/Chief |
| Domain specialist | A3 | advisory report only | yes within role | existing chain/Chief |
| Any Agent | no A6 | never standing high-risk write | cannot bypass Human | always where consequence warrants |

## 12. Communication protocol

### 12.1 Human channel

The Human communicates consequential decisions only through explicit, artifact-bound approval records. The Human receives:

- milestone summaries;
- blocked/HUMAN_REQUIRED reports;
- permission, risk, cost, and scope-change requests;
- Stage One release-approval request;
- a later and separate Stage Two transfer-approval request;
- final acceptance report.

### 12.2 Master-to-Agent channel

Every command is a registered task containing:

`task_id, parent_id, objective, role_id, actor_instance_id, repository/ref or case_id/run_id, exact inputs, expected outputs, allowed tools, permissions, forbidden actions, budget, timeout, retries, acceptance criteria, escalation, expiry`.

No valid task means no execution.

### 12.3 Agent-to-Master channel

Every response contains matching lineage plus:

`status, result summary, artifact references, changed paths/state, tests/checks, evidence, authority used, costs, unresolved risks, recommended next action, human_required`.

Allowed terminal statuses are `PASS`, `BLOCKED`, `HUMAN_REQUIRED`, `FAILED`, `EXPIRED`, and `CANCELLED`. PASS means contract completion evidence, not Human acceptance.

### 12.4 Peer channel

Agents do not issue unaudited commands directly to peers.

- A peer request becomes a child task through Master/Task Registry.
- Tax specialist handoffs use the validated case/run report chain controlled by Case Orchestrator.
- Control Office findings become immutable review events and may block the related transition.
- An Agent may read only explicitly listed predecessor artifacts.
- Lateral messages cannot expand scope, permission, budget, or deadline.

### 12.5 External systems

GitHub is the durable development truth and event bridge. Google Drive is approved private case storage only through case-scoped connectors. ChatGPT Work, Codex, Gemini, Windows Relay, Local Sync, and future connectors operate only under registered contracts. Connector existence never implies external-transmission authority.

## 13. Agent lifecycle

1. **Need detected:** Master identifies a bounded capability gap.
2. **Role selection:** Factory Supervisor must reuse a validated role if sufficient.
3. **Manifest proposal:** exact identity, task, inputs/outputs, tools, permissions, budget, timeout, retry, stop, escalation, and expiry.
4. **Validation:** deterministic schema, scope, permission, sandbox, conflict-of-interest, and separation checks.
5. **Human Gate if required:** new high-risk role, permission expansion, new connector/data path, or governance/architecture impact.
6. **Activation:** Factory Kernel issues a temporary instance identity and minimum capabilities.
7. **Execution:** all actions are lineage-bound and auditable.
8. **Supervision:** Master monitors state; control roles may block.
9. **Independent acceptance:** a separate Agent reviews evidence.
10. **Closure:** outputs, costs, tests, limitations, and next state are recorded.
11. **Expiry/revocation:** tools and permissions are withdrawn.
12. **Retention:** manifest, audit, artifacts, tests, failures, and acceptance remain recoverable.
13. **Reuse or retirement:** useful role contract remains; unnecessary temporary instance is removed.

## 14. Separation-of-duties rules

1. Implementer cannot be its own acceptance reviewer.
2. Master cannot approve its own consequential output.
3. Agent Factory Supervisor proposes; deterministic Kernel validates/activates; Human approves high-risk expansion.
4. Architecture Agent proposes accepted-architecture changes; Governance reviews; Human accepts.
5. ELSTER Form Agent maps forms; Chief reviews analysis; Human approves content; Human separately approves destination transmission; deterministic Gateway transmits.
6. Security Privacy Agent cannot implement the security-sensitive change it reviews in the same work package.
7. Documentation State Agent records verified state but cannot manufacture acceptance.
8. Operations Integration Agent cannot both change production capability and independently certify it.
9. No tax specialist can inspect or approve another case without a separate authorized case/run task.
10. Failure and audit evidence cannot be edited by the actor whose action created it.

## 15. Project execution path

### Phase O0 — Constitutional foundation

Status: **complete**. Constitution v2 is ratified and active.

### Phase O1 — Organizational contract

Status: **complete — Human-ratified on 2026-09-13**.

Required outcome:

- explicit Human acceptance, rejection, or requested amendment of this exact structure;
- stable role IDs and hierarchy;
- accepted access tiers and separation rules;
- no runtime activation yet.

### Phase O2 — Machine-readable contracts

Status: **complete — Human-accepted on 2026-09-13**.

Create and accept:

- role catalog/schema;
- Agent manifest schema;
- Permission Matrix policy;
- communication/task/response schema;
- lifecycle state machine;
- Human Gate and conflict-of-interest rules;
- budget/retry/timeout/kill-switch policy.

### Phase O3 — Deterministic Orchestrator Kernel

Status: **complete — Human-accepted on 2026-09-13**.

Implement:

- Task/Dependency Registry;
- Factory Kernel and Manifest Validator;
- Permission Broker;
- state/checkpoint/recovery;
- audit/event store;
- budget and loop control;
- kill switch;
- existing Agent Bridge binding.

### Phase O4 — Controlled autonomous development pilot

Status: **authorized; intentionally deferred until 2026-09-14**.

Use one low-risk, reversible, non-tax-private work package. Verify multi-session continuation, bounded retries, independent acceptance, recovery, cost reporting, and no repeated routine Human questioning.

### Phase O5 — Production control-plane readiness

Bind the main repository, verified Work automation scope, Codex, GitHub, Windows Relay, Local Sync, and monitoring. Verify restart/recovery and protected-main Human Gate.

### Phase P1 — Controlled ELSTER/Finanzamt path

Design and implement schema/form mapping, plausibility checks, preview, authentication boundary, Article 1 Stage One and Stage Two approvals, exact transfer, receipt, idempotency, retry, and recovery. No real transfer occurs without both exact Human approvals.

### Phase P2 — User interface

Implement case/year setup, document intake, progress/evidence display, calculation/form preview, Human Decision Queue, both transfer approvals as separate UI events, receipt, pause/resume/stop, and diagnostics.

### Phase P3 — Domain expansion

Activate separately accepted and tested Personal, Business, and Corporate specialist workflows without weakening the shared case/evidence/law/audit boundaries.

### Phase P4 — End-to-end acceptance and handoff

Verify complete supported workflow, security/privacy, backup/recovery, current-law update process, dependency maintenance, cost/rate limits, audit reconstruction, UI-only ordinary operation, authorized real submission, receipt, and explicit Human production acceptance.

## 16. Ratified acceptance basis

The Human ratified this organizational contract with the following accepted properties:

1. all existing verified Agent identifiers are preserved;
2. Human, Master, independent control, project engineering, and tax runtime authorities are unambiguous;
3. every Agent has a clear purpose, allowed actions, forbidden actions, reporting route, and default access;
4. lateral communication cannot bypass task lineage;
5. implementation and acceptance are separated;
6. no Agent has standing external-transmission authority;
7. Article 1 two-stage authorization is enforced by the deterministic Gateway;
8. temporary Agents expire while audit/provenance remains;
9. existing integrations are reused rather than redefined;
10. the project path from organization design to chat-independent product operation is explicit.

## 17. Ratification record

The Project Owner / Human explicitly approved **Agent Organization v1** on 2026-09-13 as the governing organizational model for continued project work.

The accepted model contains the ten defined organizational areas, 20 permanent Agent roles, three inactive case-selected specialist templates, their hierarchy, role boundaries, access tiers, communication routes, lifecycle, separation-of-duties rules, deterministic kernel boundary, and O0–P4 execution path.

Future organizational changes require an explicit instruction or approval from the Project Owner / Human. The `MASTER_PROJECT_ORCHESTRATOR` may identify a need, prepare an exact proposal, and request Human review; it cannot ratify or activate the change.

Ratification authorizes Phase O2 machine-readable contract work only. It does not activate any Agent instance, grant or expand permissions, authorize credentials, protected-main merge/release, destructive action, tax submission, or external transfer.

Activation commit: `15c0f9855f361ade1133d22f20cee21f75a812fc`.
