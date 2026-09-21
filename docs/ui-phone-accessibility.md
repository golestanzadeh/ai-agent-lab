# UI package 12 — phone-width and keyboard accessibility contract

Status: **IMPLEMENTED / LOCAL SYNTHETIC ONLY**

UI-12 hardens the existing Persian RTL interface for narrow phone widths and
keyboard use. Deterministic checks preserve the viewport declaration, skip link,
single-column phone layout, visible Human Gate and safety diagnostics, and the
absence of CSS rules that hide content at narrow breakpoints.

Long identifiers and status codes wrap rather than widening the page. Selects,
buttons, and diagnostic summaries use at least 44-pixel targets, while keyboard
focus receives a visible outline. These presentation changes enable no control and
add no real data, authentication, persistence, network, ERiC, or transmission path.

Verification: targeted responsive/UI `15 passed`; regression excluding the known
Windows-sensitive Google Drive provisioning file `644 passed, 1 skipped`. Two full
Windows runs each reached `658 passed, 1 skipped` before one order-varying
pre-existing provisioning journal-replace failure; the first isolated failed case
passed immediately. Hands-on phone validation remains a separate step.

UI-17 adds semantic table captions and row/column headers, labels the decision expiry,
marks decorative timeline numbers for assistive technology, and renders technical
codes, hashes, and timestamps left-to-right inside the Persian RTL layout. Its
targeted responsive/UI suite passed (`17 passed`).

UI-18 replaces the whole-workspace live region with a dedicated atomic polite
status message. A dynamic case change now announces only the selected synthetic
case and tax year instead of prompting assistive technology to reread every panel.
Targeted responsive/UI/documentation verification passed (`23 passed`).
