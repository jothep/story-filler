# Verification record

Legacy deployment reviewed on **27 September 2026**; repository migration begun on **28 September 2026**. This record distinguishes repository implementation from observations of a deployed service. A successful check applies to its stated scope and date, not to continuous uptime or all future versions.

The run links and release observations on this page belong to the former private `jothep/maori-story-fill` repository. They do not establish that `jothep/story-filler` has run the same workflows. See the [migration record](repository-migration.md) for new-repository checks and the [public aggregate snapshot](evidence/README.md) for historical activity counts.

## Pre-migration live deployment baseline

| Check | Result | Scope |
| --- | --- | --- |
| GitHub Pages in a browser | Passed | Menu loaded from the API; opening a story rendered its illustration, first paragraph and word bank |
| Story list and detail API | HTTP 200 | One story, eight paragraphs and eleven words were observed |
| Configuration API | HTTP 200 | JSON configuration was returned |
| Sample GCS image and audio | HTTP 200 | One image and one audio object were readable; complete audio playback was not tested by this probe |
| Administrator authentication | Passed | Login and logout were verified; the owner also confirmed login |
| Credential rotation | Passed | New database credentials connected; previous credentials were rejected. Cloud Run values matched the private rotation file |
| Cloud Run revision | `maori-story-backend-00026-phc`, 100% traffic | Configuration-only credential update; it retained the previously deployed application image |

The browser reported a normal autoplay restriction before user interaction. These checks do not establish a complete game walkthrough, accessibility compliance, mobile coverage, a performance target, or an availability percentage.

## Local verification of publication changes

| Check | Result | Limitation |
| --- | --- | --- |
| Backend tests | 11 passed | SQLite and local media; not PostgreSQL/GCS integration tests |
| Frontend lint | Passed | Current checked-out source and installed dependencies |
| Frontend tests | 6 passed | Component tests with mocked HTTP/audio |
| Frontend production build | Passed | Does not itself prove the artifact was deployed |
| API smoke-check tests | 6 passed | Covers response validation and retry/error behavior using mocks |
| API smoke check against production | Passed | Public story and configuration reads; no writes or media playback |
| Compose configuration | Three variants parsed | Docker daemon was unavailable; a full local container startup/build was not performed |
| Local routing review | Two corrections implemented | Development API requests now use Nginx's shared origin; production-style Compose strips the frontend base prefix. No container-level routing verification was performed |
| Terraform formatting and validation | Passed | No plan or apply was performed |
| Terraform remote state inventory | Read successfully | The configured GCS backend tracks exactly the four declared resource addresses; this does not prove absence of drift or successful recovery |
| Private local configuration generator | Passed | Owner-only permissions, no credential output, and refusal to overwrite an existing file |
| Credential scan of the portfolio candidate | Gitleaks 8.30.1: no findings | Current files and all 187 reachable commits at `a309a63`; a fresh remote clone also passed. Later revision scans are linked below |
| Known-value search of the portfolio candidate | No residual matches for 16 known values across 650 blobs | Supplemental exact-value check at `a309a63`; does not identify unknown secrets |

The history-scan workflow and updated backend delivery workflow have now passed in GitHub Actions. Their revision-specific results are recorded below, separately from local checks.

## Delivery evidence

Historical successful runs establish that the earlier delivery paths were used:

