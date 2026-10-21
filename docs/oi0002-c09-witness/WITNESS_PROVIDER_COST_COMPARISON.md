# C09 witness provider and cost comparison

Verified: 2026-10-21. No cloud call, account provisioning or paid activation occurred.

## Provider properties

| Property | Google Cloud Storage (Frankfurt `europe-west3`) | AWS S3 (Frankfurt `eu-central-1`) |
|---|---|---|
| Conditional create | `OFFICIALLY_VERIFIED`: `ifGenerationMatch=0` succeeds only when no live generation exists. [GCS preconditions](https://cloud.google.com/storage/docs/request-preconditions) | `OFFICIALLY_VERIFIED`: `If-None-Match: *`; first concurrent write succeeds, later writes fail. A current delete marker makes the key creatable again. [S3 conditional writes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html) |
| Read/list consistency | `OFFICIALLY_VERIFIED`: strong global object read-after-write and listing consistency. [GCS consistency](https://cloud.google.com/storage/docs/consistency) | `OFFICIALLY_VERIFIED`: strong read-after-write and list consistency in all regions. [S3 overview](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html#ConsistencyModel) |
| Immutable retention | `OFFICIALLY_VERIFIED`: locked bucket policy cannot be removed or shortened; object lock can prevent reduction/removal. A retained live version can still become noncurrent. [Bucket Lock](https://cloud.google.com/storage/docs/using-bucket-lock), [Object Retention Lock](https://cloud.google.com/storage/docs/object-lock) | `OFFICIALLY_VERIFIED`: Compliance mode prevents deletion by any user including root during retention, but protects versions and permits new versions/delete markers. [S3 Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html) |
| Operational-role restriction | `ASSUMPTION`: custom IAM role with create/read/list only; no delete, overwrite, retention-policy or project administration. Needs policy proof. | `ASSUMPTION`: IAM/bucket policy requires conditional PUT and denies delete/bypass/configuration to writer. Needs policy proof. |
| EU location | `OFFICIALLY_VERIFIED`: Frankfurt `europe-west3` appears in GCS regional pricing/location list. [GCS pricing](https://cloud.google.com/storage/pricing) | `OFFICIALLY_VERIFIED`: S3 is available in Europe (Frankfurt) `eu-central-1`; exact account/service availability still needs live confirmation. |
| Linux/Docker portability | `ASSUMPTION`: HTTPS JSON API/client libraries; no Windows dependency. | `ASSUMPTION`: HTTPS S3 API/client libraries; no Windows dependency. |

## Cost model

`ESTIMATE`: one 1 KiB record, one conditional PUT, and two read/list verification operations per protected event; no free tier, egress, KMS, audit-log, tax, minimum-charge or support-plan credit. GCS unit assumptions use the official example rates of USD 0.005/1,000 Class A and USD 0.0004/1,000 Class B plus about USD 0.020/GiB-month Standard storage. AWS uses typical public S3 Standard request/storage assumptions of USD 0.005/1,000 PUT, USD 0.0004/1,000 GET and USD 0.0245/GB-month for Frankfurt. Exact regional SKUs must be confirmed in each provider calculator before approval: `REQUIRES_LIVE_TEST`.

| Records/day | Annual records | GCS estimated first-year operations + average storage | S3 estimated first-year operations + average storage |
|---:|---:|---:|---:|
| 10 | 3,650 | about USD 0.02 | about USD 0.02 |
| 100 | 36,500 | about USD 0.21 | about USD 0.22 |
| 1,000 | 365,000 | about USD 2.16 | about USD 2.17 |

Audit logging, independent KMS/HSM signing and administration dominate these tiny object charges and are not priced here. Retention can make erroneous records and costs irreversible for the retention period.

## Assessment

GCS is the narrower preliminary recommendation because `ifGenerationMatch=0`, strong global listing and no S3-style delete markers simplify the verifier. This is a design preference, not deployment approval. Both require version enumeration, locked retention, separate administration/key custody and live adversarial verification. S3 remains viable but its delete-marker/current-version semantics require more careful policy and evidence handling.
