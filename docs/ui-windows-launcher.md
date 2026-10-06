# UI package 11 — one-click Windows launcher

Status: **IMPLEMENTED / LOCAL SYNTHETIC ONLY**

The Windows launcher at `scripts/start_local_ui.cmd` starts the existing synthetic
FastAPI interface without requiring the user to type a command. It resolves the
repository from its own location, sets only the process-local Python source path,
opens the loopback browser address, and binds Uvicorn exactly to `127.0.0.1:8000`.

## Use

Double-click `scripts/start_local_ui.cmd`. A small status window remains visible so
the user can stop the interface by closing that window. The browser may need one
refresh if it opens before the local server has finished starting.

The launcher installs nothing, stores nothing, requests no credential, and makes no
ELSTER/Finanzamt or other external connection. It does not add authentication, real
data, operational controls, deployment, production, or transmission. Changing the
host to a LAN/public address remains outside this package and requires separate
governance and security acceptance.

Verification: targeted launcher/UI `15 passed`; full regression
`656 passed, 1 skipped`. The known upstream Starlette TestClient deprecation
warning remains non-blocking.
