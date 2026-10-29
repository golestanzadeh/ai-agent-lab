# UI-03 Kernel-authorized Gemini execution and acceptance evidence

## Current verified outcome — 2026-10-30

PARTIAL_REAL_EXECUTION / INDEPENDENT_IMPLEMENTATION_PASS / SUCCESSOR_AUTHORITY_PENDING.
This current section supersedes the historical stop/candidate statuses below for
the bounded final directive only. Full UI-03 is not COMPLETE.

Separate reviewer /root/ui03_independent_security_review returned
INDEPENDENT_PASS / BOUNDED_IMPLEMENTATION_ONLY on exact corrected implementation
7cfa3fafea5ce93c1e7cdeb7f5af03a8f2c6ec2b. Review took place in an isolated exact
commit export at a temporary directory; no implementation edits, real-data/API,
service or credential access by that reviewer. F01/F02/F03 are independently
CLOSED. Exact focused command (existing venv, PYTHONPATH=src):

    python -m pytest tests/unit/test_case_analysis_kernel_dispatch.py tests/unit/test_case_analysis_executor.py tests/unit/test_document_extraction.py tests/unit/test_gemini_extraction_validation.py tests/unit/test_orchestrator_kernel.py tests/unit/test_runtime_activation.py tests/unit/test_ui03_gemini_authority_boundary.py -q --tb=short

Independent result73 passed,0 failed,0 skipped, exit0,39.88s. Separate command
python -m pytest tests/unit/test_case_analysis_routes.py -q --tb=short passed1,
exit0,9.33s. Independent adversarial outcomes: original cross-case response
substitution rejected; two-instance race5/5 secure; active one-second task after
1.2s denied; Kill Switch during a blocked fake provider call published no result,
dispatched no next document and retained uncertain intent/audit without replay.
The existing Starlette/httpx warning is non-failing. These tests are synthetic
implementation evidence, not independent observation of the real campaign.

Real Owner-runtime verification by the implementing worker:

- Actual scoped inventory5 PDF/1 CSV.4 PDFs produced43 candidate fields
  (14/10/10/9), each with document digest, filename/model, task/manifest/run,
  timestamps, structured extraction, evidence/page references and review status
  committed to existing Kernel SQLite responses/audit.1 PDF has the preserved
  parser-dependency failure; no successful extraction is claimed for it. CSV
  remains unsupported by this PDF tool and was not transmitted.
- Actual browser button initiated the successful bounded run, not a direct SDK
  shortcut. Browser DOM showed43 result rows/five document statuses, review
  warnings and Persian rtl/German ltr, retained across refresh/language switch.
- After actual application-process restart, all document result objects were
  byte-equivalent to the protected pre-restart readback:4 complete candidates,
  one failure. No running external call was killed during this operational test.
  Interrupted uncertain-call behavior is independently fault-tested, not claimed
  as a real destructive provider test.
- Corrected Dashboard metadata navigation HTTP200 in0.063s; during earlier real
  expansion it returned200 in3.706s while the provider batch continued. Gemini
  executes in a bounded worker thread, not on the HTTP event loop.
- Real hostile Origin POST and hostile Host progress GET both rejected403.
  Duplicate run RUN-UI03-C24A58DBD5074A2585D09093F5094291 registered zero document
  child tasks and made no new provider calls; completed/failed records persisted.
- Fresh scoped Drive API download of each original document matched all5 stored
  SHA-256 values. Kernel audit verified. No source document mutation, category
  move, tax acceptance, ELSTER or submission occurred.

| Final directive gate | Result and exact limit |
| --- | --- |
| OWNER_PRIVACY_CONFIGURATION | ACCEPTED, bounded Owner decision |
| GEMINI_CREDENTIAL_ROUTE | CLOSED, existing explicit-key route |
| KERNEL_AUTHORIZATION | PASS for executed bounded requests and tested denials |
| GEMINI_REAL_DOCUMENT_EXECUTION | FAIL for complete requested batch:4 successful/1 preserved failure |
| PER_DOCUMENT_PERSISTENCE | PASS,4 candidates plus1 failure durably retained |
| DASHBOARD_PROGRESS | PASS, actual per-document states; not registration-as-result |
| DASHBOARD_RESULT_VISIBILITY | PASS,43 candidate fields and page evidence |
| DASHBOARD_RESPONSIVENESS | PASS within observed local tests; no universal latency claim |
| RESTART_RECOVERY | PASS for actual committed readback; uncertain call recovery fault-tested separately |
| SECURITY_REGRESSION | PASS within111 worker related tests and73+1 independent checks (overlap) |
| INDEPENDENT_ACCEPTANCE | PASS for exact7cfa3fa bounded implementation only; full campaign not accepted |

