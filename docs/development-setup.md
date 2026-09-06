# Development Setup and Verified Progress

Last verified: 2026-09-06

This document records the actual development-environment setup performed during the project, including important corrections. It exists so future sessions do not reconstruct the local state from chat memory.

## Source-of-truth rule

GitHub is the durable project memory. The repository documents the intended and verified state of the project. Chat is not authoritative for historical state.

## Verified setup sequence

### Step 1 — GitHub / Codex

- Repository: `golestanzadeh/ai-agent-lab`
- Default branch: `main`
- Repository visibility: public
- GitHub write access through the current Codex-enabled integration was verified.
- Repository discovery was performed with `search_repositories` using `user:golestanzadeh ai-agent-lab`.
- `list_repositories` was intentionally not used, per project workflow.

### Step 2 — Python

The user verified:

```text
Python 3.14.2
C:\Python314\python.exe
C:\Users\rezag\AppData\Local\Programs\Python\Python311\python.exe
C:\Users\rezag\AppData\Local\Microsoft\WindowsApps\python.exe
```

A virtual environment was initially created at:

```text
C:\Users\rezag\.venv
```

This location is considered **incorrect for the project** and is not used as the final project environment.

### Step 3 — Docker

Docker Desktop was updated and the Docker Engine was verified with:

```powershell
docker run --rm hello-world
```

The command completed successfully. Verified Docker CLI version at that point:

```text
Docker version 29.7.2
```

### Step 4 — Google Drive folder structure

The user created the following folders through Google Drive for Desktop / PowerShell:

```text
Google Drive
└── My Drive
    └── AI-Tax-Agent
        ├── Cases
        │   └── CASE-001
        │       ├── Documents
        │       ├── Evidence
        │       ├── Calculations
        │       ├── Reports
        │       └── Audit
        ├── Templates
        └── System
```

This is private case storage and is not part of the GitHub repository.

### Step 5 — Google Drive API

The following Google Cloud setup was completed:

1. A Google Cloud project named `AI-Tax-Agent` was created.
2. Google Drive API was enabled.
3. Google Auth Platform / OAuth app configuration was completed.
4. An OAuth Client of type **Desktop app** was created with the name `AI-Tax-Agent Desktop`.
5. The OAuth client JSON was downloaded.

The credential file is stored outside the public repository at:

```text
C:\Users\rezag\ai-tax-agent\credentials.json
```

The credential file must remain outside GitHub and must never be committed.

A previous mistaken placement inside `C:\Users\rezag\ai-agent-lab\credentials.json` was removed. `git status` subsequently verified a clean working tree, confirming that no local Git change remained from that file.

### Step 6 — Local repository clone

The repository was successfully cloned to:

```text
C:\Users\rezag\ai-agent-lab
```

Verification:

```text
On branch main
Your branch is up to date with 'origin/main'.
nothing to commit, working tree clean
```

The local clone is therefore synchronized with `origin/main` at the time of verification.

### Step 7 — Project-local Python virtual environment

The project-local environment was created inside the cloned repository:

```text
C:\Users\rezag\ai-agent-lab\.venv
```

The environment was activated and verified with:

```powershell
python --version
python -c "import sys; print(sys.executable)"
```

Verified result:

```text
Python 3.14.2
C:\Users\rezag\ai-agent-lab\.venv\Scripts\python.exe
```

The previous home-directory environment at `C:\Users\rezag\.venv` is not the project environment.

### Step 8 — pip

The project-local pip was upgraded and verified:

```text
pip 26.2.1 from C:\Users\rezag\ai-agent-lab\.venv\Lib\site-packages\pip (python 3.14)
```

### Step 9 — VS Code

VS Code was opened from the project root with:

```powershell
code .
```

The project workspace opened successfully.

The Python interpreter must be the project-local environment:

```text
C:\Users\rezag\ai-agent-lab\.venv\Scripts\python.exe
```

VS Code's Python tooling supports workspace-local virtual environments and uses the selected interpreter for IntelliSense, running, debugging, linting, and related Python features.

### Step 10 — Credential-location and repository-safety verification

The credential file location was explicitly verified:

```powershell
Test-Path "$HOME\ai-tax-agent\credentials.json"
```

Verified result:

```text
True
```

The mistaken repository copy was removed and the repository was checked with:

```powershell
git status
```

Verified result:

```text
On branch main
Your branch is up to date with 'origin/main'.
nothing to commit, working tree clean
```

The repository's existing `.gitignore` already excludes `.env`, `.env.*`, virtual environments, caches, and local output/artifact directories. The OAuth credential is nevertheless kept physically outside the repository as the primary protection.

