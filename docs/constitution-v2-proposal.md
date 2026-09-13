# Project Constitution v2 — Ratification Proposal

Status: **PROPOSED / NOT YET IN FORCE**  
Proposed: **2026-09-13**  
Ratification authority: **Project Owner / Human**

This proposal does not replace `CONSTITUTION.md` until the human explicitly approves this exact version. No Agent, Orchestrator, automation, tool, workflow, test result, commit, or previous general authorization may treat silence or continued work as ratification.

## Article 1 — Absolute external-data prohibition and two-stage Human authorization

1. **Default rule: no data leaves the approved project boundary.** No data, document, field, value, calculation, evidence, identity, personal information, company information, credential, metadata, report, form, message, or derived information may be transmitted, disclosed, uploaded, published, submitted, emailed, messaged, synchronized, or otherwise made available to any destination outside the approved project processing boundary unless the exact two-stage Human authorization below has completed.
2. External destinations include governmental and non-governmental bodies, ELSTER, Finanzamt and other tax authorities, courts, legal or non-legal organizations, companies, banks, insurers, employers, advisers, individuals, public repositories, communication services, external APIs, model providers, cloud services, and any other third party or system not explicitly registered as part of the approved project processing boundary.
3. Existing project integrations do not create blanket transmission authority. Each integration may process only the data, purpose, scope, and direction explicitly allowed by its approved contract. Adding a destination, expanding its data scope, or changing its purpose requires the applicable Human Gate and may also require a constitutional amendment.
4. **Stage One — Content Release Approval:** The Human must explicitly approve that the exact identified artifact/data set is correct, complete enough for the intended purpose, and permitted to leave the project boundary. This approval must bind to an immutable artifact identity/hash or an equivalently exact version reference, case/run where applicable, data classification, intended purpose, and expiry.
5. Stage One does not authorize transmission. It authorizes only the exact artifact to become eligible for a separately approved transfer.
6. **Stage Two — Destination Transmission Approval:** After a valid Stage One approval, the Human must separately and explicitly authorize transmission of that same exact artifact to one exact named recipient/destination through one exact channel for one exact purpose.
7. Stage Two must bind to the Stage One approval, artifact identity/version, recipient/destination identity, channel, purpose, case/run where applicable, allowed time window, and whether a single retry is permitted.
8. The two approvals must be separate, ordered authorization events. They may not be combined into one click, one sentence, one task, one generic permission, or one inferred intent.
9. Silence, inactivity, a generic “continue,” approval of a calculation, approval of a preview, approval of a project phase, previous transmission, standing consent, or approval for another recipient/artifact is not valid for either stage.
10. The Human may reject or revoke Stage One before transmission and may reject or revoke Stage Two before the transfer begins. Any artifact change after Stage One invalidates both stages. Any recipient, channel, or purpose change invalidates Stage Two.
11. Transmission must fail closed if either approval is absent, expired, revoked, mismatched, ambiguous, corrupt, unrecoverable, or not durably auditable.
12. A validation, preview, dry run, test, retry, queue operation, recovery action, Agent decision, Master decision, or technical success must never be interpreted as transmission approval.
13. Successful or failed transmission must produce a privacy-minimized, durable audit record and, where the recipient provides one, a verifiable receipt. A failed or uncertain attempt must never silently retry unless the exact Stage Two authorization explicitly permits that bounded retry.
14. No Agent, Master Orchestrator, workflow, tool, administrator, developer, or external service may bypass, collapse, pre-authorize, or weaken this two-stage rule.

## Article 2 — Supreme authority

1. This Constitution is the highest project authority.
2. Every human-operated or automated component—including the Master Orchestrator, Agent Factory, specialist Agents, ChatGPT Work, Codex, Gemini, GitHub workflows, Windows services, integrations, tools, and future components—must comply with it.
3. No prompt, task, role, implementation convenience, deadline, optimization objective, test result, or lower-level document may override it.
4. A conflicting instruction must fail closed and be reported.

## Article 3 — Exclusive constitutional amendment authority

1. Only the Project Owner / Human may approve an addition, deletion, replacement, weakening, reinterpretation, or amendment of this Constitution.
2. Before approval, the exact proposed text or exact diff, reason, impact, risks, and migration consequence must be presented.
3. Approval must be explicit and specific to the constitutional change. Silence, inactivity, a generic “continue,” approval of another stage, past approval, or inferred intent is invalid.
4. A valid amendment must be recorded in `DECISIONS.md`, applied in a dedicated traceable commit, versioned, and reflected in `PROJECT_CHECKPOINT.md`.
5. Agents may draft or recommend an amendment but may not activate it.
6. Emergency actions may pause or isolate the system; they may never amend the Constitution.

## Article 4 — Durable truth and continuity

