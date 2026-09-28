# Repository migration: Story Filler

Migration started on **28 September 2026**. This record separates carried-forward work from checks performed for the new repository. The new repository's frontend and backend releases have both succeeded at source revision `1713b97`. The owner made the repository **public on 28 September 2026**; the former repository remains private.

## Publication target and retained history

The new repository is [`jothep/story-filler`](https://github.com/jothep/story-filler), with public name **Story Filler** and frontend target [`https://jothep.github.io/story-filler/`](https://jothep.github.io/story-filler/).

Its starting point is cleaned legacy commit `04fa234`: **185 preserved historical commits plus four preparation commits, totalling 189**. The first migration commit, `1713b97ea6264c50c3321ed3fdd164b594cff5ed`, brings the checked release history to **190 commits**. Later documentation commits are additional to that dated snapshot; a newer documentation HEAD is not evidence that the application image or Pages artifact was rebuilt. The release evidence below remains attached to `1713b97`. Credential removal changed historical commit IDs while retaining authorship and timestamps; 185 and 189 are not separate bodies of work to be added together.

The former `jothep/maori-story-fill` repository remains private. A fresh clone of its rewritten reachable history passed scanning, but an old sensitive document was still retrievable there by its old commit ID. The new repository carries forward only the cleaned history. This approach does not claim deletion of cached or external copies from the former repository. Credentials and private backups are not public evidence.

## Why the historical commits remain

The cleanup rewrote sensitive content throughout Git history with `git-filter-repo`; it preserved the project's development sequence instead of discarding commits that also contained useful code. The original 185 commits therefore have rewritten equivalents. Their commit IDs changed, while authorship, timestamps and mapped parent relationships were retained.

The post-publication anonymous clone at `805c164` contained all 185 rewritten commit objects and none of the 185 original objects. Current files and all reachable history passed the recorded rule and known-value checks. See the [anonymous verification record](verification.md#anonymous-verification-after-publication) for the snapshot and its limits. This evidence concerns the new repository; it does not claim erasure of retained objects in the former private repository.

## What moves and what stays

| Item | Migration choice | Evidence boundary |
| --- | --- | --- |
| Repository and public app name | `jothep/story-filler`, Story Filler | A new repository does not inherit GitHub Actions runs or Pages settings |
| Maintained frontend | Vite base `/story-filler/`; router and error recovery use Vite's base | Local checks and the new Pages workflow passed; Chrome menu-to-story rendering was checked on 28 September |
| Development Compose | Shared Nginx origin; frontend at `/story-filler/`, API at `/api/` | Configuration parsing does not verify container startup or writable volumes |
| Production-style Compose | Nginx strips `/story-filler/` before forwarding to `serve` | Source configuration; no fresh container execution claimed |
| Manual/Kubernetes frontend image | Nginx serves the build beneath `/story-filler/` with SPA fallback | Current Dockerfile/configuration fixed; historical manifest image tags are not rebuilt images |
| Earlier prototype | Retains root URL `http://localhost:5173/` and its separate host API | Historical implementation, not the maintained application's deployment contract |
| Cloud infrastructure | Reuse the existing Cloud Run service, registry, runtime account, database and storage | Legacy resource names remain identifiers, not incomplete branding work |
| CI authentication | Retain the service-account JSON key method through `GCP_CREDENTIALS` and `credentials_json` | Owner configured the new repository secret; backend run 36363802780, attempt 2, verified authentication, push and deployment |

The original Kubernetes illustration, earlier manifests and article remain historical material. Their names, resource IDs and original design claims are not silently rewritten into evidence for the new deployment.

The owner configured a JSON key for the existing service account in the new repository's GitHub Actions secret named `GCP_CREDENTIALS`. GitHub does not transfer that secret with Git history. No key is included in this repository, its examples or evidence. Authentication through `credentials_json` succeeded in the new backend release. Workload Identity Federation remains a possible later improvement; this migration did not introduce OIDC or change IAM roles.

Delivery ownership has moved to the new repository. The former repository's backend and frontend deployment workflows were disabled manually after the new releases succeeded, preventing them from continuing to publish the shared Cloud Run service or update the legacy Pages application. Historical run records remain in place; the other legacy workflows were not changed.

The backend CORS origin for Pages remains `https://jothep.github.io`: the repository subpath is not part of an HTTP origin. API paths and media object URLs do not gain the frontend's repository prefix.

## Legacy evidence

The [aggregate snapshot](evidence/README.md) records **198 retained Actions runs across 132 distinct source commits**, with **126 successes and 72 failures**, in the former private repository. These are workflow completion counts, not deployment counts or new-repository activity.

Old Actions links in the [verification record](verification.md) deliberately keep their original repository and run IDs. They may require access to the private repository. The public aggregates describe their scope without publishing raw private API responses or presenting historical runs as new runs.

The last pre-migration backend observation was image `7d80196` on Cloud Run revision `maori-story-backend-00027-bzj`, receiving 100% of traffic on 27 September. The new workflow retains that authentication method. The earlier frontend Pages release was `a309a63` at the old repository path. Neither proves the new Pages path or the new repository's secret configuration.

## New-repository acceptance record

The following new-repository checks were completed on **28 September 2026** for source revision [`1713b97ea6264c50c3321ed3fdd164b594cff5ed`](https://github.com/jothep/story-filler/commit/1713b97ea6264c50c3321ed3fdd164b594cff5ed). Implementation-only limitations and the subsequent visibility change remain explicit below. Old repository run IDs are not used as substitutes.

| Check | Result | Evidence and limits |
| --- | --- | --- |
| Frontend lint, six component tests and production build | Passed locally, 28 September 2026 | `npm run lint`, `npm test -- run`, `npm run build`; all three HTML asset/favicon references use `/story-filler/` and resolve to generated files |
| Compose and frontend route configuration | Passed static checks, 28 September 2026 | Three Compose variants parsed using temporary random local inputs; dev same-origin API, prod prefix stripping and current Nginx image/Ingress paths reviewed; no container-runtime claim |
| New repository full-history credential scan | Passed | [Run 36363234688](https://github.com/jothep/story-filler/actions/runs/36363234688) and [run 36363233992](https://github.com/jothep/story-filler/actions/runs/36363233992) completed successfully; pattern-based scanning is not proof that every possible secret is absent |
| New frontend Pages release | Passed | [Run 36363233923](https://github.com/jothep/story-filler/actions/runs/36363233923) completed lint, tests, build and Pages deployment at `1713b97` |
| Browser check of the new Pages path | Passed | Chrome loaded `https://jothep.github.io/story-filler/`; selecting story 1 displayed story text and an image. No full game walkthrough or audio-playback check |
| New repository CodeQL workflow | Completed successfully | [Run 36363233980](https://github.com/jothep/story-filler/actions/runs/36363233980); analysis remains advisory and workflow success does not mean zero alerts |
| New backend release using `GCP_CREDENTIALS` | Passed, attempt 2 | [Run 36363802780](https://github.com/jothep/story-filler/actions/runs/36363802780/attempts/2): 11 backend tests, six offline smoke-check tests, authentication, build, Trivy gate, push, deployment and public API smoke check succeeded |
| Deployed backend state | Verified | Ready revision `maori-story-backend-00028-gdm` received 100% of traffic, with image tag `1713b97ea6264c50c3321ed3fdd164b594cff5ed`. All environment entries, runtime service account and runtime specification apart from the image were unchanged |
| Backend release log review | No findings or known-value matches | 23 archive files, 523,552 bytes; Gitleaks 8.30.1 and checks for 20 known values plus the new key's JSON, PEM, encoded variants and 25 PEM line fragments. No credential values or raw logs are published |
| Independent public API smoke check | Passed | Public story list/detail and configuration reads; no writes, media playback or load test |
| Fresh-clone source and history review | Passed within the checked scope | 214 current tracked files, 190 reachable commits and 682 reachable blobs; Gitleaks found no findings and a supplemental search found zero matches for 20 known values |
| Selected old-content lookups in the new repository | Not retrievable by the checked requests | The old-commit query returned HTTP 422; the old-document query returned HTTP 404. This does not establish deletion from the former repository or external copies |
| Legacy deployment handover | Completed | The former repository's `deploy-backend.yml` and `deploy-frontend.yml` workflows were confirmed `disabled_manually`; their history is retained. Other workflows were left unchanged |
| Repository visibility | Public, 28 September 2026 | The owner changed the visibility. An unauthenticated GitHub repository API request returned HTTP 200 with `private: false`; the former private repository returned HTTP 404 to an unauthenticated request |

The [backend verification summary](evidence/backend-migration-verification.json), recorded at **2026-09-28 00:58 UTC**, contains run/step results, test counts, boolean configuration comparisons and scan counts. It contains no runtime environment values or key material. A clean scan covers those inputs and rules; it does not prove absence of all unknown secrets.

Local frontend checks reused the installed dependency tree; installed package versions matched the committed lockfile. They ran on Node 25.6.1 and did not repeat a clean `npm ci` or the workflow's Linux environment. Temporary Compose inputs were random local values, were not displayed and were removed after parsing.

A Pages menu-to-story check does not establish nested-route refresh support, a complete game walkthrough, media playback, or an availability target. Fresh Compose/Kubernetes execution, filesystem ownership, recovery drills, and initial cloud bootstrap remain the limitations described in the [local lab](local-platform-lab.md) and [architecture](architecture-production-gcp.md).
