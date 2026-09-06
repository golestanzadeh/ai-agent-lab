# Architecture

Status: **planned / not yet designed**

This document will contain the approved system architecture after Phase 1 requirements and domain selection are complete.

It will cover component boundaries, control flow, state transitions, tool boundaries, human approval gates, and failure handling.

Do not treat the agent list currently described in `PROJECT.md` as the final architecture.

## Development and data-storage baseline

The following baseline has been selected for the initial implementation direction. It is an architectural baseline, not yet the final production architecture.

### Source code and project source of truth

- **Python** is the primary implementation language.
- **Git** is used for version control.
- **GitHub (`golestanzadeh/ai-agent-lab`)** is the project Source of Truth for source code, documentation, tests, configuration templates, evaluation assets, architectural decisions, and verified development-state records.
- Real personal taxpayer documents and unnecessary personal data must **not** be committed to GitHub.

### Runtime environment

- **Docker** is the planned standardized runtime/containerization layer.
- Docker is used to make the Python runtime and dependencies reproducible and isolated across development and later deployment environments.
- Docker is not the project's data store.
- Docker adoption will be introduced incrementally; the user does not need prior Docker experience before implementation begins.

### Tax-case data storage

- **Google Drive** is the selected initial private storage location for real tax-case documents and case artifacts, subject to the security/privacy design being validated before real sensitive data is processed.
- A proposed case structure is:

```text
Google Drive/
└── AI-Tax-Agent/
    └── Cases/
        └── CASE-001/
            ├── Documents/
            ├── Evidence/
            ├── Calculations/
            ├── Reports/
            └── Audit/
```

- Python will access Google Drive through an authenticated API/integration layer rather than treating Drive as part of the source-code repository.
- Local files may be used temporarily for processing/cache purposes, but persistent real-case data must follow the approved private-storage and retention rules.

### Development workflow

The intended local workflow is:

```text
GitHub Source of Truth
        ↓ clone / pull
Local ai-agent-lab repository
        ↓
Project-local Python environment
        ↓
VS Code / Codex
        ↓
Python implementation + tests
        ↓
Docker runtime
        ↓
Git commit / push
        ↓
GitHub Source of Truth
```

The repository **must exist locally before project-local Python/VS Code setup is treated as complete**.

### Verified setup history

The actual setup sequence and corrections are recorded in `docs/development-setup.md`. In particular, the initial Python virtual environment was accidentally created at `C:\Users\rezag\.venv` before the repository had been cloned. This environment is not considered the project environment. The next local setup step is to clone the repository and then create a project-local `.venv`.

Codex may assist with implementation, debugging, tests, and repository changes. GitHub remains the versioned source of truth.

### Agent implementation principle

An Agent is not merely an LLM prompt. A production agent definition must eventually specify at least:

- role and responsibility;
- inputs and outputs;
- available tools;
- state/context access;
- permissions and action boundaries;
- evidence requirements;
- decision/stop conditions;
- failure and recovery behavior;
- evaluation criteria and tests.

Each proposed agent must pass through problem definition, role definition, interface/contract design, tool and permission design, evaluation design, implementation, integration, and real-case validation before being treated as an approved project component.

## Security and privacy note

Because the first case uses real tax data, the private-storage choice and Google Drive integration must be explicitly reviewed for authentication, access control, encryption, retention, accidental synchronization, logging, and data minimization before sensitive documents are processed by the implemented system.

OAuth credentials and tokens must never be committed to GitHub.
