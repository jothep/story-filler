# Repository migration: Story Filler

Migration started on **28 September 2026**. This record separates carried-forward work from checks performed for the new repository.

## Publication target and retained history

The new repository is [`jothep/story-filler`](https://github.com/jothep/story-filler), with public name **Story Filler** and frontend target [`https://jothep.github.io/story-filler/`](https://jothep.github.io/story-filler/).

Its starting point is cleaned legacy commit `04fa234`: **185 preserved historical commits plus four preparation commits, totalling 189**. Migration commits are added after that baseline. Credential removal changed historical commit IDs while retaining authorship and timestamps; 185 and 189 are not separate bodies of work to be added together.

The former `jothep/maori-story-fill` repository remains private. A fresh clone of its rewritten reachable history passed scanning, but an old sensitive document was still retrievable there by its old commit ID. The new repository carries forward only the cleaned history. This approach does not claim deletion of cached or external copies from the former repository. Credentials and private backups are not public evidence.

## What moves and what stays

| Item | Migration choice | Evidence boundary |
| --- | --- | --- |
| Repository and public app name | `jothep/story-filler`, Story Filler | A new repository does not inherit GitHub Actions runs or Pages settings |
| Maintained frontend | Vite base `/story-filler/`; router and error recovery use Vite's base | Lint, component tests and asset build are local checks; Pages publication needs a new run |
| Development Compose | Shared Nginx origin; frontend at `/story-filler/`, API at `/api/` | Configuration parsing does not verify container startup or writable volumes |
| Production-style Compose | Nginx strips `/story-filler/` before forwarding to `serve` | Source configuration; no fresh container execution claimed |
| Manual/Kubernetes frontend image | Nginx serves the build beneath `/story-filler/` with SPA fallback | Current Dockerfile/configuration fixed; historical manifest image tags are not rebuilt images |
| Earlier prototype | Retains root URL `http://localhost:5173/` and its separate host API | Historical implementation, not the maintained application's deployment contract |
| Cloud infrastructure | Reuse the existing Cloud Run service, registry, runtime account, database and storage | Legacy resource names remain identifiers, not incomplete branding work |
| CI authentication | Retain the service-account JSON key method through `GCP_CREDENTIALS` and `credentials_json` | Owner manually configures the new repository secret; a new run must verify authentication, push and deployment |

The original Kubernetes illustration, earlier manifests and article remain historical material. Their names, resource IDs and original design claims are not silently rewritten into evidence for the new deployment.

The owner sets the existing service-account JSON key in the new repository's GitHub Actions secret named `GCP_CREDENTIALS`. GitHub does not transfer that secret with Git history. The key is not written into this repository, its examples or evidence. Workload Identity Federation is deferred; no OIDC or IAM change is part of this migration.

The backend CORS origin for Pages remains `https://jothep.github.io`: the repository subpath is not part of an HTTP origin. API paths and media object URLs do not gain the frontend's repository prefix.

## Legacy evidence

The [aggregate snapshot](evidence/README.md) records **198 retained Actions runs across 132 distinct source commits**, with **126 successes and 72 failures**, in the former private repository. These are workflow completion counts, not deployment counts or new-repository activity.

Old Actions links in the [verification record](verification.md) deliberately keep their original repository and run IDs. They may require access to the private repository. The public aggregates describe their scope without publishing raw private API responses or presenting historical runs as new runs.

The last pre-migration backend observation was image `7d80196` on Cloud Run revision `maori-story-backend-00027-bzj`, receiving 100% of traffic on 27 September. The new workflow retains that authentication method. The earlier frontend Pages release was `a309a63` at the old repository path. Neither proves the new Pages path or the new repository's secret configuration.

## New-repository acceptance record

At preparation time, the migration is implemented in source. Record each new workflow's source revision, run URL and result here after it executes. Do not reuse an old run ID as a substitute.

| Check | Status at preparation | Required evidence |
| --- | --- | --- |
| Frontend lint, six component tests and production build | Passed locally, 28 September 2026 | `npm run lint`, `npm test -- run`, `npm run build`; all three HTML asset/favicon references use `/story-filler/` and resolve to generated files |
| Compose and frontend route configuration | Passed static checks, 28 September 2026 | Three Compose variants parsed using temporary random local inputs; dev same-origin API, prod prefix stripping and current Nginx image/Ingress paths reviewed; no container-runtime claim |
| New repository full-history credential scan | Pending | New run URL and exact revision |
| New frontend Pages release | Pending | New run URL, `/story-filler/` menu/story rendering and asset loading |
| New backend release using `GCP_CREDENTIALS` | Pending | New run URL, authentication, image scan/push, Cloud Run revision and smoke check |
| Publication review | Pending | Clean reachable history and current content checked before public visibility |

Local frontend checks reused the installed dependency tree; installed package versions matched the committed lockfile. They ran on Node 25.6.1 and did not repeat a clean `npm ci` or the workflow's Linux environment. Temporary Compose inputs were random local values, were not displayed and were removed after parsing.

A Pages menu-to-story check does not establish nested-route refresh support, a complete game walkthrough, media playback, or an availability target. Fresh Compose/Kubernetes execution, filesystem ownership, recovery drills, and initial cloud bootstrap remain the limitations described in the [local lab](local-platform-lab.md) and [architecture](architecture-production-gcp.md).
