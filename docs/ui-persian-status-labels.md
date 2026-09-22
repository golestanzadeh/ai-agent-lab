# UI package 14 — closed Persian status labels

Status: **IMPLEMENTED / LOCAL SYNTHETIC ONLY**

UI-14 gives critical workflow, readiness, review, and support codes concise Persian
labels while retaining the exact technical code for troubleshooting. Labels come
from a closed catalog; unknown or arbitrary text fails closed and cannot enter the
view through the label function.

UI-15 extends the same closed catalog to every workflow stage, stage state, and
recovery state. The timeline is readable in Persian while exact enum codes remain
visible for audit and support.

UI-16 extends the catalog to case lifecycle, document category/status, Human Gate
status, and the allowlisted decision action/destination. Workspace and queue views
therefore no longer require the user to interpret English state codes.

This presentation layer adds no free-form diagnostic channel, private content,
control, approval, authentication, persistence, external connection, ERiC execution,
or transmission capability.

Verification: targeted label/UI/documentation `20 passed`; regression excluding the
known Windows-sensitive Google Drive provisioning file `652 passed, 1 skipped`.
The UI-15 refinement passed its targeted label/workflow/UI suite (`21 passed`).
The UI-16 refinement passed its targeted label/UI/document/decision suite
(`27 passed`).