The original failed task/manifest max_retries0 is immutable. Its raw provider
response was not retained before the local parser error, so local revalidation
cannot reconstruct it. Exact one-successor authorization was requested through
the Owner question with the protected document/digest and previous task; no
answer has been received at this checkpoint. This is not renewed generic Gemini
or privacy consent. Do not disguise a retry as a fresh task, overwrite that
manifest or transmit that failed document again without the scoped authority.

Next executable step: after the Owner's exact successor decision, bind it to
the failed source identity/digest, corrected implementation and one new bounded
Kernel task/manifest; preserve the old failure, execute once, verify result/audit,
restart/UI readback and obtain the required acceptance. If rejected, retain
the failure and partial result without claiming COMPLETE. No other project stage
is activated. No active OPEN_ITEMS row closes. Existing unrelated Owner UI work
remains uncommitted and preserved.

## Final Owner directive continuation — 2026-10-29

### Implementation and real execution update — 2026-10-30

Implementation candidate f1d46565389545bb097a694a03840a50c358e736 was independently FAIL by separate read-only reviewer /root/ui03_independent_security_review: F01 HIGH multi-dispatcher duplicate admission; F02 HIGH response-row cross-case substitution; F03 HIGH elapsed task deadline. The reviewer exported that exact commit to an isolated temporary directory, reproduced68 passing tests plus three adversarial counterexamples (each exit0), and did not access live credentials/data or change implementation. These findings are not erased by the original tests passing.

Corrections reuse existing Kernel.atomic_execution/BEGIN IMMEDIATE to serialize check+batch intent; verify exact response/task/parent/role/actor/manifest/status/audit linkage and uniqueness before returning fields; and enforce per-task and batch deadlines. Regression probes cover two dispatcher instances, elapsed deadline, response reassignment/deletion and manifest substitution. The existing TEST-only projection is preserved: the real Owner-authorized adapter reuses the response-digest invariant without expanding that frozen synthetic API. Navigation now reads the existing durable registry directly rather than waiting on a document-download lock; the new results route rejects hostile Host/Origin. No new store, scheduler, role, capability or unrestricted transfer permission is introduced.

Actual inventory:5 PDF +1 CSV, verified through the scoped Drive API registry. First batch RUN-UI03-7A2B9D56E6CA463A8B79A966E71A1AD7 failed before any child/API call at the old projection's TEST-only restriction; the failure was durably recorded, not overwritten. A later first-PDF attempt TASK-UI03-0C9D8791F5F3456C941B69DA2783C77C / MAN-UI03-F5467AEB18D842B1A4D89FAFC75C13C4 failed at a missing optional jsonschema import after the provider response. The parser now implements closed, bounded validation without introducing that dependency;15 positive/negative validation tests pass. The failed source/task remains preserved with max_retries0. No blind replay occurred. Exact successor authorization for that document/digest has been requested from the Owner; no new generic Gemini consent is requested.

Actual completed candidates:4 PDF, with14/10/10/9 evidence-bearing fields, each separately committed in the protected existing Kernel SQLite responses/audit. One PDF remains FAILED, CSV is unsupported and was not sent to the PDF worker. Successful first UI-click run is RUN-UI03-7FAB99D67AB64F13BD838D82B56EC2C3; expansion run is RUN-UI03-90B138958F9641E88649A53F9A38648E. No extracted taxpayer values, names, filenames, original document IDs/bytes or provider secrets are included in Git. Private readbacks are under ignored .runtime/ui03 and the existing Windows local Cases/orchestrator-kernel.sqlite.