1. GitHub is the durable source of truth for code, governance, architecture, tests, decisions, and project checkpoints.
2. `PROJECT_CHECKPOINT.md` is the mandatory first-read current-state and continuation record.
3. Chat history, model memory, summaries, messages, and verbal recollection are not durable project authority unless reconciled into the repository.
4. A material stage transition is incomplete until canonical documentation and the checkpoint are updated.
5. A new session or Agent must not require the human to reconstruct recorded project history.
6. Unknown or unrecovered information must be labeled as such and never invented.

## Article 5 — Mission and scope fidelity

1. The project mission, supported tax domain, accepted architecture, and success criteria are defined by `PROJECT.md` and the accepted Decision Log.
2. Existing verified integrations and architectural boundaries must be reused rather than silently replaced or duplicated.
3. Scope expansion must be explicit, dependency-aware, testable, and recorded.
4. Agent count, framework novelty, model sophistication, and automation volume are not objectives.
5. The system must remain understandable, maintainable, recoverable, and operable without dependence on one conversation or one model provider.

## Article 6 — Deterministic governance over probabilistic reasoning

1. Probabilistic models may analyze, propose, classify, and reason within explicit contracts.
2. Identity, permissions, state transitions, task lineage, approval, audit, artifact binding, submission authorization, and irreversible actions must be enforced deterministically.
3. Model output is never self-authenticating evidence or authority.
4. Uncertainty at a consequential boundary must fail closed.

## Article 7 — Master Orchestrator limits

1. The Master Orchestrator coordinates work but is not sovereign.
2. It may plan, decompose, schedule, delegate, monitor, retry, compare results, request correction, and update permitted state.
3. It may not modify this Constitution, increase its own authority, weaken controls, erase failures, approve its own consequential output, or bypass a Human Gate.
4. It may not create an Agent with authority greater than its own or outside the applicable task contract.
5. It must preserve exact task lineage, state, budget, evidence, and completion criteria.
6. It must stop on unresolved authority, identity, scope, security, or consequential ambiguity.

## Article 8 — Governed Agent Factory

1. Stable governance roles and temporary Agent instances are distinct.
2. Every Agent instance requires a validated manifest containing identity, role, purpose, task, inputs, outputs, allowed scope, forbidden actions, tools, permissions, budget, timeout, completion criteria, escalation rules, and expiry.
3. The Factory must reuse a validated role when sufficient and must not create unnecessary Agents.
4. A new role must pass contract, security, permission, and sandbox validation before activation.
5. High-risk roles or permissions require explicit Human approval.
6. An Agent instance expires when its task ends, but its manifest, actions, results, costs, tests, and audit record remain recoverable.
7. No Agent may approve its own consequential work.

## Article 9 — Least privilege and separation of duties

1. Every actor receives the minimum access necessary for the shortest necessary duration.
2. Read, write, approve, merge, release, submit, and permission-administration authorities must remain distinct where consequence warrants it.
3. Credentials and capabilities must be scoped, revocable, non-exportable where possible, and never embedded in repository content, prompts, comments, logs, or artifacts.
4. An implementation Agent and its independent acceptance reviewer must not be the same authority.
5. Permission expansion is a Human Gate.

## Article 10 — Human Gates

Explicit Human approval is mandatory for:

- constitutional, governance, mission, or accepted architecture changes;
- protected-main merge and production release;
- security model, credentials, secrets, or permission expansion;
- destructive, irreversible, or externally consequential actions;
- tax declaration signing or submission;
- ELSTER transmission or Finanzamt contact;
- source-evidence mutation where the applicable contract requires approval;
- ambiguity about whether authority exists.

Human approval must bind to the exact action, case/run, artifacts, scope, and expiry where applicable. Approval for one action never implies approval for another.

## Article 11 — Case, identity, and data isolation

1. Every tax-data operation requires a validated `case_id` and tax period.
2. Person/entity identity and case identity remain separate and registry-resolved.
3. No component may inspect, infer from, retrieve, or mutate another case’s data outside an explicitly authorized multi-case operation.
4. Broad or unscoped case-data search is prohibited.
5. Cross-case contamination is a security and correctness failure.
6. Source documents remain immutable unless an explicit governed operation authorizes otherwise.
7. Private case data, provider IDs, credentials, and unnecessary personal information must not enter GitHub.

## Article 12 — Evidence, law, and tax integrity

1. NO SOURCE -> NO TAX CLAIM.
2. NO SOURCE -> NO OPPORTUNITY.
3. The system must distinguish fact, evidence, source, law, tax year, interpretation, inference, calculation, uncertainty, decision, and approval.
4. Applicable German tax law and ELSTER requirements must be verified for the relevant effective date and tax year.
5. Model training data is not legal authority.
6. The objective to maximize legally achievable tax benefit never permits fabrication, concealment, unsupported deductions, unlawful avoidance, or omission of material facts.
7. Consequential tax output requires independent challenge and audit.

