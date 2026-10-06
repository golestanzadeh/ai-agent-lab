# Local synthetic E10/2024 declaration validation

This package promotes the bounded Anlage N mapping result to an immutable synthetic E10/2024 declaration payload and validates it locally against the exact recovered official `E10-2024.xsd` from ERiC `44.3.6.0`.

The schema is supplied through an explicit local `pathlib.Path`. Its exact filename and SHA-256 digest are verified before loading. Protected schema content remains outside Git. Missing, renamed, modified, unreadable, or invalid schema input fails closed.

The official schema defines the E10 declaration root and its form components as optional, while requiring the fixed `version="2024"` attribute. The assembled payload retains the verified Anlage N component, exact E10 namespace and version, and deterministic mapping identity. No synthetic identity, tax number, address, transfer header, or Manufacturer-ID is invented merely to populate optional form sections.

Successful XSD validation proves structural conformance to that official schema only. It is not ERiC plausibility execution, signing, authentication, production readiness, or permission to transmit. ERiC FFI, the official plausibility engine, credentials/certificates, Manufacturer-ID, networking, signing, and transmission remain denied; official ERiC plausibility execution remains the explicit blocker.
