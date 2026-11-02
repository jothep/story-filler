# Story Filler — infrastructure and delivery case study

A Māori vocabulary application used to explore container delivery, Kubernetes, and a move to managed cloud services. Originally a course project, it now provides a recent, hands-on infrastructure example alongside my professional experience in enterprise environments.

**[Application URL](https://jothep.github.io/story-filler/)** · **[Engineering case study](docs/engineering-case-study.md)** · **[Local platform lab](docs/local-platform-lab.md)** · **[Verification record](docs/verification.md)**

## Start here

This is the `jothep/story-filler` publication repository. It carries forward 185 sanitised historical commits plus four preparation commits: a 189-commit migration baseline. The [migration record](docs/repository-migration.md) separates new-repository checks from evidence collected in the former private repository.

For a short review, read the [case study](docs/engineering-case-study.md): the constraints, decisions, trade-offs, and boundaries of what has been demonstrated. The source and dated evidence are linked throughout.

The application provides stories with drag-and-drop vocabulary, illustrations, pronunciation audio, and Django administration. Its value as a portfolio project is the infrastructure around that workload: choosing an appropriate operating model, separating persistent state from compute, and making delivery repeatable.

## Current deployment

```mermaid
flowchart LR
    Pages[GitHub Pages: React assets] --> Browser
    Browser -->|HTTPS API| Run[Cloud Run: Django and Gunicorn]
    Run -->|PostgreSQL over TLS| Neon[(Neon PostgreSQL)]
    Run -->|Media storage API| GCS[Google Cloud Storage]
    Browser -->|Public image and audio URLs| GCS
```

- **Frontend:** React/Vite, built and published through GitHub Pages artifacts.
- **Backend:** a non-root container on Cloud Run, with Gunicorn and WhiteNoise.
- **Persistent state:** PostgreSQL on Neon; public learning media in GCS.
- **Infrastructure:** Terraform manages Cloud Run, its runtime service account, Artifact Registry, and public invocation permission. Other setup dependencies remain outside this Terraform configuration.
- **Capacity choice:** Cloud Run is configured for **0–1 instances**, 1 vCPU and 512 MiB. This limits idle compute and scaling exposure for a small demonstration workload; cold starts and a low capacity ceiling are accepted trade-offs.

The [production architecture](docs/architecture-production-gcp.md) explains the live path. The local environments below show the development and orchestration work that preceded and supports it.

## Local engineering practice

The legacy `scripts/restore-volumes.sh` and `scripts/restore-volumes-ec2.sh` commands are disabled. They exit before touching services or data because the previous implementation could delete data before validating a backup. Their replacement requires an isolated restore exercise; see the [verification record](docs/verification.md#local-safety-review-2-november-2026). These scripts do not operate the current Cloud Run/Neon deployment.

These environments serve different purposes. The [local platform lab](docs/local-platform-lab.md) links their implementation, startup order and verification limits.

| Environment | Engineering work it exposes | Evidence boundary |
| --- | --- | --- |
| Development Compose | Source mounts and hot reload, service discovery, a shared Nginx entry point, separate database/media volumes, database readiness before application startup | Configuration reviewed; full container startup not revalidated in this review |
| Local Kubernetes | Deployments and Services, a PostgreSQL StatefulSet/PVC, media persistence, separate migration/admin Jobs, Secret references and a diagnostic Pod | Manifests in `Infra/` and the original migration account; cluster execution not repeated here |
| Production-style Compose | A multi-container, single-host packaging option with Gunicorn, static serving and a reverse proxy | An alternative implementation, not the current hosted service; HTTPS and recovery are not demonstrated |
| Earlier demo | A separate Django/MUI prototype with a story-list/full-text API, before the main application's paragraph and word-bank design | Preserved in `demo/`; its Compose file runs only PostgreSQL, and it is not a miniature copy of current production |

The Kubernetes work demonstrates practical concerns around state, network routing and operational tasks. The later managed-service deployment shows how the operating model changed for a small public workload; both stages are part of this case study.

## Engineering decisions worth reviewing

| Decision | Why it matters | Source and limitation |
| --- | --- | --- |
| Move database and media outside the application container | Container replacement does not require carrying local content between instances | [Storage configuration](backend/maori_story_project/settings.py); restore procedures have not been demonstrated |
| Give Terraform and application delivery different responsibilities | Terraform maintains service configuration; CI selects the application image | [Terraform lifecycle rule](terraform/main.tf), [backend workflow](.github/workflows/deploy-backend.yml); the image field is excluded from Terraform drift reconciliation |
| Publish the frontend independently | Static hosting removes a continuously running frontend service | [Pages workflow](.github/workflows/deploy-frontend.yml); the API URL is a build-time setting |
| Use a non-root backend image with locked runtime dependencies | Keep development tools out of the image and verify downloaded package hashes | [Dockerfile](backend/dockerfile), [dependency maintenance](backend/README.md); the base image is pinned by digest |
| Deploy the scanned image by digest, in source-history order | Prevent an older workflow from replacing a newer serving release | [Backend workflow](.github/workflows/deploy-backend.yml), [release checks](scripts/cloud_run_release.py); the lock covers this workflow's deployment and verification |
| Verify the release and keep credentials out of source | Make publication and delivery checks explicit | [Secret scan](.github/workflows/secret-scan.yml), [API smoke check](scripts/smoke-check.py); see dated execution status below |

## What has actually been demonstrated

The [verification record](docs/verification.md) separates **implemented**, **deployment verified**, and **planned** work.

- **Review batches published, 2 November 2026:** [frontend run 41404713288](https://github.com/jothep/story-filler/actions/runs/41404713288) and [backend run 41404713244](https://github.com/jothep/story-filler/actions/runs/41404713244) publish the fourth maintenance batch on top of the safety, dependency and frontend lifecycle fixes. The final pre-release suite passed 159 tests, with separate browser and container checks. The [verification record](docs/verification.md) gives exact commits, scope and remaining findings.
- **New frontend deployment verified, 28 September 2026:** [Pages run 36363233923](https://github.com/jothep/story-filler/actions/runs/36363233923) deployed `1713b97` at `/story-filler/`. Chrome loaded the menu and story 1 text/image; full gameplay and audio playback were not checked. New-repository credential scans and CodeQL workflow runs also completed; see the [verification record](docs/verification.md#new-repository-28-september-2026).
- **New backend deployment verified, 28 September 2026:** [run 36363802780, attempt 2](https://github.com/jothep/story-filler/actions/runs/36363802780/attempts/2) passed tests, image scanning, deployment and API smoke verification. At that verification, revision `maori-story-backend-00028-gdm` served image `1713b97` with 100% traffic; runtime configuration and identity were preserved.
- **Pre-migration deployment verified, 27 September 2026:** the public frontend rendered a story; story/configuration APIs, sampled GCS media, and administrator login worked. The updated frontend and backend pipelines subsequently completed deployment, including the backend's image scan and public API smoke check.
- **Implemented:** Terraform configuration, Kubernetes manifests, backend and frontend delivery workflows, basic automated tests, image scanning, and CodeQL configuration.
- **Publication migration:** credentials were rotated and reachable Git history was cleaned. The former repository remains private because old commit content was still retrievable there. This new repository starts from the cleaned baseline; old Actions runs and aggregate counts are historical evidence, not new-repository runs. The owner made the new repository public on **28 September 2026**; the former repository remains private. See the [migration record](docs/repository-migration.md) for completed checks and their scope.
- **CI authentication:** the backend workflow retains the existing service-account JSON key method through the `GCP_CREDENTIALS` GitHub Actions secret. The owner configured that secret manually, and authentication succeeded in the new backend release; this migration does not change the authentication model.
- **Not demonstrated:** sustained availability or latency targets, load capacity, automatic rollback, database restore drills, a complete observability system, or a reproducible billing total of zero.

Backend tests use SQLite, not Neon. Frontend tests mock HTTP and audio. In the fourth maintenance batch, formatting and backend lint become required checks, with Django-aware analysis and regression tests for the lint configuration. CodeQL analysis remains advisory; the backend Trivy gate blocks fixable HIGH/CRITICAL findings. Frontend production dependencies must pass `npm audit`; the full frontend toolchain blocks HIGH/CRITICAL findings and currently retains moderate ESLint-chain advisories. The secret scan is a separate workflow, not a dependency of deployment. Dated results and remaining work are in the [verification record](docs/verification.md).

## Dependency and delivery maintenance

- **Backend:** edit direct dependencies in `backend/requirements.in` and `backend/requirements-dev.in`, then regenerate their hash-locked `.txt` files. The production image installs only the runtime lock. See the [backend guide](backend/README.md) for the Python 3.13 commands.
- **Frontend:** use Node 24 and `npm ci`. Review `package.json` and `package-lock.json` together. Nginx serves the optional local production containers; the hosted frontend still uses GitHub Pages. See the [frontend guide](frontend/README.md).
- **Terraform:** commit the provider lock file; keep state and private inputs ignored. [Local validation](terraform/README.md#provider-versions-and-local-validation) disables the remote backend.
- **Delivery:** pull requests run checks without deployment credentials. Main-branch backend releases build and scan once, push a uniquely tagged image, and pass its digest to the deployment job. Before updating Cloud Run, that job compares the candidate with the currently serving source commit. Unknown or conflicting release metadata stops automatic deployment. [Release maintenance](scripts/README.md) describes the checks and recovery from a refused release.

Package locks, image digests and pinned workflow actions make selected inputs reviewable. Registry availability, hosted runner updates and explicit operating-system package updates still affect a rebuild. Update pins deliberately and repeat tests and security checks; a passed scan is dated evidence.

## Read the story

1. [Original Medium article: the migration from local Kubernetes to managed services](https://medium.com/@shelldry325/from-on-premises-kubernetes-to-zero-cost-serverless-architecture-a-practical-guide-to-cloud-70e68304e835).
2. [Follow-up article draft: operating the migration](docs/articles/02-operating-the-migration.md). This continues the first article's delivery and security theme; it is not yet published on Medium.
3. [Architecture and historical implementation index](docs/ARCHITECTURE.md).
4. [Legacy delivery-history snapshot](docs/evidence/README.md): 198 retained Actions runs across 132 source commits, comprising 126 successes and 72 failures. These count workflow runs in the former repository, not deployments or activity in this repository.

The original article's “zero-cost” framing describes the project's cost objective. This repository does not claim a verified current monthly bill, unlimited free usage, or enterprise high availability. Older deployment and planning documents are supporting historical material; use the current architecture and verification record for current claims.

## Explore locally

Docker with Compose is required for this development path. It uses a separate local PostgreSQL database and local media storage. This startup path still needs a fresh container run, including the non-root user's write access to source mounts and media volumes; see the [local lab's reproduction gaps](docs/local-platform-lab.md#local-filesystem-permissions).

```bash
python3 scripts/init-local-env.py
docker compose -f docker-compose.dev.yml up --build
```

The generator creates an ignored `.env` with random local credentials and refuses to overwrite an existing file. Open `http://localhost/story-filler/` after the services start. A fresh database contains no stories; create an administrator and add content:

```bash
docker compose -f docker-compose.dev.yml exec backend python manage.py createsuperuser
```

Enter credentials interactively, then use `/admin/`. Production credentials and private backups are not part of the repository. Compose configuration parsing has been checked; see the verification record for the status of a full container startup.

## Repository map

| Path | Purpose |
| --- | --- |
| [`backend/`](backend/) | Django API, administration, models, and basic tests |
| [`frontend/`](frontend/) | React application, component tests, Pages build |
| [`terraform/`](terraform/) | Current GCP infrastructure configuration and bootstrap boundaries |
| [`Infra/`](Infra/) | Earlier Kubernetes manifests and operational Jobs |
| [`demo/`](demo/) | Separate earlier Django/MUI prototype |
| [`.github/workflows/`](.github/workflows/) | Delivery and security workflows |
| [`scripts/`](scripts/) | Private local configuration generation and public API verification |
| [`docs/engineering-case-study.md`](docs/engineering-case-study.md) | Decisions, alternatives, and evidence for portfolio review |

For security scope and reporting, see [SECURITY.md](SECURITY.md).
