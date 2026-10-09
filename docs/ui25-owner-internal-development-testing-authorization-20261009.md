# Owner Authorization — UI25 Internal Development and Testing

Date: 2026-10-09
Authority: Explicit Owner instruction in ChatGPT
Status: OWNER-AUTHORIZED / INTERNAL DEVELOPMENT AND TESTING ONLY
Scope: AI-Tax-Agent UI completion, integration and 2025 case workflow

## Authorized
Within the project's existing authorized environment and access controls, the Owner authorizes all necessary internal development, tests, debugging, structural code corrections, integration, agent-to-agent communications, document analysis, reanalysis, issue resolution, incremental document intake, calculations, and end-to-end verification needed to complete and test the product. This authorization covers existing GitHub development workflows, the Owner's local environment, and the designated project Google Drive, subject to their permissions and data classification.

Work must preserve the existing Deterministic Orchestrator Kernel, case isolation, durable evidence, auditability, security controls, protected data handling, and all applicable project rules. This authorization does not silently close, waive or mark PASS any existing Human Gate, acceptance gate or prerequisite. Development/test tasks may proceed where those gates do not restrict the particular action.

## Explicitly prohibited without additional exact Owner authorization
- Any transfer or communication of project code, documents, results, case data, credentials or other project information to a destination outside the approved project environment (GitHub, Owner local environment, designated project Google Drive), except where a separately existing, specific Owner authorization demonstrably covers the exact operation and destination.
- Any public internet publication, public release, public issue/PR/comment/artifact/log containing sensitive or non-public project data, or transmission of data to third parties.
- Any real ELSTER/ERiC/Finanzamt submission or other external tax filing before both independent Owner approval stages required by the Constitution and submission contract have been completed.
- Any weakening of the existing Constitution, access restrictions, Human Gates, data isolation, or external transmission safeguards.

## Interpretation and operational boundaries
- GitHub repository visibility is PUBLIC as checked on 2026-10-09. Only non-sensitive source code, synthetic fixtures and privacy-safe documentation may be committed there; actual taxpayer documents, identity data, private results, secrets and sensitive logs must never be committed, pushed or exposed.
- Gemini and other remote model/provider APIs are outside the three named environments. Sending documents or case contents to such APIs requires a separately verified exact authorization and applicable data protection; this blanket authorization alone does not grant it.
- GitHub Actions, external package registries, telemetry, outbound notifications and other network paths are not blanket-authorized simply because code executes inside GitHub or locally. Apply existing explicit permissions and egress restrictions.
- Internal agent-to-agent exchange is authorized only within the approved environment, subject to case-scoped access and existing controls.
- New late-arriving documents may trigger versioned incremental reanalysis; accepted historical results are not silently overwritten. A later filing correction is not automatically submitted.
- If an action's destination, publicity or permission status is unclear, stop only that action and request the exact missing approval. Continue unrelated authorized work.

## Authorization scope and precedence
This Owner authorization expands internal implementation/testing discretion, not external communication or submission authority. Higher-priority project rules remain effective. This record is not a grant to merge/release, activate production access, or bypass previously blocked real-data gates.

Source: Owner message, 2026-10-09. No taxpayer-specific data is included.


## Gemini API — Owner-approved narrow exception (2026-10-09)
The Owner expressly authorizes use of the **already registered Gemini API** solely for the existing previously specified and approved prompt scope, to perform **initial document analysis, translation and interpretation**. Gemini is an extraction/interpretation aid, **not** a tax decision maker: it must not decide or recommend how any particular document should be used in the tax return, classify a tax deduction as allowable as an authoritative conclusion, approve calculations, or authorize submission. Those decisions remain with the existing internal specialist/Chief/Kernel workflow and Human Gates.

This is a **destination-specific exception** to the general external-communication restriction above, not permission to use any other external provider, endpoint, model, plugin, storage service or publication channel. Use only the configured API and the minimum document content necessary under the previously approved prompt and project privacy/security controls. Do not include credentials in prompts, logs or GitHub.

**Prohibited:** unauthorized use, secondary use, public disclosure, or deliberate registration, storage, publication or forwarding of document content, analysis, translation, interpretations or results to any external repository or service. No public GitHub artifacts or external logging containing private data.

**Provider-side limitation:** the project can constrain its own requests, retention and forwarding, but cannot establish or guarantee Google's provider-side retention, logging or processing policy merely by this authorization. Before processing protected real documents, verify the actual Gemini API product, data-use/retention terms and configuration against the Owner's no-unauthorized-external-registration requirement. If incompatible or unverified, block real-data API transmission while allowing authorized synthetic tests and unrelated internal work.

This authorization does not alter the two independent Owner approvals required before any ELSTER/ERiC/Finanzamt submission, nor waive any existing project security or Human Gate.
