# UI package 13 — loopback browser security headers

Status: **IMPLEMENTED / LOCAL SYNTHETIC ONLY**

UI-13 applies the same fail-closed browser policy to the full page, HTMX partial,
health response, and error responses. The app disables caching and referrers, MIME
sniffing, framing, camera/geolocation/microphone access, form actions, and non-self
script/style/connect sources. Static assets remain self-hosted.

These headers reduce accidental browser exposure but do not turn the prototype into
a deployed or authenticated service. The server remains loopback-only through the
documented launcher. Public/LAN binding, real data, authentication, persistence,
external connectivity, ERiC invocation, and transmission remain separate gates.

Verification: targeted UI/security/documentation `24 passed`; regression excluding
the known Windows-sensitive Google Drive provisioning file `650 passed, 1 skipped`.
The full run reached `663 passed, 1 skipped`; after correcting the package-local
documentation-index entry, its only remaining failure was the pre-existing
order-varying provisioning journal-replace issue.
