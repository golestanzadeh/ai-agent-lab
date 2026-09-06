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

This location is now considered **incorrect for the project**, because the repository had not yet been cloned locally. It must not be treated as the project's final virtual environment.

### Step 3 — VS Code

VS Code was opened with `code .` while the current directory was `C:\Users\rezag`.

The interpreter was selected as:

```text
.venv\Scripts\python.exe
```

and verified with:

```powershell
python -c "import sys; print(sys.executable)"
```

which returned:

```text
C:\Users\rezag\.venv\Scripts\python.exe
```

This verification is valid for the temporary/home-directory environment only. The project-local interpreter must be configured after cloning the repository.

### Step 4 — Docker

Docker Desktop was updated and the Docker Engine was verified with:

```powershell
docker run --rm hello-world
```

The command completed successfully. Verified Docker CLI version at that point:

```text
Docker version 29.7.2
```

### Step 5 — Google Drive folder structure

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

### Step 6 — Google Drive API

The following Google Cloud setup was completed:

1. A Google Cloud project named `AI-Tax-Agent` was created.
2. Google Drive API was enabled.
3. Google Auth Platform / OAuth app configuration was completed.
4. An OAuth Client of type **Desktop app** was created with the name `AI-Tax-Agent Desktop`.
5. The OAuth client JSON was downloaded.

The downloaded credential file must remain outside GitHub and must never be committed.

## Important correction: local repository did not exist yet

At the time the first local Python/VS Code steps were performed, the user had **not cloned `ai-agent-lab` to the PC**. The project had previously been created and maintained directly on GitHub through the Codex-enabled GitHub integration.

Therefore:

- `C:\Users\rezag` is not the project directory.
- `C:\Users\rezag\.venv` is not the final project virtual environment.
- There is currently no verified local `ai-agent-lab` clone from these setup steps.
- The next local setup action must be to clone `https://github.com/golestanzadeh/ai-agent-lab.git` to a deliberate project location.
- Only after cloning should the project-local `.venv` be created.
- Only after the local repository exists should the downloaded Google OAuth credential be placed in the local project environment, preferably outside the repository or otherwise protected by `.gitignore` and secret-handling rules.

## Next verified setup action

Clone the GitHub repository locally, then establish the project-local Python environment and verify the repository/venv relationship before continuing with Google Drive API code.

## Security rules

Never commit:

- OAuth client credentials
- OAuth tokens
- `.env` files containing secrets
- real taxpayer documents
- private tax-case evidence
- private personal data

All credentials and real tax data must remain outside the public GitHub repository.
