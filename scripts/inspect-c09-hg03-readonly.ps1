[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$gcloud = 'C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd'
$project = 'ai-tax-agent-507813'
$bucket = 'ai-tax-agent-c09-witness-test-507813'
$writer = 'c09-witness-test@ai-tax-agent-507813.iam.gserviceaccount.com'
$reader = 'c09-witness-reader@ai-tax-agent-507813.iam.gserviceaccount.com'
if (-not (Test-Path -LiteralPath $gcloud -PathType Leaf)) { throw 'Pinned gcloud executable is unavailable.' }
& $gcloud config get project
& $gcloud storage buckets describe "gs://$bucket" --format=json
& $gcloud storage buckets get-iam-policy "gs://$bucket" --format=json
& $gcloud projects get-iam-policy $project --format=json
& $gcloud iam roles list --project=$project --format=json
& $gcloud iam service-accounts describe $writer --project=$project --format=json
& $gcloud iam service-accounts describe $reader --project=$project --format=json
& $gcloud iam service-accounts get-iam-policy $writer --project=$project --format=json
& $gcloud iam service-accounts get-iam-policy $reader --project=$project --format=json
& $gcloud iam service-accounts keys list --iam-account=$writer --project=$project --managed-by=user --format=json
& $gcloud iam service-accounts keys list --iam-account=$reader --project=$project --managed-by=user --format=json
& $gcloud iam workload-identity-pools list --location=global --project=$project --format=json