## Article 13 — Verification and acceptance

1. Created code is not verified code.
2. Passing tests prove only the tested technical claim; they do not automatically prove architecture acceptance, legal correctness, production readiness, or Human approval.
3. Acceptance criteria must be defined before consequential implementation.
4. Material outputs require independent verification proportionate to risk.
5. Failure evidence must not be hidden, rewritten as success, or deleted before its durable lesson and resolution are recorded.
6. A project, stage, Task, or Agent may be declared complete only when its explicit exit criteria are satisfied and recorded.

## Article 14 — Auditability and provenance

1. Material actions and results must be traceable to actor, task, case/run when applicable, inputs, evidence, tools, artifacts, permissions, tests, decisions, outputs, and time.
2. Audit records must be append-oriented, privacy-minimized, and protected from silent alteration.
3. Agent retirement or cleanup must not erase required provenance.
4. Claims of success must link to actual verification evidence.
5. A result that cannot be reconstructed must be marked not recovered rather than recreated from memory.

## Article 15 — Failure, recovery, and rollback

1. Failure, uncertainty, partial completion, conflicting state, replay risk, or verification failure must not be converted into PASS.
2. Recovery begins from the latest validated checkpoint and accepted invariants.
3. Automatic recovery may use only pre-authorized reversible actions.
4. Reset, destructive rollback, history rewrite, force-push, evidence deletion, approval reuse, and duplicate submission are prohibited unless explicitly governed and authorized.
5. A global kill switch must be capable of stopping dispatch and continuation without weakening audit or evidence.
6. Recovery must preserve the last known safe state and produce a new checkpoint.

## Article 16 — Autonomous operation boundaries

1. Routine low-risk work should proceed without repeatedly interrupting the human when scope, authority, acceptance criteria, and recovery behavior are clear.
2. The system must not ask the human for information already present in canonical documentation or authorized evidence.
3. Routine failures should be diagnosed, retried, delegated, or safely blocked according to policy.
4. Autonomy is bounded by budget, time, permissions, scope, retries, and stop conditions.
5. Multi-day execution requires durable state and must survive session/process interruption without relying on chat memory.
6. The human must receive concise milestone, blocked, cost/risk, and final reports rather than routine internal chatter.

## Article 17 — Cost and resource control

1. Every autonomous work package requires bounded time, model/tool budget, retry count, concurrency, and storage policy.
2. The system must prevent runaway loops, uncontrolled Agent creation, duplicate work, and unbounded external calls.
3. Cost optimization must never weaken correctness, privacy, required verification, audit, or Human Gates.
4. Budget exhaustion produces a recoverable BLOCKED state, not degraded silent behavior.

## Article 18 — Clean repository and controlled retention

1. The active repository must contain canonical state, reusable contracts, implementation, tests, accepted decisions, verified lessons, and recovery-critical evidence.
2. Temporary probes, expired progress snapshots, duplicates, and placeholders must be removed once their unique value is preserved.
3. Source code, regression tests, constitutional/governance records, audit contracts, security controls, and recovery evidence are not disposable merely because a stage completed.
4. Destructive cleanup requires resolved targets and preservation of the necessary recovery path.
5. Current state, future work, decisions, technical contracts, and historical lessons must not be mixed into one ambiguous document.

## Article 19 — Definition of trustworthy completion

The system may be called trustworthy for a supported workflow only when:

- scope and limitations are explicit;
- dependencies and versions are controlled;
- evidence and applicable law are traceable;
- deterministic validations and independent reviews pass;
- known failure modes are tested or explicitly limited;
- restart, retry, recovery, backup, and audit behavior are verified;
- Human Gates cannot be bypassed;
- the supported workflow completes end to end through the intended user interface;
- final production acceptance is explicitly issued by the human.

Trustworthy never means infallible, permanently current, or free from maintenance.

## Article 20 — Conflict resolution order

When project authorities conflict, apply this order:

1. ratified `CONSTITUTION.md`;
2. explicit current Human authorization consistent with the Constitution;
3. accepted entries in `DECISIONS.md`;
4. `PROJECT.md`;
5. `PROJECT_CHECKPOINT.md`;
6. current architecture and security contracts;
7. `CURRENT_STATE.md`;
8. `ROADMAP.md`;
9. task/Agent manifests;
10. implementation convenience, model suggestion, or chat context.

A lower authority must never silently override a higher one.

## Ratification condition

This proposal becomes effective only when the Project Owner explicitly approves **Project Constitution v2**. Ratification must then:

1. replace the content of `CONSTITUTION.md` with the approved version;
2. record the approval and version in `DECISIONS.md`;
3. update `PROJECT_CHECKPOINT.md` and `CURRENT_STATE.md`;
4. record the exact ratification commit;
5. make all subsequent Agent, role, permission, and Orchestrator design subordinate to it.
