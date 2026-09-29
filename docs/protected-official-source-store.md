# Protected Official Source Store

Status: **`ACCEPTED`**  
Accepted: **2026-09-29**  
Release: **ERiC 44.3.6.0**

The portable configuration key is `AI_TAX_PROTECTED_SOURCE_ROOT`. The current machine uses `C:\AI-Tax-Agent-Protected\Official-Sources`; this absolute path is not embedded in tax/business logic or the Git registry.

The runtime hierarchy is `ELSTER/ERiC/44.3.6.0`, with verified packages under `packages` and the minimally extracted E10/2024 artifacts under `extracted/ESt/2024`. The local protected manifest is `ELSTER/ERiC/44.3.6.0/manifest.json`. Official binaries and protected artifact contents remain outside Git.

Verified package identities:

- documentation ZIP: 123,217,775 bytes, SHA-256 `bad21c27ecce56d04fc04bccfd2dfa17b9ff2455aa878758100fc73a28492ad5`;
- schema-documentation ZIP: 35,503,440 bytes, SHA-256 `a77cca9e5a0ddb4eae9e2548f57fc3a064432c1b71c1ff1e53ca9085a8be779e`;
- Vordruck archive: 979,804,359 bytes, SHA-256 `488953db7d11385a09f2b1ab09a84b68be27321d6bf79078850032279823862b`.

Verified embedded artifacts:

- `Jahresdokumentation_E10_2024.ods`: 960,439 bytes, SHA-256 `6379af3c83b8d8ea1f5b8e683d2cfc401cb1506a6018cd44d68452f8b67dacd5`;
- `E10-2024.xsd`: 1,412,558 bytes, SHA-256 `86c735c6a3070aad1ccd90e5bdc8a0999099f44ed76b5752e74d8dfa5cd7d272`.

The repository registry `contracts/official-source-registry-v1.json` maps logical IDs to versioned relative paths, sizes and hashes. `OfficialSourceResolver` requires the configured root, rejects missing/unknown sources with `OFFICIAL_SOURCE_MISSING`, rejects corruption or path escape with `OFFICIAL_SOURCE_INTEGRITY_FAILURE`, and never falls back to another release, year, network source or backup.

The three originals at `E:\ERic` were preserved. Their independently calculated hashes match both the copied protected-store files and the Owner-provided expected hashes. Google Drive remains backup/recovery only and is not a runtime dependency.

Acceptance verification: focused source-resolver and documentation tests `14 passed`; all five registered sources resolved through the configured logical root with exact size and SHA-256. Git ignore rules explicitly exclude the official package/artifact filename families.
