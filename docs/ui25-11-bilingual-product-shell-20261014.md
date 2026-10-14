# UI25-11 bilingual product-shell completion — 2026-10-14

Status: **TECHNICAL PASS / OWNER DEVICE ACCEPTED (OWNER-REPORTED)**

Baseline: `a246e392e57c5a9e020892821cd8c30edf0ef675`

## Admission and policy

Authenticated admission capacity was 97% five-hour and 86% weekly remaining. The existing `BOUNDED (15/5)` Limit Guard returned `RUN_OPERATION_FITS` while preserving the mandatory 15-point reserve.

The Owner policy `C09_NOT_ACCEPTED != PROJECT_EXECUTION_BLOCKED` was applied without altering the frozen C01–C13 matrix. C09 remains OPEN / NOT ACCEPTED. This package changes only the fail-closed, read-only product dashboard copy and therefore does not depend on rollback acceptance, protected persistence, real case data, IPC activation or external transmission.

## Recovered branch conflict

The primary checkout `C:\Users\rezag\ai-agent-lab` remains clean on `d021-agent-case-provisioning` at `41554eb`, whose checkpoint predates the C09 policy. The existing `oi0002-identity-persistence` worktree is sixteen commits behind and contains unrelated local modifications/untracked files. Neither checkout was switched, reset, merged or modified. Work used a detached clean worktree from exact remote policy baseline `a246e39`; delivery is a fast-forward push to the authorized policy branch.

## Implemented bounded package

The German dashboard mode previously changed direction and navigation labels but retained Persian text in the page title, accessibility labels, overview cards, empty/fail-closed states and every product tab. The product shell now obtains all common and tab-specific copy from the selected locale:

- complete German and Persian shell/overview/tab copy;
- localized accessibility and connection-state labels;
- language preserved in case-selection links;
- localized disabled two-stage approval presentation;
- unchanged fail-closed source behavior and inert ELSTER submission boundary.

The isolated functional-test console remains test-only and is not promoted as product data or a production persistence path.

## Verification

- Initial focused collection without `PYTHONPATH=src`: no tests executed; import failed. The documented environment path was then applied.
- Focused dashboard suite: `10 passed`, exit 0.
- Relevant UI and launcher regression: `84 passed`, exit 0.
- New negative coverage visits every product tab in German mode, permits only the intentional Persian language-switch label and rejects all other Persian-script copy leakage.

No Owner visual/device PASS is claimed. No real case resolver, protected operation, submission route, IPC implementation, database, scheduler or alternate authority was added.

## Exact continuation

The next executable UI25-11 action requiring no backend gate is Owner hands-on phone/desktop review of the German LTR and Persian RTL product shell. Engineering work that needs real case persistence remains gated independently; C09 alone must not block other explicitly authorized synthetic/navigation/localization packages.

## Owner hands-on acceptance — 2026-10-14

The Owner explicitly confirmed completing hands-on UI25-11 review on desktop and mobile, in both German and Persian, and accepting all five criteria: German LTR without Persian copy leakage; Persian RTL; language persistence through navigation; mobile layout/navigation in both languages; and continued inert approval/ELSTER and fail-closed synthetic-vs-real presentation. This is Owner-attested manual acceptance, not a separately captured device automation trace. UI25-11 is accepted for its bounded bilingual product-shell scope only; no live case persistence, real taxpayer data, OI-0002/C09, or submission release is implied.

Next: admit the next independent UI25 package only after fresh authenticated Limit Guard measurement, then implement/test and update canonical checkpoint. The prior 'Owner acceptance outstanding' statements above are historical pre-acceptance observations.
