# UI-03 Owner directive: Gemini is the project's principal analysis worker

Owner reaffirmed 2026-10-29: "جمینای بازوی اصلی پروژه است" (Gemini is the project's main arm).

## Scope
Gemini is an authorized project analysis provider for case-owned document extraction and proposed classification. The Owner does not require a first or second per-document approval to use Gemini for this bounded analytical purpose. The Owner's explicit dashboard analysis request initiates that work.

## Distinct protected actions
The authorization does not accept a Gemini classification as tax truth, approve moving documents, authorize ELSTER or other tax submissions, or permit unrelated external transfers. Existing Human Gates and evidence/permission checks for those actions remain in force. Gemini output is a candidate until independently validated and accepted.

## Implementation note
The UI-03 Worker and dispatcher are connected for bounded extraction; production end-to-end verification and Kernel dispatch-policy acceptance remain separate acceptance requirements. Never represent a registered task alone as completed analysis.

## Verified clarification — 2026-10-29
The preceding implementation note is an earlier candidate intention, not an execution result. Recovery at f473111ac4ce02fa00387613fe686fab4645b684 found an uncommitted dispatcher that registers a task and never invokes its worker. No real Kernel-authorized execution or accepted provider configuration was established. The Owner's generic Gemini authorization stands; applicable product/privacy/retention verification is still required before protected real-data transmission. See ui03-kernel-gemini-execution-gate-20261029.md. This clarification preserves, rather than silently converts, the prior statement.