First successful document references: TASK-UI03-C8F7BF6E638144B79DB453CB61F3E759 / MAN-UI03-A1EB128841A34B88903AA454D8DA3201. Expansion documents: TASK-UI03-3763864D8E6B49D1B57F5361367914E1 / MAN-UI03-18B62CBFB4D84C8FB0F3A82C7693D311; TASK-UI03-A47BE33FB286481AB1052B170BE19EAF / MAN-UI03-77AF945E6B744A959417B5C82A9FA6A1; TASK-UI03-D42DEFD190B34B34AD47C2DF3EAF98A1 / MAN-UI03-BB2B16E257E34079AC610817ED51D2D3. These identify candidate extraction, not accepted tax facts.

Real browser DOM verified Persian rtl, two document rows including the initial failure,14 result-field rows and the candidate warning after the first success. Actual HTTP POST returned REGISTERED in0.632s; hostile-Origin POST returned403. German Dashboard returned200 during expansion in3.706s before the subsequent metadata-navigation lock correction. Full refresh/restart and corrected-SHA independent acceptance still require final verification. Candidate testing53 passed; first expanded run3 failed/108 passed (two test SQL-column mistakes and an existing unindexed credential report), corrected; subsequent relevant suite111 passed, exit0,64.94s. New actual-route integration1 passed, exit0,7.98s after correcting the fake downloader fixture; no real API in these tests. Counts overlap, do not sum them as unique coverage. Remaining real failed document is not a successful extraction and full UI-03 completion is not claimed.

The final Owner directive8b4c7499 expressly accepts the existing privacy configuration for development/document-analysis testing: project ai-tax-agent-507813, billed/enabled API, explicit GEMINI_API_KEY, model gemini-3.8-flash, AI Studio logging off and Interactions store=False. Credential route is CLOSED at3bc1e54. The historical stop below is superseded for this scope, not erased. No zero-retention guarantee or general external-transfer authority is inferred. Frozen roles/capabilities are unchanged: EVIDENCE_AGENT A3/A4 reads one exact case/run and writes candidate evidence; its tool binding is limited to the registered Owner-approved Gemini destination and Drive reads, not A6 external_transfer.

Current implementation candidate reuses the existing Kernel SQLite tasks/manifests/responses/audit. A single bounded thread transports registered work off HTTP; it is not a scheduler or separate state authority. Every document intent precedes its API call; the full structured candidate result is committed in its own Kernel response/audit event. Kernel response-digest projection verifies readback. Unchanged completed candidates are not resent; uncertain interrupted intents block replay and preserve earlier results. New API requests explicitly use store=False, no automatic continuation, one SDK attempt and a bounded deadline. Both per-document and batch budgets reserve conservative ceilings, not claims of actual metered provider billing. Output never becomes accepted tax evidence automatically. Focused integration6 and combined53 tests pass before final candidate verification. Real execution and separate exact-SHA independent review remain pending at this candidate checkpoint.

Historical stop record,2026-10-29: HUMAN_REQUIRED / REAL_EXECUTION_NOT_STARTED.
Owner execution attachment: 35c94966-f16a-4416-bba6-c33eba766e3e.
Recovered branch: c09-witness-hardening.
Recovered HEAD and fetched origin: f473111ac4ce02fa00387613fe686fab4645b684.

## Scope and resource admission

The requested deliverable is actual CASE-2025-0001/2025 PDF execution through
the existing Kernel, durable per-document results and visible Dashboard progress.
No such completion is claimed. Initial capacity was Owner-reported 100/92;
no initial usage query was performed, as expressly instructed. The bounded
recovery, contract verification, negative tests and publication package was
estimated at no more than 10 five-hour / 3 weekly percentage points, preserving
the mission's 10-point five-hour reserve. No unbounded implementation was begun.
Authenticated observations and reset times are recorded in the checkpoint.

## Recovered facts, not acceptance

Fourteen preexisting dirty/untracked entries were recovered. Implementation
files and UI edits remain uncommitted and were not reset, replaced, activated,
or included in this evidence-only publication. The preexisting Owner directive
is separately preserved as authority evidence, with this dated clarification.

