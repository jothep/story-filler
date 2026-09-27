# Verification record

Reviewed on **27 September 2026**. This record distinguishes repository implementation from observations of a deployed service. A successful check applies to its stated scope and date, not to continuous uptime or all future versions.

## Live deployment baseline

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
| Credential scan of the initial rewritten candidate | Gitleaks 8.30.1: no findings | The earlier candidate contained 186 commits; the final portfolio candidate must be rescanned after edits |
| Known-value search of the initial rewritten candidate | No residual matches for 16 known values | Supplemental exact-value check; does not identify unknown secrets |

The new history-scan workflow and deployment smoke-check step are implemented. Their GitHub Actions execution status will be recorded below after the final candidate is pushed and run. Local success is not presented as a completed CI deployment.

## Delivery evidence

Historical successful runs establish that the earlier delivery paths were used:

- [Backend delivery](https://github.com/jothep/maori-story-fill/actions/runs/25036589237)
- [Frontend delivery](https://github.com/jothep/maori-story-fill/actions/runs/25902475995)
- [CodeQL workflow run](https://github.com/jothep/maori-story-fill/actions/runs/35554033791) — this records workflow completion, not a claim that no alerts exist.

These runs refer to commits from before credential-related history rewriting. They do **not** verify the rewritten commit IDs or the new publication changes. Old-to-new commit mappings are retained privately for audit; private archives and credentials are not portfolio attachments.

**Final-candidate delivery status:** pending execution. This section will identify the candidate commit, workflow runs and resulting deployment separately from the baseline above.

## Publication state

The repository remains private while publication preparation is in progress. An isolated, rewritten history was scanned and backed up. Remote history replacement, fresh-clone scanning, checks for old remote references/cached sensitive content, and final visibility review are still required before the public release is described as complete.

## Implemented but not fully proven

- Terraform declares the registry, runtime service account, Cloud Run service and public invoker binding, and those four addresses were confirmed in remote state. No clean-room recreation of the whole environment has been demonstrated; Neon, media/state buckets, IAM setup and GitHub configuration are prerequisites outside that resource set.
- Kubernetes manifests preserve the earlier deployment design. The original article reports the historical exercise; the current review did not redeploy a cluster.
- The [local platform lab](local-platform-lab.md) covers Compose, local Kubernetes and the earlier demo separately. The current machine has local cluster tooling, but Colima is stopped. Neither the existing clusters nor other local projects were started or modified. The current Kubernetes image tags/base-path configuration need alignment before a fresh reproduction; the demo has no dedicated dependency lock or substantive tests.
- CodeQL and image scanning are configured. Scan results depend on definitions, scope and advisory settings; no “zero vulnerabilities” claim is made.
- ORM prefetching and image processing exist in code. The previously stated percentage improvements have no reproducible benchmark included here.

## Planned, not claimed as delivered

Workload Identity Federation, Secret Manager integration, application-test PR gates, automated rollback, a database/media restore exercise, measured SLOs, load testing and billing evidence are possible next steps. There is no need to implement all of them to explain the existing architecture honestly.
