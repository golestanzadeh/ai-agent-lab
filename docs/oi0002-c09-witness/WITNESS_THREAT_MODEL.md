# C09 witness threat model

Status: `NON-OPERATIONAL / OWNER_DECISION_REQUIRED`

## Protected property

An older mutually consistent Kernel+Identity snapshot must be detected before another protected operation is accepted. Availability is secondary to integrity: uncertainty stops protected operations.

## In scope

- coordinated, Kernel-only and Identity-only rollback;
- crash at every local/witness/finalization boundary;
- replay, concurrent writers, conflicting successors and gaps;
- malicious future-sequence insertion and epoch fork;
- stale backup, restore-token replay and unauthorized reset;
- compromised operational cloud write credential;
- object versions, noncurrent versions and delete markers;
- witness outage and stale/inconsistent local checkpoints.

## Trust assumptions and limits

- Provider API semantics, availability and account isolation are trusted only after live verification.
- Record authentication and Owner restore authorization are independently custodied from the operational writer and both local stores.
- Provider/billing/project administrators cannot be inside the ordinary Kernel or Identity service roles.
- Retention protection must cover the complete rollback-detection horizon. Expired retention permits later deletion and destroys the guarantee unless records are re-anchored to a still-protected independent authority.
- Cloud-writer compromise alone can cause denial of service by inserting invalid objects; it cannot create an authenticated record. Cloud-admin plus signing-key compromise, provider failure, account deletion and compelled provider action are outside the claimed guarantee.
- GCS/AWS immutable retention protects versions, not uniqueness or chain correctness. S3 explicitly permits new versions and delete markers above locked versions; GCS object-versioning can make a retained live version noncurrent. The verifier must inspect versions, not only the current object.

## Privacy

Records contain deployment-scoped opaque identifiers and commitments only. No case ID, name, tax year tied to a person, document, amount, extracted field, credential or taxpayer data is permitted. Provider logs therefore expose timing, volume and opaque deployment/operation correlation only.

## Security outcome

The design detects rollback under its stated independent-authority assumptions. It does not eliminate denial of service, does not prove a cloud provider's internal behavior, and does not establish C09 operational acceptance.