- Candidate case_analysis_kernel_dispatch.py:30-35 registers IMPLEMENTATION_AGENT
  with report_evidence and no tools. Lines53-55 explicitly return REGISTERED
  without worker execution. The injected worker is never called. There is no
  validated/active Gemini manifest or Gemini permission receipt in that path.
- Candidate case_analysis_gemini_worker.py:34-57 calls the provider and only
  writes the aggregate JSON after the entire PDF loop. It is not a durable
  per-document runner; do not invoke it directly to bypass the missing boundary.
- Candidate local_case_host.py:465-474 treats an executor object and environment
  key as readiness. This is not operational authority. The existing readiness
  UI must not be used as acceptance evidence. No production source correction
  or live reload is claimed by this report.
- Candidate analysis_request.js reports registration, not completed analysis.
  No real per-document progress/result projection or restart proof was recovered.

These are observations of the preserved local candidate, not claims about
the published baseline, whose acceptance remains bounded to prior reports.

## Exact mandatory boundary

1. docs/ui25-owner-internal-development-testing-authorization-20261009.md:33-40
   expressly authorizes the existing registered Gemini API for initial analysis,
   translation and interpretation. Generic Gemini approval is NOT missing and
   must not be requested again. Its provider-side limitation nevertheless
   requires verification of the actual API product, data-use/retention terms
   and configuration before protected real documents are transmitted. No
   accepted product/configuration privacy/retention evidence was recovered in
   this execution path. That is not a claim that the provider is incompatible,
   or that no such evidence can exist elsewhere.
2. src/agent_lab/runtime_activation.py:37 names the existing gemini_extraction
   gate: KERNEL_AND_OWNER_PROVIDER_BINDING, provider-privacy-retention-pass,
   document-attribution-pass, provider_authorization_ref, privacy_ref and
   retention_ref. Its evaluator never grants execution (lines130-132).
   Credentials and self-asserted hash references cannot substitute for accepted
   evidence. This report does not turn that evaluator's historical service-gap
   reason into a newly proven global architecture blocker.
3. contracts/orchestrator/v1/roles.json:119-127 and169-171, and
   permission-matrix.json:60,73,77 distinguish implementation evidence reporting,
   A3/A4 case evidence work and A6 external transfer. Listing a provider tool
   does not grant a capability. The narrow registered-Gemini exception must be
   bound through the existing governed provider path; it must not be implemented
   by granting EVIDENCE_AGENT unrestricted external_transfer. Negative tests
   prove these distinctions; absence of a literal gemini_extraction capability
   alone is NOT proof that a new capability or constitutional amendment is needed.

The current directive expressly preserves frozen contracts. The October29
Owner statement waives repeated per-document Gemini consent; it does not
document verification of Google's actual privacy/retention configuration.
No per-document tax-submission approval is requested, and no C09 global stop
is inferred. The provider-evidence boundary stops real transmission only.

## Verification actually executed

All commands use the existing venv, PYTHONPATH=src, temporary SQLite and synthetic
fixtures. No Owner database, original document bytes, API key, live Gemini call,
Drive mutation, service restart or privileged configuration was used.

1. C:\Users\rezag\ai-agent-lab\.venv\Scripts\python.exe -m pytest
   tests/unit/test_case_analysis_executor.py
   tests/unit/test_case_analysis_kernel_dispatch.py
   tests/unit/test_runtime_activation.py -q --tb=short
   Result: 11 passed, 0 failed, 0 skipped, exit0, 8.64s.
   The first two test files are preexisting uncommitted candidate files, not
   accepted implementation or part of this evidence commit.
2. Same interpreter -m pytest
   tests/unit/test_ui03_gemini_authority_boundary.py
   tests/unit/test_orchestrator_kernel.py
   tests/unit/test_runtime_activation.py
   tests/unit/test_document_extraction.py -q --tb=short
   Result: 41 passed, 0 failed, 0 skipped, exit0, 20.86s.
   Includes four new role/capability/provider-tool negative combinations.
   Existing Kernel audit verification passed in each negative probe.
