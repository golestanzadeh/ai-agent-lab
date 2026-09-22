# UI package 3 — local interactive prototype

## Boundary

This package implements the Human-selected FastAPI + Jinja/HTMX architecture as a
local, synthetic, non-production prototype. It reads only an in-memory synthetic
Case Registry. It has no login, persistent storage, real data, protected ERiC
material access, external API, submission route, official receipt, or deployment.

HTMX `2.0.10` is pinned and served from the local static directory. The browser
does not need a CDN or other runtime network destination.

## Run locally

From the repository root after installing `requirements.txt`:

```powershell
$env:PYTHONPATH = "src"
python -m uvicorn agent_lab.ui_app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. Do not change the host to a LAN/public address; that
would exceed this package's local-only boundary.

## Implemented flow

- responsive Persian right-to-left shell for phone and Windows widths;
- synthetic case/year selection through an HTMX partial request;
- exact case-scoped document, finding, gap, preview, and Human-Gate state;
- visible synthetic/local environment label;
- disabled ELSTER submission and operational controls;
- no FastAPI OpenAPI or interactive documentation endpoints.

## Verification

Route tests use FastAPI's in-process TestClient and create no network socket. They
verify the local synthetic shell, exact partial scope, unknown/year-mismatch denial,
absence of a submission route, explicit health mode, and disabled API documentation.

Observed results: UI-2/UI-3 targeted `13 passed`; full regression
`518 passed, 1 skipped`; Python compile check passed; loopback visual inspection
passed. The suite emits one upstream Starlette TestClient deprecation warning about
a future `httpx2` migration. It is recorded rather than hidden and does not change
the current result.

## Remaining gates

Real case data, storage/Drive integration, authentication, multi-user access,
protected ERiC materials, external connectivity, deployment, production activation,
and any ELSTER/Finanzamt transmission require separate governed work and authority.
