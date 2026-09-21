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