3. Same interpreter -m pytest tests/unit/test_documentation_index.py -q --tb=short:
   18 passed, 0 failed, 0 skipped, exit0, 1.26s. Scoped documentation diff
   check passed. Whole-worktree diff check found the already present trailing
   whitespace in the unrelated uncommitted local_case_host.py:473 readiness
   hunk; it was preserved, not silently repaired or included in this commit.

Both test commands produced the existing Starlette/httpx deprecation warning.
Suites overlap; do not add their counts as unique coverage. These are development
tests, not independent acceptance or real end-to-end evidence.

## Historical required gate matrix before final Owner directive

| Required gate | Actual outcome |
| --- | --- |
| KERNEL_AUTHORIZATION_PASS | NOT_ESTABLISHED for real provider execution; negative denials verified |
| GEMINI_REAL_EXECUTION_PASS | NOT_EXECUTED / provider evidence boundary |
| PER_DOCUMENT_PERSISTENCE_PASS | NOT_EXECUTED; candidate only aggregates after loop |
| DASHBOARD_PROGRESS_PASS | NOT_EXECUTED |
| DASHBOARD_RESULT_VISIBILITY_PASS | NOT_EXECUTED |
| DASHBOARD_RESPONSIVENESS_PASS | NOT_EXECUTED |
| RESTART_RECOVERY_PASS | NOT_EXECUTED for this workflow |
| SECURITY_REGRESSION_PASS | 41 bounded synthetic tests passed; not real-workflow acceptance |

Real inventory remains NOT_REVALIDATED, not an invented current 5-PDF/1-CSV
observation. No actual task/manifest/run was issued, no document was sent and
no original evidence was modified. CSV was not sent to a PDF worker.

## Exact continuation and evidence ownership

Recover or complete the existing registered-provider privacy/retention and
runtime-binding acceptance evidence, with exact API product/configuration and
responsible acceptance authority. Do not request generic Gemini consent again.
If that evidence is not already available, the responsible Owner/security
authority must accept the specific configuration after verification, rather
than authorize an unrestricted external capability or waive safeguards.

Once the boundary is satisfied, resume the already requested existing-Kernel
adapter: proper case-evidence role and manifest, actual permission/budget/deadline
checks, durable per-document intent/result/reconciliation, no automatic retry
of uncertain external outcomes, and real bilingual UI progress/readback. Obtain
the applicable independent acceptance before claiming operational success.
Do not repeat TPM/GCS investigations or require C09 closure for unrelated work.

PROJECT_CHECKPOINT.md and OPEN_ITEMS.md are assessed together: no active item
closes; no UI-03, provider, protected-data, C09, identity or tax acceptance is
granted. Approval and Submission remain disabled. The report's publication
commit is the commit introducing this file (git log -1 -- this path); exact
remote readback is delivered in the final chat report, avoiding a self-hash.

## Authenticated capacity handoff

At2026-10-29T20:47:06Z the signed-in Codex app get_usage_limits source reports
92% five-hour remaining, reset2026-10-30T01:39:46Z;91% weekly remaining,
reset2026-11-04T12:52:37Z. Ordinary usage is allowed. These are actual remaining
percentages (100 minus usedPercent), not the Owner's initial100/92 report.
The10-point mission reserve was not approached; this is an evidence/security
stop, not a capacity stop. No parallel Bridge state or new authority is created.

## Final continuation capacity and publication handoff — 2026-10-30

Latest authenticated observation2026-10-29T23:15:28Z (2026-10-30 local Berlin):
signed-in Codex app get_usage_limits,47% five-hour remaining, reset
2026-10-30T01:39:46Z;83% weekly remaining, reset2026-11-04T12:52:37Z. Ordinary
usage allowed. Mission10-point reserve respected. Owner's starting90/90 was
supplied, not independently measured; account-wide changes must not be called
precise isolated mission consumption. No initial quota query, system quota
bypass or parallel state store was used. Final documentation suite18 passed,
exit0,0.92s. Implementation review attaches to exact7cfa3fa; publication-only
commit records the evidence and remote readback without self-referential hashes.
Pending scoped successor authority remains unanswered at this checkpoint;
full requested campaign remains incomplete and no automatic resend is scheduled.