### Step 11 — Google Drive Python dependency and import verification

The following dependencies were installed successfully into the project-local `.venv`:

```text
google-api-python-client==2.200.0
google-auth-httplib2==0.4.2
google-auth-oauthlib==1.4.1
google-auth==2.57.1
google-api-core==2.36.0
protobuf==7.36.1
cryptography==50.0.1
requests==2.34.2
```

The import smoke check was executed with:

```powershell
python -c "from googleapiclient.discovery import build; from google_auth_oauthlib.flow import InstalledAppFlow; print('Google Drive libraries: OK')"
```

Verified output:

```text
Google Drive libraries: OK
```

The verified dependency set is recorded in the repository root `requirements.txt`.

This verifies that the required Google Drive Python libraries can be imported in the project environment.

### Step 12 — Google Drive OAuth and metadata smoke test

The smoke-test script was executed from the project-local environment with:

```powershell
python .\src\drive_smoke_test.py
```

The first execution required Google OAuth authorization. After the user account was added as an approved test user in the Google Auth Platform configuration, the browser authentication flow completed successfully.

The subsequent execution produced:

```text
Google Drive smoke test: PASS
Folder: AI-Tax-Agent | ID: <private Drive folder ID>
```

This verifies all of the following:

- Local OAuth authentication completed successfully.
- The Python application obtained usable authorization for the configured Drive scope.
- The Drive API responded successfully.
- The application could locate the private `AI-Tax-Agent` folder by metadata.
- The test did not read, modify, upload, or process tax-document contents.

The smoke test uses:

```text
https://www.googleapis.com/auth/drive.metadata.readonly
```

which is appropriate for the current metadata-only validation. The private folder ID is intentionally not recorded in this public repository.

The OAuth token generated by the local flow must remain outside the repository, under the local `C:\Users\rezag\ai-tax-agent\` directory. It must never be committed to GitHub.

### Step 13 — CASE-001 source-document placement

The user placed the first Golden Test Case source documents in:

```text
Google Drive
└── My Drive
    └── AI-Tax-Agent
        └── Cases
            └── CASE-001
                └── Documents
```

The user reported the following local Google Drive mirror state on 2026-09-06:

```text
15 PDF files
approximately 4.25 MB total
```

The filenames reported by the user include tax-related supporting documents, receipts, donation records, insurance records, a wage-tax certificate, and a WISO Steuer export. These names are not treated as evidence of their tax meaning. The authoritative inventory must come from the Drive API.

No document was uploaded to the chat for this milestone.

### Step 14 — Approved Document Inventory boundary

The first real processing stage has now been formally defined as **Document Inventory**.

Its responsibility is limited to establishing exactly which source items exist in the approved case folder before document contents are interpreted.

The inventory stage must:

- authenticate using the existing approved OAuth flow;
- resolve only the approved case path;
- enumerate direct children of `CASE-001/Documents`;
- use pagination until completion;
- request only the metadata fields needed for inventory;
- identify folders versus document files;
- produce a structured inventory snapshot;
- report anomalies such as duplicate names or unexpected subfolders;
- perform no source-document mutation;
- perform no tax interpretation.

The inventory stage is deterministic code, not an LLM agent.

The detailed architecture and acceptance criteria are recorded in `docs/document-inventory.md`. The broader logical architecture, including source boundaries, evidence/provenance, permissions, auditability, evaluation, and implementation sequence, is recorded in `docs/architecture.md`.

## Current local development state

The verified local development chain is now:

```text
C:\Users\rezag\ai-agent-lab
        ↓
      .venv
        ↓
 Python 3.14.2
        ↓
    pip 26.2.1
        ↓
 Google Drive libraries installed + import verified
        ↓
 Google OAuth + Drive metadata API verified
        ↓
 CASE-001 source documents present in private Drive storage
        ↓
      VS Code
        ↓
    Git / GitHub
```

Google OAuth credentials and tokens are stored separately at:

```text
C:\Users\rezag\ai-tax-agent\
```

Real tax documents and private case evidence remain outside the public GitHub repository.

## Security rules

Never commit:

- OAuth client credentials
- OAuth tokens
- `.env` files containing secrets
- real taxpayer documents
- private tax-case evidence
- private personal data

All credentials and real tax data must remain outside the public GitHub repository.

The current Drive test deliberately uses a read-only metadata scope. Broader content-read or write scopes must not be introduced until the corresponding workflow requires them and the security/privacy implications have been reviewed.

## Continuity rule

Whenever a setup step is completed, corrected, or materially changed, update this document and `CURRENT_STATE.md` before moving to the next project-level setup step. The repository must remain sufficient to reconstruct the verified local setup without relying on chat history.