- [Backend delivery](https://github.com/jothep/maori-story-fill/actions/runs/25036589237)
- [Frontend delivery](https://github.com/jothep/maori-story-fill/actions/runs/25902475995)
- [CodeQL workflow run](https://github.com/jothep/maori-story-fill/actions/runs/35554033791) — this records workflow completion, not a claim that no alerts exist.

These runs refer to commits from before credential-related history rewriting. They do **not** verify the rewritten commit IDs or the new publication changes. Old-to-new commit mappings are retained privately for audit; private archives and credentials are not portfolio attachments.

## Legacy publication-preparation release runs

| Source revision | Workflow | Result |
| --- | --- | --- |
| `a309a63` | [Frontend delivery](https://github.com/jothep/maori-story-fill/actions/runs/36298824448) | Passed lint, tests, build and Pages deployment |
| `a309a63` | [Git-history credential scan](https://github.com/jothep/maori-story-fill/actions/runs/36298820622) | Passed |
| `a309a63` | [Initial backend release](https://github.com/jothep/maori-story-fill/actions/runs/36298822546) | Tests and image build passed; Trivy blocked 12 fixable HIGH findings before image push or service update |
| `7d80196` | [Git-history credential scan](https://github.com/jothep/maori-story-fill/actions/runs/36299274040) | Passed |
| `7d80196` | [Backend release after remediation](https://github.com/jothep/maori-story-fill/actions/runs/36299274042) | Passed 11 backend tests, 6 smoke-check tests, image build/scan, image push, Cloud Run deployment and public API smoke check |

The blocked findings comprised ten Pillow advisories and two libraries bundled inside pip. Pillow was updated from 12.2.0 to 12.3.0. The final runtime image now removes pip, its ensurepip seed and wheel archives after installation and dependency checks; the builder retains installation tools. Adding unrelated top-level packages would not replace pip's bundled copies. The scan policy and its severity threshold were not relaxed.

In a separate local Python environment with pip and ensurepip absent, application imports and all 11 backend tests passed. The subsequent Linux image scan and deployment also passed in the workflow above. No database schema change is included. Backend lint remains advisory; workflow success does not mean every lint check passed.

After deployment, Cloud Run reported revision `maori-story-backend-00027-bzj` receiving 100% of traffic, with image tag `7d8019603925de68306585f701e5eb5a7442f854`. The database and signing-key values still matched the private rotated configuration. This application release supersedes the configuration-only `00026-phc` baseline above. Passing the configured Trivy gate means no blocking findings under that run's policy and database, not that the image has no vulnerabilities.

## Legacy publication state and new repository

The former `jothep/maori-story-fill` repository remains **private**. The cleaned history was pushed with an exact force-with-lease, and a fresh remote clone passed its full reachable-history scan. The original 185 commits' authorship and timestamps were retained; credential cleanup changed commit IDs. The owner's original staged working draft was not included in the published branch.

A separate GitHub contents-API check found that the previous sensitive document is still retrievable through its old commit ID, outside the new reachable history. That retained content prevents making the former repository public under the owner's publication requirement. A support request has been prepared but not sent. GitHub documents that force-pushing alone may leave cached views accessible and that Support assistance is limited; see [removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository). No claim is made that all historic copies have been erased. The chosen publication path is a separate `jothep/story-filler` repository, starting from the 189-commit clean baseline (185 preserved historical commits plus four preparation commits). Its own acceptance evidence is tracked in the migration record, rather than relabelling the old runs.

## Implemented but not fully proven

- Terraform declares the registry, runtime service account, Cloud Run service and public invoker binding, and those four addresses were confirmed in remote state. No clean-room recreation of the whole environment has been demonstrated; Neon, media/state buckets, IAM setup and GitHub configuration are prerequisites outside that resource set.
- Kubernetes manifests preserve the earlier deployment design. The original article reports the historical exercise; the current review did not redeploy a cluster.
- The [local platform lab](local-platform-lab.md) covers Compose, local Kubernetes and the earlier demo separately. The current machine has local cluster tooling, but Colima is stopped. Neither the existing clusters nor other local projects were started or modified. The current NGINX image source now supports `/story-filler/`, but the historical Kubernetes image tags still need replacement with a rebuilt image before a fresh reproduction; the demo has no dedicated dependency lock or substantive tests.
- CodeQL and image scanning are configured. Scan results depend on definitions, scope and advisory settings; no “zero vulnerabilities” claim is made.
- ORM prefetching and image processing exist in code. The previously stated percentage improvements have no reproducible benchmark included here.

The new repository retains the service-account JSON key authentication method used by the old successful releases. The owner configures `GCP_CREDENTIALS` manually as a GitHub Actions secret. Workload Identity Federation is not implemented. The old runs do not verify the new repository's secret setup or delivery; see the migration record for its execution status.

## Planned, not claimed as delivered

Workload Identity Federation, Secret Manager integration, application-test PR gates, automated rollback, a database/media restore exercise, measured SLOs, load testing and billing evidence are possible next steps. There is no need to implement all of them to explain the existing architecture honestly.
